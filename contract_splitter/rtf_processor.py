#!/usr/bin/env python3
"""
RTF文档处理模块
用于处理从WPS转换而来的RTF文件
"""

import re
import logging
from typing import List, Dict, Any
from .legal_structure_detector import get_legal_detector

try:
    from striprtf.striprtf import rtf_to_text
    RTF_PARSER_AVAILABLE = True
except ImportError:
    RTF_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


class RTFProcessor:
    """RTF文档处理器"""
    
    def __init__(self, document_type: str = "legal"):
        """
        初始化RTF处理器

        Args:
            document_type: 文档类型
        """
        self.document_type = document_type
        self.structure_detector = get_legal_detector(document_type)
    
    def extract_text_from_rtf(self, rtf_file_path: str) -> str:
        """
        从RTF文件中提取纯文本

        Args:
            rtf_file_path: RTF文件路径

        Returns:
            提取的纯文本
        """
        try:
            # 首先尝试使用专业的RTF解析库
            if RTF_PARSER_AVAILABLE:
                try:
                    with open(rtf_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        rtf_content = f.read()

                    # 使用striprtf库解析
                    text = rtf_to_text(rtf_content)

                    if text and len(text.strip()) > 100:
                        # 清理和规范化文本
                        cleaned_text = self._clean_extracted_text(text.strip())
                        logger.info(f"使用striprtf库提取文本成功，长度: {len(cleaned_text)} 字符")
                        return cleaned_text
                    else:
                        logger.warning("striprtf库提取的内容不足，尝试备用方法")

                except Exception as e:
                    logger.warning(f"striprtf库解析失败: {e}，尝试备用方法")

            # 备用方法：自定义解析
            with open(rtf_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()

            # 提取RTF中的文本内容
            text = self._parse_rtf_content(rtf_content)

            logger.info(f"从RTF文件提取文本成功，长度: {len(text)} 字符")
            return text

        except Exception as e:
            logger.error(f"RTF文件处理失败: {e}")
            return ""
    
    def _parse_rtf_content(self, rtf_content: str) -> str:
        """
        解析RTF内容，提取纯文本

        Args:
            rtf_content: RTF文件内容

        Returns:
            提取的纯文本
        """
        try:
            # 移除RTF控制字符和格式代码
            text = rtf_content

            # 移除RTF头部信息
            text = re.sub(r'\\rtf1.*?\\deflang\d+', '', text, flags=re.DOTALL)

            # 移除字体表
            text = re.sub(r'\\fonttbl\{.*?\}', '', text, flags=re.DOTALL)

            # 移除颜色表
            text = re.sub(r'\\colortbl;.*?;', '', text, flags=re.DOTALL)

            # 移除样式表
            text = re.sub(r'\\stylesheet\{.*?\}', '', text, flags=re.DOTALL)

            # 移除列表表
            text = re.sub(r'\{\\\*\\listtable.*?\}', '', text, flags=re.DOTALL)

            # 移除其他RTF控制序列
            text = re.sub(r'\\[a-z]+\d*\s?', '', text)
            text = re.sub(r'\{\\\*\\[^}]*\}', '', text, flags=re.DOTALL)

            # 移除大括号
            text = re.sub(r'[{}]', '', text)

            # 处理特殊字符编码
            text = self._decode_rtf_special_chars(text)

            # 清理多余的空白字符
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)

            # 移除开头和结尾的空白
            text = text.strip()

            return text

        except re.error as e:
            logger.error(f"正则表达式错误: {e}")
            # 如果正则表达式失败，尝试简单的文本提取
            return self._simple_text_extraction(rtf_content)
        except Exception as e:
            logger.error(f"RTF解析错误: {e}")
            return ""

    def _simple_text_extraction(self, rtf_content: str) -> str:
        """
        简单的RTF文本提取方法（备用方案）

        Args:
            rtf_content: RTF文件内容

        Returns:
            提取的文本
        """
        try:
            # 查找所有可能的中文文本
            import re

            # 提取十六进制编码的中文字符
            chinese_chars = []
            hex_pattern = r"\\\'([0-9a-fA-F]{2})"

            for match in re.finditer(hex_pattern, rtf_content):
                try:
                    hex_code = match.group(1)
                    char = bytes.fromhex(hex_code).decode('gbk', errors='ignore')
                    if char and ord(char) > 127:  # 非ASCII字符
                        chinese_chars.append(char)
                except:
                    continue

            # 组合提取的字符
            extracted_text = ''.join(chinese_chars)

            # 如果提取到足够的中文内容，返回
            if len(extracted_text) > 100:
                logger.info(f"简单提取成功，提取到 {len(extracted_text)} 个字符")
                return extracted_text

            # 否则尝试更安全的文本提取
            try:
                # 只保留中文字符、数字、字母和基本标点
                safe_chars = []
                for char in rtf_content:
                    if ('\u4e00' <= char <= '\u9fff' or  # 中文
                        '\u3000' <= char <= '\u303f' or  # 中文标点
                        '\uff00' <= char <= '\uffef' or  # 全角字符
                        char.isalnum() or char.isspace() or
                        char in '()（）、，。！？：；""''【】《》-.,!?:;'):
                        safe_chars.append(char)

                readable_text = ''.join(safe_chars)
                readable_text = re.sub(r'\s+', ' ', readable_text).strip()

                return readable_text
            except:
                return ""

        except Exception as e:
            logger.error(f"简单文本提取失败: {e}")
            return ""

    def _decode_rtf_special_chars(self, text: str) -> str:
        """
        解码RTF特殊字符
        
        Args:
            text: 包含RTF编码的文本
            
        Returns:
            解码后的文本
        """
        # 处理Unicode编码 \uNNNN
        def replace_unicode(match):
            try:
                code = int(match.group(1))
                if code < 0:
                    code = 65536 + code  # 处理负数
                return chr(code)
            except:
                return match.group(0)
        
        text = re.sub(r'\\u(-?\d+)', replace_unicode, text)
        
        # 处理十六进制编码 \'XX
        def replace_hex(match):
            try:
                hex_code = match.group(1)
                return bytes.fromhex(hex_code).decode('gbk', errors='ignore')
            except:
                return match.group(0)
        
        text = re.sub(r"\\\'([0-9a-fA-F]{2})", replace_hex, text)
        
        # 处理常见的RTF转义字符
        try:
            text = re.sub(r'\\par\s*', '\n', text)
            text = re.sub(r'\\line\s*', '\n', text)
            text = re.sub(r'\\tab\s*', '\t', text)
            text = re.sub(r'\\\\', '\\', text)
            text = re.sub(r'\\\{', '{', text)
            text = re.sub(r'\\\}', '}', text)
        except re.error as e:
            logger.warning(f"RTF转义字符处理失败: {e}")
            pass
        
        return text
    
    def split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本分割为sections

        Args:
            text: 纯文本内容

        Returns:
            sections列表
        """
        sections = []

        # 清理文本，添加适当的换行
        cleaned_text = self._clean_extracted_text(text)

        # 按法律条文进行智能分割
        article_sections = self._split_by_articles(cleaned_text)
        
        # 如果成功按条文分割，使用条文分割结果
        if len(article_sections) > 2:  # 至少有标题+一个条文
            sections.extend(article_sections)
        else:
            # 否则使用原有简单分割方法
            # 简单的分段处理 - 为法律文档优化
            paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]

            if paragraphs:
                # 查找标题（通常包含"管理办法"、"条例"等）
                title_found = False
                title_content = ""
                main_content_parts = []

                for para in paragraphs:
                    if not title_found and ('管理办法' in para or '条例' in para or '规定' in para):
                        title_content = para
                        title_found = True
                    else:
                        main_content_parts.append(para)

                # 添加标题section
                if title_content:
                    sections.append({
                        'heading': title_content,
                        'content': title_content,
                        'subsections': []
                    })

                # 添加主要内容section
                if main_content_parts:
                    main_content = '\n\n'.join(main_content_parts)
                    sections.append({
                        'heading': '',
                        'content': main_content,
                        'subsections': []
                    })

        return sections

    def _split_by_articles(self, text: str) -> List[Dict[str, Any]]:
        """
        按法律条文进行智能分割

        Args:
            text: 清理后的文本

        Returns:
            按条文分割的sections列表
        """
        import re
        
        sections = []
        
        # 查找标题（包含管理办法、条例等）
        title_match = re.search(r'(.*?)(?:管理办法|条例|规定|办法|细则|规则)', text)
        title_content = ""
        if title_match:
            title_content = title_match.group(0).strip()
            if title_content:
                sections.append({
                    'heading': title_content,
                    'content': title_content,
                    'subsections': []
                })
        
        # 使用统一的结构识别器提取法律条文
        legal_sections = self.structure_detector.extract_legal_sections(text)

        # 转换为articles格式以保持兼容性
        articles = []
        for section in legal_sections:
            if section['type'] == 'article':  # 只处理条文
                # 创建一个模拟的match对象
                class MockMatch:
                    def __init__(self, heading, content):
                        self._groups = (heading, content)

                    def groups(self):
                        return self._groups

                    def group(self, index):
                        return self._groups[index - 1] if index <= len(self._groups) else ""

                articles.append(MockMatch(section['heading'], section['content']))
        
        if articles:
            article_sections = []
            for i, match in enumerate(articles):
                heading = match.group(1).strip() if match.groups() and len(match.groups()) >= 1 else f"条文 {i+1}"
                content = ""
                if match.groups() and len(match.groups()) >= 2:
                    content = (match.group(1) + "\n" + match.group(2)).strip()
                else:
                    content = match.group(0).strip()
                
                if content and len(content) > 10:  # 过滤太短的内容
                    article_sections.append({
                        'heading': heading,
                        'content': content,
                        'subsections': []
                    })
            
            # 确保至少有合理的条文分割
            if len(article_sections) >= 2:
                sections.extend(article_sections)
            elif article_sections:
                # 如果只有一个条文但是内容很长，尝试进一步分割
                single_section = article_sections[0]
                if len(single_section['content']) > 500:
                    # 按段落分割
                    paragraphs = [p.strip() for p in single_section['content'].split('\n\n') if p.strip()]
                    if len(paragraphs) > 3:
                        # 按段落创建多个sections
                        for i, para in enumerate(paragraphs):
                            if len(para) > 20:  # 过滤太短的段落
                                sections.append({
                                    'heading': f"{single_section['heading']} - 段落 {i+1}",
                                    'content': para,
                                    'subsections': []
                                })
                    else:
                        sections.append(single_section)
                else:
                    sections.append(single_section)
        else:
            # 如果没有找到条文，使用基于段落的分割
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) > 2:
                # 检查是否有类似条文的段落
                article_like_paragraphs = []
                for i, para in enumerate(paragraphs):
                    if re.match(r'^第[一二三四五六七八九十百千万\d]+[条章]', para):
                        article_like_paragraphs.append({
                            'heading': para.split('\n')[0],  # 第一行作为标题
                            'content': para,
                            'subsections': []
                        })
                    elif len(para) > 50:  # 过滤太短的段落
                        article_like_paragraphs.append({
                            'heading': f"段落 {i+1}",
                            'content': para,
                            'subsections': []
                        })
                
                if len(article_like_paragraphs) >= 2:
                    sections.extend(article_like_paragraphs)
                else:
                    # 使用简单的标题+内容结构
                    if title_content and len(paragraphs) > 1:
                        main_content = '\n\n'.join(paragraphs[1:])  # 除了标题外的所有内容
                        if main_content:
                            sections.append({
                                'heading': '主要内容',
                                'content': main_content,
                                'subsections': []
                            })
                    else:
                        # 没有明显标题，将所有内容作为一个section
                        all_content = '\n\n'.join(paragraphs)
                        if all_content:
                            sections.append({
                                'heading': '文档内容',
                                'content': all_content,
                                'subsections': []
                            })
        
        return sections if sections else []

    def _clean_extracted_text(self, text: str) -> str:
        """
        清理提取的文本，修复换行和条文结构

        Args:
            text: 原始提取的文本

        Returns:
            清理后的文本
        """
        import re

        # 首先修复可能的换行问题
        # 将所有换行符统一为空格，然后重新组织
        text = re.sub(r'\s+', ' ', text)

        # 特别修复被错误分割的条文内容
        # 修复"应当对本办法第十条到第十九条"这种被分割的情况
        text = re.sub(r'应当对\s*本办法\s*第([一二三四五六七八九十百千万\d]+)条到\s*第([一二三四五六七八九十百千万\d]+)条的内容',
                     r'应当对本办法第\1条到第\2条的内容', text)

        # 修复被截断的条文内容（如"制定本"应该是"制定本办法"）
        text = re.sub(r'制定本(?!\w)', '制定本办法', text)
        text = re.sub(r'根据本(?!\w)', '根据本办法', text)
        text = re.sub(r'按照本(?!\w)', '按照本办法', text)
        text = re.sub(r'违反本(?!\w)', '违反本办法', text)

        # 在重要的法律结构前添加换行 - 使用统一的模式
        legal_patterns = self.structure_detector.get_all_legal_patterns()
        for pattern in legal_patterns:
            # 将模式转换为捕获组形式
            capture_pattern = f'({pattern.strip("^").strip("\\s*")})'
            text = re.sub(capture_pattern, r'\n\n\1', text)

        # 确保条文内容的完整性 - 修复被错误换行分割的句子
        # 如果一行以不完整的词结尾，尝试与下一行合并
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()

            # 如果当前行以不完整的词结尾（如"制定本"、"根据"等），尝试与下一行合并
            if (i + 1 < len(lines) and current_line and
                (current_line.endswith('本') or current_line.endswith('根据') or
                 current_line.endswith('按照') or current_line.endswith('违反') or
                 current_line.endswith('依据') or current_line.endswith('遵循'))):

                next_line = lines[i + 1].strip()
                # 如果下一行不是法律标题，则合并
                if next_line and not self.structure_detector.is_legal_heading(next_line):
                    merged_line = current_line + next_line
                    fixed_lines.append(merged_line)
                    i += 2  # 跳过下一行
                    continue

            fixed_lines.append(current_line)
            i += 1

        text = '\n'.join(fixed_lines)

        # 在序号前添加换行
        text = re.sub(r'(\（[一二三四五六七八九十\d]+\）)', r'\n\1', text)
        text = re.sub(r'(\([一二三四五六七八九十\d]+\))', r'\n\1', text)

        # 在"前款"、"本条"等引用前添加换行，但要避免破坏条文的完整性
        text = re.sub(r'(?<!\w)(前款)', r'\n\1', text)  # 前款前面不是字母数字时才换行
        text = re.sub(r'(?<!\w)(本条)', r'\n\1', text)   # 本条前面不是字母数字时才换行
        # 不对"本办法"添加换行，因为它经常出现在条文中间

        # 清理多余的空白和换行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # 最多两个连续换行
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # 移除行首空白
        text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)  # 移除行尾空白

        # 确保文档开头没有多余换行
        text = text.strip()

        return text
