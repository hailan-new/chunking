#!/bin/bash
# macOS installation script for contract_splitter with WPS support
# Run with: bash install_macos.sh

set -e  # Exit on any error

echo "========================================"
echo "Contract Splitter macOS Installation"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org or use Homebrew:"
    echo "  brew install python"
    exit 1
fi

echo "Python 3 found. Installing contract_splitter..."
echo

# Install core package
echo "Installing core dependencies..."
pip3 install python-docx pdfplumber PyMuPDF striprtf requests

# Install enhanced features
echo "Installing enhanced features..."
pip3 install tiktoken docx2txt textract markitdown

# Check for Homebrew
if command -v brew &> /dev/null; then
    echo "Homebrew found. Installing system dependencies..."
    
    # Install LibreOffice via Homebrew
    if ! brew list libreoffice &> /dev/null; then
        echo "Installing LibreOffice..."
        brew install --cask libreoffice
    else
        echo "LibreOffice already installed"
    fi
    
    # Install antiword for legacy .doc files
    if ! brew list antiword &> /dev/null; then
        echo "Installing antiword for .doc file support..."
        brew install antiword
    else
        echo "antiword already installed"
    fi
    
    # Install pandoc for universal document conversion
    if ! brew list pandoc &> /dev/null; then
        echo "Installing pandoc..."
        brew install pandoc
    else
        echo "pandoc already installed"
    fi
else
    echo "WARNING: Homebrew not found"
    echo "Please install Homebrew from https://brew.sh/ for easier dependency management"
    echo "Or manually install:"
    echo "  - LibreOffice: https://www.libreoffice.org/"
    echo "  - antiword: for .doc file support"
    echo "  - pandoc: https://pandoc.org/"
fi

# Check for LibreOffice
echo
echo "Checking for LibreOffice..."
if command -v soffice &> /dev/null; then
    echo "LibreOffice found - WPS file conversion will work"
elif [ -d "/Applications/LibreOffice.app" ]; then
    echo "LibreOffice app found - WPS file conversion will work"
else
    echo "WARNING: LibreOffice not found"
    echo "Please install LibreOffice from https://www.libreoffice.org/"
    echo "This is required for WPS file conversion"
fi

# Check for WPS Office (unlikely on macOS but check anyway)
echo
echo "Checking for WPS Office..."
if [ -d "/Applications/WPS Office.app" ]; then
    echo "WPS Office found - Limited native support may be available"
else
    echo "INFO: WPS Office not found (not commonly available on macOS)"
    echo "LibreOffice will be used for WPS file conversion"
fi

echo
echo "========================================"
echo "Installation completed!"
echo "========================================"
echo
echo "Available WPS processing methods on macOS:"
echo "1. LibreOffice conversion (primary method)"
echo "2. WPS API (with API key)"
echo "3. Alternative libraries (docx2txt, etc.)"
echo
echo "Note: Native WPS Office integration is limited on macOS"
echo "LibreOffice provides excellent WPS file conversion support"
echo
echo "To use WPS API, set your API key:"
echo "  from contract_splitter.wps_processor import WPSProcessor"
echo "  processor = WPSProcessor(wps_api_key='your_api_key')"
echo
echo "Test installation with:"
echo "  python3 -c \"from contract_splitter import split_legal_document; print('Installation successful!')\""
echo
