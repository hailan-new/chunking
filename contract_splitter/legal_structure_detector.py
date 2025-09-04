"""
法律文档结构识别器
统一管理法律文档中的结构化标识识别，避免hardcode重复
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum

logger = logging.getLogger(__name__)


class LegalStructureLevel(Enum):
    """法律文档结构层级"""
    BOOK = 1      # 编
    PART = 2      # 篇  
    CHAPTER = 3   # 章
    SECTION = 4   # 节
    ARTICLE = 5   # 条
    CLAUSE = 6    # 款
    ITEM = 7      # 项
    SUBITEM = 8   # 目
    PARAGRAPH = 9 # 段
    ENUMERATION = 10  # 序号 (一)、(二)
    NUMBERING = 11    # 编号 1、2、


class LegalStructureDetector:
    """
    法律文档结构识别器
    
    提供统一的法律文档结构化标识识别功能，包括：
    - 法律条文模式识别
    - 层级结构判断
    - 标题提取和清理
    - 内容分割
    """
    
    # 法律文档结构模式定义
    LEGAL_PATTERNS = {
        LegalStructureLevel.BOOK: [
            r'^第[一二三四五六七八九十百千万\d]+编\s*',
        ],
        LegalStructureLevel.PART: [
            r'^第[一二三四五六七八九十百千万\d]+篇\s*',
        ],
        LegalStructureLevel.CHAPTER: [
            r'^第[一二三四五六七八九十百千万\d]+章\s*',
        ],
        LegalStructureLevel.SECTION: [
            r'^第[一二三四五六七八九十百千万\d]+节\s*',
        ],
        LegalStructureLevel.ARTICLE: [
            r'^第[一二三四五六七八九十百千万\d]+条\s*',
        ],
        LegalStructureLevel.CLAUSE: [
            r'^第[一二三四五六七八九十百千万\d]+款\s*',
        ],
        LegalStructureLevel.ITEM: [
            r'^第[一二三四五六七八九十百千万\d]+项\s*',
        ],
        LegalStructureLevel.SUBITEM: [
            r'^第[一二三四五六七八九十百千万\d]+目\s*',
        ],
        LegalStructureLevel.ENUMERATION: [
            r'^（[一二三四五六七八九十百千万\d]+）\s*',
            r'^\([一二三四五六七八九十百千万\d]+\)\s*',
            r'^[一二三四五六七八九十百千万]+[、．.]\s*',
        ],
        LegalStructureLevel.NUMBERING: [
            r'^\d+[、．.]\s*',
            r'^\d+\.\d+[、．.]?\s*',
            r'^\d+\)\s*',
        ]
    }
    
    # 通用标题模式（非法律特定）
    GENERAL_PATTERNS = {
        'chinese_numbering': [
            r'^[一二三四五六七八九十\d]+[、．.]\s*',
            r'^（[一二三四五六七八九十\d]+）\s*',
        ],
        'english_numbering': [
            r'^Chapter\s+\d+',
            r'^Section\s+\d+',
            r'^Article\s+\d+',
            r'^\d+\.?\s+',
            r'^\d+\.\d+\.?\s+',
        ]
    }
    
    def __init__(self, 
                 document_type: str = "legal",
                 custom_patterns: Optional[Dict[str, List[str]]] = None,
                 enable_fuzzy_matching: bool = True):
        """
        初始化法律结构识别器
        
        Args:
            document_type: 文档类型 ("legal", "contract", "regulation", "general")
            custom_patterns: 自定义模式
            enable_fuzzy_matching: 是否启用模糊匹配
        """
        self.document_type = document_type
        self.enable_fuzzy_matching = enable_fuzzy_matching
        
        # 构建完整的模式列表
        self.patterns = self._build_patterns(custom_patterns)
        
        # 编译正则表达式以提高性能
        self.compiled_patterns = self._compile_patterns()
    
    def _build_patterns(self, custom_patterns: Optional[Dict[str, List[str]]]) -> Dict[str, List[str]]:
        """构建模式列表"""
        patterns = {}
        
        # 添加法律文档模式
        for level, pattern_list in self.LEGAL_PATTERNS.items():
            patterns[level.name.lower()] = pattern_list.copy()
        
        # 添加通用模式
        for category, pattern_list in self.GENERAL_PATTERNS.items():
            patterns[category] = pattern_list.copy()
        
        # 添加自定义模式
        if custom_patterns:
            for category, pattern_list in custom_patterns.items():
                if category in patterns:
                    patterns[category].extend(pattern_list)
                else:
                    patterns[category] = pattern_list.copy()
        
        return patterns
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """编译正则表达式"""
        compiled = {}
        for category, pattern_list in self.patterns.items():
            compiled[category] = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
        return compiled
    
    def is_legal_heading(self, text: str) -> bool:
        """
        判断文本是否为法律文档标题
        
        Args:
            text: 待检测文本
            
        Returns:
            True if text is a legal heading
        """
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip()
        
        # 过滤过长的文本（通常不是标题）
        if len(text) > 200:
            return False
        
        # 检查法律结构模式
        for level in LegalStructureLevel:
            if self._matches_level(text, level):
                # 对于条文，需要额外检查是否真的是标题而不是内容
                if level == LegalStructureLevel.ARTICLE:
                    # 如果文本太长或包含明显的内容词，则不认为是标题
                    if (len(text) > 50 or
                        any(word in text for word in ['内容', '规定', '说明', '包含', '详细', '很长', '多'])):
                        continue
                return True
        
        # 如果是法律文档，优先使用法律模式
        if self.document_type == "legal":
            return False
        
        # 检查通用模式
        for category in ['chinese_numbering', 'english_numbering']:
            if category in self.compiled_patterns:
                for pattern in self.compiled_patterns[category]:
                    if pattern.match(text):
                        return True
        
        # 模糊匹配：检查是否不以句号结尾且较短
        if self.enable_fuzzy_matching:
            if (len(text) < 30 and  # 更严格的长度限制
                not text.endswith(('。', '.', '！', '!', '？', '?', '；', ';', '：', ':')) and
                not any(char in text for char in '，,、') and
                not any(word in text for word in ['内容', '规定', '说明', '包含', '详细'])):  # 排除明显的内容词
                return True
        
        return False
    
    def get_heading_level(self, text: str) -> int:
        """
        获取标题层级

        Args:
            text: 标题文本

        Returns:
            层级数字（1=最高级，数字越大级别越低）
        """
        if not text:
            return 10

        text = text.strip()

        # 检查法律结构层级
        for level in LegalStructureLevel:
            if self._matches_level(text, level):
                # 对于条文，需要额外检查是否真的是标题而不是内容
                if level == LegalStructureLevel.ARTICLE:
                    # 如果文本太长或包含明显的内容词，则返回默认层级
                    if (len(text) > 50 or
                        any(word in text for word in ['内容', '规定', '说明', '包含', '详细', '很长', '多'])):
                        return 10
                return level.value

        # 默认层级
        return 10
    
    def _matches_level(self, text: str, level: LegalStructureLevel) -> bool:
        """检查文本是否匹配特定层级"""
        level_name = level.name.lower()
        if level_name in self.compiled_patterns:
            for pattern in self.compiled_patterns[level_name]:
                if pattern.match(text):
                    return True
        return False
    
    def extract_legal_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取法律条文结构
        
        Args:
            text: 输入文本
            
        Returns:
            结构化的条文列表
        """
        sections = []
        
        # 构建所有法律结构的匹配模式
        all_patterns = []
        for level in LegalStructureLevel:
            level_name = level.name.lower()
            if level_name in self.patterns:
                for pattern_str in self.patterns[level_name]:
                    all_patterns.append((pattern_str, level))
        
        # 按优先级排序（编 > 篇 > 章 > 节 > 条 > ...）
        all_patterns.sort(key=lambda x: x[1].value)
        
        # 构建统一的匹配模式
        pattern_groups = []
        for pattern_str, level in all_patterns:
            # 安全地清理模式：保持正则表达式语法完整性
            clean_pattern = self._clean_pattern_for_search(pattern_str)
            if clean_pattern:  # 只添加有效的模式
                pattern_groups.append(f"({clean_pattern})")

        if not pattern_groups:
            return []

        combined_pattern = "|".join(pattern_groups)
        
        # 查找所有匹配
        matches = []
        for match in re.finditer(combined_pattern, text, re.MULTILINE):
            start_pos = match.start()
            matched_text = match.group()
            
            # 确定匹配的层级
            for i, (pattern_str, level) in enumerate(all_patterns):
                # 使用原始模式进行匹配验证
                if self._pattern_matches_text(pattern_str, matched_text):
                    matches.append({
                        'start': start_pos,
                        'text': matched_text,
                        'level': level,
                        'type': level.name.lower()
                    })
                    break
        
        # 按位置排序
        matches.sort(key=lambda x: x['start'])
        
        # 提取内容
        for i, match in enumerate(matches):
            start_pos = match['start']
            
            # 确定结束位置
            if i + 1 < len(matches):
                end_pos = matches[i + 1]['start']
            else:
                end_pos = len(text)
            
            # 提取内容
            content = text[start_pos:end_pos].strip()
            
            sections.append({
                'heading': match['text'].strip(),
                'content': content,
                'level': match['level'].value,
                'type': match['type'],
                'start_pos': start_pos,
                'end_pos': end_pos
            })
        
        return sections

    def _clean_pattern_for_search(self, pattern_str: str) -> str:
        """
        安全地清理正则表达式模式以用于搜索

        Args:
            pattern_str: 原始正则表达式模式

        Returns:
            清理后的模式，如果无法安全清理则返回空字符串
        """
        try:
            # 移除行首锚点 ^
            if pattern_str.startswith('^'):
                pattern_str = pattern_str[1:]

            # 安全地移除末尾的 \s*
            if pattern_str.endswith('\\s*'):
                pattern_str = pattern_str[:-3]

            # 验证清理后的模式是否有效
            import re
            re.compile(pattern_str)
            return pattern_str

        except re.error:
            # 如果清理后的模式无效，返回原始模式（不进行清理）
            try:
                import re
                re.compile(pattern_str)
                return pattern_str
            except re.error:
                # 如果原始模式也无效，返回空字符串
                logger.warning(f"Invalid regex pattern: {pattern_str}")
                return ""

    def _pattern_matches_text(self, pattern_str: str, text: str) -> bool:
        """
        检查模式是否匹配文本

        Args:
            pattern_str: 正则表达式模式
            text: 待匹配的文本

        Returns:
            是否匹配
        """
        try:
            import re
            # 如果模式以^开头，使用match；否则使用search
            if pattern_str.startswith('^'):
                return bool(re.match(pattern_str, text, re.IGNORECASE))
            else:
                return bool(re.search(pattern_str, text, re.IGNORECASE))
        except re.error:
            return False

    def clean_legal_text(self, text: str) -> str:
        """
        清理法律文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除重复的标题前缀
        text = re.sub(r'（征求意见稿）\s*>\s*', '', text)
        text = re.sub(r'[^第]*?>\s*(?=第)', '', text)
        
        # 修复常见的截断问题
        text = re.sub(r'制定本(?!\w)', '制定本办法', text)
        text = re.sub(r'根据本(?!\w)', '根据本办法', text)
        text = re.sub(r'按照本(?!\w)', '按照本办法', text)
        text = re.sub(r'违反本(?!\w)', '违反本办法', text)
        
        return text.strip()
    
    def get_all_legal_patterns(self) -> List[str]:
        """
        获取所有法律文档模式
        
        Returns:
            模式字符串列表
        """
        all_patterns = []
        for level in LegalStructureLevel:
            level_name = level.name.lower()
            if level_name in self.patterns:
                all_patterns.extend(self.patterns[level_name])
        return all_patterns
    
    def get_patterns_by_priority(self, document_type: str = None) -> List[str]:
        """
        按优先级获取模式
        
        Args:
            document_type: 文档类型
            
        Returns:
            按优先级排序的模式列表
        """
        doc_type = document_type or self.document_type
        
        if doc_type == "legal":
            # 法律文档：法律模式优先
            patterns = []
            for level in LegalStructureLevel:
                level_name = level.name.lower()
                if level_name in self.patterns:
                    patterns.extend(self.patterns[level_name])
            
            # 添加通用模式
            for category in ['chinese_numbering', 'english_numbering']:
                if category in self.patterns:
                    patterns.extend(self.patterns[category])
            
            return patterns
        else:
            # 其他文档：通用模式优先
            patterns = []
            for category in ['chinese_numbering', 'english_numbering']:
                if category in self.patterns:
                    patterns.extend(self.patterns[category])
            
            # 添加法律模式
            for level in LegalStructureLevel:
                level_name = level.name.lower()
                if level_name in self.patterns:
                    patterns.extend(self.patterns[level_name])
            
            return patterns


# 全局实例
_default_detector = None


def get_legal_detector(document_type: str = "legal", 
                      custom_patterns: Optional[Dict[str, List[str]]] = None) -> LegalStructureDetector:
    """
    获取法律结构检测器实例
    
    Args:
        document_type: 文档类型
        custom_patterns: 自定义模式
        
    Returns:
        检测器实例
    """
    global _default_detector
    
    if _default_detector is None or _default_detector.document_type != document_type:
        _default_detector = LegalStructureDetector(document_type, custom_patterns)
    
    return _default_detector
