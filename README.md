# Document Conversion & Compression Toolkit

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

A comprehensive, all-in-one document conversion and compression toolkit with both web interface and command-line tools. Convert, compress, and manage your documents with ease.

![Dashboard Preview](https://via.placeholder.com/800x400?text=DocConvert+Pro+Dashboard)

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Web Interface](#-web-interface)
- [Command Line Interface](#-command-line-interface)
- [Python Scripts](#-python-scripts)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Use Cases](#-use-cases)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 📄 Document Conversion
- **Text to PDF** - Convert `.txt`, `.md` files to PDF
- **Image to PDF** - Single or multiple images to PDF
- **Word to PDF** - Convert `.docx` documents to PDF (requires LibreOffice)
- **Excel ⇄ CSV** - Bidirectional conversion between Excel and CSV
- **JSON to CSV** - Flatten JSON structures to CSV format

### 🗜️ Compression Tools
- **ZIP Compression** - Compress files and folders to ZIP format
- **TAR Archives** - Create TAR archives
- **GZIP/BZIP2** - Advanced compression algorithms
- **Extract Archives** - Decompress ZIP, TAR, GZ, BZ2 files

### 📑 PDF Operations
- **Merge PDFs** - Combine multiple PDF files into one
- **Split PDF** - Extract specific pages or split all pages
- **Page Extraction** - Extract custom page ranges

### 🔄 Batch Processing
- **Folder Conversion** - Convert entire directories
- **Watch Folder** - Monitor folders for new files
- **Rule-based Processing** - Define custom rules per file type
- **Logging** - Detailed logs of all operations

### 📊 File Management
- **File Information** - View metadata, size, hash, dates
- **Organize Files** - Sort files by type into folders
- **Find Duplicates** - Identify and remove duplicate files
- **MD5 Hashing** - Calculate file checksums

### 🖥️ Multiple Interfaces
- **Web Dashboard** - Modern, responsive web interface
- **Command Line** - Powerful CLI for automation
- **Python API** - Import and use in your scripts
- **GUI Launcher** - Optional desktop application

## 🚀 Quick Start

### One-liner Installation
```bash
pip install -r requirements.txt
```

### Start Web Interface
```bash
# Open index.html in your browser
open index.html  # macOS
start index.html # Windows
xdg-open index.html # Linux
```

### Basic CLI Usage
```bash
# Convert text to PDF
python document_converter.py convert document.txt --to pdf

# Compress a folder
python document_converter.py compress my_folder/ --method zip

# Get file information
python document_converter.py info document.pdf
```

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager
- Modern web browser (for web interface)

### Step-by-Step Installation

1. **Clone or download the repository**
```bash
git clone https://github.com/yourusername/doc-convert-toolkit.git
cd doc-convert-toolkit
```

2. **Install required packages**
```bash
pip install -r requirements.txt
```

3. **Verify installation**
```bash
python document_converter.py --help
```

### Optional Dependencies
For full functionality, install additional tools:
```bash
# For Word to PDF conversion
# Install LibreOffice: https://www.libreoffice.org/

# For enhanced PDF features
pip install PyPDF2 reportlab

# For image processing
pip install Pillow

# For Excel/CSV handling
pip install pandas openpyxl xlrd
```

## 🌐 Web Interface

The web interface provides a modern, user-friendly dashboard for all toolkit features.

### Accessing the Web Interface
Simply open `index.html` in any modern web browser.

### Web Interface Sections

#### 1. **Dashboard**
- Overview of all tools
- Quick access to popular features
- Recent activity log

#### 2. **Quick Converter**
- Drag & drop file upload
- Format selection dropdown
- Instant conversion preview

#### 3. **Document Conversion Tools**
- Text to PDF converter
- Image to PDF (single/multiple)
- Word to PDF converter
- Excel ↔ CSV converter
- JSON to CSV converter

#### 4. **Compression Tools**
- ZIP compressor for files/folders
- TAR archive creator
- GZIP/BZIP2 compression
- Archive extractor

#### 5. **PDF Operations**
- **Merge PDFs**: Combine multiple PDFs
  - Add multiple files
  - Rearrange order
  - Custom output name
  
- **Split PDF**: Extract pages
  - Split all pages
  - Custom page ranges (e.g., 1,3,5-8)
  - Extract to separate files

#### 6. **Batch Processing**
- Input folder selection
- Output folder selection
- Target format selection
- Processing options:
  - Include subfolders
  - Overwrite existing
  - Create log file
- File preview before processing

#### 7. **File Information**
- File metadata display:
  - File name and size
  - File type
  - Creation/modification dates
  - MD5 hash
- Browse or drag & drop files

#### 8. **File Management**
- Organize files by type
- Find and remove duplicates
- Move/categorize files

### Web Interface Customization

The web interface is fully customizable via CSS variables:
```css
:root {
    --primary-color: #3b82f6;
    --secondary-color: #10b981;
    --danger-color: #ef4444;
    --dark-bg: #0f172a;
    --light-bg: #f8fafc;
}
```

## 💻 Command Line Interface

### Global Options
```bash
python document_converter.py [command] [options]
```

### Commands

#### File Information
```bash
# Get detailed file information
python document_converter.py info <file>

# Example
python document_converter.py info document.pdf
```

#### Document Conversion
```bash
# Text to PDF
python document_converter.py convert file.txt --to pdf

# Image to PDF
python document_converter.py convert image.jpg --to pdf

# Word to PDF
python document_converter.py convert document.docx --to pdf

# Excel to CSV
python document_converter.py convert data.xlsx --to csv

# CSV to Excel
python document_converter.py convert data.csv --to xlsx

# JSON to CSV
python document_converter.py convert data.json --to csv

# With custom output
python document_converter.py convert file.txt --to pdf --output output.pdf
```

#### Compression
```bash
# Compress single file
python document_converter.py compress file.txt --method zip

# Compress folder
python document_converter.py compress my_folder/ --method zip

# Different compression methods
python document_converter.py compress file.txt --method tar
python document_converter.py compress file.txt --method gz
python document_converter.py compress file.txt --method bz2

# Compress folder to tar.gz
python document_converter.py compress my_folder/ --method targz

# Custom output
python document_converter.py compress file.txt --method zip --output archive.zip
```

#### Decompression
```bash
# Extract archive
python document_converter.py decompress archive.zip

# Extract to specific folder
python document_converter.py decompress archive.zip --output ./extracted
```

#### PDF Operations
```bash
# Merge PDFs
python document_converter.py pdf merge file1.pdf file2.pdf -o merged.pdf

# Split PDF (all pages)
python document_converter.py pdf split document.pdf

# Split specific pages
python document_converter.py pdf split document.pdf --pages 1 3 5-8

# Split to custom folder
python document_converter.py pdf split document.pdf --output ./split_pages
```

#### Batch Processing
```bash
# Convert all files in folder to PDF
python document_converter.py batch /path/to/folder --to pdf

# Convert to specific format with output folder
python document_converter.py batch /input/folder --to csv --output /output/folder
```

#### File Organization
```bash
# Organize files by type
python document_converter.py organize /path/to/folder

# Find and remove duplicates
python document_converter.py clean /path/to/folder --find-duplicates
```

## 🐍 Python Scripts

### Main Converter Class

```python
from document_converter import DocumentConverter

# Initialize converter
converter = DocumentConverter()

# Get file information
info = converter.get_file_info("document.pdf")
print(f"File size: {info['size_readable']}")
print(f"MD5: {info['md5_hash']}")

# Convert text to PDF
success, message = converter.convert_text_to_pdf(
    "input.txt", 
    "output.pdf"
)

# Compress folder
success, message = converter.compress_folder(
    "my_folder",
    "archive.zip",
    method="zip"
)

# Merge PDFs
success, message = converter.merge_pdfs(
    ["file1.pdf", "file2.pdf"],
    "merged.pdf"
)
```

### Batch Processor

```python
from batch_processor import BatchProcessor

# Initialize processor
processor = BatchProcessor("config.json")

# Setup logging
processor.setup_logging()

# Process folder
processed, errors = processor.process_watch_folder(
    watch_folder="./incoming",
    output_folder="./processed"
)

print(f"Processed: {processed}, Errors: {errors}")
```

### Watch Service

```python
# Monitor folder continuously
processor.create_watch_service(
    watch_folder="./watch",
    output_folder="./output",
    interval=30  # Check every 30 seconds
)
```

## 📚 API Reference

### DocumentConverter Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get_file_info()` | `filepath: str` | `dict` | File metadata |
| `convert_text_to_pdf()` | `input_file, output_file` | `(bool, str)` | Text to PDF |
| `convert_image_to_pdf()` | `input_file, output_file` | `(bool, str)` | Image to PDF |
| `convert_docx_to_pdf()` | `input_file, output_file` | `(bool, str)` | Word to PDF |
| `convert_csv_to_excel()` | `input_file, output_file` | `(bool, str)` | CSV to Excel |
| `convert_excel_to_csv()` | `input_file, output_file` | `(bool, str)` | Excel to CSV |
| `convert_json_to_csv()` | `input_file, output_file` | `(bool, str)` | JSON to CSV |
| `compress_file()` | `input_file, output_file, method` | `(bool, str)` | Compress file |
| `compress_folder()` | `folder_path, output_file, method` | `(bool, str)` | Compress folder |
| `decompress_file()` | `input_file, output_dir` | `(bool, str)` | Decompress archive |
| `merge_pdfs()` | `pdf_files, output_file` | `(bool, str)` | Merge PDFs |
| `split_pdf()` | `input_file, output_dir, pages` | `(bool, str)` | Split PDF |
| `batch_convert()` | `input_folder, target_format, output_folder` | `list` | Batch convert |
| `organize_by_type()` | `folder_path` | `(bool, str)` | Organize files |
| `remove_duplicates()` | `folder_path` | `(bool, str)` | Remove duplicates |

## ⚙️ Configuration

### Configuration File (config.json)

```json
{
    ".txt": {
        "action": "convert",
        "to": "pdf"
    },
    ".jpg": {
        "action": "convert",
        "to": "pdf"
    },
    ".png": {
        "action": "convert",
        "to": "pdf"
    },
    ".csv": {
        "action": "convert",
        "to": "xlsx"
    },
    ".xlsx": {
        "action": "convert",
        "to": "csv"
    },
    ".docx": {
        "action": "convert",
        "to": "pdf"
    },
    ".zip": {
        "action": "decompress"
    },
    "photos": {
        "action": "move",
        "category": "images"
    },
    "documents": {
        "action": "move",
        "category": "docs"
    }
}
```

### Environment Variables

```bash
# Set output directory
export DOC_CONVERT_OUTPUT_DIR="/path/to/output"

# Set log level
export DOC_CONVERT_LOG_LEVEL="INFO"

# Enable debug mode
export DOC_CONVERT_DEBUG="true"
```

## 🎯 Use Cases

### 1. **Office Document Management**
```bash
# Convert all Word docs to PDF for archiving
python document_converter.py batch ./documents --to pdf

# Organize files by type
python document_converter.py organize ./documents
```

### 2. **Image to PDF Conversion**
```bash
# Convert scanned images to PDF
python document_converter.py convert scan.jpg --to pdf

# Multiple images to single PDF
# (Use web interface for multi-select)
```

### 3. **Data Processing Pipeline**
```bash
# Watch folder for new CSV files and convert to Excel
python batch_processor.py watch --watch ./data --output ./processed
```

### 4. **Backup and Archiving**
```bash
# Compress project folder
python document_converter.py compress ./project --method zip

# Create tar.gz archive
python document_converter.py compress ./project --method targz
```

### 5. **PDF Report Generation**
```python
from document_converter import DocumentConverter

converter = DocumentConverter()

# Merge monthly reports
converter.merge_pdfs(
    ["jan.pdf", "feb.pdf", "mar.pdf"],
    "q1_report.pdf"
)
```

## 🔧 Troubleshooting

### Common Issues

#### 1. **"Module not found" errors**
```bash
pip install -r requirements.txt --upgrade
```

#### 2. **Word to PDF conversion fails**
- Install LibreOffice
- Ensure `soffice` is in system PATH
- Try manual conversion as fallback

#### 3. **Large file memory issues**
```python
# Process in chunks
converter.split_pdf("large.pdf", pages=[1,2,3])  # Process specific pages
```

#### 4. **Permission denied errors**
```bash
# On Linux/macOS
chmod +x *.py

# On Windows (run as administrator)
# Right-click -> Run as administrator
```

### Debug Mode

```bash
# Enable verbose output
python document_converter.py --verbose convert file.txt --to pdf

# Save debug log
python document_converter.py --log-file debug.log convert file.txt --to pdf
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup
```bash
# Fork the repository
git clone https://github.com/yourusername/doc-convert-toolkit.git
cd doc-convert-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Guidelines

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Style
- Follow PEP 8 guidelines
- Add docstrings for new functions
- Include tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 DocConvert Pro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **Font Awesome** for icons
- **Python community** for amazing libraries
- **Contributors** who help improve this toolkit

## 📞 Support

- **Documentation**: [Read the docs](https://github.com/yourusername/doc-convert-toolkit/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/doc-convert-toolkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/doc-convert-toolkit/discussions)

---

**Made with ❤️ for document management**

[⬆ Back to Top](#document-conversion--compression-toolkit)