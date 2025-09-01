"""
Base splitter abstract class for contract document splitting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import os


class BaseSplitter(ABC):
    """
    Abstract base class for document splitters.
    
    All splitters must implement the split method to extract hierarchical
    sections from documents and return them in a standardized format.
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200, 
                 split_by_sentence: bool = True, token_counter: str = "character"):
        """
        Initialize the base splitter.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method ("character" or "tiktoken")
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.split_by_sentence = split_by_sentence
        self.token_counter = token_counter
        
    @abstractmethod
    def split(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Split document into hierarchical sections.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of section dictionaries with structure:
            {
                "heading": "Section title",
                "content": "Section content",
                "level": 1,  # Heading level
                "subsections": [...]  # Nested subsections
            }
        """
        pass
    
    def validate_file(self, file_path: str, supported_extensions: List[str]) -> None:
        """
        Validate that the file exists and has a supported extension.
        
        Args:
            file_path: Path to the file
            supported_extensions: List of supported file extensions
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file extension is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in supported_extensions:
            raise ValueError(f"Unsupported file type: {file_ext}. "
                           f"Supported types: {supported_extensions}")
    
    def flatten(self, sections: List[Dict[str, Any]]) -> List[str]:
        """
        Flatten hierarchical sections into a list of text chunks.
        
        Args:
            sections: List of hierarchical section dictionaries
            
        Returns:
            List of text chunks ready for LLM ingestion
        """
        chunks = []
        
        def extract_chunks(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])
                
                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading
                
                # Add content if present
                if content.strip():
                    chunk_text = f"{full_heading}\n\n{content}" if heading else content
                    chunks.append(chunk_text.strip())
                
                # Recursively process subsections
                if subsections:
                    extract_chunks(subsections, full_heading)
        
        extract_chunks(sections)
        return chunks


class ContractSplitter:
    """
    Main contract splitter that automatically detects file type and uses
    appropriate splitter implementation.
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200, 
                 split_by_sentence: bool = True, token_counter: str = "character"):
        """
        Initialize the contract splitter.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method ("character" or "tiktoken")
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.split_by_sentence = split_by_sentence
        self.token_counter = token_counter
        
        # Lazy import to avoid circular dependencies
        self._docx_splitter = None
        self._pdf_splitter = None
    
    def _get_docx_splitter(self):
        """Lazy initialization of DOCX splitter."""
        if self._docx_splitter is None:
            from .docx_splitter import DocxSplitter
            self._docx_splitter = DocxSplitter(
                max_tokens=self.max_tokens,
                overlap=self.overlap,
                split_by_sentence=self.split_by_sentence,
                token_counter=self.token_counter
            )
        return self._docx_splitter
    
    def _get_pdf_splitter(self):
        """Lazy initialization of PDF splitter."""
        if self._pdf_splitter is None:
            from .pdf_splitter import PdfSplitter
            self._pdf_splitter = PdfSplitter(
                max_tokens=self.max_tokens,
                overlap=self.overlap,
                split_by_sentence=self.split_by_sentence,
                token_counter=self.token_counter
            )
        return self._pdf_splitter
    
    def split(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Split document into hierarchical sections based on file type.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of hierarchical section dictionaries
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.doc', '.docx']:
            return self._get_docx_splitter().split(file_path)
        elif file_ext == '.pdf':
            return self._get_pdf_splitter().split(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. "
                           f"Supported types: .doc, .docx, .pdf")
    
    def flatten(self, sections: List[Dict[str, Any]]) -> List[str]:
        """
        Flatten hierarchical sections into a list of text chunks.

        Args:
            sections: List of hierarchical section dictionaries

        Returns:
            List of text chunks ready for LLM ingestion
        """
        chunks = []

        def extract_chunks(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                # Add content if present
                if content.strip():
                    chunk_text = f"{full_heading}\n\n{content}" if heading else content
                    chunks.append(chunk_text.strip())

                # Recursively process subsections
                if subsections:
                    extract_chunks(subsections, full_heading)

        extract_chunks(sections)
        return chunks
