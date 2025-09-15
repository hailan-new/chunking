"""
Base splitter abstract class for contract document splitting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseSplitter(ABC):
    """
    Abstract base class for document splitters.
    
    All splitters must implement the split method to extract hierarchical
    sections from documents and return them in a standardized format.
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200,
                 split_by_sentence: bool = True, token_counter: str = "character",
                 chunking_strategy: str = "finest_granularity",
                 strict_max_tokens: bool = False):
        """
        Initialize the base splitter.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method ("character" or "tiktoken")
            chunking_strategy: Chunking strategy for flatten operation
            strict_max_tokens: Whether to strictly enforce max_tokens limit
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.split_by_sentence = split_by_sentence
        self.token_counter = token_counter
        self.chunking_strategy = chunking_strategy
        self.strict_max_tokens = strict_max_tokens
        
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

    def extract_text(self, file_path: str) -> str:
        """
        Extract plain text from document

        Args:
            file_path: Path to the document file

        Returns:
            Extracted plain text content
        """
        # Default implementation: split then merge
        sections = self.split(file_path)
        return self._extract_text_from_sections(sections)

    def _extract_text_from_sections(self, sections: List[Dict[str, Any]]) -> str:
        """
        Extract text content from sections recursively

        Args:
            sections: List of section dictionaries

        Returns:
            Combined text content
        """
        text_parts = []

        for section in sections:
            # Add heading if present
            if section.get('heading'):
                text_parts.append(section['heading'])

            # Add content if present
            if section.get('content'):
                text_parts.append(section['content'])

            # Recursively process subsections
            if section.get('subsections'):
                subsection_text = self._extract_text_from_sections(section['subsections'])
                if subsection_text:
                    text_parts.append(subsection_text)

        return '\n'.join(text_parts)

    @classmethod
    def detect_file_format(cls, file_path: str) -> str:
        """
        Detect file format based on extension.

        Args:
            file_path: Path to the file

        Returns:
            File format (extension without dot, lowercase)
        """
        return Path(file_path).suffix.lower().lstrip('.')

    @classmethod
    def normalize_file_path(cls, file_path: str) -> str:
        """
        Normalize file path to handle spaces and special characters.

        Args:
            file_path: Original file path

        Returns:
            Normalized file path
        """
        return os.path.normpath(file_path)

    @classmethod
    def get_file_info(cls, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        normalized_path = cls.normalize_file_path(file_path)

        info = {
            'path': normalized_path,
            'exists': os.path.exists(normalized_path),
            'format': cls.detect_file_format(normalized_path),
            'size': 0,
            'name': os.path.basename(normalized_path),
            'directory': os.path.dirname(normalized_path)
        }

        if info['exists']:
            info['size'] = os.path.getsize(normalized_path)

        return info

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
    
    def flatten(self, sections: List[Dict[str, Any]], strategy: str = "finest_granularity") -> List[str]:
        """
        Flatten hierarchical sections into a list of text chunks.

        Args:
            sections: List of hierarchical section dictionaries
            strategy: Chunking strategy
                - "finest_granularity": 同等最细粒度拆分（默认）- 只处理叶子节点，避免重复
                - "all_levels": 所有层级拆分 - 处理所有有内容的节点
                - "parent_only": 仅父级拆分 - 只处理有内容且无子节点的父级

        Returns:
            List of text chunks ready for LLM ingestion
        """
        chunks = []

        def extract_chunks_finest_granularity(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            """同等最细粒度拆分策略：只处理叶子节点，避免重复"""
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                if subsections:
                    # 有子sections，递归处理子sections，不处理当前content
                    extract_chunks_finest_granularity(subsections, full_heading)
                else:
                    # 没有子sections，这是叶子节点，处理其content
                    # 新逻辑：当content为空时保留heading，否则只保留content
                    if content.strip():
                        # 有内容，只保留content，避免重复
                        chunks.append(content.strip())
                    elif heading.strip():
                        # 没有内容但有标题，保留标题
                        chunks.append(full_heading.strip())

        def extract_chunks_all_levels(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            """所有层级拆分策略：处理所有有内容的节点"""
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                # 处理当前节点的内容（如果有）
                # 新逻辑：当content为空时保留heading，否则只保留content
                if content.strip():
                    # 有内容，只保留content，避免重复
                    chunks.append(content.strip())
                elif heading.strip() and not subsections:
                    # 没有内容但有标题且没有子节点，保留标题
                    chunks.append(full_heading.strip())

                # 递归处理子sections
                if subsections:
                    extract_chunks_all_levels(subsections, full_heading)

        def extract_chunks_parent_only(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            """仅父级拆分策略：只处理有内容且无子节点的父级"""
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                if not subsections:
                    # 没有子sections，处理当前节点
                    # 新逻辑：当content为空时保留heading，否则只保留content
                    if content.strip():
                        # 有内容，只保留content，避免重复
                        chunks.append(content.strip())
                    elif heading.strip():
                        # 没有内容但有标题，保留标题
                        chunks.append(full_heading.strip())
                elif subsections:
                    # 有子sections，递归处理
                    extract_chunks_parent_only(subsections, full_heading)

        # 根据策略选择处理方法
        if strategy == "finest_granularity":
            extract_chunks_finest_granularity(sections)
        elif strategy == "all_levels":
            extract_chunks_all_levels(sections)
        elif strategy == "parent_only":
            extract_chunks_parent_only(sections)
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Supported: 'finest_granularity', 'all_levels', 'parent_only'")

        return chunks

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the configured method.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        from .utils import count_tokens
        return count_tokens(text, self.token_counter)

    def _apply_strict_max_tokens(self, chunks: List[str]) -> List[str]:
        """
        Apply strict max tokens control by splitting oversized chunks.

        Args:
            chunks: List of text chunks

        Returns:
            List of chunks with strict size control applied
        """
        result_chunks = []

        for chunk in chunks:
            token_count = self._count_tokens(chunk)

            if token_count <= self.max_tokens:
                # Chunk is within limit
                result_chunks.append(chunk)
            else:
                # Chunk exceeds limit, need to split
                logger.info(f"Splitting oversized chunk ({token_count} tokens > {self.max_tokens})")
                split_chunks = self._split_oversized_chunk(chunk)
                result_chunks.extend(split_chunks)

        return result_chunks

    def _split_oversized_chunk(self, chunk: str) -> List[str]:
        """
        Split an oversized chunk into smaller pieces.

        Args:
            chunk: The oversized chunk text

        Returns:
            List of smaller chunks
        """
        # Extract heading if present
        lines = chunk.split('\n')
        heading = ""
        content_start_idx = 0

        # Check if first line is a heading
        if lines and ' > ' in lines[0]:
            heading = lines[0] + '\n\n'
            content_start_idx = 1
            # Skip empty lines after heading
            while content_start_idx < len(lines) and not lines[content_start_idx].strip():
                content_start_idx += 1

        content = '\n'.join(lines[content_start_idx:])

        # Split content by sentences
        sentence_endings = ['。', '！', '？', '.', '!', '?', '；', ';']

        # Find sentence boundaries
        sentences = []
        current_sentence = ""

        for char in content:
            current_sentence += char
            if char in sentence_endings:
                sentences.append(current_sentence.strip())
                current_sentence = ""

        # Add remaining text as last sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        if not sentences:
            # No sentences found, return original chunk
            logger.warning(f"Cannot split chunk further, no sentence boundaries found")
            return [chunk]

        # Group sentences into chunks
        result_chunks = []
        current_chunk_content = ""

        for sentence in sentences:
            # Test if adding this sentence would exceed limit
            test_chunk = heading + current_chunk_content
            if current_chunk_content:
                test_chunk += '\n' + sentence
            else:
                test_chunk += sentence

            if self._count_tokens(test_chunk) <= self.max_tokens:
                # Can add this sentence
                if current_chunk_content:
                    current_chunk_content += '\n' + sentence
                else:
                    current_chunk_content = sentence
            else:
                # Adding this sentence would exceed limit
                if current_chunk_content:
                    # Save current chunk
                    result_chunks.append(heading + current_chunk_content)

                    # Start new chunk with overlap
                    if self.overlap > 0:
                        # Add overlap from previous chunk
                        overlap_text = self._get_overlap_text(current_chunk_content, self.overlap)
                        current_chunk_content = overlap_text + '\n' + sentence if overlap_text else sentence
                    else:
                        current_chunk_content = sentence
                else:
                    # Single sentence exceeds limit, add as is
                    logger.warning(f"Single sentence exceeds max_tokens limit: {len(sentence)} chars")
                    result_chunks.append(heading + sentence)
                    current_chunk_content = ""

        # Add remaining content
        if current_chunk_content:
            result_chunks.append(heading + current_chunk_content)

        logger.info(f"Split oversized chunk into {len(result_chunks)} smaller chunks")
        return result_chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        Get overlap text from the end of a chunk.

        Args:
            text: Source text
            overlap_size: Number of characters for overlap

        Returns:
            Overlap text
        """
        if len(text) <= overlap_size:
            return text

        # Try to find a good break point (sentence ending) within overlap range
        overlap_text = text[-overlap_size:]
        sentence_endings = ['。', '！', '？', '.', '!', '?', '；', ';']

        # Look for sentence ending in the overlap text
        for i, char in enumerate(overlap_text):
            if char in sentence_endings:
                # Found sentence ending, use text from this point
                return overlap_text[i+1:].strip()

        # No sentence ending found, use the full overlap
        return overlap_text.strip()


class ContractSplitter:
    """
    Main contract splitter that automatically detects file type and uses
    appropriate splitter implementation.
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200,
                 split_by_sentence: bool = True, token_counter: str = "character",
                 chunking_strategy: str = "finest_granularity",
                 strict_max_tokens: bool = False):
        """
        Initialize the contract splitter.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method ("character" or "tiktoken")
            chunking_strategy: Chunking strategy for flatten operation
                - "finest_granularity": 同等最细粒度拆分（默认）- 只处理叶子节点，避免重复
                - "all_levels": 所有层级拆分 - 处理所有有内容的节点
                - "parent_only": 仅父级拆分 - 只处理有内容且无子节点的父级
            strict_max_tokens: Whether to strictly enforce max_tokens limit
                - True: 对超过max_tokens的chunk进行进一步分割
                - False: 允许叶子节点超过max_tokens（默认）
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.split_by_sentence = split_by_sentence
        self.token_counter = token_counter
        self.chunking_strategy = chunking_strategy
        self.strict_max_tokens = strict_max_tokens
        
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
    
    def flatten(self, sections: List[Dict[str, Any]], strategy: str = None) -> List[str]:
        """
        Flatten hierarchical sections into a list of text chunks.

        Args:
            sections: List of hierarchical section dictionaries
            strategy: Chunking strategy (if None, uses instance default)

        Returns:
            List of text chunks ready for LLM ingestion
        """
        # Use instance default strategy if not specified
        if strategy is None:
            strategy = self.chunking_strategy

        chunks = []

        def extract_chunks_finest_granularity(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            """同等最细粒度拆分策略：只处理叶子节点，避免重复"""
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                if subsections:
                    # 有子sections，递归处理子sections，不处理当前content
                    extract_chunks_finest_granularity(subsections, full_heading)
                else:
                    # 没有子sections，这是叶子节点，处理其content
                    if content.strip():
                        from .utils import clean_text
                        chunk_text = f"{full_heading}\n\n{content}" if heading else content
                        chunks.append(clean_text(chunk_text))

        def extract_chunks_all_levels(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            """所有层级拆分策略：处理所有有内容的节点"""
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                # 处理当前节点的内容（如果有）
                if content.strip():
                    from .utils import clean_text
                    chunk_text = f"{full_heading}\n\n{content}" if heading else content
                    chunks.append(clean_text(chunk_text))

                # 递归处理子sections
                if subsections:
                    extract_chunks_all_levels(subsections, full_heading)

        def extract_chunks_parent_only(section_list: List[Dict[str, Any]], parent_heading: str = ""):
            """仅父级拆分策略：只处理有内容且无子节点的父级"""
            for section in section_list:
                heading = section.get("heading", "")
                content = section.get("content", "")
                subsections = section.get("subsections", [])

                # Create full heading path
                full_heading = f"{parent_heading} > {heading}" if parent_heading else heading

                if not subsections and content.strip():
                    # 只有没有子sections且有内容的才处理
                    from .utils import clean_text
                    chunk_text = f"{full_heading}\n\n{content}" if heading else content
                    chunks.append(clean_text(chunk_text))
                elif subsections:
                    # 有子sections，递归处理
                    extract_chunks_parent_only(subsections, full_heading)

        # 根据策略选择处理方法
        if strategy == "finest_granularity":
            extract_chunks_finest_granularity(sections)
        elif strategy == "all_levels":
            extract_chunks_all_levels(sections)
        elif strategy == "parent_only":
            extract_chunks_parent_only(sections)
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Supported: 'finest_granularity', 'all_levels', 'parent_only'")

        # Remove duplicates while preserving order
        chunks = self._remove_duplicate_chunks(chunks)

        # Apply strict max tokens control if enabled
        if self.strict_max_tokens:
            chunks = self._apply_strict_max_tokens(chunks)

        return chunks

    def _remove_duplicate_chunks(self, chunks: List[str]) -> List[str]:
        """
        Remove duplicate chunks while preserving order.

        Args:
            chunks: List of text chunks

        Returns:
            List of unique chunks
        """
        seen = set()
        unique_chunks = []

        for chunk in chunks:
            # Use first 200 characters as fingerprint for similarity detection
            fingerprint = chunk[:200].strip()

            # Also check for substantial overlap (>80% similarity)
            is_duplicate = False
            for seen_fp in seen:
                if self._chunks_are_similar(fingerprint, seen_fp):
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.add(fingerprint)
                unique_chunks.append(chunk)

        return unique_chunks

    def _chunks_are_similar(self, chunk1: str, chunk2: str, threshold: float = 0.7) -> bool:
        """
        Check if two chunks are similar enough to be considered duplicates.
        Enhanced version with content fingerprinting.

        Args:
            chunk1: First chunk
            chunk2: Second chunk
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            True if chunks are similar
        """
        if len(chunk1) == 0 or len(chunk2) == 0:
            return False

        # Create content fingerprints by removing formatting
        fp1 = self._create_content_fingerprint(chunk1)
        fp2 = self._create_content_fingerprint(chunk2)

        if len(fp1) == 0 or len(fp2) == 0:
            return False

        # Character-level similarity
        set1 = set(fp1.lower())
        set2 = set(fp2.lower())

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        if union == 0:
            return False

        similarity = intersection / union
        return similarity >= threshold

    def _create_content_fingerprint(self, text: str) -> str:
        """
        Create a content fingerprint by removing formatting and noise.

        Args:
            text: Original text

        Returns:
            Cleaned content fingerprint
        """
        import re

        # Remove chunk headers and formatting
        clean_text = re.sub(r'【Chunk \d+】.*?\n', '', text)
        clean_text = re.sub(r'={50,}', '', clean_text)
        clean_text = re.sub(r'-{20,}', '', clean_text)
        clean_text = re.sub(r'\(长度: \d+ 字符\)', '', clean_text)
        clean_text = re.sub(r'立项申请表 > .*? > .*? \(Part \d+\)', '', clean_text)

        # Remove excessive whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Return first 300 characters as fingerprint
        return clean_text[:300]
