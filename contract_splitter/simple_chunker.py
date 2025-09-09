#!/usr/bin/env python3
"""
简单粗暴的文档chunking模块
不依赖文档结构，纯粹基于文本长度和句子边界进行分割
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SimpleChunker:
    """
    简单粗暴的文档chunker
    
    特点:
    1. 在max_chunk_size范围内尽量取最大chunk
    2. chunk必须以完整句子结尾（换行、句号、叹号）
    3. 支持overlap_ratio比例的重叠
    4. 下一个chunk从完整句子开头开始
    5. 复用现有文档转换方法，不使用分层结构
    """
    
    def __init__(self, max_chunk_size: int = 1500, overlap_ratio: float = 0.1):
        """
        初始化SimpleChunker
        
        Args:
            max_chunk_size: 最大chunk大小（字符数）
            overlap_ratio: 重叠比例（0.0-1.0）
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio
        self.min_overlap_size = int(max_chunk_size * overlap_ratio)
        
        # 句子结束标记
        self.sentence_endings = ['\n', '。', '！', '？', '.', '!', '?']
        
        logger.info(f"SimpleChunker initialized: max_size={max_chunk_size}, overlap_ratio={overlap_ratio}")
    
    def chunk_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        对文件进行chunking
        
        Args:
            file_path: 文件路径
            
        Returns:
            List of chunk dictionaries with 'content', 'start_pos', 'end_pos', 'chunk_id'
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 提取文本
        text = self._extract_text_from_file(file_path)
        
        if not text.strip():
            logger.warning(f"No text extracted from {file_path}")
            return []
        
        # 进行chunking
        chunks = self._chunk_text(text)
        
        # 添加元数据
        for i, chunk in enumerate(chunks):
            chunk.update({
                'chunk_id': i + 1,
                'source_file': os.path.basename(file_path),
                'file_type': self._get_file_type(file_path),
                'total_chunks': len(chunks)
            })
        
        logger.info(f"Chunked {file_path}: {len(text)} chars -> {len(chunks)} chunks")
        return chunks
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        对纯文本进行chunking
        
        Args:
            text: 输入文本
            
        Returns:
            List of chunk dictionaries
        """
        chunks = self._chunk_text(text)
        
        # 添加基本元数据
        for i, chunk in enumerate(chunks):
            chunk.update({
                'chunk_id': i + 1,
                'source_file': 'text_input',
                'file_type': 'text',
                'total_chunks': len(chunks)
            })
        
        return chunks
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        从文件中提取文本，复用现有的文档转换方法
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本
        """
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_ext == '.wps':
                return self._extract_from_wps(file_path)
            elif file_ext == '.rtf':
                return self._extract_from_rtf(file_path)
            elif file_ext == '.txt':
                return self._extract_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """从PDF提取文本"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            text_parts = []
            
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text.strip())
            
            doc.close()
            return '\n\n'.join(text_parts)
            
        except ImportError:
            logger.warning("PyMuPDF not available, trying PyPDF2")
            try:
                import PyPDF2
                
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_parts = []
                    
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text.strip():
                            text_parts.append(text.strip())
                    
                    return '\n\n'.join(text_parts)
                    
            except ImportError:
                logger.error("No PDF library available")
                return ""
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return ""
    
    def _extract_from_docx(self, file_path: str) -> str:
        """从DOCX/DOC提取文本"""
        try:
            from contract_splitter.docx_splitter import DocxSplitter
            
            # 使用现有的DOCX splitter提取文本
            splitter = DocxSplitter()
            
            # 直接提取文本而不进行结构化分割
            if hasattr(splitter, '_extract_text_from_docx'):
                return splitter._extract_text_from_docx(file_path)
            else:
                # Fallback: 使用python-docx
                import docx
                
                doc = docx.Document(file_path)
                text_parts = []
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text.strip())
                
                return '\n\n'.join(text_parts)
                
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            return ""
    
    def _extract_from_wps(self, file_path: str) -> str:
        """从WPS提取文本"""
        try:
            from contract_splitter.wps_splitter import WpsSplitter
            from contract_splitter.wps_processor import WPSProcessor
            
            # 使用WPS processor转换为RTF然后提取文本
            processor = WPSProcessor()
            rtf_content = processor.convert_wps_to_rtf(file_path)
            
            if rtf_content:
                return self._extract_text_from_rtf_content(rtf_content)
            else:
                logger.warning(f"Failed to convert WPS file: {file_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting WPS: {e}")
            return ""
    
    def _extract_from_rtf(self, file_path: str) -> str:
        """从RTF提取文本"""
        try:
            from contract_splitter.rtf_processor import RTFProcessor
            
            processor = RTFProcessor()
            return processor.extract_text_from_rtf(file_path)
            
        except Exception as e:
            logger.error(f"Error extracting RTF: {e}")
            return ""
    
    def _extract_text_from_rtf_content(self, rtf_content: str) -> str:
        """从RTF内容提取文本"""
        try:
            from striprtf.striprtf import rtf_to_text
            return rtf_to_text(rtf_content)
        except Exception as e:
            logger.error(f"Error extracting text from RTF content: {e}")
            return ""
    
    def _extract_from_txt(self, file_path: str) -> str:
        """从TXT提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading TXT file: {e}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting TXT: {e}")
            return ""
    
    def _chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        对文本进行chunking的核心逻辑
        
        Args:
            text: 输入文本
            
        Returns:
            List of chunk dictionaries
        """
        if not text.strip():
            return []
        
        chunks = []
        text_length = len(text)
        current_pos = 0
        
        while current_pos < text_length:
            # 确定chunk的结束位置
            chunk_end = self._find_chunk_end(text, current_pos)
            
            if chunk_end <= current_pos:
                # 无法找到合适的结束位置，强制截断
                chunk_end = min(current_pos + self.max_chunk_size, text_length)
            
            # 提取chunk内容
            chunk_content = text[current_pos:chunk_end].strip()
            
            if chunk_content:
                chunks.append({
                    'content': chunk_content,
                    'start_pos': current_pos,
                    'end_pos': chunk_end,
                    'length': len(chunk_content)
                })
            
            # 计算下一个chunk的开始位置（考虑重叠）
            current_pos = self._find_next_start(text, chunk_end, current_pos)
            
            # 防止无限循环
            if current_pos >= text_length:
                break
        
        return chunks
    
    def _find_chunk_end(self, text: str, start_pos: int) -> int:
        """
        找到chunk的结束位置，必须以完整句子结尾
        
        Args:
            text: 文本
            start_pos: 开始位置
            
        Returns:
            结束位置
        """
        max_end = min(start_pos + self.max_chunk_size, len(text))
        
        # 从最大位置向前查找句子结束标记
        for pos in range(max_end - 1, start_pos, -1):
            if text[pos] in self.sentence_endings:
                return pos + 1
        
        # 如果找不到句子结束标记，返回最大位置
        return max_end
    
    def _find_next_start(self, text: str, prev_end: int, prev_start: int) -> int:
        """
        找到下一个chunk的开始位置，考虑重叠
        
        Args:
            text: 文本
            prev_end: 上一个chunk的结束位置
            prev_start: 上一个chunk的开始位置
            
        Returns:
            下一个chunk的开始位置
        """
        if prev_end >= len(text):
            return len(text)
        
        # 计算重叠大小
        chunk_size = prev_end - prev_start
        overlap_size = min(self.min_overlap_size, chunk_size // 2)
        
        # 从重叠位置开始查找完整句子的开头
        overlap_start = max(prev_start, prev_end - overlap_size)
        
        # 查找句子开始位置（句子结束标记的下一个字符）
        for pos in range(overlap_start, prev_end):
            if pos > 0 and text[pos - 1] in self.sentence_endings:
                # 跳过空白字符
                while pos < len(text) and text[pos].isspace():
                    pos += 1
                return pos
        
        # 如果找不到合适的开始位置，使用重叠位置
        return overlap_start
    
    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        return Path(file_path).suffix.lower().lstrip('.')


# 便捷函数接口
def simple_chunk_file(file_path: str, max_chunk_size: int = 1500, overlap_ratio: float = 0.1) -> List[Dict[str, Any]]:
    """
    简单chunking函数接口
    
    Args:
        file_path: 文件路径
        max_chunk_size: 最大chunk大小
        overlap_ratio: 重叠比例
        
    Returns:
        List of chunk dictionaries
    """
    chunker = SimpleChunker(max_chunk_size=max_chunk_size, overlap_ratio=overlap_ratio)
    return chunker.chunk_file(file_path)


def simple_chunk_text(text: str, max_chunk_size: int = 1500, overlap_ratio: float = 0.1) -> List[Dict[str, Any]]:
    """
    简单文本chunking函数接口
    
    Args:
        text: 输入文本
        max_chunk_size: 最大chunk大小
        overlap_ratio: 重叠比例
        
    Returns:
        List of chunk dictionaries
    """
    chunker = SimpleChunker(max_chunk_size=max_chunk_size, overlap_ratio=overlap_ratio)
    return chunker.chunk_text(text)
