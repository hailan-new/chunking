"""
DOCX document splitter for extracting hierarchical sections from Word documents.
"""

from typing import List, Dict, Any, Optional
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from .base import BaseSplitter
from .utils import count_tokens, sliding_window_split, clean_text, detect_heading_level

# Try to import textract for .doc file support
try:
    import textract
    TEXTRACT_AVAILABLE = True
except ImportError:
    TEXTRACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocxSplitter(BaseSplitter):
    """
    Splitter for .doc and .docx files using python-docx.
    
    Extracts document structure based on heading styles and paragraph content.
    Supports Chinese documents with proper text handling.
    """
    
    def __init__(self, max_tokens: int = 2000, overlap: int = 200, 
                 split_by_sentence: bool = True, token_counter: str = "character"):
        """
        Initialize DOCX splitter.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Overlap length for sliding window
            split_by_sentence: Whether to split at sentence boundaries
            token_counter: Token counting method
        """
        super().__init__(max_tokens, overlap, split_by_sentence, token_counter)
        
    def split(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Split DOCX document into hierarchical sections.

        Args:
            file_path: Path to the DOCX file

        Returns:
            List of hierarchical section dictionaries
        """
        self.validate_file(file_path, ['.doc', '.docx'])

        # Try different approaches based on file type and format
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.doc':
            # Handle legacy .doc files
            return self._handle_legacy_doc(file_path)
        else:
            # Handle .docx files
            return self._handle_docx_file(file_path)

    def _handle_legacy_doc(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Handle legacy .doc files using automatic conversion and alternative methods.

        Args:
            file_path: Path to the .doc file

        Returns:
            List of hierarchical section dictionaries
        """
        # First, try automatic conversion to .docx
        try:
            logger.info(f"Attempting automatic conversion of .doc file: {file_path}")
            from .converter import DocumentConverter

            converter = DocumentConverter(cleanup_temp_files=True)
            converted_path = converter.convert_to_docx(file_path)

            logger.info(f"✓ Successfully converted to: {converted_path}")

            # Process the converted .docx file
            from docx import Document
            doc = Document(converted_path)
            elements = self._extract_elements(doc)
            elements = self._enhance_structure_detection(elements)
            sections = self._build_hierarchy(elements)
            result = self._apply_size_constraints(sections)

            # Cleanup will happen automatically when converter is destroyed
            return result

        except Exception as e1:
            logger.warning(f"Automatic conversion failed: {e1}")

        # Fallback to direct processing methods
        try:
            # Try python-docx first (sometimes works with .doc)
            from docx import Document
            doc = Document(file_path)
            elements = self._extract_elements(doc)
            elements = self._enhance_structure_detection(elements)
            sections = self._build_hierarchy(elements)
            return self._apply_size_constraints(sections)
        except Exception as e2:
            logger.warning(f"python-docx direct processing failed: {e2}")

            # Try alternative text extraction methods
            try:
                text = self._extract_with_antiword(file_path)
                return self._process_plain_text(text, file_path)
            except Exception as e3:
                logger.warning(f"antiword failed: {e3}")

            # Try alternative: use win32com (Windows only)
            if os.name == 'nt':
                try:
                    return self._convert_doc_with_win32com(file_path)
                except Exception as e4:
                    logger.warning(f"win32com failed: {e4}")

            # Try alternative: use pandoc
            try:
                text = self._extract_with_pandoc(file_path)
                return self._process_plain_text(text, file_path)
            except Exception as e5:
                logger.warning(f"pandoc failed: {e5}")

            # Last resort: provide helpful error message
            raise ValueError(f"Unable to process .doc file: {file_path}. "
                           f"This appears to be a legacy or non-standard .doc format. "
                           f"Automatic conversion failed: {e1}. "
                           f"Direct processing failed: {e2}. "
                           f"Install LibreOffice, pandoc, or convert manually to .docx format.")

    def _handle_docx_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Handle .docx files with fallback strategies.

        Args:
            file_path: Path to the .docx file

        Returns:
            List of hierarchical section dictionaries
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for DOCX processing. "
                            "Install with: pip install python-docx")

        try:
            doc = Document(file_path)
            elements = self._extract_elements(doc)
            # Enhance structure detection for documents without clear headings
            elements = self._enhance_structure_detection(elements)
            sections = self._build_hierarchy(elements)
            return self._apply_size_constraints(sections)
        except Exception as e:
            logger.warning(f"Standard DOCX processing failed: {e}")

            # Try alternative: extract as plain text and process
            try:
                import docx2txt
                text = docx2txt.process(file_path)
                return self._process_plain_text(text, file_path)
            except ImportError:
                logger.warning("docx2txt not available for fallback")
            except Exception as e2:
                logger.warning(f"docx2txt fallback failed: {e2}")

            # Final fallback: try to read as zip and extract text manually
            try:
                return self._extract_docx_as_zip(file_path)
            except Exception as e3:
                logger.warning(f"ZIP extraction failed: {e3}")

            raise ValueError(f"Failed to open DOCX file: {e}. "
                           f"File may be corrupted or in an unsupported format.")
    
    def _extract_elements(self, doc) -> List[Dict[str, Any]]:
        """
        Extract all document elements (headings, paragraphs, and tables).

        Args:
            doc: python-docx Document object

        Returns:
            List of element dictionaries
        """
        elements = []

        # Process document in order (paragraphs and tables)
        for element in doc.element.body:
            if element.tag.endswith('p'):  # Paragraph
                # Find corresponding paragraph object
                for paragraph in doc.paragraphs:
                    if paragraph._element == element:
                        text = clean_text(paragraph.text)
                        if text:
                            elem = {
                                'text': text,
                                'style': paragraph.style.name if paragraph.style else 'Normal',
                                'is_heading': self._is_heading(paragraph),
                                'level': self._get_heading_level(paragraph),
                                'type': 'paragraph'
                            }
                            elements.append(elem)
                        break

            elif element.tag.endswith('tbl'):  # Table
                # Find corresponding table object
                for table in doc.tables:
                    if table._element == element:
                        table_content = self._extract_table_content(table)
                        if table_content:
                            elem = {
                                'text': table_content,
                                'style': 'Table',
                                'is_heading': False,
                                'level': 3,  # Default level for tables
                                'type': 'table'
                            }
                            elements.append(elem)
                        break

        # Fallback: if no elements found, use simple paragraph extraction
        if not elements:
            for paragraph in doc.paragraphs:
                text = clean_text(paragraph.text)
                if text:
                    element = {
                        'text': text,
                        'style': paragraph.style.name if paragraph.style else 'Normal',
                        'is_heading': self._is_heading(paragraph),
                        'level': self._get_heading_level(paragraph),
                        'type': 'paragraph'
                    }
                    elements.append(element)

        return elements
    
    def _is_heading(self, paragraph) -> bool:
        """
        Determine if a paragraph is a heading.
        
        Args:
            paragraph: python-docx Paragraph object
            
        Returns:
            True if paragraph is a heading
        """
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        
        # Check for heading styles
        if 'heading' in style_name:
            return True
        
        # Check for title styles
        if 'title' in style_name:
            return True
        
        # Check text patterns for Chinese/English headings
        text = paragraph.text.strip()
        if self._looks_like_heading(text):
            return True
        
        return False
    
    def _looks_like_heading(self, text: str) -> bool:
        """
        Check if text looks like a heading based on patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like a heading
        """
        import re
        
        # Chinese heading patterns
        chinese_patterns = [
            r'^第[一二三四五六七八九十\d]+章',  # Chapter
            r'^第[一二三四五六七八九十\d]+节',  # Section
            r'^[一二三四五六七八九十\d]+[、．.]',  # Numbered
            r'^（[一二三四五六七八九十\d]+）',  # Parenthetical
        ]
        
        # English heading patterns
        english_patterns = [
            r'^Chapter\s+\d+',
            r'^Section\s+\d+',
            r'^\d+\.?\s+',
            r'^\d+\.\d+\.?\s+',
        ]
        
        for pattern in chinese_patterns + english_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Check if text is short and might be a heading
        if len(text) < 100 and not text.endswith(('。', '.', '！', '!', '？', '?')):
            return True
        
        return False
    
    def _get_heading_level(self, paragraph) -> int:
        """
        Get heading level from paragraph.
        
        Args:
            paragraph: python-docx Paragraph object
            
        Returns:
            Heading level (1-6)
        """
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        
        # Extract level from style name
        if 'heading' in style_name:
            import re
            match = re.search(r'heading\s*(\d+)', style_name)
            if match:
                return int(match.group(1))
        
        # Use text pattern detection
        return detect_heading_level(paragraph.text)
    
    def _build_hierarchy(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build hierarchical structure from flat list of elements.
        
        Args:
            elements: List of document elements
            
        Returns:
            List of hierarchical sections
        """
        sections = []
        current_section = None
        section_stack = []  # Stack to track nested sections
        
        for element in elements:
            if element['is_heading']:
                # Create new section
                section = {
                    'heading': element['text'],
                    'content': '',
                    'level': element['level'],
                    'subsections': []
                }
                
                # Determine where to place this section
                if not section_stack or element['level'] <= section_stack[-1]['level']:
                    # Pop sections until we find the right parent level
                    while section_stack and element['level'] <= section_stack[-1]['level']:
                        section_stack.pop()
                    
                    if section_stack:
                        # Add as subsection to parent
                        section_stack[-1]['subsections'].append(section)
                    else:
                        # Add as top-level section
                        sections.append(section)
                else:
                    # Add as subsection to current section
                    if section_stack:
                        section_stack[-1]['subsections'].append(section)
                    else:
                        sections.append(section)
                
                section_stack.append(section)
                current_section = section
            else:
                # Add content to current section
                if current_section is not None:
                    if current_section['content']:
                        current_section['content'] += '\n\n' + element['text']
                    else:
                        current_section['content'] = element['text']
                else:
                    # No current section, create a default one
                    if not sections:
                        sections.append({
                            'heading': 'Document Content',
                            'content': element['text'],
                            'level': 1,
                            'subsections': []
                        })
                        current_section = sections[0]
                        section_stack = [current_section]
                    else:
                        # Add to last section
                        last_section = self._find_last_section(sections)
                        if last_section['content']:
                            last_section['content'] += '\n\n' + element['text']
                        else:
                            last_section['content'] = element['text']
        
        return sections
    
    def _find_last_section(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find the last section in the hierarchy for adding content.
        
        Args:
            sections: List of sections
            
        Returns:
            Last section dictionary
        """
        if not sections:
            return None
        
        last_section = sections[-1]
        while last_section.get('subsections'):
            last_section = last_section['subsections'][-1]
        
        return last_section
    
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

    def _process_plain_text(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Process plain text extracted from document.

        Args:
            text: Extracted plain text
            file_path: Original file path for reference

        Returns:
            List of sections
        """
        if not text or not text.strip():
            return [{
                'heading': f'Document Content ({os.path.basename(file_path)})',
                'content': 'No readable content found.',
                'level': 1,
                'subsections': []
            }]

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
                        'heading': f'Document Content ({os.path.basename(file_path)})',
                        'content': paragraph,
                        'level': 1,
                        'subsections': []
                    })
                    current_section = sections[0]

        return self._apply_size_constraints(sections)

    def _convert_doc_with_win32com(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Convert .doc file using win32com (Windows only).

        Args:
            file_path: Path to .doc file

        Returns:
            List of sections
        """
        try:
            import win32com.client

            # Create Word application
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False

            # Open document
            doc = word.Documents.Open(os.path.abspath(file_path))

            # Extract text
            text = doc.Content.Text

            # Close document and application
            doc.Close()
            word.Quit()

            return self._process_plain_text(text, file_path)

        except ImportError:
            raise ImportError("win32com not available. Install with: pip install pywin32")
        except Exception as e:
            raise ValueError(f"Failed to convert .doc file with win32com: {e}")

    def _extract_docx_as_zip(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract DOCX content by treating it as a ZIP file.

        Args:
            file_path: Path to DOCX file

        Returns:
            List of sections
        """
        import zipfile
        import xml.etree.ElementTree as ET

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Read document.xml
                doc_xml = zip_file.read('word/document.xml')
                root = ET.fromstring(doc_xml)

                # Extract text from XML
                text_parts = []
                for elem in root.iter():
                    if elem.text:
                        text_parts.append(elem.text)

                text = ' '.join(text_parts)
                return self._process_plain_text(text, file_path)

        except Exception as e:
            raise ValueError(f"Failed to extract DOCX as ZIP: {e}")

    def _enhance_structure_detection(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance structure detection for documents without clear headings.

        Args:
            elements: List of document elements

        Returns:
            Enhanced elements with better structure detection
        """
        enhanced_elements = []

        for element in elements:
            text = element['text']

            # Enhanced heading detection
            if not element['is_heading']:
                # Check for numbered patterns
                import re

                # Chinese patterns
                chinese_patterns = [
                    r'^第[一二三四五六七八九十\d]+[章节条款项]',
                    r'^[一二三四五六七八九十]+[、．.]',
                    r'^（[一二三四五六七八九十\d]+）',
                    r'^\d+[、．.]',
                    r'^\d+\.\d+',
                ]

                # English patterns
                english_patterns = [
                    r'^Chapter\s+\d+',
                    r'^Section\s+\d+',
                    r'^Article\s+\d+',
                    r'^\d+\.\s+[A-Z]',
                    r'^[A-Z][A-Z\s]+:$',  # ALL CAPS headings
                ]

                for pattern in chinese_patterns + english_patterns:
                    if re.match(pattern, text, re.IGNORECASE):
                        element['is_heading'] = True
                        element['level'] = detect_heading_level(text)
                        break

                # Check for short lines that might be headings
                if (len(text) < 100 and
                    not text.endswith(('。', '.', '！', '!', '？', '?', '；', ';')) and
                    len(text.split()) < 10):
                    element['is_heading'] = True
                    element['level'] = 3  # Default level for detected headings

            enhanced_elements.append(element)

        return enhanced_elements

    def _extract_table_content(self, table) -> str:
        """
        Extract content from a table in a structured format with improved layout handling.

        Args:
            table: python-docx Table object

        Returns:
            Formatted table content as string
        """
        table_text = []
        table_text.append("【表格内容】")

        # Method 1: Smart table extraction that handles merged cells and layout
        try:
            extracted_content = self._extract_table_smart(table)
            if extracted_content:
                table_text.extend(extracted_content)
                table_text.append("【表格结束】")
                return "\n".join(table_text)
        except Exception as e:
            logger.warning(f"Smart table extraction failed: {e}")

        # Method 2: Traditional row-by-row extraction
        try:
            extracted_content = []
            for i, row in enumerate(table.rows):
                row_data = []
                for j, cell in enumerate(row.cells):
                    cell_text = clean_text(cell.text)
                    if cell_text:
                        row_data.append(f"列{j+1}: {cell_text}")

                if row_data:
                    extracted_content.append(f"行{i+1}: {' | '.join(row_data)}")

            if extracted_content:
                table_text.extend(extracted_content)
                table_text.append("【表格结束】")
                return "\n".join(table_text)
        except Exception as e:
            logger.warning(f"Row-by-row extraction failed: {e}")

        # Method 3: Cell by cell extraction (fallback)
        try:
            all_cells = []
            for i, row in enumerate(table.rows):
                for j, cell in enumerate(row.cells):
                    # Extract all paragraphs from cell
                    cell_paragraphs = []
                    for paragraph in cell.paragraphs:
                        text = clean_text(paragraph.text)
                        if text:
                            cell_paragraphs.append(text)

                    if cell_paragraphs:
                        cell_content = " ".join(cell_paragraphs)
                        all_cells.append(f"单元格({i+1},{j+1}): {cell_content}")

            if all_cells:
                table_text.extend(all_cells)
                table_text.append("【表格结束】")
                return "\n".join(table_text)
        except Exception as e:
            logger.warning(f"Cell-by-cell extraction failed: {e}")

        # Method 4: Try key-value extraction for form-like tables
        try:
            kv_content = self._extract_table_as_key_value(table)
            if kv_content:
                table_text.append(kv_content)
                table_text.append("【表格结束】")
                return "\n".join(table_text)
        except Exception as e:
            logger.warning(f"Key-value extraction failed: {e}")

        table_text.append("表格内容为空或无法提取")
        table_text.append("【表格结束】")
        return "\n".join(table_text)

    def _extract_table_smart(self, table) -> List[str]:
        """
        Smart table extraction that handles complex layouts and merged cells.

        Args:
            table: python-docx Table object

        Returns:
            List of formatted content strings
        """
        content = []

        # First, analyze the table structure
        num_rows = len(table.rows)
        num_cols = len(table.columns) if table.rows else 0

        if num_rows == 0:
            return []

        # Get the maximum number of cells in any row (handles irregular tables)
        max_cells = max(len(row.cells) for row in table.rows)

        # Create a grid to track cell content and merged cells
        cell_grid = {}
        processed_cells = set()

        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):
                if (i, j) in processed_cells:
                    continue

                cell_text = clean_text(cell.text)
                if not cell_text:
                    continue

                # Check if this is a merged cell by looking at cell dimensions
                cell_width = getattr(cell, '_tc', None)
                if cell_width is not None:
                    # Try to detect merged cells (this is approximate)
                    colspan = 1
                    rowspan = 1

                    # Mark cells as processed
                    for r in range(i, i + rowspan):
                        for c in range(j, j + colspan):
                            processed_cells.add((r, c))

                cell_grid[(i, j)] = {
                    'text': cell_text,
                    'row': i,
                    'col': j,
                    'colspan': colspan,
                    'rowspan': rowspan
                }

        # Now extract content in a more structured way
        if num_rows <= 3 and max_cells <= 4:
            # Likely a form-like table, extract as key-value pairs
            content.extend(self._extract_form_table(cell_grid, num_rows, max_cells))
        else:
            # Larger table, extract with better structure preservation
            content.extend(self._extract_structured_table(cell_grid, num_rows, max_cells))

        return content

    def _extract_form_table(self, cell_grid: dict, num_rows: int, max_cells: int) -> List[str]:
        """Extract form-like table as key-value pairs."""
        content = []

        # Group cells by row and try to pair them as key-value
        for row in range(num_rows):
            row_cells = [(col, cell) for (r, col), cell in cell_grid.items() if r == row]
            row_cells.sort(key=lambda x: x[0])  # Sort by column

            if len(row_cells) == 2:
                # Two cells: likely key-value pair
                key_cell = row_cells[0][1]['text']
                value_cell = row_cells[1][1]['text']
                content.append(f"{key_cell}: {value_cell}")
            elif len(row_cells) == 4:
                # Four cells: likely two key-value pairs
                if len(row_cells) >= 2:
                    key1 = row_cells[0][1]['text']
                    value1 = row_cells[1][1]['text']
                    content.append(f"{key1}: {value1}")
                if len(row_cells) >= 4:
                    key2 = row_cells[2][1]['text']
                    value2 = row_cells[3][1]['text']
                    content.append(f"{key2}: {value2}")
            else:
                # Other cases: just list the content
                for col, cell in row_cells:
                    content.append(f"行{row+1}列{col+1}: {cell['text']}")

        return content

    def _extract_structured_table(self, cell_grid: dict, num_rows: int, max_cells: int) -> List[str]:
        """Extract larger table with structure preservation."""
        content = []

        # Extract row by row, but with better formatting
        for row in range(num_rows):
            row_cells = [(col, cell) for (r, col), cell in cell_grid.items() if r == row]
            row_cells.sort(key=lambda x: x[0])  # Sort by column

            if row_cells:
                if row == 0 and len(row_cells) > 2:
                    # First row might be headers
                    headers = [cell['text'] for col, cell in row_cells]
                    content.append(f"表头: {' | '.join(headers)}")
                else:
                    # Regular data row
                    row_data = []
                    for col, cell in row_cells:
                        row_data.append(f"列{col+1}: {cell['text']}")
                    content.append(f"行{row+1}: {' | '.join(row_data)}")

        return content

    def _extract_table_as_key_value(self, table) -> str:
        """
        Extract table content as key-value pairs (useful for forms).

        Args:
            table: python-docx Table object

        Returns:
            Formatted key-value content
        """
        content = []

        for row in table.rows:
            cells = [clean_text(cell.text) for cell in row.cells if clean_text(cell.text)]

            if len(cells) >= 2:
                # Treat as key-value pairs
                key = cells[0]
                value = " | ".join(cells[1:])
                content.append(f"{key}: {value}")
            elif len(cells) == 1:
                # Single cell content
                content.append(cells[0])

        return "\n".join(content) if content else ""

    def _extract_with_antiword(self, file_path: str) -> str:
        """
        Extract text using antiword command-line tool.

        Args:
            file_path: Path to .doc file

        Returns:
            Extracted text
        """
        import subprocess

        try:
            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except FileNotFoundError:
            raise ValueError("antiword not found. Install with: brew install antiword (Mac) or apt-get install antiword (Linux)")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"antiword failed: {e}")

    def _extract_with_pandoc(self, file_path: str) -> str:
        """
        Extract text using pandoc.

        Args:
            file_path: Path to .doc file

        Returns:
            Extracted text
        """
        import subprocess
        import tempfile

        try:
            # Convert to plain text using pandoc
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                result = subprocess.run(
                    ['pandoc', file_path, '-t', 'plain', '-o', tmp_file.name],
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Read the converted text
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    text = f.read()

                # Clean up
                os.unlink(tmp_file.name)
                return text

        except FileNotFoundError:
            raise ValueError("pandoc not found. Install from https://pandoc.org/")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"pandoc failed: {e}")
        except Exception as e:
            raise ValueError(f"pandoc extraction failed: {e}")
