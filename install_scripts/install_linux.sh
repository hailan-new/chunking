#!/bin/bash
# Linux installation script for contract_splitter with WPS support
# Run with: bash install_linux.sh

set -e  # Exit on any error

echo "========================================"
echo "Contract Splitter Linux Installation"
echo "========================================"
echo

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "Cannot detect Linux distribution"
    OS="Unknown"
fi

echo "Detected OS: $OS"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
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

# Install system dependencies based on distribution
echo "Installing system dependencies..."

if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    echo "Installing dependencies for Ubuntu/Debian..."
    sudo apt-get update
    
    # Install LibreOffice
    if ! dpkg -l | grep -q libreoffice-core; then
        echo "Installing LibreOffice..."
        sudo apt-get install -y libreoffice
    else
        echo "LibreOffice already installed"
    fi
    
    # Install antiword for .doc files
    if ! dpkg -l | grep -q antiword; then
        echo "Installing antiword..."
        sudo apt-get install -y antiword
    else
        echo "antiword already installed"
    fi
    
    # Install pandoc
    if ! dpkg -l | grep -q pandoc; then
        echo "Installing pandoc..."
        sudo apt-get install -y pandoc
    else
        echo "pandoc already installed"
    fi
    
    # Try to install WPS Office for Linux (if available)
    echo "Checking for WPS Office availability..."
    if wget -q --spider https://wps-linux-personal.wpscdn.cn/wps/download/ep/Linux2019/10161/wps-office_11.1.0.10161_amd64.deb; then
        echo "WPS Office for Linux is available. Install manually if needed:"
        echo "  wget https://wps-linux-personal.wpscdn.cn/wps/download/ep/Linux2019/10161/wps-office_11.1.0.10161_amd64.deb"
        echo "  sudo dpkg -i wps-office_11.1.0.10161_amd64.deb"
    fi

elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"RHEL"* ]]; then
    echo "Installing dependencies for CentOS/RHEL..."
    
    # Install LibreOffice
    if ! rpm -q libreoffice-core &> /dev/null; then
        echo "Installing LibreOffice..."
        sudo yum install -y libreoffice
    else
        echo "LibreOffice already installed"
    fi
    
    # Install antiword
    if ! rpm -q antiword &> /dev/null; then
        echo "Installing antiword..."
        sudo yum install -y antiword
    else
        echo "antiword already installed"
    fi

elif [[ "$OS" == *"Fedora"* ]]; then
    echo "Installing dependencies for Fedora..."
    
    # Install LibreOffice
    if ! rpm -q libreoffice-core &> /dev/null; then
        echo "Installing LibreOffice..."
        sudo dnf install -y libreoffice
    else
        echo "LibreOffice already installed"
    fi
    
    # Install antiword
    if ! rpm -q antiword &> /dev/null; then
        echo "Installing antiword..."
        sudo dnf install -y antiword
    else
        echo "antiword already installed"
    fi

else
    echo "Unknown Linux distribution. Please manually install:"
    echo "  - LibreOffice"
    echo "  - antiword"
    echo "  - pandoc"
fi

# Check installations
echo
echo "Checking installations..."

if command -v soffice &> /dev/null; then
    echo "✓ LibreOffice found - WPS file conversion will work"
else
    echo "✗ LibreOffice not found - please install manually"
fi

if command -v antiword &> /dev/null; then
    echo "✓ antiword found - .doc file support available"
else
    echo "✗ antiword not found - limited .doc file support"
fi

if command -v wps &> /dev/null || command -v wpsoffice &> /dev/null; then
    echo "✓ WPS Office found - Native WPS support available"
else
    echo "ℹ WPS Office not found - LibreOffice will be used for WPS files"
fi

echo
echo "========================================"
echo "Installation completed!"
echo "========================================"
echo
echo "Available WPS processing methods on Linux:"
echo "1. WPS Office native (if WPS Office for Linux installed)"
echo "2. LibreOffice conversion (primary fallback)"
echo "3. WPS API (with API key)"
echo "4. Alternative libraries"
echo
echo "To use WPS API, set your API key:"
echo "  from contract_splitter.wps_processor import WPSProcessor"
echo "  processor = WPSProcessor(wps_api_key='your_api_key')"
echo
echo "Test installation with:"
echo "  python3 -c \"from contract_splitter import split_legal_document; print('Installation successful!')\""
echo
