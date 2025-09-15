"""
Contract Splitter Package

A Python package for splitting contract documents (.doc, .docx, .pdf, .wps) into
hierarchical sections with size constraints. Supports Chinese documents.

Main Classes:
    SplitterFactory: Factory for automatic format detection and splitter selection
    ContractSplitter: Main interface for document splitting
    BaseSplitter: Abstract base class for custom splitters
    DocxSplitter: Splitter for Word documents (.docx, .doc)
    PdfSplitter: Splitter for PDF documents
    WpsSplitter: Splitter for WPS documents

Example Usage:
    # Using factory (recommended)
    from contract_splitter import split_document
    chunks = split_document("contract.docx", max_tokens=2000)

    # Using specific splitter
    from contract_splitter import DocxSplitter
    splitter = DocxSplitter(max_tokens=2000, overlap=200)
    sections = splitter.split("contract.docx")
    chunks = splitter.flatten(sections)
"""

__version__ = "2.0.0"
__author__ = "Contract Splitter Team"
__email__ = "contact@example.com"

# Import main classes for easy access
from .base import ContractSplitter, BaseSplitter
from .docx_splitter import DocxSplitter
from .pdf_splitter import PdfSplitter
from .wps_splitter import WpsSplitter
from .excel_splitter import ExcelSplitter
from .splitter_factory import SplitterFactory, get_default_factory
from .simple_chunker import SimpleChunker, simple_chunk_file, simple_chunk_text
from .utils import count_tokens, sliding_window_split, clean_text
from .converter import DocumentConverter, convert_doc_to_docx, is_conversion_available

# Import domain helpers
try:
    from .domain_helpers import (
        LegalClauseSplitter,
        DomainContractSplitter,
        RegulationSplitter,
        split_legal_document,
        split_contract,
        split_regulation
    )
except ImportError:
    # Domain helpers might not be available in minimal installations
    pass

# Import configuration system
try:
    from .config import Config, get_config, reset_config
    from .llm_client import create_llm_client
except ImportError:
    # Configuration system might not be available
    pass

# Define what gets imported with "from contract_splitter import *"
__all__ = [
    # Core classes
    'SplitterFactory',
    'get_default_factory',
    'ContractSplitter',
    'BaseSplitter',
    'DocxSplitter',
    'PdfSplitter',
    'WpsSplitter',
    'ExcelSplitter',
    'DocumentConverter',
    'SimpleChunker',
    'simple_chunk_file',
    'simple_chunk_text',

    # Domain helpers (if available)
    'LegalClauseSplitter',
    'DomainContractSplitter',
    'RegulationSplitter',

    # Utility functions
    'convert_doc_to_docx',
    'is_conversion_available',
    'count_tokens',
    'sliding_window_split',
    'clean_text',

    # Convenience functions
    'split_document',
    'flatten_sections',
    'simple_chunk_file',
    'extract_text',
    'split_legal_document',
    'split_contract',
    'split_regulation',

    # Configuration (if available)
    'Config',
    'get_config',
    'reset_config',
    'create_llm_client',
]

# Package metadata
__package_info__ = {
    'name': 'contract_splitter',
    'version': __version__,
    'description': 'Split contract documents into hierarchical sections with size constraints',
    'author': __author__,
    'author_email': __email__,
    'url': 'https://github.com/example/contract_splitter',
    'license': 'MIT',
    'python_requires': '>=3.7',
    'keywords': ['document', 'splitting', 'contract', 'pdf', 'docx', 'chinese'],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
}

# Configure logging for the package
import logging

# Create package logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler if no handlers exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)

# Convenience function for quick splitting
def split_document(file_path: str, max_tokens: int = 2000, overlap: int = 200,
                  split_by_sentence: bool = True, token_counter: str = "character",
                  strict_max_tokens: bool = False, **kwargs):
    """
    Convenience function to quickly split a document using automatic format detection.

    Args:
        file_path: Path to the document file (.docx, .doc, .pdf, .wps, .xlsx, .xls, .xlsm)
        max_tokens: Maximum tokens per chunk
        overlap: Overlap length for sliding window
        split_by_sentence: Whether to split at sentence boundaries
        token_counter: Token counting method ("character" or "tiktoken")
        strict_max_tokens: Whether to strictly enforce max_tokens limit
        **kwargs: Additional arguments passed to the splitter (e.g., extract_mode for Excel)

    Returns:
        List of flattened text chunks ready for LLM ingestion
    """
    factory = get_default_factory()
    return factory.split_and_flatten(
        file_path,
        max_tokens=max_tokens,
        overlap=overlap,
        split_by_sentence=split_by_sentence,
        token_counter=token_counter,
        strict_max_tokens=strict_max_tokens,
        **kwargs
    )

def flatten_sections(sections, max_tokens: int = 2000, overlap: int = 200, 
                    split_by_sentence: bool = True, token_counter: str = "character"):
    """
    Convenience function to flatten hierarchical sections.
    
    Args:
        sections: List of hierarchical section dictionaries
        max_tokens: Maximum tokens per chunk
        overlap: Overlap length for sliding window
        split_by_sentence: Whether to split at sentence boundaries
        token_counter: Token counting method ("character" or "tiktoken")
        
    Returns:
        List of text chunks ready for LLM ingestion
    """
    splitter = ContractSplitter(
        max_tokens=max_tokens,
        overlap=overlap,
        split_by_sentence=split_by_sentence,
        token_counter=token_counter
    )
    return splitter.flatten(sections)


def simple_chunk_file(file_path: str, max_chunk_size: int = 800, overlap_ratio: float = 0.1):
    """
    Simple chunking function for any supported file format.

    Args:
        file_path: Path to the file
        max_chunk_size: Maximum chunk size in characters
        overlap_ratio: Overlap ratio between chunks (0.0 to 0.5)

    Returns:
        List of chunk dictionaries with 'content' and metadata
    """
    chunker = SimpleChunker(max_chunk_size=max_chunk_size, overlap_ratio=overlap_ratio)
    return chunker.chunk_file(file_path)


def extract_text(file_path: str) -> str:
    """
    Extract plain text from any supported document format.

    This is the core text extraction interface that automatically detects
    the file format and uses the appropriate extractor.

    Args:
        file_path: Path to the document file

    Returns:
        Extracted plain text content

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    factory = get_default_factory()
    return factory.extract_text(file_path)

# Version check function
def check_dependencies():
    """
    Check if all required dependencies are available.

    Returns:
        Dict with dependency status
    """
    dependencies = {
        'python-docx': False,
        'pdfplumber': False,
        'PyMuPDF': False,
        'PyPDF2': False,
        'tiktoken': False,
        'win32com': False,
        'libreoffice': False
    }
    
    try:
        import docx
        dependencies['python-docx'] = True
    except ImportError:
        pass
    
    try:
        import pdfplumber
        dependencies['pdfplumber'] = True
    except ImportError:
        pass
    
    try:
        import fitz
        dependencies['PyMuPDF'] = True
    except ImportError:
        pass
    
    try:
        import PyPDF2
        dependencies['PyPDF2'] = True
    except ImportError:
        pass

    try:
        import tiktoken
        dependencies['tiktoken'] = True
    except ImportError:
        pass

    try:
        import win32com.client
        dependencies['win32com'] = True
    except ImportError:
        pass

    # Check LibreOffice
    try:
        import subprocess
        result = subprocess.run(['libreoffice', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            dependencies['libreoffice'] = True
    except:
        pass

    return dependencies

# Print dependency status on import (optional)
def print_dependency_status():
    """Print the status of optional dependencies."""
    deps = check_dependencies()
    logger.info("Contract Splitter dependency status:")
    for dep, available in deps.items():
        status = "✓" if available else "✗"
        logger.info(f"  {status} {dep}")
    
    if not deps['python-docx']:
        logger.warning("python-docx not found. DOCX support will be limited.")
    if not deps['pdfplumber'] and not deps['PyMuPDF']:
        logger.warning("Neither pdfplumber nor PyMuPDF found. PDF support will be limited.")
    if not deps['tiktoken']:
        logger.info("tiktoken not found. Using character-based token counting.")

# Uncomment the line below to print dependency status on import
# print_dependency_status()
