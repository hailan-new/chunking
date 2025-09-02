@echo off
REM Windows installation script for contract_splitter with WPS native support
REM Run as Administrator for best results

echo ========================================
echo Contract Splitter Windows Installation
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing contract_splitter...
echo.

REM Install core package
echo Installing core dependencies...
pip install python-docx pdfplumber PyMuPDF striprtf requests

REM Install Windows-specific WPS support
echo Installing Windows WPS native support...
pip install pywin32

REM Try to install WPS RPC (may not be available on all systems)
echo Attempting to install WPS Office RPC support...
pip install pywpsrpc
if errorlevel 1 (
    echo Warning: pywpsrpc installation failed. WPS native support will be limited.
    echo You can still use LibreOffice fallback for WPS files.
)

REM Install enhanced features
echo Installing enhanced features...
pip install tiktoken docx2txt textract markitdown

REM Check for LibreOffice
echo.
echo Checking for LibreOffice...
where soffice >nul 2>&1
if errorlevel 1 (
    echo WARNING: LibreOffice not found
    echo Please install LibreOffice from https://www.libreoffice.org/
    echo This is required for WPS file conversion fallback
) else (
    echo LibreOffice found - WPS file conversion will work
)

REM Check for WPS Office
echo.
echo Checking for WPS Office...
where wps >nul 2>&1
if errorlevel 1 (
    where wpsoffice >nul 2>&1
    if errorlevel 1 (
        echo INFO: WPS Office not found
        echo For best WPS file support, install WPS Office from https://www.wps.com/
        echo LibreOffice will be used as fallback
    ) else (
        echo WPS Office found - Native WPS support available
    )
) else (
    echo WPS Office found - Native WPS support available
)

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo.
echo Available WPS processing methods:
echo 1. WPS Office COM interface (if WPS Office installed)
echo 2. WPS Office command line (if WPS Office installed)
echo 3. LibreOffice conversion (fallback)
echo 4. WPS API (with API key)
echo.
echo To use WPS API, set your API key:
echo   from contract_splitter.wps_processor import WPSProcessor
echo   processor = WPSProcessor(wps_api_key="your_api_key")
echo.
echo Test installation with:
echo   python -c "from contract_splitter import split_legal_document; print('Installation successful!')"
echo.
pause
