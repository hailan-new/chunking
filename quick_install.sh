#!/bin/bash
# Quick install script for contract_splitter with WPS support
# Usage: curl -sSL https://raw.githubusercontent.com/your-repo/contract_splitter/main/quick_install.sh | bash

set -e

echo "🚀 Contract Splitter Quick Install"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found"

# Install core package
echo "📦 Installing contract_splitter..."
pip3 install python-docx pdfplumber PyMuPDF striprtf requests

# Install WPS support
echo "📄 Installing WPS support..."
pip3 install docx2txt

# Platform-specific installations
OS="$(uname -s)"
case "${OS}" in
    Linux*)
        echo "🐧 Linux detected - installing system dependencies..."
        if command -v apt-get &> /dev/null; then
            echo "Installing via apt-get..."
            sudo apt-get update && sudo apt-get install -y libreoffice antiword
        elif command -v yum &> /dev/null; then
            echo "Installing via yum..."
            sudo yum install -y libreoffice antiword
        elif command -v dnf &> /dev/null; then
            echo "Installing via dnf..."
            sudo dnf install -y libreoffice antiword
        else
            echo "⚠️  Please install LibreOffice manually"
        fi
        ;;
    Darwin*)
        echo "🍎 macOS detected"
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install libreoffice antiword
        else
            echo "⚠️  Please install Homebrew and LibreOffice manually"
        fi
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo "🪟 Windows detected - please run install_scripts/install_windows.bat"
        ;;
    *)
        echo "❓ Unknown OS: ${OS}"
        ;;
esac

# Test installation
echo "🔍 Testing installation..."
if python3 -c "from contract_splitter import split_document; print('✅ Installation successful!')" 2>/dev/null; then
    echo "🎉 Contract Splitter is ready to use!"
    echo ""
    echo "📚 Quick start:"
    echo "  python3 -c \"from contract_splitter import split_document; chunks = split_document('your_file.wps'); print(f'Generated {len(chunks)} chunks')\""
    echo ""
    echo "📄 For WPS files, the system will automatically:"
    echo "  1. Try WPS Office native methods (if available)"
    echo "  2. Use LibreOffice conversion (fallback)"
    echo "  3. Apply intelligent text processing"
    echo ""
    echo "🔧 For advanced WPS support:"
    echo "  - Get WPS API key from WPS Open Platform"
    echo "  - Install WPS Office for native processing"
else
    echo "❌ Installation test failed"
    exit 1
fi
