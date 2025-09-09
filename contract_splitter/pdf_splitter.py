"""
PDF document splitter for extracting hierarchical sections from structured PDFs.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from .base import BaseSplitter
from .utils import count_tokens, sliding_window_split, clean_text
from .legal_structure_detector import get_legal_detector

logger = logging.getLogger(__name__)


class PdfSplitter(BaseSplitter):
    """
    Splitter for structured PDF files using pdfplumber and PyMuPDF.

    Extracts document structure from PDF outline/bookmarks or falls back
    to font-size based heading detection. Supports Chinese PDFs and legal documents.
    """

    def __init__(self, max_tokens: int = 2000, overlap: int = 200,
                 split_by_sentence: bool = True, token_counter: str = "character",
                 document_type: str = "general", legal_patterns: List[str] = None):
        """
        Initialize PDF splitter.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method
            document_type: Type of document ("general", "legal", "contract")
            legal_patterns: Custom legal heading patterns for legal documents
        """
        super().__init__(max_tokens, overlap, split_by_sentence, token_counter)
        self.document_type = document_type
        self.legal_patterns = legal_patterns or []

        # 初始化法律结构检测器
        custom_patterns = {'custom_legal': self.legal_patterns} if self.legal_patterns else None
        self.structure_detector = get_legal_detector(document_type, custom_patterns)
        
    def split(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Split PDF document into hierarchical sections.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of hierarchical section dictionaries
        """
        self.validate_file(file_path, ['.pdf'])

        # 对于法律文档，优先使用文本模式识别
        if self.document_type == "legal":
            logger.info("Legal document detected, using text pattern recognition first")
            sections = self._extract_by_text_patterns_pymupdf(file_path)

            if sections and len(sections) > 5:  # 如果识别到足够多的结构
                logger.info(f"Using text pattern results: {len(sections)} sections")
                # 直接使用文本模式识别的结果，进行过滤和清理
                return self._filter_and_clean_sections(sections)

        # 原有的处理逻辑作为fallback
        sections = self._extract_with_pymupdf(file_path)

        if not sections:
            # Fallback to pdfplumber with font-based detection
            sections = self._extract_with_pdfplumber(file_path)

        if not sections:
            # For legal documents, try text pattern recognition
            if self.document_type == "legal":
                logger.info("Trying text pattern recognition for legal document")
                sections = self._extract_by_text_patterns_pymupdf(file_path)

        if not sections:
            # Last resort: treat entire PDF as single section
            sections = self._extract_as_single_section(file_path)

        # Apply size constraints and splitting
        sections = self._apply_size_constraints(sections)

        # 扁平化sections，确保返回有内容的chunks
        flattened_sections = self._flatten_sections(sections)

        return flattened_sections
    
    def _extract_with_pymupdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections using PyMuPDF (fitz) with outline/bookmark support.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of sections or empty list if extraction fails
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not available, skipping outline extraction")
            return []
        
        try:
            doc = fitz.open(file_path)
            
            # Get document outline/bookmarks
            outline = doc.get_toc()
            
            if not outline:
                logger.info("No outline found in PDF, trying font-based detection")
                return self._extract_by_font_size(doc)
            
            # Extract text for each section based on outline
            sections = self._build_sections_from_outline(doc, outline)
            
            doc.close()
            return sections
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return []
    
    def _extract_by_font_size(self, doc) -> List[Dict[str, Any]]:
        """
        Extract sections by analyzing font sizes to detect headings.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of sections
        """
        # Analyze font sizes across the document
        font_sizes = {}
        page_texts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            page_elements = []
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                font_size = span["size"]
                                font_sizes[font_size] = font_sizes.get(font_size, 0) + len(text)
                                
                                page_elements.append({
                                    'text': text,
                                    'font_size': font_size,
                                    'bbox': span["bbox"]
                                })
            
            page_texts.append(page_elements)
        
        # Determine heading font sizes (larger than average)
        if not font_sizes:
            return []
        
        avg_font_size = sum(size * count for size, count in font_sizes.items()) / sum(font_sizes.values())
        heading_sizes = [size for size in font_sizes.keys() if size > avg_font_size * 1.2]
        heading_sizes.sort(reverse=True)
        
        # Build sections based on font sizes
        sections = self._build_sections_from_fonts(page_texts, heading_sizes)
        
        return sections
    
    def _build_sections_from_outline(self, doc, outline: List[Tuple]) -> List[Dict[str, Any]]:
        """
        Build sections from PDF outline/bookmarks.
        
        Args:
            doc: PyMuPDF document object
            outline: List of outline entries (level, title, page)
            
        Returns:
            List of hierarchical sections
        """
        sections = []
        section_stack = []
        
        for i, (level, title, page_num) in enumerate(outline):
            # Get text content for this section
            start_page = page_num - 1  # Convert to 0-based
            
            # Find end page (next section's page or document end)
            end_page = len(doc) - 1
            if i + 1 < len(outline):
                end_page = outline[i + 1][2] - 2  # Convert to 0-based and go to previous page
            
            content = self._extract_text_range(doc, start_page, end_page)
            
            section = {
                'heading': clean_text(title),
                'content': content,
                'level': level,
                'subsections': []
            }
            
            # Build hierarchy
            while section_stack and level <= section_stack[-1]['level']:
                section_stack.pop()
            
            if section_stack:
                section_stack[-1]['subsections'].append(section)
            else:
                sections.append(section)
            
            section_stack.append(section)
        
        return sections
    
    def _build_sections_from_fonts(self, page_texts: List[List[Dict]], 
                                  heading_sizes: List[float]) -> List[Dict[str, Any]]:
        """
        Build sections based on font size analysis.
        
        Args:
            page_texts: List of page elements with font information
            heading_sizes: List of font sizes considered as headings
            
        Returns:
            List of sections
        """
        sections = []
        current_section = None
        section_stack = []
        
        for page_elements in page_texts:
            for element in page_elements:
                text = element['text']
                font_size = element['font_size']
                
                if font_size in heading_sizes and self._looks_like_heading(text):
                    # Determine heading level based on font size rank
                    level = heading_sizes.index(font_size) + 1
                    
                    section = {
                        'heading': text,
                        'content': '',
                        'level': level,
                        'subsections': []
                    }
                    
                    # Build hierarchy
                    while section_stack and level <= section_stack[-1]['level']:
                        section_stack.pop()
                    
                    if section_stack:
                        section_stack[-1]['subsections'].append(section)
                    else:
                        sections.append(section)
                    
                    section_stack.append(section)
                    current_section = section
                else:
                    # Add as content
                    if current_section:
                        if current_section['content']:
                            current_section['content'] += ' ' + text
                        else:
                            current_section['content'] = text
                    else:
                        # Create default section
                        if not sections:
                            sections.append({
                                'heading': 'Document Content',
                                'content': text,
                                'level': 1,
                                'subsections': []
                            })
                            current_section = sections[0]
                            section_stack = [current_section]
        
        return sections
    
    def _looks_like_heading(self, text: str) -> bool:
        """
        Check if text looks like a heading using unified structure detector.

        Args:
            text: Text to check

        Returns:
            True if text looks like a heading
        """
        return self.structure_detector.is_legal_heading(text)

    def _extract_by_text_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Extract sections by analyzing text patterns when outline is not available.
        Specifically designed for legal documents.

        Args:
            doc: PyMuPDF document

        Returns:
            List of sections with heading and content
        """
        import re

        sections = []
        current_section = None

        # Extract all text with page information
        full_text = ""
        page_breaks = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            page_breaks.append(len(full_text))
            full_text += page_text + "\n"

        # Split into lines and analyze
        lines = full_text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if this line looks like a heading
            if self._looks_like_heading(line):
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                current_section = {
                    'heading': line,
                    'content': '',
                    'level': self._determine_heading_level(line),
                    'subsections': []
                }
            else:
                # Add to current section content
                if current_section:
                    if current_section['content']:
                        current_section['content'] += '\n' + line
                    else:
                        current_section['content'] = line
                else:
                    # No current section, create a default one
                    if not sections:
                        current_section = {
                            'heading': '',
                            'content': line,
                            'level': 0,
                            'subsections': []
                        }

        # Add the last section
        if current_section:
            sections.append(current_section)

        return sections

    def _determine_heading_level(self, heading: str) -> int:
        """
        Determine the hierarchical level of a heading using unified structure detector.

        Args:
            heading: Heading text

        Returns:
            Level number (1 = highest, higher numbers = lower levels)
        """
        return self.structure_detector.get_heading_level(heading)

    def _extract_by_text_patterns_pymupdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections using PyMuPDF with text pattern recognition.
        Specifically for legal documents without outline structure.

        Args:
            file_path: Path to PDF file

        Returns:
            List of sections or empty list if extraction fails
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not available for text pattern extraction")
            return []

        try:
            doc = fitz.open(file_path)
            sections = self._extract_by_text_patterns(doc)
            doc.close()

            if sections:
                logger.info(f"Extracted {len(sections)} sections using text patterns")

            return sections

        except Exception as e:
            logger.error(f"Error in text pattern extraction: {e}")
            return []

    def _extract_text_range(self, doc, start_page: int, end_page: int) -> str:
        """
        Extract text from a range of pages.
        
        Args:
            doc: PyMuPDF document object
            start_page: Starting page (0-based)
            end_page: Ending page (0-based, inclusive)
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        for page_num in range(start_page, min(end_page + 1, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(clean_text(text))
        
        return '\n\n'.join(text_parts)
    
    def _extract_with_pdfplumber(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections using pdfplumber as fallback.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of sections or empty list if extraction fails
        """
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not available, skipping extraction")
            return []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract all text
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n\n"
                
                if not full_text.strip():
                    return []
                
                # Simple section detection based on text patterns
                sections = self._detect_sections_in_text(full_text)
                return sections
                
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return []
    
    def _detect_sections_in_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sections in plain text using pattern matching.
        
        Args:
            text: Full document text
            
        Returns:
            List of sections
        """
        import re
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        sections = []
        current_section = None
        
        for paragraph in paragraphs:
            if self._looks_like_heading(paragraph):
                # Create new section
                section = {
                    'heading': paragraph,
                    'content': '',
                    'level': detect_heading_level(paragraph),
                    'subsections': []
                }
                sections.append(section)
                current_section = section
            else:
                # Add to current section
                if current_section:
                    if current_section['content']:
                        current_section['content'] += '\n\n' + paragraph
                    else:
                        current_section['content'] = paragraph
                else:
                    # Create default section
                    sections.append({
                        'heading': 'Document Content',
                        'content': paragraph,
                        'level': 1,
                        'subsections': []
                    })
                    current_section = sections[0]
        
        return sections
    
    def _extract_as_single_section(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract entire PDF as a single section (last resort).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List with single section
        """
        try:
            import pdfplumber
            
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n\n"
                
                return [{
                    'heading': 'Document Content',
                    'content': clean_text(full_text),
                    'level': 1,
                    'subsections': []
                }]
                
        except Exception as e:
            logger.error(f"Failed to extract PDF as single section: {e}")
            return []
    
    def _apply_size_constraints(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply size constraints to sections, splitting large ones.
        
        Args:
            sections: List of hierarchical sections
            
        Returns:
            List of size-constrained sections
        """
        result = []
        
        for section in sections:
            result.append(self._process_section(section))
        
        return result
    
    def _process_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single section, applying size constraints.
        
        Args:
            section: Section dictionary
            
        Returns:
            Processed section dictionary
        """
        # Process subsections first
        processed_subsections = []
        for subsection in section.get('subsections', []):
            processed_subsections.append(self._process_section(subsection))
        
        # Check if content needs splitting
        content = section.get('content', '')
        if content and count_tokens(content, self.token_counter) > self.max_tokens:
            # Split content using sliding window
            chunks = sliding_window_split(
                content, 
                self.max_tokens, 
                self.overlap,
                self.split_by_sentence,
                self.token_counter
            )
            
            # Create subsections for chunks
            for i, chunk in enumerate(chunks):
                chunk_section = {
                    'heading': f"{section['heading']} (Part {i+1})" if section['heading'] else f"Part {i+1}",
                    'content': chunk,
                    'level': section.get('level', 1) + 1,
                    'subsections': []
                }
                processed_subsections.append(chunk_section)
            
            # Clear original content since it's now in subsections
            content = ''
        
        return {
            'heading': section.get('heading', ''),
            'content': content,
            'level': section.get('level', 1),
            'subsections': processed_subsections
        }

    def _flatten_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        扁平化sections，确保返回有内容的chunks

        Args:
            sections: 层次化的sections列表

        Returns:
            扁平化的sections列表，只包含有内容的chunks
        """
        result = []

        for section in sections:
            content = section.get('content', '')
            subsections = section.get('subsections', [])

            # 如果父section有内容，添加它
            if content.strip():
                result.append({
                    'heading': section.get('heading', ''),
                    'content': content,
                    'level': section.get('level', 1),
                    'subsections': []
                })

            # 递归处理子sections
            if subsections:
                result.extend(self._flatten_sections(subsections))

        return result

    def _filter_and_clean_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤和清理sections，移除空的或过短的sections

        Args:
            sections: 原始sections列表

        Returns:
            过滤后的sections列表
        """
        result = []

        for section in sections:
            content = section.get('content', '').strip()
            heading = section.get('heading', '').strip()

            # 过滤条件
            if len(content) < 10 and len(heading) < 5:  # 太短的跳过
                continue

            if not content and not heading:  # 完全空的跳过
                continue

            # 合并标题和内容
            if heading and content:
                full_content = f"{heading}\n{content}"
            elif heading:
                full_content = heading
            else:
                full_content = content

            result.append({
                'heading': heading,
                'content': full_content,
                'level': section.get('level', 1),
                'subsections': []
            })

        return result
