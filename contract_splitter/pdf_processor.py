#!/usr/bin/env python3
"""
PDF文档处理模块
支持数字化PDF文件的文本提取和结构化处理
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# PDF处理库导入
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF文档处理器
    
    支持多种PDF处理库，优先使用最佳可用选项
    专门处理数字化PDF（非OCR扫描件）
    """
    
    def __init__(self):
        """初始化PDF处理器"""
        self.available_backends = self._detect_available_backends()
        logger.info(f"可用的PDF处理后端: {self.available_backends}")
    
    def _detect_available_backends(self) -> List[str]:
        """检测可用的PDF处理后端"""
        backends = []
        
        if PDFPLUMBER_AVAILABLE:
            backends.append("pdfplumber")
        
        if PYMUPDF_AVAILABLE:
            backends.append("pymupdf")
        
        if PYPDF2_AVAILABLE:
            backends.append("pypdf2")
        
        return backends
    
    def extract_text(self, pdf_file: str) -> Optional[str]:
        """
        从PDF文件提取文本
        
        Args:
            pdf_file: PDF文件路径
            
        Returns:
            提取的文本内容，失败返回None
        """
        if not os.path.exists(pdf_file):
            logger.error(f"PDF文件不存在: {pdf_file}")
            return None
        
        # 按优先级尝试不同的后端
        for backend in self.available_backends:
            try:
                if backend == "pdfplumber":
                    return self._extract_with_pdfplumber(pdf_file)
                elif backend == "pymupdf":
                    return self._extract_with_pymupdf(pdf_file)
                elif backend == "pypdf2":
                    return self._extract_with_pypdf2(pdf_file)
            except Exception as e:
                logger.warning(f"使用{backend}提取PDF失败: {e}")
                continue
        
        logger.error(f"所有PDF处理后端都失败: {pdf_file}")
        return None
    
    def _extract_with_pdfplumber(self, pdf_file: str) -> str:
        """使用pdfplumber提取文本"""
        text_content = []
        
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- 第{page_num + 1}页 ---\n{text}")
                except Exception as e:
                    logger.warning(f"pdfplumber处理第{page_num + 1}页失败: {e}")
                    continue
        
        if text_content:
            full_text = '\n\n'.join(text_content)
            logger.info(f"✓ pdfplumber提取成功: {len(full_text)} 字符, {len(text_content)} 页")
            return full_text
        
        raise ValueError("pdfplumber未能提取到任何文本")
    
    def _extract_with_pymupdf(self, pdf_file: str) -> str:
        """使用PyMuPDF提取文本"""
        text_content = []
        
        doc = fitz.open(pdf_file)
        try:
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text:
                        text_content.append(f"--- 第{page_num + 1}页 ---\n{text}")
                except Exception as e:
                    logger.warning(f"PyMuPDF处理第{page_num + 1}页失败: {e}")
                    continue
        finally:
            doc.close()
        
        if text_content:
            full_text = '\n\n'.join(text_content)
            logger.info(f"✓ PyMuPDF提取成功: {len(full_text)} 字符, {len(text_content)} 页")
            return full_text
        
        raise ValueError("PyMuPDF未能提取到任何文本")
    
    def _extract_with_pypdf2(self, pdf_file: str) -> str:
        """使用PyPDF2提取文本"""
        text_content = []
        
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- 第{page_num + 1}页 ---\n{text}")
                except Exception as e:
                    logger.warning(f"PyPDF2处理第{page_num + 1}页失败: {e}")
                    continue
        
        if text_content:
            full_text = '\n\n'.join(text_content)
            logger.info(f"✓ PyPDF2提取成功: {len(full_text)} 字符, {len(text_content)} 页")
            return full_text
        
        raise ValueError("PyPDF2未能提取到任何文本")
    
    def extract_with_structure(self, pdf_file: str) -> Dict[str, Any]:
        """
        提取PDF文本并尝试保持结构
        
        Args:
            pdf_file: PDF文件路径
            
        Returns:
            包含文本和结构信息的字典
        """
        if "pdfplumber" in self.available_backends:
            return self._extract_structure_with_pdfplumber(pdf_file)
        else:
            # 回退到基本文本提取
            text = self.extract_text(pdf_file)
            return {
                'text': text,
                'pages': [],
                'structure': 'basic'
            }
    
    def _extract_structure_with_pdfplumber(self, pdf_file: str) -> Dict[str, Any]:
        """使用pdfplumber提取结构化信息"""
        pages_info = []
        full_text_parts = []
        
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    # 提取文本
                    text = page.extract_text()
                    
                    # 提取表格
                    tables = page.extract_tables()
                    
                    # 页面信息
                    page_info = {
                        'page_number': page_num + 1,
                        'text': text,
                        'tables': tables,
                        'bbox': page.bbox,
                        'width': page.width,
                        'height': page.height
                    }
                    pages_info.append(page_info)
                    
                    # 构建全文
                    if text:
                        full_text_parts.append(f"--- 第{page_num + 1}页 ---\n{text}")
                    
                    # 处理表格
                    if tables:
                        for i, table in enumerate(tables):
                            table_text = self._format_table_as_text(table)
                            full_text_parts.append(f"\n--- 第{page_num + 1}页 表格{i + 1} ---\n{table_text}")
                
                except Exception as e:
                    logger.warning(f"处理第{page_num + 1}页失败: {e}")
                    continue
        
        return {
            'text': '\n\n'.join(full_text_parts),
            'pages': pages_info,
            'structure': 'enhanced'
        }
    
    def _format_table_as_text(self, table: List[List[str]]) -> str:
        """将表格格式化为文本"""
        if not table:
            return ""
        
        # 简单的表格文本格式化
        formatted_rows = []
        for row in table:
            if row:
                # 过滤空值并连接
                clean_row = [str(cell) if cell is not None else "" for cell in row]
                formatted_rows.append(" | ".join(clean_row))
        
        return "\n".join(formatted_rows)
    
    def is_digital_pdf(self, pdf_file: str) -> bool:
        """
        检测PDF是否为数字化文档（非扫描件）
        
        Args:
            pdf_file: PDF文件路径
            
        Returns:
            True表示数字化PDF，False表示可能是扫描件
        """
        try:
            # 尝试提取少量文本进行检测
            if "pdfplumber" in self.available_backends:
                with pdfplumber.open(pdf_file) as pdf:
                    # 检查前几页
                    for page in pdf.pages[:3]:
                        text = page.extract_text()
                        if text and len(text.strip()) > 50:
                            # 如果能提取到足够的文本，认为是数字化PDF
                            return True
            
            # 如果提取不到文本，可能是扫描件
            return False
        
        except Exception as e:
            logger.warning(f"检测PDF类型失败: {e}")
            return False


# 便捷函数
def extract_pdf_text(pdf_file: str) -> Optional[str]:
    """
    便捷函数：提取PDF文本
    
    Args:
        pdf_file: PDF文件路径
        
    Returns:
        提取的文本内容
    """
    processor = PDFProcessor()
    return processor.extract_text(pdf_file)


def is_digital_pdf(pdf_file: str) -> bool:
    """
    便捷函数：检测是否为数字化PDF
    
    Args:
        pdf_file: PDF文件路径
        
    Returns:
        True表示数字化PDF
    """
    processor = PDFProcessor()
    return processor.is_digital_pdf(pdf_file)
