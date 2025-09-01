# Contract Splitter

An advanced Python package for splitting contract documents (.doc, .docx, .pdf) into hierarchical sections with enhanced table extraction and automatic format conversion. Designed for legal and financial documents with comprehensive Chinese language support.

## 🚀 Key Features

- **🔄 Automatic Format Conversion**: Seamlessly converts legacy .doc files to .docx using LibreOffice/pandoc
- **📊 Enhanced Table Extraction**: Advanced table structure preservation with smart cell mapping
- **📁 Multi-format Support**: Process .doc, .docx, and structured PDF files
- **🏗️ Hierarchical Structure**: Maintains document hierarchy (chapters, sections, subsections)
- **🇨🇳 Chinese Language Support**: Optimized for Chinese contracts and legal documents
- **⚙️ Flexible Splitting**: Size-constrained splitting with configurable parameters
- **🔢 Multiple Token Counters**: Character-based or tiktoken-based token counting
- **🪟 Sliding Window**: Overlapping chunks for better context preservation
- **📝 Natural Breakpoints**: Respects sentence and paragraph boundaries
- **🛡️ Robust Error Handling**: Multiple fallback methods for problematic documents

## 📦 Installation

### Quick Install (Recommended)

```bash
pip install contract-splitter
```

### Core Dependencies Only

```bash
pip install python-docx pdfplumber PyMuPDF
```

### Enhanced Features

```bash
# For enhanced table extraction and document conversion
pip install contract-splitter[enhanced]

# For accurate token counting
pip install contract-splitter[tiktoken]

# For document conversion support
pip install contract-splitter[conversion]
```

### System Dependencies (for .doc conversion)

**macOS:**
```bash
brew install libreoffice  # or pandoc
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libreoffice  # or pandoc
```

**Windows:**
- Install LibreOffice from https://www.libreoffice.org/
- Or install pandoc from https://pandoc.org/

## 🚀 Quick Start

```python
from contract_splitter import ContractSplitter

# Create splitter with default settings
splitter = ContractSplitter(max_tokens=2000, overlap=200)

# Split a document (supports .doc, .docx, .pdf)
sections = splitter.split("contract.doc")  # Automatic conversion!

# Print section structure
for section in sections:
    print(f"Heading: {section['heading']}")
    print(f"Content: {section['content'][:100]}...")
    print(f"Subsections: {len(section['subsections'])}")

# Flatten to chunks for LLM ingestion
chunks = splitter.flatten(sections)
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk[:100]}...")
```

### 📊 Enhanced Table Processing

```python
# The package now automatically extracts tables with proper structure
sections = splitter.split("document_with_tables.docx")

# Tables are extracted as structured content:
# 项目名称: 首创证券新增代销机构
# 客户名称: 广州农村商业银行股份有限公司
# 业务类型: 新增代销合作机构
```

## Configuration Options

```python
splitter = ContractSplitter(
    max_tokens=2000,           # Maximum tokens per chunk
    overlap=200,               # Overlap length for sliding window
    split_by_sentence=True,    # Respect sentence boundaries
    token_counter="character"  # "character" or "tiktoken"
)
```

## Document Structure

The package returns hierarchical sections in this format:

```json
{
  "heading": "第一章 总则",
  "content": "本章规定了合同的基本原则...",
  "level": 1,
  "subsections": [
    {
      "heading": "第一条 合同目的",
      "content": "本合同是甲方与乙方...",
      "level": 2,
      "subsections": []
    }
  ]
}
```

## 📄 Supported Document Types

### 📝 Word Documents (.doc, .docx)
- **✅ Legacy .doc Support**: Automatic conversion using LibreOffice/pandoc
- **📊 Enhanced Table Extraction**: Smart table structure preservation
- **🎯 Heading Detection**: Extracts heading styles (Heading 1, Heading 2, etc.)
- **🇨🇳 Chinese Patterns**: Detects Chinese and English heading patterns
- **📋 Structure Preservation**: Maintains paragraph and list structure
- **🔄 Multiple Fallbacks**: Robust error handling for corrupted files

### 📄 PDF Files (.pdf)
- **🔖 Outline Extraction**: Uses document outline/bookmarks when available
- **🎨 Font-based Detection**: Falls back to font-size based heading detection
- **📊 Structured PDFs**: Supports structured (non-OCR) PDFs
- **🔍 Content Analysis**: Advanced text extraction and structure detection

### 🆕 New in v1.1.0
- **🔄 Automatic .doc Conversion**: Seamless legacy format support
- **📊 Smart Table Processing**: Enhanced table content extraction
- **🛡️ Robust Error Handling**: Multiple conversion methods with fallbacks
- **⚡ Performance Improvements**: Optimized processing pipeline

## Chinese Language Support

The package includes specialized support for Chinese documents:

- **Heading Detection**: Recognizes Chinese chapter/section patterns
  - `第一章` (Chapter 1)
  - `第二节` (Section 2)  
  - `一、` (Item 1)
  - `（一）` (Subitem 1)

- **Sentence Splitting**: Handles Chinese punctuation (。！？；)

- **Text Processing**: Proper handling of mixed Chinese/English content

## 🔧 Advanced Usage

### 📊 Enhanced Table Extraction

The package now includes advanced table processing capabilities:

```python
# Tables are automatically detected and extracted with proper structure
sections = splitter.split("document_with_tables.docx")

# Example output for a form-like table:
# 【表格内容】
# 项目名称: 首创证券新增代销机构-广州农商行
# 项目所在地: 广东省
# 客户名称: 广州农村商业银行股份有限公司
# 业务类型: 新增代销合作机构
# 【表格结束】
```

### 🔄 Document Conversion

```python
from contract_splitter.converter import DocumentConverter

# Convert .doc to .docx automatically
converter = DocumentConverter()
docx_path = converter.convert_to_docx("legacy_document.doc")

# The conversion uses multiple methods:
# 1. LibreOffice (preferred)
# 2. pandoc (fallback)
# 3. win32com (Windows only)
# 4. unoconv (alternative)
```

### Custom Token Counting

```python
from contract_splitter.utils import count_tokens

# Character-based counting
char_count = count_tokens(text, "character")

# OpenAI tiktoken-based counting (requires tiktoken)
token_count = count_tokens(text, "tiktoken")
```

### Manual Text Splitting

```python
from contract_splitter.utils import sliding_window_split

chunks = sliding_window_split(
    text=long_text,
    max_tokens=1000,
    overlap=100,
    by_sentence=True,
    token_counter="character"
)
```

### Convenience Functions

```python
from contract_splitter import split_document, flatten_sections

# Quick document splitting
sections = split_document("contract.pdf", max_tokens=1500)

# Quick flattening
chunks = flatten_sections(sections, max_tokens=1500)
```

## Error Handling

The package provides robust error handling:

```python
try:
    sections = splitter.split("document.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Unsupported file type: {e}")
```

## 🧪 Testing

### Run the comprehensive test suite:

```bash
# Basic functionality tests
python3 tests/test_contract_splitter.py

# Comprehensive capability testing
python3 output/final_test.py

# Document conversion testing
python3 output/test_conversion.py
```

### Run the demo:

```bash
python3 contract_splitter/examples/demo.py
```

### Performance Testing

```bash
# Test with real documents
python3 -c "
from contract_splitter import ContractSplitter
import time

splitter = ContractSplitter(max_tokens=2000)
start = time.time()
sections = splitter.split('your_document.docx')
print(f'Processing time: {time.time() - start:.2f}s')
print(f'Sections: {len(sections)}, Chunks: {len(splitter.flatten(sections))}')
"
```

## 📁 Project Structure

```
contract_splitter/
├── __init__.py          # Main package interface
├── base.py              # Abstract base classes
├── docx_splitter.py     # DOCX/DOC document processor (enhanced)
├── pdf_splitter.py      # PDF document processor
├── converter.py         # Document format converter (NEW)
├── utils.py             # Utility functions
├── examples/
│   └── demo.py          # Usage examples
tests/
├── test_contract_splitter.py  # Test suite
output/
├── final_test.py        # Comprehensive test suite
├── test_conversion.py   # Conversion testing
└── *.json              # Test results and outputs
requirements.txt         # Dependencies
README.md               # This file
setup.py                # Package configuration
```

## 📝 Changelog

### v1.1.0 (Latest)
- ✅ **Enhanced Table Extraction**: Smart table structure preservation with proper key-value mapping
- ✅ **Automatic .doc Conversion**: Seamless legacy format support using LibreOffice/pandoc
- ✅ **Robust Error Handling**: Multiple fallback methods for document processing
- ✅ **Improved Content Structure**: Better handling of complex document layouts
- ✅ **Performance Optimizations**: Faster processing and memory efficiency

### v1.0.0
- Initial release with basic .docx and .pdf support
- Chinese language optimization
- Hierarchical structure extraction

## 📋 Dependencies

### Required
- `python-docx>=0.8.11` - For .doc/.docx processing
- `pdfplumber>=0.7.0` - Primary PDF processing
- `PyMuPDF>=1.20.0` - PDF outline extraction

### Optional
- `tiktoken>=0.4.0` - Accurate token counting
- `docx2txt>=0.8` - Alternative text extraction
- `textract>=1.6.3` - Universal text extraction

### System Dependencies (for .doc conversion)
- **LibreOffice** (recommended) - Universal document converter
- **pandoc** (alternative) - Document conversion tool
- **win32com** (Windows only) - COM automation for Office

## ⚠️ Limitations

- PDF support is limited to structured (non-OCR) documents
- Very large documents may require memory optimization
- ~~Complex table structures may not be perfectly preserved~~ ✅ **FIXED in v1.1.0**
- .doc conversion requires system dependencies (LibreOffice/pandoc)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Examples

See `contract_splitter/examples/demo.py` for comprehensive usage examples including:

- Basic document splitting
- Hierarchical structure handling
- Chinese text processing
- Error handling
- Advanced configuration options

## Support

For issues and questions:
1. Check the examples and documentation
2. Run the test suite to verify installation
3. Create an issue with detailed information about your use case
