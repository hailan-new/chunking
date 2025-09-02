#!/usr/bin/env python3
"""
LLM-based智能标题检测器
考虑token限制和响应速度的优化实现
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class LLMHeadingDetector:
    """
    基于LLM的智能标题检测器
    
    特点：
    1. 批量处理以提高效率
    2. 考虑token限制，智能分批
    3. 缓存结果避免重复调用
    4. 回退到规则检测确保可靠性
    """
    
    def __init__(self, 
                 llm_client=None,
                 max_tokens_per_batch: int = 3000,
                 max_texts_per_batch: int = 20,
                 cache_enabled: bool = True):
        """
        初始化LLM标题检测器
        
        Args:
            llm_client: LLM客户端（如OpenAI、Claude等）
            max_tokens_per_batch: 每批次最大token数
            max_texts_per_batch: 每批次最大文本数
            cache_enabled: 是否启用缓存
        """
        self.llm_client = llm_client
        self.max_tokens_per_batch = max_tokens_per_batch
        self.max_texts_per_batch = max_texts_per_batch
        self.cache_enabled = cache_enabled
        self.cache = {} if cache_enabled else None
        
    def detect_headings_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        批量检测文本是否为标题
        
        Args:
            texts: 待检测的文本列表
            
        Returns:
            检测结果列表，每个元素包含 {'is_heading': bool, 'level': int, 'confidence': float}
        """
        if not texts:
            return []
        
        # 如果没有LLM客户端，回退到规则检测
        if not self.llm_client:
            logger.warning("No LLM client provided, falling back to rule-based detection")
            return self._fallback_rule_detection(texts)
        
        results = []
        
        # 智能分批处理
        batches = self._create_smart_batches(texts)
        
        for batch_texts, batch_indices in batches:
            try:
                batch_results = self._process_batch(batch_texts)
                
                # 将结果映射回原始索引
                for i, result in enumerate(batch_results):
                    original_index = batch_indices[i]
                    while len(results) <= original_index:
                        results.append(None)
                    results[original_index] = result
                    
            except Exception as e:
                logger.error(f"LLM batch processing failed: {e}")
                # 对失败的批次使用规则检测
                fallback_results = self._fallback_rule_detection(batch_texts)
                for i, result in enumerate(fallback_results):
                    original_index = batch_indices[i]
                    while len(results) <= original_index:
                        results.append(None)
                    results[original_index] = result
        
        # 确保所有位置都有结果
        for i in range(len(texts)):
            if i >= len(results) or results[i] is None:
                results.append(self._fallback_rule_detection([texts[i]])[0])
        
        return results[:len(texts)]
    
    def _create_smart_batches(self, texts: List[str]) -> List[Tuple[List[str], List[int]]]:
        """
        智能创建批次，考虑token限制和文本数量限制
        
        Args:
            texts: 文本列表
            
        Returns:
            批次列表，每个批次包含 (文本列表, 原始索引列表)
        """
        batches = []
        current_batch_texts = []
        current_batch_indices = []
        current_tokens = 0
        
        for i, text in enumerate(texts):
            # 估算token数（粗略估计：中文1字符≈1token，英文1词≈1token）
            estimated_tokens = len(text) + len(text.split()) // 2
            
            # 检查是否需要开始新批次
            if (len(current_batch_texts) >= self.max_texts_per_batch or
                current_tokens + estimated_tokens > self.max_tokens_per_batch):
                
                if current_batch_texts:
                    batches.append((current_batch_texts, current_batch_indices))
                    current_batch_texts = []
                    current_batch_indices = []
                    current_tokens = 0
            
            current_batch_texts.append(text)
            current_batch_indices.append(i)
            current_tokens += estimated_tokens
        
        # 添加最后一个批次
        if current_batch_texts:
            batches.append((current_batch_texts, current_batch_indices))
        
        return batches
    
    def _process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        处理单个批次
        
        Args:
            texts: 文本列表
            
        Returns:
            检测结果列表
        """
        # 检查缓存
        if self.cache_enabled:
            cache_key = self._get_cache_key(texts)
            if cache_key in self.cache:
                logger.debug(f"Cache hit for batch of {len(texts)} texts")
                return self.cache[cache_key]
        
        # 构建LLM提示
        prompt = self._build_prompt(texts)
        
        # 调用LLM
        start_time = time.time()
        response = self._call_llm(prompt)
        end_time = time.time()
        
        logger.info(f"LLM call took {end_time - start_time:.2f}s for {len(texts)} texts")
        
        # 解析响应
        results = self._parse_llm_response(response, len(texts))
        
        # 缓存结果
        if self.cache_enabled:
            self.cache[cache_key] = results
        
        return results
    
    def _build_prompt(self, texts: List[str]) -> str:
        """
        构建LLM提示
        
        Args:
            texts: 文本列表
            
        Returns:
            LLM提示字符串
        """
        prompt = """你是一个专业的文档结构分析专家。请分析以下文本片段，判断每个是否为标题，以及标题的层级。

判断标准：
1. 标题通常较短（一般不超过50字符）
2. 标题不以句号、问号、感叹号结尾
3. 标题可能包含编号（如"一、"、"（一）"、"1."等）
4. 标题描述章节、部分或主题
5. 列表项（如"1、代销机构依法注册..."）通常不是标题，而是内容

层级规则：
- 1级：一、二、三、等
- 2级：（一）、（二）、等（仅当内容很短且明显是小标题时）
- 3级：1、2、3、等（仅当内容很短时）
- 4级：(1)、(2)、等

请以JSON格式返回结果，格式如下：
[
  {"is_heading": true/false, "level": 1-4, "confidence": 0.0-1.0},
  ...
]

待分析文本：
"""
        
        for i, text in enumerate(texts):
            prompt += f"\n{i+1}. {text[:200]}{'...' if len(text) > 200 else ''}"
        
        prompt += "\n\n请返回JSON格式的分析结果："
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM API
        
        Args:
            prompt: 提示字符串
            
        Returns:
            LLM响应
        """
        # 这里需要根据具体的LLM客户端实现
        # 示例：OpenAI GPT
        if hasattr(self.llm_client, 'chat'):
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        # 示例：Claude
        elif hasattr(self.llm_client, 'messages'):
            response = self.llm_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        # 通用接口
        else:
            return self.llm_client.generate(prompt)
    
    def _parse_llm_response(self, response: str, expected_count: int) -> List[Dict[str, Any]]:
        """
        解析LLM响应
        
        Args:
            response: LLM响应字符串
            expected_count: 期望的结果数量
            
        Returns:
            解析后的结果列表
        """
        try:
            # 尝试提取JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                results = json.loads(json_str)
                
                # 验证结果格式
                if isinstance(results, list) and len(results) == expected_count:
                    validated_results = []
                    for result in results:
                        if isinstance(result, dict):
                            validated_results.append({
                                'is_heading': bool(result.get('is_heading', False)),
                                'level': int(result.get('level', 0)),
                                'confidence': float(result.get('confidence', 0.5))
                            })
                        else:
                            validated_results.append({
                                'is_heading': False,
                                'level': 0,
                                'confidence': 0.0
                            })
                    return validated_results
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        
        # 解析失败，返回默认结果
        logger.warning("LLM response parsing failed, using fallback")
        return [{'is_heading': False, 'level': 0, 'confidence': 0.0} for _ in range(expected_count)]
    
    def _fallback_rule_detection(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        规则检测回退方案
        
        Args:
            texts: 文本列表
            
        Returns:
            检测结果列表
        """
        results = []
        
        for text in texts:
            text = text.strip()
            
            # 一级标题：一、二、三、等
            if text.startswith(('一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、')):
                if len(text) <= 100:
                    results.append({'is_heading': True, 'level': 1, 'confidence': 0.9})
                else:
                    results.append({'is_heading': False, 'level': 0, 'confidence': 0.8})
            
            # 二级标题：（一）、（二）等 - 严格限制
            elif text.startswith(('（一）', '（二）', '（三）', '（四）', '（五）', '（六）', '（七）', '（八）', '（九）', '（十）')):
                if len(text) <= 20 and not ('：' in text or ':' in text or '，' in text or '。' in text):
                    results.append({'is_heading': True, 'level': 2, 'confidence': 0.7})
                else:
                    results.append({'is_heading': False, 'level': 0, 'confidence': 0.8})
            
            # 三级标题：1、2、3、等
            elif text.startswith(('1、', '2、', '3、', '4、', '5、', '6、', '7、', '8、', '9、', '10、')):
                if len(text) <= 15 and not ('：' in text or ':' in text or '，' in text):
                    results.append({'is_heading': True, 'level': 3, 'confidence': 0.6})
                else:
                    results.append({'is_heading': False, 'level': 0, 'confidence': 0.7})
            
            # 四级标题：(1)、(2)等
            elif text.startswith(('(1)', '(2)', '(3)', '(4)', '(5)', '(6)', '(7)', '(8)', '(9)', '(10)')):
                if len(text) <= 15 and not ('：' in text or ':' in text or '，' in text):
                    results.append({'is_heading': True, 'level': 4, 'confidence': 0.5})
                else:
                    results.append({'is_heading': False, 'level': 0, 'confidence': 0.6})
            
            else:
                results.append({'is_heading': False, 'level': 0, 'confidence': 0.9})
        
        return results
    
    def _get_cache_key(self, texts: List[str]) -> str:
        """
        生成缓存键
        
        Args:
            texts: 文本列表
            
        Returns:
            缓存键
        """
        import hashlib
        content = '|'.join(texts)
        return hashlib.md5(content.encode('utf-8')).hexdigest()


# 工厂函数
def create_llm_heading_detector(llm_type: str = "openai", **kwargs) -> LLMHeadingDetector:
    """
    创建LLM标题检测器
    
    Args:
        llm_type: LLM类型 ("openai", "claude", "custom")
        **kwargs: 其他参数
        
    Returns:
        LLM标题检测器实例
    """
    llm_client = None
    
    if llm_type == "openai":
        try:
            import openai
            llm_client = openai.OpenAI(api_key=kwargs.get('api_key'))
        except ImportError:
            logger.warning("OpenAI library not installed")
    
    elif llm_type == "claude":
        try:
            import anthropic
            llm_client = anthropic.Anthropic(api_key=kwargs.get('api_key'))
        except ImportError:
            logger.warning("Anthropic library not installed")
    
    elif llm_type == "custom":
        llm_client = kwargs.get('client')
    
    return LLMHeadingDetector(
        llm_client=llm_client,
        max_tokens_per_batch=kwargs.get('max_tokens_per_batch', 3000),
        max_texts_per_batch=kwargs.get('max_texts_per_batch', 20),
        cache_enabled=kwargs.get('cache_enabled', True)
    )
