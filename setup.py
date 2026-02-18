#!/usr/bin/env python3
"""
Setup script for Document Conversion Toolkit
Run: python setup.py install
"""

from setuptools import setup, find_packages

setup(
    name="document-converter-toolkit",
    version="1.0.0",
    description="Comprehensive document conversion and compression toolkit",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    py_modules=["document_converter"],
    install_requires=[
        "Pillow>=9.0.0",        # Image processing
        "PyPDF2>=3.0.0",        # PDF manipulation
        "python-docx>=0.8.11",  # Word documents
        "pandas>=1.3.0",        # Excel/CSV processing
        "openpyxl>=3.0.0",      # Excel support
        "reportlab>=3.6.0",     # PDF generation
    ],
    entry_points={
        "console_scripts": [
            "doc-convert=document_converter:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)