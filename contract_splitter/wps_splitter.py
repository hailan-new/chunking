#!/usr/bin/env python3
"""
WPS document splitter for extracting hierarchical sections from WPS documents.
"""

import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseSplitter
from .utils import count_tokens, sliding_window_split, clean_text, detect_heading_level
from .wps_processor import WPSProcessor
from .docx_splitter import DocxSplitter
from .rtf_processor import RTFProcessor

logger = logging.getLogger(__name__)


class WpsSplitter(BaseSplitter):
    """
    Splitter for WPS files using conversion to DOCX format.
    
    Converts WPS files to DOCX format and then uses DocxSplitter
    for hierarchical section extraction. Supports Chinese documents.
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200,
                 split_by_sentence: bool = True, token_counter: str = "character",
                 chunking_strategy: str = "finest_granularity",
                 strict_max_tokens: bool = False,
                 use_llm_heading_detection: bool = False,
                 llm_config: dict = None):
        """
        Initialize WPS splitter.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method
            chunking_strategy: Chunking strategy for flatten operation
            strict_max_tokens: Whether to strictly enforce max_tokens limit
            use_llm_heading_detection: Whether to use LLM for heading detection
            llm_config: LLM configuration dict
        """
        super().__init__(max_tokens, overlap, split_by_sentence, token_counter,
                        chunking_strategy, strict_max_tokens)
        
        # 初始化WPS处理器
        self.wps_processor = WPSProcessor()
        
        # 初始化DOCX处理器（用于处理转换后的文件）
        self.docx_splitter = DocxSplitter(
            max_tokens=max_tokens,
            overlap=overlap,
            split_by_sentence=split_by_sentence,
            token_counter=token_counter,
            chunking_strategy=chunking_strategy,
            strict_max_tokens=strict_max_tokens,
            use_llm_heading_detection=use_llm_heading_detection,
            llm_config=llm_config
        )

        # 初始化RTF处理器（用于处理RTF转换结果）
        self.rtf_processor = RTFProcessor()
        
        logger.info("WpsSplitter initialized with WPS conversion support")
    
    def split(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Split WPS document into hierarchical sections.

        Args:
            file_path: Path to the WPS file

        Returns:
            List of hierarchical section dictionaries
        """
        self.validate_file(file_path, ['.wps'])
        
        logger.info(f"Processing WPS file: {file_path}")
        
        # 检查WPS处理器可用性
        if not self.wps_processor.available_converters:
            raise ValueError("No WPS converters available. Please install LibreOffice or use Windows with Office.")
        
        # 使用临时目录进行转换
        with tempfile.TemporaryDirectory() as temp_dir:
            # 转换WPS到DOCX
            docx_file = self.wps_processor.convert_to_docx(file_path, temp_dir)
            
            if not docx_file or not os.path.exists(docx_file):
                raise ValueError(f"Failed to convert WPS file: {file_path}")
            
            # 检查是否有更好的源文件（ODT、DOC、RTF）
            odt_source_file = docx_file + '.odt_source'
            doc_source_file = docx_file + '.doc_source'
            rtf_source_file = docx_file + '.rtf_source'

            try:
                # 优先尝试ODT格式
                if os.path.exists(odt_source_file):
                    logger.info(f"Found ODT source file, using DOCX processor: {odt_source_file}")

                    # 将ODT转换为DOCX再处理
                    temp_docx = self._convert_to_docx_if_needed(odt_source_file, temp_dir)
                    if temp_docx:
                        sections = self.docx_splitter.split(temp_docx)

                        # 更新section信息
                        for section in sections:
                            if 'metadata' not in section:
                                section['metadata'] = {}
                            section['metadata']['original_format'] = 'wps'
                            section['metadata']['original_file'] = file_path
                            section['metadata']['conversion_method'] = 'odt'

                        logger.info(f"WPS file processed via ODT: {len(sections)} sections")
                        return sections

                # 其次尝试DOC格式
                elif os.path.exists(doc_source_file):
                    logger.info(f"Found DOC source file, using DOCX processor: {doc_source_file}")

                    # 将DOC转换为DOCX再处理
                    temp_docx = self._convert_to_docx_if_needed(doc_source_file, temp_dir)
                    if temp_docx:
                        sections = self.docx_splitter.split(temp_docx)

                        # 更新section信息
                        for section in sections:
                            if 'metadata' not in section:
                                section['metadata'] = {}
                            section['metadata']['original_format'] = 'wps'
                            section['metadata']['original_file'] = file_path
                            section['metadata']['conversion_method'] = 'doc'

                        logger.info(f"WPS file processed via DOC: {len(sections)} sections")
                        return sections

                # 最后尝试RTF格式
                elif os.path.exists(rtf_source_file):
                    logger.info(f"Found RTF source file, using RTF processor: {rtf_source_file}")

                    # 从RTF文件提取文本
                    text_content = self.rtf_processor.extract_text_from_rtf(rtf_source_file)

                    if text_content and len(text_content) > 100:  # 确保提取到了有意义的内容
                        # 将文本转换为sections格式
                        sections = self.rtf_processor.split_into_sections(text_content)

                        # 更新section信息
                        for section in sections:
                            if 'metadata' not in section:
                                section['metadata'] = {}
                            section['metadata']['original_format'] = 'wps'
                            section['metadata']['original_file'] = file_path
                            section['metadata']['conversion_method'] = 'rtf'

                        logger.info(f"WPS file processed via RTF: {len(sections)} sections, {len(text_content)} chars")
                        return sections
                    else:
                        logger.warning("RTF extraction failed or produced insufficient content, falling back to DOCX")

                # 回退到DOCX处理
                logger.info(f"Processing converted DOCX file: {docx_file}")
                sections = self.docx_splitter.split(docx_file)

                # 更新section信息，标记原始文件类型
                for section in sections:
                    if 'metadata' not in section:
                        section['metadata'] = {}
                    section['metadata']['original_format'] = 'wps'
                    section['metadata']['original_file'] = file_path
                    section['metadata']['converted_file'] = docx_file
                    section['metadata']['conversion_method'] = 'docx'

                logger.info(f"WPS file processed successfully: {len(sections)} sections")
                return sections

            except Exception as e:
                logger.error(f"Failed to process converted file: {e}")
                raise ValueError(f"Failed to process WPS file after conversion: {e}")

    def _convert_to_docx_if_needed(self, source_file: str, temp_dir: str) -> str:
        """
        如果需要，将源文件转换为DOCX格式

        Args:
            source_file: 源文件路径
            temp_dir: 临时目录

        Returns:
            转换后的DOCX文件路径，如果失败返回None
        """
        import subprocess

        try:
            # 获取文件扩展名
            file_ext = os.path.splitext(source_file)[1].lower()

            if file_ext == '.docx':
                return source_file

            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(source_file))[0]
            output_file = os.path.join(temp_dir, f"{base_name}_converted.docx")

            # 使用LibreOffice转换
            cmd = [
                'soffice', '--headless', '--convert-to', 'docx',
                '--outdir', temp_dir, source_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                # 检查转换后的文件
                expected_output = os.path.join(temp_dir, f"{base_name}.docx")
                if os.path.exists(expected_output):
                    logger.info(f"Successfully converted {file_ext} to DOCX: {expected_output}")
                    return expected_output

            logger.warning(f"Failed to convert {file_ext} to DOCX: {result.stderr}")
            return None

        except Exception as e:
            logger.warning(f"Error converting {source_file} to DOCX: {e}")
            return None
    
    def get_conversion_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get WPS file conversion information.
        
        Args:
            file_path: Path to the WPS file
            
        Returns:
            Dictionary with conversion information
        """
        return self.wps_processor.get_conversion_info(file_path)
    
    def test_conversion(self, file_path: str) -> bool:
        """
        Test if WPS file can be converted successfully.
        
        Args:
            file_path: Path to the WPS file
            
        Returns:
            True if conversion is possible, False otherwise
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                docx_file = self.wps_processor.convert_to_docx(file_path, temp_dir)
                return docx_file is not None and os.path.exists(docx_file)
        except Exception as e:
            logger.warning(f"WPS conversion test failed: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['.wps']
    
    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about the WPS processor.
        
        Returns:
            Dictionary with processor information
        """
        return {
            'processor_type': 'WpsSplitter',
            'supported_formats': self.get_supported_formats(),
            'available_converters': self.wps_processor.available_converters,
            'recommended_converter': self.wps_processor.get_conversion_info('')['recommended_converter'],
            'docx_splitter_config': {
                'max_tokens': self.docx_splitter.max_tokens,
                'overlap': self.docx_splitter.overlap,
                'chunking_strategy': self.docx_splitter.chunking_strategy,
                'strict_max_tokens': self.docx_splitter.strict_max_tokens,
                'use_llm_heading_detection': self.docx_splitter.use_llm_heading_detection
            }
        }


# 便捷函数
def split_wps_document(file_path: str, max_tokens: int = 2000, 
                      strict_max_tokens: bool = False,
                      use_llm_heading_detection: bool = False,
                      llm_config: dict = None) -> List[Dict[str, Any]]:
    """
    便捷函数：分割WPS文档
    
    Args:
        file_path: WPS文件路径
        max_tokens: 最大token数
        strict_max_tokens: 是否严格控制token数
        use_llm_heading_detection: 是否使用LLM标题检测
        llm_config: LLM配置
        
    Returns:
        分割后的sections列表
    """
    splitter = WpsSplitter(
        max_tokens=max_tokens,
        strict_max_tokens=strict_max_tokens,
        use_llm_heading_detection=use_llm_heading_detection,
        llm_config=llm_config
    )
    
    sections = splitter.split(file_path)
    return splitter.flatten(sections)


def test_wps_support(file_path: str = None) -> Dict[str, Any]:
    """
    便捷函数：测试WPS支持情况
    
    Args:
        file_path: 可选的WPS文件路径用于测试转换
        
    Returns:
        WPS支持信息字典
    """
    splitter = WpsSplitter()
    info = splitter.get_processor_info()
    
    if file_path and os.path.exists(file_path):
        info['test_conversion'] = splitter.test_conversion(file_path)
        info['conversion_info'] = splitter.get_conversion_info(file_path)
    
    return info
