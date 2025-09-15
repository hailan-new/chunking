# Contract Splitter

An advanced Python package for splitting contract documents (.doc, .docx, .pdf, .wps, .xlsx, .xls, .xlsm) into hierarchical sections with intelligent format detection, specialized domain processing, and automatic format conversion. Features a factory pattern architecture for optimal document processing and comprehensive Chinese language support.

## 🚀 Key Features

- **🏭 Factory Pattern Architecture**: Intelligent splitter selection based on file format
- **🎯 Specialized Domain Processing**: Dedicated splitters for legal documents, contracts, and regulations
- **🔄 WPS Native Support**: First-class WPS file processing with multiple conversion methods
- **🔄 Automatic Format Conversion**: Seamlessly converts .doc and .wps files using WPS Office, LibreOffice, or Win32COM
- **📁 Multi-format Support**: Process .doc, .docx, .pdf, .wps, .xlsx, .xls, .xlsm files with automatic detection
- **📊 Enhanced Table Extraction**: Advanced table structure preservation with smart cell mapping
- **🏗️ Hierarchical Structure**: Maintains document hierarchy (chapters, sections, subsections)
- **🇨🇳 Chinese Language Support**: Optimized for Chinese contracts and legal documents
- **⚙️ Flexible Splitting**: Size-constrained splitting with configurable parameters
- **🔢 Multiple Token Counters**: Character-based or tiktoken-based token counting
- **🪟 Sliding Window**: Overlapping chunks for better context preservation
- **📝 Natural Breakpoints**: Respects sentence and paragraph boundaries
- **🛡️ Robust Error Handling**: Multiple fallback methods for problematic documents

## 📦 Installation

### 🚀 Smart Installer (Recommended)

The smart installer automatically detects your platform and installs the best dependencies:

```bash
# Download and run smart installer
python3 install.py

# Or one-line quick install
curl -sSL https://raw.githubusercontent.com/your-repo/contract_splitter/main/quick_install.sh | bash
```

### 📦 Standard Installation

```bash
pip install contract-splitter
```

### 🔧 Core Dependencies Only

```bash
pip install python-docx pdfplumber PyMuPDF striprtf requests openpyxl xlrd
```

### Enhanced Features

```bash
# For enhanced table extraction and document conversion
pip install contract-splitter[enhanced]

# For accurate token counting
pip install contract-splitter[tiktoken]

# For document conversion support
pip install contract-splitter[conversion]

# For Excel processing support
pip install contract-splitter[excel]         # Excel processing with openpyxl and xlrd

# For WPS native support (choose based on your platform)
pip install contract-splitter[wps]           # Basic WPS support
pip install contract-splitter[wps-windows]   # Windows native WPS support
pip install contract-splitter[wps-api]       # WPS API support
```

### Platform-Specific Installation

**Windows (with WPS native support):**
```bash
# Run the automated installer
install_scripts/install_windows.bat

# Or install manually
pip install contract-splitter[wps-windows]
```

**macOS:**
```bash
# Run the automated installer
bash install_scripts/install_macos.sh

# Or install manually
brew install libreoffice  # Recommended for .doc/.wps conversion
pip install contract-splitter[wps]
```

**Linux:**
```bash
# Run the automated installer
bash install_scripts/install_linux.sh

# Or install manually
sudo apt-get install libreoffice  # Ubuntu/Debian
sudo yum install libreoffice      # CentOS/RHEL
pip install contract-splitter[wps]
```

**Windows:**
- Install LibreOffice from https://www.libreoffice.org/
- For native WPS support: Install WPS Office from https://www.wps.com/
- Or install pandoc from https://pandoc.org/

## 📄 WPS File Processing Methods

Contract Splitter provides multiple methods for processing WPS files, automatically selecting the best available option:

### 🥇 Priority Order (Automatic Selection)

1. **WPS Office Native** (Windows/Linux) - Best quality
   - Uses WPS Office COM interface (Windows)
   - Uses WPS Office command line (Linux)
   - Preserves original formatting and structure

2. **WPS API** (All platforms) - Cloud-based
   - Requires WPS Open Platform API key
   - High-quality conversion via WPS cloud services
   - Works on all platforms

3. **LibreOffice Conversion** (All platforms) - Reliable fallback
   - Uses LibreOffice for format conversion
   - Good compatibility and quality
   - Available on all platforms

4. **Alternative Libraries** (All platforms) - Last resort
   - Uses docx2txt and other libraries
   - Basic text extraction
   - May lose some formatting

### 🔧 Manual Configuration

```python
from contract_splitter.wps_processor import WPSProcessor

# With WPS API key (recommended for production)
processor = WPSProcessor(wps_api_key="your_api_key_here")

# The system will automatically try methods in priority order
chunks = split_document("document.wps", max_tokens=2000)
```

### 🎯 Platform-Specific Recommendations

- **Windows**: Install WPS Office for best results
- **macOS**: Use LibreOffice (WPS Office not available)
- **Linux**: Install WPS Office for Linux or use LibreOffice
- **Cloud/Server**: Use WPS API with API key

## 🚀 Quick Start

### Simple Usage (Recommended)

```python
from contract_splitter import split_document

# Automatic format detection and processing
chunks = split_document("contract.docx", max_tokens=2000)
print(f"Generated {len(chunks)} chunks")

# Works with multiple formats
chunks = split_document("legal_doc.pdf", max_tokens=1500)  # PDF support
chunks = split_document("old_contract.doc", max_tokens=2000)  # Auto-converts DOC
chunks = split_document("wps_file.wps", max_tokens=2000)  # WPS support
chunks = split_document("data.xlsx", max_tokens=1500)      # Excel support
chunks = split_document("legal_table.xls", max_tokens=2000, extract_mode="legal_content")  # Excel with legal optimization
```

### Advanced Usage with Factory Pattern

```python
from contract_splitter import SplitterFactory

# Create factory instance
factory = SplitterFactory()

# Get file information and format support
file_info = factory.get_file_info("contract.docx")
print(f"Format: {file_info['format']}, Supported: {file_info['supported']}")
print(f"Will use: {file_info['splitter_class']}")

# Process with custom settings
chunks = factory.split_and_flatten(
    "contract.docx",
    max_tokens=2000,
    overlap=200,
    strict_max_tokens=True
)
```

### Specialized Domain Processing

```python
from contract_splitter.domain_helpers import (
    split_legal_document,
    split_contract,
    split_regulation
)

# Legal documents (optimized for laws, regulations)
legal_chunks = split_legal_document("law.docx", max_tokens=1500)

# Contracts (optimized for business contracts)
contract_chunks = split_contract("contract.docx", contract_type="general")

# Regulations (optimized for internal policies)
regulation_chunks = split_regulation("policy.docx", regulation_type="general")
```

### 📄 WPS File Processing Workflow

The system automatically handles WPS files through an intelligent workflow:

```python
from contract_splitter import split_document
from contract_splitter.wps_processor import WPSProcessor

# Simple usage - automatic method selection
chunks = split_document("document.wps", max_tokens=2000)

# Advanced usage with custom WPS processor
processor = WPSProcessor(wps_api_key="your_api_key")  # Optional API key

# The system follows this workflow:
# 1. Detect WPS file format
# 2. Try WPS native methods (if available)
# 3. Fallback to LibreOffice conversion
# 4. Extract text using RTF processing
# 5. Apply legal document splitting logic
# 6. Return structured chunks

# Check available conversion methods
print("Available converters:", processor.available_converters)
# Output: ['wps_native', 'libreoffice', 'direct'] (platform-dependent)
```

### 🔄 WPS Processing Method Details

```python
# Method 1: WPS Office Native (Windows/Linux)
# - Uses WPS Office COM interface (Windows)
# - Uses WPS Office command line (Linux)
# - Highest quality, preserves formatting

# Method 2: WPS Cloud API (All platforms)
# - Requires WPS Open Platform API key
# - High-quality cloud conversion
# - Works on all platforms

# Method 3: LibreOffice Conversion (All platforms)
# - Converts WPS to RTF/DOCX format
# - Uses professional RTF parsing (striprtf library)
# - Reliable fallback method

# Method 4: Alternative Libraries (All platforms)
# - Uses docx2txt and similar libraries
# - Basic text extraction
# - Last resort method
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

## 🏗️ Architecture Overview

The package uses a **Factory Pattern** architecture for optimal document processing:

```
SplitterFactory
├── DocxSplitter (.docx, .doc)
├── PdfSplitter (.pdf)
├── WpsSplitter (.wps)
└── Automatic Format Detection
```

### Format-Specific Processing

| Format | Splitter | Features |
|--------|----------|----------|
| **DOCX** | `DocxSplitter` | Native python-docx processing, table extraction |
| **DOC** | `DocxSplitter` | Auto-conversion via LibreOffice |
| **PDF** | `PdfSplitter` | Multi-backend (pdfplumber, PyMuPDF, PyPDF2) |
| **WPS** | `WpsSplitter` | Conversion to DOCX then processing |

### Domain-Specific Helpers

- **Legal Documents**: Optimized for laws, regulations, court decisions
- **Contracts**: Specialized for business contracts and agreements
- **Regulations**: Tailored for internal policies and procedures

## Configuration Options

```python
# Using specific splitter
from contract_splitter import DocxSplitter
splitter = DocxSplitter(
    max_tokens=2000,           # Maximum tokens per chunk
    overlap=200,               # Overlap length for sliding window
    split_by_sentence=True,    # Respect sentence boundaries
    token_counter="character", # "character" or "tiktoken"
    strict_max_tokens=True     # Enforce strict token limits
)

# Using factory with auto-detection
from contract_splitter import split_document
chunks = split_document(
    "document.docx",
    max_tokens=2000,
    strict_max_tokens=True
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
- **✅ Native DOCX Support**: Direct processing with python-docx
- **🔄 Legacy .doc Support**: Automatic conversion using LibreOffice
- **📊 Enhanced Table Extraction**: Smart table structure preservation
- **🎯 Heading Detection**: Extracts heading styles (Heading 1, Heading 2, etc.)
- **🇨🇳 Chinese Patterns**: Detects Chinese and English heading patterns
- **📋 Structure Preservation**: Maintains paragraph and list structure
- **🛡️ Multiple Fallbacks**: Robust error handling for corrupted files

### 📄 PDF Files (.pdf)
- **🔖 Multi-Backend Support**: pdfplumber, PyMuPDF, PyPDF2
- **📊 Digital PDF Processing**: Optimized for text-based (non-OCR) PDFs
- **🎨 Font-based Detection**: Intelligent heading detection
- **🔍 Content Analysis**: Advanced text extraction and structure detection
- **⚠️ OCR Detection**: Automatically detects scanned documents

### 📋 WPS Files (.wps)
- **🔄 Automatic Conversion**: Converts to DOCX using LibreOffice or Win32COM
- **🖥️ Cross-Platform**: Works on Windows (COM), macOS/Linux (LibreOffice)
- **📊 Full Feature Support**: All DOCX features after conversion
- **🛡️ Fallback Methods**: Multiple conversion strategies

### 🆕 New in v2.0.0
- **🏭 Factory Pattern Architecture**: Intelligent format detection and splitter selection
- **🎯 Specialized Domain Processing**: Legal, contract, and regulation-specific splitters
- **📋 WPS File Support**: Native WPS document processing
- **🔄 Enhanced Format Conversion**: Improved .doc and .wps conversion
- **📊 Multi-Backend PDF Support**: pdfplumber, PyMuPDF, PyPDF2 integration
- **🛡️ Robust Error Handling**: Multiple fallback strategies for each format
- **⚡ Performance Improvements**: Optimized processing pipeline with caching

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

### 📊 Excel Document Processing

The package includes specialized Excel processing with legal document optimization:

```python
from contract_splitter import ExcelSplitter

# Legal content mode - optimized for legal documents
splitter = ExcelSplitter(
    max_tokens=1500,
    extract_mode="legal_content"  # Detects legal structures
)
sections = splitter.split("legal_regulations.xlsx")

# Table structure mode - preserves table format
splitter = ExcelSplitter(
    extract_mode="table_structure"  # Maintains table structure
)
sections = splitter.split("data_table.xlsx")

# All content mode - comprehensive extraction
splitter = ExcelSplitter(
    extract_mode="all_content"  # Extracts everything
)
sections = splitter.split("mixed_content.xlsx")

# Example output for legal content:
# 【工作表: 法律条文】
# ★ 第一条 | 为了规范证券公司分类监管... | 全部证券公司
# ★ 第二条 | 本规定适用于在中华人民共和国... | 境内证券公司
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
