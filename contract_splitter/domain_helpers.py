#!/usr/bin/env python3
"""
专业领域的chunking helper函数
针对法律条款、合同、规章制度等特定场景的优化切分方案
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from .base import BaseSplitter
from .splitter_factory import SplitterFactory
from .legal_structure_detector import get_legal_detector

logger = logging.getLogger(__name__)


class LegalClauseSplitter:
    """
    法律条款专用切分器
    
    特点：
    - 以条款为基本单位进行切分
    - 保持条款的完整性和语义连贯性
    - 适合法律文件、法规、条例等
    """
    
    def __init__(self,
                 max_tokens: int = None,  # 如果为None，从配置获取
                 overlap: int = None,
                 strict_max_tokens: bool = None,
                 use_llm_heading_detection: bool = None,
                 llm_config: dict = None,
                 config_file: str = None):
        """
        初始化法律条款切分器

        Args:
            max_tokens: 最大token数，如果为None则从配置获取
            overlap: 重叠长度，如果为None则从配置获取
            strict_max_tokens: 是否严格控制token数，如果为None则从配置获取
            use_llm_heading_detection: 是否使用LLM检测标题，如果为None则从配置获取
            llm_config: LLM配置，如果为None则从配置获取
            config_file: 配置文件路径
        """
        # 获取配置
        from .config import get_config
        config = get_config(config_file)

        # 获取法律文档配置
        legal_config = config.get_document_config("legal")

        # 使用参数或配置中的值
        max_tokens = max_tokens if max_tokens is not None else legal_config.get('max_tokens', 1500)
        overlap = overlap if overlap is not None else legal_config.get('overlap', 100)
        strict_max_tokens = strict_max_tokens if strict_max_tokens is not None else legal_config.get('strict_max_tokens', True)
        use_llm_heading_detection = use_llm_heading_detection if use_llm_heading_detection is not None else legal_config.get('use_llm_heading_detection', False)

        # 如果没有提供llm_config且启用了LLM，从配置获取
        if llm_config is None and use_llm_heading_detection:
            llm_config = config.get_llm_config()

        # 初始化法律结构检测器
        self.structure_detector = get_legal_detector("legal")

        # 使用工厂模式支持多种文件格式
        self.factory = SplitterFactory()
        self.splitter_config = {
            'max_tokens': max_tokens,
            'overlap': overlap,
            'split_by_sentence': True,
            'token_counter': "character",
            'chunking_strategy': "finest_granularity",
            'strict_max_tokens': strict_max_tokens,
            'use_llm_heading_detection': use_llm_heading_detection,
            'llm_config': llm_config
        }
    
    def split_legal_document(self, file_path: str) -> List[str]:
        """
        切分法律文档

        Args:
            file_path: 文档路径 (支持 .docx, .doc, .pdf, .wps)

        Returns:
            切分后的chunks列表
        """
        logger.info(f"Processing legal document: {file_path}")

        # 检查文件格式支持
        if not self.factory.is_supported_format(file_path):
            file_format = self.factory.detect_file_format(file_path)
            raise ValueError(f"Unsupported file format: .{file_format}. Supported formats: {self.factory.get_supported_formats()}")

        # 使用工厂模式创建合适的splitter
        splitter = self.factory.create_splitter(file_path, **self.splitter_config)

        # 使用层次化分割
        sections = splitter.split(file_path)

        # 对于法律文档，使用改进的句子优先分块
        full_text = self._extract_full_text_from_sections(sections)

        # 使用句子优先的分块策略，保持句子完整性
        from .utils import sliding_window_split
        processed_chunks = sliding_window_split(
            full_text,
            max_tokens=self.splitter_config.get('max_tokens', 1500),
            overlap=int(self.splitter_config.get('max_tokens', 1500) * 0.1),  # 10% overlap
            by_sentence=True,  # 优先保持句子完整性
            token_counter="character"
        )

        # 后处理：修复被错误截断的条文（现在应该很少需要）
        fixed_chunks = self._fix_truncated_articles(processed_chunks)

        logger.info(f"Legal document split into {len(fixed_chunks)} chunks")
        return fixed_chunks

    def _extract_full_text_from_sections(self, sections: List[Dict[str, Any]]) -> str:
        """
        从sections中提取完整文本

        Args:
            sections: 文档sections

        Returns:
            完整文本
        """
        def extract_text_recursive(section):
            text_parts = []

            # 添加标题
            if section.get('heading'):
                text_parts.append(section['heading'])

            # 添加内容
            if section.get('content'):
                text_parts.append(section['content'])

            # 递归处理子sections
            for subsection in section.get('subsections', []):
                subsection_text = extract_text_recursive(subsection)
                if subsection_text:
                    text_parts.append(subsection_text)

            return '\n\n'.join(text_parts)

        all_text_parts = []
        for section in sections:
            section_text = extract_text_recursive(section)
            if section_text:
                all_text_parts.append(section_text)

        return '\n\n'.join(all_text_parts)

    def _fix_truncated_articles(self, chunks: List[str]) -> List[str]:
        """
        修复被错误截断的条文

        Args:
            chunks: 原始chunks

        Returns:
            修复后的chunks
        """
        import re

        fixed_chunks = []
        i = 0

        while i < len(chunks):
            current_chunk = chunks[i]

            # 检查是否是被截断的条文（以"应当对本办法"结尾）
            if (current_chunk.endswith('应当对本办法') and
                i + 1 < len(chunks)):

                next_chunk = chunks[i + 1]

                # 检查下一个chunk是否包含条文引用内容
                if re.search(r'第[一二三四五六七八九十百千万\d]+条.*?的内容进行', next_chunk):
                    # 合并当前chunk和下一个chunk
                    merged_chunk = current_chunk + next_chunk
                    fixed_chunks.append(merged_chunk)
                    i += 2  # 跳过下一个chunk
                    continue

            # 检查是否是其他类型的截断条文（长度过短且包含条文标识）
            if (len(current_chunk) < 100 and
                re.search(r'第[一二三四五六七八九十百千万\d]+条', current_chunk) and
                i + 1 < len(chunks)):

                next_chunk = chunks[i + 1]

                # 如果下一个chunk不是以"第X条"开头，可能是当前条文的延续
                if not re.match(r'^第[一二三四五六七八九十百千万\d]+条', next_chunk):
                    # 合并
                    merged_chunk = current_chunk + '\n\n' + next_chunk
                    fixed_chunks.append(merged_chunk)
                    i += 2  # 跳过下一个chunk
                    continue

            # 正常添加chunk
            fixed_chunks.append(current_chunk)
            i += 1

        return fixed_chunks

    def _split_legal_text_by_articles(self, text: str) -> List[str]:
        """
        按法律条文切分文本

        Args:
            text: 完整文本

        Returns:
            按条文切分的chunks
        """
        import re

        # 清理文本
        cleaned_text = self._clean_legal_text_advanced(text)

        # 按条文切分
        return self._split_by_articles_advanced(cleaned_text)

    def _clean_legal_text_advanced(self, text: str) -> str:
        """
        高级法律文本清理

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        import re

        # 移除重复的前缀模式
        text = re.sub(r'（征求意见稿）\s*>\s*', '', text)
        text = re.sub(r'[^第]*?>\s*(?=第)', '', text)  # 移除"第X条"前的前缀

        # 按行处理，移除重复行
        lines = text.split('\n')
        cleaned_lines = []
        seen_lines = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 避免重复行
            if line not in seen_lines:
                cleaned_lines.append(line)
                seen_lines.add(line)

        return '\n\n'.join(cleaned_lines)

    def _split_by_articles_advanced(self, text: str) -> List[str]:
        """
        简单有效的法律条文切分 - 以条文为主要切分单位

        Args:
            text: 清理后的文本

        Returns:
            按条文切分的chunks
        """
        import re

        # 简单而有效的策略：以"第X条"为主要分割点
        article_pattern = r'第[一二三四五六七八九十百千万\d]+条'
        chapter_pattern = r'第[一二三四五六七八九十百千万\d]+章'

        # 找到所有条文和章节位置
        article_matches = list(re.finditer(article_pattern, text))
        chapter_matches = list(re.finditer(chapter_pattern, text))

        # 合并所有标记并排序
        all_matches = []
        for match in article_matches:
            all_matches.append({
                'start': match.start(),
                'text': match.group(),
                'type': 'article'
            })
        for match in chapter_matches:
            all_matches.append({
                'start': match.start(),
                'text': match.group(),
                'type': 'chapter'
            })

        # 按位置排序
        all_matches.sort(key=lambda x: x['start'])

        if not all_matches:
            # 没有找到条文或章节，按段落分割
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            return [p for p in paragraphs if len(p) > 20]  # 过滤太短的段落

        chunks = []

        # 处理第一个标记之前的内容（通常是标题）
        if all_matches[0]['start'] > 0:
            pre_content = text[:all_matches[0]['start']].strip()
            if pre_content:
                # 按段落分割前置内容
                pre_paragraphs = [p.strip() for p in pre_content.split('\n\n') if p.strip() and len(p) > 10]
                chunks.extend(pre_paragraphs)

        # 处理每个标记
        for i, match in enumerate(all_matches):
            # 跳过被标记为None的匹配（已经被合并处理）
            if match is None:
                continue

            start_pos = match['start']

            # 确定结束位置 - 找到下一个非None的匹配
            end_pos = len(text)  # 默认到文本结尾
            for j in range(i + 1, len(all_matches)):
                if all_matches[j] is not None:
                    end_pos = all_matches[j]['start']
                    break

            # 提取内容
            content = text[start_pos:end_pos].strip()

            if content and len(content) > 10:  # 过滤太短的内容
                # 对于章节，检查是否应该与下一个条文合并
                next_match_idx = None
                for j in range(i + 1, len(all_matches)):
                    if all_matches[j] is not None:
                        next_match_idx = j
                        break

                if (match['type'] == 'chapter' and
                    next_match_idx is not None and
                    all_matches[next_match_idx]['type'] == 'article' and
                    all_matches[next_match_idx]['start'] - match['start'] < 200):  # 章节和条文距离很近

                    # 合并章节和下一个条文
                    # 找到再下一个匹配作为结束位置
                    merged_end = len(text)
                    for j in range(next_match_idx + 1, len(all_matches)):
                        if all_matches[j] is not None:
                            merged_end = all_matches[j]['start']
                            break

                    merged_content = text[start_pos:merged_end].strip()
                    if merged_content and len(merged_content) > 10:
                        chunks.append(merged_content)

                    # 跳过下一个条文（已经合并了）
                    all_matches[next_match_idx] = None  # 标记为已处理
                else:
                    chunks.append(content)

        # 过滤掉None值（被合并的条文）
        return [chunk for chunk in chunks if chunk is not None]

    def _merge_chapter_with_content(self, content: str, marker: dict) -> str:
        """
        将章节标题与其内容智能合并

        Args:
            content: 章节内容
            marker: 章节标记信息

        Returns:
            处理后的内容
        """
        lines = content.split('\n\n')

        # 如果章节标题后面只有很少内容，保持原样
        if len(lines) <= 2:
            return content

        # 检查第一行是否只是章节标题
        first_line = lines[0].strip()
        if len(first_line) < 50 and marker['text'] in first_line:
            # 这是一个简短的章节标题，应该与后续内容合并
            return content

        return content

    def _post_process_legal_chunks(self, chunks: List[str]) -> List[str]:
        """
        法律条款的后处理 - 以条文为单位进行智能切分

        Args:
            chunks: 原始chunks

        Returns:
            处理后的chunks
        """
        import re

        # 合并所有chunks为一个完整文本
        full_text = '\n\n'.join(chunks)

        # 清理文本
        cleaned_text = self._clean_legal_text(full_text)

        # 按条文切分
        article_chunks = self._split_by_articles_simple(cleaned_text)

        return article_chunks

    def _clean_legal_text(self, text: str) -> str:
        """
        清理法律文本，移除重复内容和无用前缀

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        import re

        # 按行分割
        lines = text.split('\n')
        cleaned_lines = []
        seen_lines = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 移除重复的前缀模式
            cleaned_line = re.sub(r'^（征求意见稿）\s*>\s*', '', line)
            cleaned_line = re.sub(r'^[^第]*?>\s*', '', cleaned_line)  # 更精确的模式
            cleaned_line = cleaned_line.strip()

            # 避免重复行
            if cleaned_line and cleaned_line not in seen_lines:
                cleaned_lines.append(cleaned_line)
                seen_lines.add(cleaned_line)

        return '\n\n'.join(cleaned_lines)

    def _split_by_articles_simple(self, text: str) -> List[str]:
        """
        简单按条文切分文本

        Args:
            text: 清理后的文本

        Returns:
            按条文切分的chunks
        """
        import re

        # 条文分割模式
        article_pattern = r'第[一二三四五六七八九十百千万\d]+条'

        # 找到所有条文位置
        matches = list(re.finditer(article_pattern, text))

        if not matches:
            # 如果没有找到条文，返回原文本
            return [text] if text.strip() else []

        chunks = []

        # 处理第一个条文之前的内容（标题等）
        if matches[0].start() > 0:
            pre_content = text[:matches[0].start()].strip()
            if pre_content:
                chunks.append(pre_content)

        # 处理每个条文
        for i, match in enumerate(matches):
            start_pos = match.start()

            # 确定结束位置
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            # 提取条文内容
            article_content = text[start_pos:end_pos].strip()
            if article_content:
                chunks.append(article_content)

        return chunks

    def _split_by_articles(self, text: str) -> List[str]:
        """
        按条文切分文本

        Args:
            text: 完整文本

        Returns:
            按条文切分的chunks
        """
        import re

        # 条文分割模式 - 以"第X条"为主要分割点
        article_pattern = r'(第[一二三四五六七八九十百千万\d]+条)'

        # 章节分割模式 - 以"第X章"为分割点
        chapter_pattern = r'(第[一二三四五六七八九十百千万\d]+章)'

        chunks = []

        # 首先按章节分割
        chapter_parts = re.split(chapter_pattern, text)

        for part in chapter_parts:
            part = part.strip()
            if not part:
                continue

            # 检查是否是章节标题
            if re.match(chapter_pattern, part):
                # 章节标题独立成chunk
                chunks.append(part)
            else:
                # 按条文分割
                article_parts = re.split(article_pattern, part)

                current_article = ""
                for article_part in article_parts:
                    article_part = article_part.strip()
                    if not article_part:
                        continue

                    # 检查是否是条文标题
                    if re.match(article_pattern, article_part):
                        # 保存之前的条文
                        if current_article:
                            chunks.append(current_article.strip())
                        # 开始新条文
                        current_article = article_part
                    else:
                        # 添加到当前条文
                        if current_article:
                            current_article += '\n\n' + article_part
                        else:
                            current_article = article_part

                # 保存最后一个条文
                if current_article:
                    chunks.append(current_article.strip())

        return chunks

    def _clean_legal_chunk(self, chunk: str) -> str:
        """
        清理法律条文chunk

        Args:
            chunk: 原始chunk

        Returns:
            清理后的chunk
        """
        import re

        # 移除重复的前缀（如"（征求意见稿） >"）
        lines = chunk.split('\n')
        cleaned_lines = []
        seen_content = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 移除重复的前缀模式
            cleaned_line = re.sub(r'^（征求意见稿）\s*>\s*', '', line)
            cleaned_line = re.sub(r'^.*?>\s*', '', cleaned_line, count=1)
            cleaned_line = cleaned_line.strip()

            # 避免重复内容
            if cleaned_line and cleaned_line not in seen_content:
                cleaned_lines.append(cleaned_line)
                seen_content.add(cleaned_line)

        return '\n\n'.join(cleaned_lines)






class DomainContractSplitter:
    """
    合同专用切分器
    
    特点：
    - 根据合同类型调整切分策略
    - 保持合同条款的完整性
    - 考虑合同的层次结构
    """
    
    def __init__(self,
                 contract_type: str = "general",  # general, service, purchase, employment, etc.
                 max_tokens: int = None,
                 overlap: int = None,
                 strict_max_tokens: bool = None,
                 use_llm_heading_detection: bool = None,
                 llm_config: dict = None,
                 config_file: str = None):
        """
        初始化合同切分器

        Args:
            contract_type: 合同类型
            max_tokens: 最大token数，如果为None则从配置获取
            overlap: 重叠长度，如果为None则从配置获取
            strict_max_tokens: 是否严格控制token数，如果为None则从配置获取
            use_llm_heading_detection: 是否使用LLM检测标题，如果为None则从配置获取
            llm_config: LLM配置，如果为None则从配置获取
            config_file: 配置文件路径
        """
        self.contract_type = contract_type

        # 获取配置
        from .config import get_config
        global_config = get_config(config_file)

        # 获取合同文档配置
        contract_config = global_config.get_document_config("contract")

        # 根据合同类型调整参数
        type_config = self._get_contract_config(contract_type)

        # 使用参数或配置中的值
        max_tokens = max_tokens if max_tokens is not None else contract_config.get('max_tokens', type_config.get('max_tokens', 2000))
        overlap = overlap if overlap is not None else contract_config.get('overlap', type_config.get('overlap', 200))
        strict_max_tokens = strict_max_tokens if strict_max_tokens is not None else contract_config.get('strict_max_tokens', True)
        use_llm_heading_detection = use_llm_heading_detection if use_llm_heading_detection is not None else contract_config.get('use_llm_heading_detection', False)

        # 如果没有提供llm_config且启用了LLM，从配置获取
        if llm_config is None and use_llm_heading_detection:
            llm_config = global_config.get_llm_config()

        # 使用工厂模式支持多种文件格式
        self.factory = SplitterFactory()
        self.splitter_config = {
            'max_tokens': max_tokens,
            'overlap': overlap,
            'split_by_sentence': True,
            'token_counter': "character",
            'chunking_strategy': type_config.get('strategy', "finest_granularity"),
            'strict_max_tokens': strict_max_tokens,
            'use_llm_heading_detection': use_llm_heading_detection,
            'llm_config': llm_config
        }
    
    def _get_contract_config(self, contract_type: str) -> Dict[str, Any]:
        """
        根据合同类型获取配置
        
        Args:
            contract_type: 合同类型
            
        Returns:
            配置字典
        """
        configs = {
            "service": {
                "max_tokens": 1800,  # 服务合同条款较详细
                "overlap": 150,
                "strategy": "finest_granularity"
            },
            "purchase": {
                "max_tokens": 2200,  # 采购合同可能包含详细规格
                "overlap": 200,
                "strategy": "finest_granularity"
            },
            "employment": {
                "max_tokens": 1600,  # 劳动合同条款相对简洁
                "overlap": 100,
                "strategy": "finest_granularity"
            },
            "partnership": {
                "max_tokens": 2500,  # 合作协议可能较复杂
                "overlap": 250,
                "strategy": "all_levels"
            },
            "general": {
                "max_tokens": 2000,
                "overlap": 200,
                "strategy": "finest_granularity"
            }
        }
        
        return configs.get(contract_type, configs["general"])
    
    def split_contract(self, file_path: str) -> List[str]:
        """
        切分合同文档

        Args:
            file_path: 文档路径 (支持 .docx, .doc, .pdf, .wps)

        Returns:
            切分后的chunks列表
        """
        logger.info(f"Processing {self.contract_type} contract: {file_path}")

        # 检查文件格式支持
        if not self.factory.is_supported_format(file_path):
            file_format = self.factory.detect_file_format(file_path)
            raise ValueError(f"Unsupported file format: .{file_format}. Supported formats: {self.factory.get_supported_formats()}")

        # 使用工厂模式创建合适的splitter
        splitter = self.factory.create_splitter(file_path, **self.splitter_config)

        # 使用层次化分割
        sections = splitter.split(file_path)

        # 根据合同类型选择策略
        config = self._get_contract_config(self.contract_type)
        chunks = splitter.flatten(sections, strategy=config['strategy'])

        # 合同特定的后处理
        processed_chunks = self._post_process_contract_chunks(chunks)

        logger.info(f"Contract split into {len(processed_chunks)} chunks")
        return processed_chunks
    
    def _post_process_contract_chunks(self, chunks: List[str]) -> List[str]:
        """
        合同的后处理
        
        Args:
            chunks: 原始chunks
            
        Returns:
            处理后的chunks
        """
        # 识别重要条款（如违约、终止、争议解决等）
        important_keywords = [
            "违约", "breach", "termination", "终止", "争议", "dispute",
            "赔偿", "compensation", "liability", "责任", "保密", "confidential"
        ]
        
        processed = []
        
        for chunk in chunks:
            # 检查是否包含重要条款
            is_important = any(keyword in chunk.lower() for keyword in important_keywords)
            
            if is_important:
                # 重要条款保持完整，不进行进一步分割
                logger.debug(f"Important clause detected, keeping intact: {chunk[:50]}...")
            
            processed.append(chunk)
        
        return processed


class RegulationSplitter:
    """
    规章制度专用切分器
    
    特点：
    - 适合公司规章、管理制度、操作规程等
    - 保持制度条款的逻辑完整性
    - 支持多级标题结构
    """
    
    def __init__(self,
                 regulation_type: str = "general",  # general, hr, finance, operation, safety, etc.
                 max_tokens: int = None,
                 overlap: int = None,
                 strict_max_tokens: bool = None,
                 use_llm_heading_detection: bool = None,
                 llm_config: dict = None,
                 config_file: str = None):
        """
        初始化规章制度切分器

        Args:
            regulation_type: 规章类型
            max_tokens: 最大token数，如果为None则从配置获取
            overlap: 重叠长度，如果为None则从配置获取
            strict_max_tokens: 是否严格控制token数，如果为None则从配置获取
            use_llm_heading_detection: 是否使用LLM检测标题，如果为None则从配置获取
            llm_config: LLM配置，如果为None则从配置获取
            config_file: 配置文件路径
        """
        self.regulation_type = regulation_type

        # 获取配置
        from .config import get_config
        global_config = get_config(config_file)

        # 获取规章制度文档配置
        regulation_config = global_config.get_document_config("regulation")

        # 根据规章类型调整参数
        type_config = self._get_regulation_config(regulation_type)

        # 使用参数或配置中的值
        max_tokens = max_tokens if max_tokens is not None else regulation_config.get('max_tokens', type_config.get('max_tokens', 1800))
        overlap = overlap if overlap is not None else regulation_config.get('overlap', type_config.get('overlap', 150))
        strict_max_tokens = strict_max_tokens if strict_max_tokens is not None else regulation_config.get('strict_max_tokens', True)
        use_llm_heading_detection = use_llm_heading_detection if use_llm_heading_detection is not None else regulation_config.get('use_llm_heading_detection', True)

        # 如果没有提供llm_config且启用了LLM，从配置获取
        if llm_config is None and use_llm_heading_detection:
            llm_config = global_config.get_llm_config()

        # 使用工厂模式支持多种文件格式
        self.factory = SplitterFactory()
        self.splitter_config = {
            'max_tokens': max_tokens,
            'overlap': overlap,
            'split_by_sentence': True,
            'token_counter': "character",
            'chunking_strategy': type_config.get('strategy', "finest_granularity"),
            'strict_max_tokens': strict_max_tokens,
            'use_llm_heading_detection': use_llm_heading_detection,
            'llm_config': llm_config
        }
    
    def _get_regulation_config(self, regulation_type: str) -> Dict[str, Any]:
        """
        根据规章类型获取配置
        
        Args:
            regulation_type: 规章类型
            
        Returns:
            配置字典
        """
        configs = {
            "hr": {
                "max_tokens": 1600,  # 人事制度条款相对简洁
                "overlap": 120,
                "strategy": "finest_granularity"
            },
            "finance": {
                "max_tokens": 2000,  # 财务制度可能包含详细流程
                "overlap": 180,
                "strategy": "finest_granularity"
            },
            "operation": {
                "max_tokens": 2200,  # 操作规程可能较详细
                "overlap": 200,
                "strategy": "all_levels"
            },
            "safety": {
                "max_tokens": 1500,  # 安全制度条款需要精确
                "overlap": 100,
                "strategy": "finest_granularity"
            },
            "general": {
                "max_tokens": 1800,
                "overlap": 150,
                "strategy": "finest_granularity"
            }
        }
        
        return configs.get(regulation_type, configs["general"])
    
    def split_regulation(self, file_path: str) -> List[str]:
        """
        切分规章制度文档

        Args:
            file_path: 文档路径 (支持 .docx, .doc, .pdf, .wps)

        Returns:
            切分后的chunks列表
        """
        logger.info(f"Processing {self.regulation_type} regulation: {file_path}")

        # 检查文件格式支持
        if not self.factory.is_supported_format(file_path):
            file_format = self.factory.detect_file_format(file_path)
            raise ValueError(f"Unsupported file format: .{file_format}. Supported formats: {self.factory.get_supported_formats()}")

        # 使用工厂模式创建合适的splitter
        splitter = self.factory.create_splitter(file_path, **self.splitter_config)

        # 使用层次化分割
        sections = splitter.split(file_path)

        # 根据规章类型选择策略
        config = self._get_regulation_config(self.regulation_type)
        chunks = splitter.flatten(sections, strategy=config['strategy'])

        # 规章制度特定的后处理
        processed_chunks = self._post_process_regulation_chunks(chunks)

        logger.info(f"Regulation split into {len(processed_chunks)} chunks")
        return processed_chunks
    
    def _post_process_regulation_chunks(self, chunks: List[str]) -> List[str]:
        """
        规章制度的后处理
        
        Args:
            chunks: 原始chunks
            
        Returns:
            处理后的chunks
        """
        processed = []
        
        for chunk in chunks:
            # 识别流程性条款（包含步骤、程序等）
            process_keywords = ["步骤", "程序", "流程", "process", "procedure", "step"]
            is_process = any(keyword in chunk.lower() for keyword in process_keywords)
            
            if is_process:
                # 流程性条款保持完整
                logger.debug(f"Process clause detected: {chunk[:50]}...")
            
            processed.append(chunk)
        
        return processed


# 便捷函数
def split_legal_document(file_path: str, **kwargs) -> List[str]:
    """
    便捷函数：切分法律文档
    
    Args:
        file_path: 文档路径
        **kwargs: 其他参数
        
    Returns:
        切分后的chunks列表
    """
    splitter = LegalClauseSplitter(**kwargs)
    return splitter.split_legal_document(file_path)


def split_contract(file_path: str, contract_type: str = "general", **kwargs) -> List[str]:
    """
    便捷函数：切分合同文档
    
    Args:
        file_path: 文档路径
        contract_type: 合同类型
        **kwargs: 其他参数
        
    Returns:
        切分后的chunks列表
    """
    splitter = DomainContractSplitter(contract_type=contract_type, **kwargs)
    return splitter.split_contract(file_path)


def split_regulation(file_path: str, regulation_type: str = "general", **kwargs) -> List[str]:
    """
    便捷函数：切分规章制度文档
    
    Args:
        file_path: 文档路径
        regulation_type: 规章类型
        **kwargs: 其他参数
        
    Returns:
        切分后的chunks列表
    """
    splitter = RegulationSplitter(regulation_type=regulation_type, **kwargs)
    return splitter.split_regulation(file_path)
