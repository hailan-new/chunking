#!/usr/bin/env python3
"""
Excel文档分割器
基于BaseSplitter实现，专门处理Excel文件的分割和结构化
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import BaseSplitter
from .excel_processor import ExcelProcessor
from .legal_structure_detector import LegalStructureDetector

logger = logging.getLogger(__name__)


class ExcelSplitter(BaseSplitter):
    """
    Excel文档分割器
    继承BaseSplitter，专门处理Excel文件的分割和结构化
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200, 
                 split_by_sentence: bool = True, token_counter: str = "character",
                 strict_max_tokens: bool = False, extract_mode: str = "legal_content"):
        """
        初始化Excel分割器
        
        Args:
            max_tokens: 最大token数
            overlap: 重叠长度
            split_by_sentence: 是否按句子分割
            token_counter: token计数方法
            strict_max_tokens: 是否严格限制token数
            extract_mode: 提取模式 ("legal_content", "table_structure", "all_content")
        """
        super().__init__(max_tokens, overlap, split_by_sentence, token_counter, strict_max_tokens)
        
        self.extract_mode = extract_mode
        self.excel_processor = ExcelProcessor()
        self.legal_detector = LegalStructureDetector()
        
        logger.info(f"Excel分割器初始化完成，提取模式: {extract_mode}")
    
    def split(self, file_path: str) -> List[Dict[str, Any]]:
        """
        分割Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            分割后的sections列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel文件不存在: {file_path}")
        
        if not self.excel_processor.is_excel_file(file_path):
            raise ValueError(f"不是有效的Excel文件: {file_path}")
        
        logger.info(f"开始分割Excel文件: {file_path}")
        
        # 提取文本内容
        text_content = self.excel_processor.extract_text(file_path, self.extract_mode)
        
        if not text_content:
            logger.warning(f"Excel文件无内容: {file_path}")
            return []
        
        logger.info(f"提取文本长度: {len(text_content)} 字符")
        
        # 根据提取模式选择处理方法
        if self.extract_mode == "legal_content":
            return self._split_legal_content(text_content, file_path)
        elif self.extract_mode == "table_structure":
            return self._split_table_structure(text_content, file_path)
        else:  # all_content
            return self._split_all_content(text_content, file_path)
    
    def _split_legal_content(self, text_content: str, file_path: str) -> List[Dict[str, Any]]:
        """分割法律内容"""
        sections = []
        
        # 按工作表分割
        sheet_sections = text_content.split('【工作表:')
        
        for i, sheet_section in enumerate(sheet_sections):
            if not sheet_section.strip():
                continue
            
            # 提取工作表名称
            if i == 0:
                sheet_name = "主要内容"
                content = sheet_section
            else:
                lines = sheet_section.split('\n', 1)
                sheet_name = lines[0].replace('】', '').strip()
                content = lines[1] if len(lines) > 1 else ""
            
            if not content.strip():
                continue
            
            # 检测法律结构
            legal_sections = self.legal_detector.extract_legal_sections(content)
            
            if legal_sections:
                # 有法律结构，按法律条文分割
                for j, legal_section in enumerate(legal_sections):
                    section = {
                        'heading': f"{sheet_name} - {legal_section.get('heading', f'第{j+1}部分')}",
                        'content': legal_section.get('content', ''),
                        'level': legal_section.get('level', 1),
                        'source_sheet': sheet_name,
                        'section_type': 'legal_article',
                        'subsections': []
                    }
                    sections.append(section)
            else:
                # 无明显法律结构，按内容分割
                content_sections = self._split_content_by_importance(content, sheet_name)
                sections.extend(content_sections)
        
        # 应用大小限制
        return self._apply_size_constraints(sections)
    
    def _split_table_structure(self, text_content: str, file_path: str) -> List[Dict[str, Any]]:
        """分割表格结构"""
        sections = []
        
        # 按工作表分割
        sheet_sections = text_content.split('【工作表:')
        
        for i, sheet_section in enumerate(sheet_sections):
            if not sheet_section.strip():
                continue
            
            # 提取工作表名称
            if i == 0:
                sheet_name = "主要内容"
                content = sheet_section
            else:
                lines = sheet_section.split('\n', 1)
                sheet_name = lines[0].replace('】', '').strip()
                content = lines[1] if len(lines) > 1 else ""
            
            if not content.strip():
                continue
            
            # 按表格结构分割
            table_sections = self._split_by_table_structure(content, sheet_name)
            sections.extend(table_sections)
        
        return self._apply_size_constraints(sections)
    
    def _split_all_content(self, text_content: str, file_path: str) -> List[Dict[str, Any]]:
        """分割所有内容"""
        sections = []
        
        # 按工作表分割
        sheet_sections = text_content.split('【工作表:')
        
        for i, sheet_section in enumerate(sheet_sections):
            if not sheet_section.strip():
                continue
            
            # 提取工作表名称
            if i == 0:
                sheet_name = "主要内容"
                content = sheet_section
            else:
                lines = sheet_section.split('\n', 1)
                sheet_name = lines[0].replace('】', '').strip()
                content = lines[1] if len(lines) > 1 else ""
            
            if not content.strip():
                continue
            
            # 简单按长度分割
            content_sections = self._split_by_length(content, sheet_name)
            sections.extend(content_sections)
        
        return self._apply_size_constraints(sections)
    
    def _split_content_by_importance(self, content: str, sheet_name: str) -> List[Dict[str, Any]]:
        """按内容重要性分割"""
        sections = []
        lines = content.split('\n')
        
        current_section = {
            'heading': f"{sheet_name} - 重要内容",
            'content': '',
            'level': 1,
            'source_sheet': sheet_name,
            'section_type': 'important_content',
            'subsections': []
        }
        
        normal_section = {
            'heading': f"{sheet_name} - 一般内容",
            'content': '',
            'level': 1,
            'source_sheet': sheet_name,
            'section_type': 'normal_content',
            'subsections': []
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否为重要内容（以★标记）
            if line.startswith('★'):
                current_section['content'] += line[1:].strip() + '\n'
            else:
                normal_section['content'] += line + '\n'
        
        if current_section['content'].strip():
            sections.append(current_section)
        
        if normal_section['content'].strip():
            sections.append(normal_section)
        
        return sections
    
    def _split_by_table_structure(self, content: str, sheet_name: str) -> List[Dict[str, Any]]:
        """按表格结构分割"""
        sections = []
        lines = content.split('\n')
        
        current_section = None
        section_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否为表头
            if line.startswith('表头:'):
                # 开始新的表格section
                if current_section and current_section['content'].strip():
                    sections.append(current_section)
                
                current_section = {
                    'heading': f"{sheet_name} - 表格{section_counter}",
                    'content': line + '\n',
                    'level': 1,
                    'source_sheet': sheet_name,
                    'section_type': 'table',
                    'subsections': []
                }
                section_counter += 1
            
            elif line.startswith('-' * 10):  # 分隔线
                if current_section:
                    current_section['content'] += line + '\n'
            
            else:
                # 表格数据行
                if current_section is None:
                    current_section = {
                        'heading': f"{sheet_name} - 内容{section_counter}",
                        'content': '',
                        'level': 1,
                        'source_sheet': sheet_name,
                        'section_type': 'content',
                        'subsections': []
                    }
                    section_counter += 1
                
                current_section['content'] += line + '\n'
        
        # 添加最后一个section
        if current_section and current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _split_by_length(self, content: str, sheet_name: str) -> List[Dict[str, Any]]:
        """按长度分割"""
        sections = []
        lines = content.split('\n')
        
        current_section = {
            'heading': f"{sheet_name} - 第1部分",
            'content': '',
            'level': 1,
            'source_sheet': sheet_name,
            'section_type': 'content_part',
            'subsections': []
        }
        
        section_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否超过长度限制
            if len(current_section['content']) + len(line) > self.max_tokens:
                # 保存当前section
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # 开始新section
                section_counter += 1
                current_section = {
                    'heading': f"{sheet_name} - 第{section_counter}部分",
                    'content': line + '\n',
                    'level': 1,
                    'source_sheet': sheet_name,
                    'section_type': 'content_part',
                    'subsections': []
                }
            else:
                current_section['content'] += line + '\n'
        
        # 添加最后一个section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _apply_size_constraints(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用大小限制到sections

        Args:
            sections: sections列表

        Returns:
            应用大小限制后的sections
        """
        if not sections:
            return sections

        from .utils import count_tokens, sliding_window_split

        result = []

        for section in sections:
            content = section.get('content', '')

            if content and count_tokens(content, self.token_counter) > self.max_tokens:
                # 内容超过限制，需要分割
                chunks = sliding_window_split(
                    content,
                    self.max_tokens,
                    self.overlap,
                    self.split_by_sentence,
                    self.token_counter
                )

                # 为每个chunk创建新的section
                for i, chunk in enumerate(chunks):
                    new_section = section.copy()
                    new_section['content'] = chunk
                    new_section['subsections'] = []
                    if i > 0:
                        new_section['heading'] = f"{section['heading']} (Part {i+1})"
                    result.append(new_section)
            else:
                result.append(section)

        return result

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取Excel文件信息

        Args:
            file_path: Excel文件路径

        Returns:
            文件信息字典
        """
        return self.excel_processor.get_file_info(file_path)

    def extract_text(self, file_path: str) -> str:
        """
        Extract plain text from Excel document efficiently

        Args:
            file_path: Path to the Excel file

        Returns:
            Extracted plain text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel文件不存在: {file_path}")

        if not self.excel_processor.is_excel_file(file_path):
            raise ValueError(f"不是有效的Excel文件: {file_path}")

        logger.info(f"提取Excel文本: {file_path}")

        # 直接使用ExcelProcessor提取文本，不进行分割处理
        text_content = self.excel_processor.extract_text(file_path, mode="all_content")

        if not text_content:
            logger.warning(f"Excel文件无内容: {file_path}")
            return ""

        # 清理格式标记，返回纯文本
        cleaned_text = self._clean_excel_text(text_content)

        logger.info(f"提取文本长度: {len(cleaned_text)} 字符")
        return cleaned_text

    def _clean_excel_text(self, text_content: str) -> str:
        """
        清理Excel提取的文本，移除格式标记

        Args:
            text_content: 原始文本内容

        Returns:
            清理后的纯文本
        """
        import re

        # 移除工作表标记
        text = re.sub(r'【工作表:[^】]*】', '', text_content)

        # 移除表头标记
        text = re.sub(r'表头:', '', text)

        # 移除分隔线
        text = re.sub(r'-{10,}', '', text)

        # 移除重要内容标记
        text = re.sub(r'★\s*', '', text)

        # 清理多余的空行
        text = re.sub(r'\n\s*\n', '\n', text)

        # 清理首尾空白
        text = text.strip()

        return text
