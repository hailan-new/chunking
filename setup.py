#!/usr/bin/env python3
"""
Setup script for contract_splitter package.
"""

from setuptools import setup, find_packages
import os
import platform

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# Read requirements
def read_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract just the package name and version
                    if ">=" in line:
                        requirements.append(line.split(">=")[0] + ">=" + line.split(">=")[1])
                    else:
                        requirements.append(line)
    return requirements

setup(
    name="contract_splitter",
    version="2.0.0",
    author="Contract Splitter Team",
    author_email="contact@example.com",
    description="Advanced document splitter with WPS native support, enhanced table extraction and multi-format support for contracts and legal documents",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/contract_splitter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-docx>=0.8.11",
        "pdfplumber>=0.7.0",
        "PyMuPDF>=1.20.0",
        "striprtf>=0.0.26",  # RTF processing for WPS files
        "requests>=2.25.0",  # For WPS API support
        "openpyxl>=3.0.0",  # Excel processing
        "xlrd>=2.0.0",  # Legacy Excel support
    ],
    extras_require={
        "tiktoken": ["tiktoken>=0.4.0"],
        "enhanced": [
            "tiktoken>=0.4.0",
            "docx2txt>=0.8",
            "textract>=1.6.3",
        ],
        "conversion": [
            "docx2txt>=0.8",
            "textract>=1.6.3",
        ],
        # WPS native support (platform-specific)
        "wps": [
            "docx2txt>=0.8",
            "striprtf>=0.0.26",
            "requests>=2.25.0",
        ] + (["pywin32>=306"] if platform.system() == "Windows" else []),
        "wps-windows": [
            "pywin32>=306",
            "pywpsrpc>=2.3.0",  # WPS Office RPC for Windows
        ],
        "wps-api": [
            "requests>=2.25.0",
            "httpx>=0.24.0",  # Alternative HTTP client
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "examples": [
            "jupyter>=1.0.0",
            "matplotlib>=3.5.0",
            "pandas>=1.4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "contract-splitter=contract_splitter.examples.demo:main",
        ],
    },
    include_package_data=True,
    package_data={
        "contract_splitter": [
            "examples/*.py",
        ],
    },
    keywords=[
        "document", "splitting", "contract", "pdf", "docx", "doc", "wps",
        "chinese", "nlp", "text-processing", "chunking", "table-extraction",
        "legal-documents", "financial-documents", "document-conversion",
        "hierarchical-parsing", "content-extraction", "wps-native", "rtf-processing"
    ],
    project_urls={
        "Bug Reports": "https://github.com/example/contract_splitter/issues",
        "Source": "https://github.com/example/contract_splitter",
        "Documentation": "https://contract-splitter.readthedocs.io/",
    },
)
