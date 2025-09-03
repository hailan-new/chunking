#!/usr/bin/env python3
"""
Document splitter factory for automatic format detection and splitter selection.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Type, Union
from pathlib import Path

from .base import BaseSplitter
from .docx_splitter import DocxSplitter
from .pdf_splitter import PdfSplitter
from .wps_splitter import WpsSplitter

logger = logging.getLogger(__name__)


class SplitterFactory:
    """
    Factory class for creating appropriate document splitters based on file format.
    
    Automatically detects file format and returns the most suitable splitter instance.
    Supports DOCX, DOC, PDF, WPS formats with intelligent fallback mechanisms.
    """
    
    # 格式到splitter类的映射
    FORMAT_SPLITTER_MAP = {
        'docx': DocxSplitter,
        'doc': DocxSplitter,  # DOC files are handled by DocxSplitter with conversion
        'pdf': PdfSplitter,
        'wps': WpsSplitter,
    }
    
    # 支持的文件格式
    SUPPORTED_FORMATS = list(FORMAT_SPLITTER_MAP.keys())
    
    def __init__(self):
        """Initialize the splitter factory."""
        self._splitter_cache = {}
        logger.info(f"SplitterFactory initialized. Supported formats: {self.SUPPORTED_FORMATS}")
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        Get list of all supported file formats.
        
        Returns:
            List of supported file extensions (without dots)
        """
        return cls.SUPPORTED_FORMATS.copy()
    
    @classmethod
    def detect_file_format(cls, file_path: str) -> str:
        """
        Detect file format from file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File format (extension without dot, lowercase)
        """
        return Path(file_path).suffix.lower().lstrip('.')
    
    @classmethod
    def is_supported_format(cls, file_path: str) -> bool:
        """
        Check if file format is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if format is supported, False otherwise
        """
        format_type = cls.detect_file_format(file_path)
        return format_type in cls.SUPPORTED_FORMATS
    
    def create_splitter(self, file_path: str, **kwargs) -> BaseSplitter:
        """
        Create appropriate splitter for the given file.
        
        Args:
            file_path: Path to the document file
            **kwargs: Additional arguments to pass to the splitter constructor
            
        Returns:
            Appropriate splitter instance
            
        Raises:
            ValueError: If file format is not supported or file doesn't exist
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        # 检测文件格式
        format_type = self.detect_file_format(file_path)
        
        if not self.is_supported_format(file_path):
            raise ValueError(f"Unsupported file format: {format_type}. Supported formats: {self.SUPPORTED_FORMATS}")
        
        # 获取对应的splitter类
        splitter_class = self.FORMAT_SPLITTER_MAP[format_type]
        
        # 创建splitter实例
        logger.info(f"Creating {splitter_class.__name__} for {format_type.upper()} file: {file_path}")

        try:
            # 根据splitter类型过滤参数
            filtered_kwargs = self._filter_kwargs_for_splitter(splitter_class, kwargs)

            # 为PDF文件添加法律文档的特殊配置
            if format_type == 'pdf':
                # 检查是否是法律文档处理上下文
                if self._is_legal_document_context(file_path, kwargs):
                    filtered_kwargs['document_type'] = 'legal'
                    # 添加法律文档的特殊模式
                    filtered_kwargs['legal_patterns'] = [
                        r'^第[一二三四五六七八九十百千万\d]+条\s*',  # 第X条
                        r'^第[一二三四五六七八九十百千万\d]+章\s*',  # 第X章
                        r'^第[一二三四五六七八九十百千万\d]+节\s*',  # 第X节
                        r'^第[一二三四五六七八九十百千万\d]+编\s*',  # 第X编
                        r'^第[一二三四五六七八九十百千万\d]+篇\s*',  # 第X篇
                    ]
                    logger.info("Configured PDF splitter for legal document processing")

            splitter = splitter_class(**filtered_kwargs)
            return splitter
        except Exception as e:
            logger.error(f"Failed to create splitter for {format_type} file: {e}")
            raise ValueError(f"Failed to create splitter for {format_type} file: {e}")

    def _is_legal_document_context(self, file_path: str, kwargs: dict) -> bool:
        """
        检测是否是法律文档处理上下文

        Args:
            file_path: 文件路径
            kwargs: 传入的参数

        Returns:
            True if this is a legal document context
        """
        # 检查调用栈，看是否来自LegalClauseSplitter
        import inspect

        # 检查调用栈
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            # 检查是否在LegalClauseSplitter的方法中
            if 'self' in frame_locals:
                obj = frame_locals['self']
                if obj.__class__.__name__ == 'LegalClauseSplitter':
                    return True

        # 检查文件路径是否包含法律相关关键词
        legal_keywords = ['law', 'legal', 'regulation', 'rule', 'act', '法', '条例', '规定', '办法', '法律']
        file_path_lower = file_path.lower()

        for keyword in legal_keywords:
            if keyword in file_path_lower:
                return True

        # 检查kwargs中是否有法律文档的标识
        if kwargs.get('document_type') == 'legal':
            return True

        return False

    def split_document(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Split document using appropriate splitter.
        
        Args:
            file_path: Path to the document file
            **kwargs: Additional arguments to pass to the splitter
            
        Returns:
            List of hierarchical sections
        """
        splitter = self.create_splitter(file_path, **kwargs)
        return splitter.split(file_path)
    
    def split_and_flatten(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Split document and return flattened chunks.
        
        Args:
            file_path: Path to the document file
            **kwargs: Additional arguments to pass to the splitter
            
        Returns:
            List of flattened chunks
        """
        splitter = self.create_splitter(file_path, **kwargs)
        sections = splitter.split(file_path)
        return splitter.flatten(sections)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information including format support.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        info = BaseSplitter.get_file_info(file_path)
        
        # 添加格式支持信息
        info['supported'] = self.is_supported_format(file_path)
        
        if info['supported']:
            format_type = info['format']
            splitter_class = self.FORMAT_SPLITTER_MAP[format_type]
            info['splitter_class'] = splitter_class.__name__
            info['splitter_module'] = splitter_class.__module__
        else:
            info['splitter_class'] = None
            info['splitter_module'] = None
        
        return info
    
    def test_format_support(self, file_path: str) -> Dict[str, Any]:
        """
        Test format support and splitter creation for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with test results
        """
        result = {
            'file_path': file_path,
            'file_exists': os.path.exists(file_path),
            'format_detected': self.detect_file_format(file_path),
            'format_supported': False,
            'splitter_created': False,
            'error': None
        }
        
        if not result['file_exists']:
            result['error'] = "File not found"
            return result
        
        result['format_supported'] = self.is_supported_format(file_path)
        
        if not result['format_supported']:
            result['error'] = f"Unsupported format: {result['format_detected']}"
            return result
        
        # 尝试创建splitter
        try:
            splitter = self.create_splitter(file_path)
            result['splitter_created'] = True
            result['splitter_class'] = splitter.__class__.__name__
            
            # 对于特殊格式，进行额外测试
            if result['format_detected'] == 'wps':
                if hasattr(splitter, 'test_conversion'):
                    result['conversion_test'] = splitter.test_conversion(file_path)
                    result['conversion_info'] = splitter.get_conversion_info(file_path)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_format_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Get capabilities information for all supported formats.
        
        Returns:
            Dictionary mapping formats to their capabilities
        """
        capabilities = {}
        
        for format_type, splitter_class in self.FORMAT_SPLITTER_MAP.items():
            capabilities[format_type] = {
                'splitter_class': splitter_class.__name__,
                'module': splitter_class.__module__,
                'description': splitter_class.__doc__.split('\n')[0] if splitter_class.__doc__ else "No description",
                'supports_conversion': format_type in ['doc', 'wps'],
                'native_support': format_type in ['docx', 'pdf']
            }
        
        return capabilities

    def _filter_kwargs_for_splitter(self, splitter_class: Type[BaseSplitter], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter kwargs based on splitter class constructor parameters.

        Args:
            splitter_class: The splitter class
            kwargs: Original kwargs

        Returns:
            Filtered kwargs that match the constructor
        """
        import inspect

        # 获取构造函数的参数
        try:
            signature = inspect.signature(splitter_class.__init__)
            valid_params = set(signature.parameters.keys()) - {'self'}

            # 过滤kwargs，只保留有效参数
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

            # 记录被过滤掉的参数
            filtered_out = set(kwargs.keys()) - set(filtered_kwargs.keys())
            if filtered_out:
                logger.debug(f"Filtered out unsupported parameters for {splitter_class.__name__}: {filtered_out}")

            return filtered_kwargs

        except Exception as e:
            logger.warning(f"Failed to filter kwargs for {splitter_class.__name__}: {e}")
            # 如果过滤失败，返回基本参数
            basic_params = ['max_tokens', 'overlap', 'split_by_sentence', 'token_counter']
            return {k: v for k, v in kwargs.items() if k in basic_params}


# 全局工厂实例
_default_factory = None


def get_default_factory() -> SplitterFactory:
    """
    Get the default splitter factory instance.
    
    Returns:
        Default SplitterFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = SplitterFactory()
    return _default_factory


# 便捷函数
def split_document(file_path: str, **kwargs) -> List[Dict[str, Any]]:
    """
    便捷函数：自动检测格式并分割文档
    
    Args:
        file_path: 文档文件路径
        **kwargs: 传递给splitter的额外参数
        
    Returns:
        分割后的sections列表
    """
    factory = get_default_factory()
    return factory.split_document(file_path, **kwargs)


def split_and_flatten(file_path: str, **kwargs) -> List[Dict[str, Any]]:
    """
    便捷函数：自动检测格式并分割文档，返回扁平化chunks
    
    Args:
        file_path: 文档文件路径
        **kwargs: 传递给splitter的额外参数
        
    Returns:
        扁平化的chunks列表
    """
    factory = get_default_factory()
    return factory.split_and_flatten(file_path, **kwargs)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    便捷函数：获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    factory = get_default_factory()
    return factory.get_file_info(file_path)


def test_format_support(file_path: str) -> Dict[str, Any]:
    """
    便捷函数：测试格式支持
    
    Args:
        file_path: 文件路径
        
    Returns:
        测试结果字典
    """
    factory = get_default_factory()
    return factory.test_format_support(file_path)
