#!/usr/bin/env python3
"""
Document Conversion and Compression Toolkit
A comprehensive tool for converting, compressing, and manipulating documents
"""

import os
import sys
import shutil
import zipfile
import tarfile
import argparse
from pathlib import Path
from datetime import datetime
import json
import hashlib
import subprocess
import platform

# Try importing optional dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not installed. Image conversion will be disabled.")
    print("Install with: pip install Pillow")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("PyPDF2 not installed. PDF operations will be limited.")
    print("Install with: pip install PyPDF2")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("python-docx not installed. Word document operations will be disabled.")
    print("Install with: pip install python-docx")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("pandas not installed. Excel/CSV operations will be disabled.")
    print("Install with: pip install pandas")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("reportlab not installed. PDF creation will be disabled.")
    print("Install with: pip install reportlab")


class DocumentConverter:
    """Main class for document conversion and manipulation"""
    
    def __init__(self, input_file=None, output_dir=None):
        self.input_file = input_file
        self.output_dir = output_dir or os.getcwd()
        self.supported_formats = self._get_supported_formats()
        
    def _get_supported_formats(self):
        """Return dictionary of supported formats"""
        formats = {
            'text': ['.txt', '.md', '.rst', '.log'],
            'document': ['.docx', '.doc', '.odt', '.rtf'],
            'pdf': ['.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'spreadsheet': ['.xlsx', '.xls', '.csv', '.ods'],
            'archive': ['.zip', '.tar', '.gz', '.bz2'],
            'web': ['.html', '.htm', '.xml', '.json'],
        }
        return formats
    
    def get_file_info(self, filepath):
        """Get detailed information about a file"""
        path = Path(filepath)
        if not path.exists():
            return None
            
        stats = path.stat()
        file_info = {
            'name': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': stats.st_size,
            'size_readable': self._bytes_to_readable(stats.st_size),
            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'path': str(path.absolute()),
            'md5_hash': self._calculate_md5(filepath)
        }
        return file_info
    
    def _bytes_to_readable(self, bytes_size):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    def _calculate_md5(self, filepath, chunk_size=8192):
        """Calculate MD5 hash of a file"""
        md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            return f"Error: {str(e)}"
    
    # ============= CONVERSION FUNCTIONS =============
    
    def convert_text_to_pdf(self, input_file, output_file=None):
        """Convert text file to PDF"""
        if not REPORTLAB_AVAILABLE:
            return False, "ReportLab not installed"
            
        if not output_file:
            output_file = str(Path(input_file).with_suffix('.pdf'))
        
        try:
            # Read text file
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Create PDF
            c = canvas.Canvas(output_file, pagesize=letter)
            width, height = letter
            
            # Write text to PDF
            y = height - 50
            for line in text.split('\n'):
                if y < 50:  # New page if near bottom
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line[:80])  # Limit line length
                y -= 15
            
            c.save()
            return True, f"Created PDF: {output_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def convert_image_to_pdf(self, input_file, output_file=None):
        """Convert image to PDF"""
        if not PIL_AVAILABLE:
            return False, "Pillow not installed"
            
        if not output_file:
            output_file = str(Path(input_file).with_suffix('.pdf'))
        
        try:
            image = Image.open(input_file)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            image.save(output_file, 'PDF', resolution=100.0)
            return True, f"Created PDF: {output_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def convert_multiple_images_to_pdf(self, image_files, output_file):
        """Convert multiple images to a single PDF"""
        if not PIL_AVAILABLE:
            return False, "Pillow not installed"
            
        try:
            images = []
            for img_file in image_files:
                img = Image.open(img_file)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                images.append(img)
            
            if images:
                images[0].save(output_file, 'PDF', save_all=True, 
                             append_images=images[1:])
                return True, f"Created multi-page PDF: {output_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def convert_docx_to_pdf(self, input_file, output_file=None):
        """Convert DOCX to PDF (requires LibreOffice)"""
        if not output_file:
            output_file = str(Path(input_file).with_suffix('.pdf'))
        
        try:
            # Try using LibreOffice if available
            if platform.system() == 'Windows':
                soffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
            else:
                soffice_path = "libreoffice"
            
            cmd = [soffice_path, '--headless', '--convert-to', 'pdf', 
                   '--outdir', str(Path(output_file).parent), input_file]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Converted to PDF: {output_file}"
            else:
                return False, "LibreOffice conversion failed"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def convert_csv_to_excel(self, input_file, output_file=None):
        """Convert CSV to Excel"""
        if not PANDAS_AVAILABLE:
            return False, "pandas not installed"
            
        if not output_file:
            output_file = str(Path(input_file).with_suffix('.xlsx'))
        
        try:
            df = pd.read_csv(input_file)
            df.to_excel(output_file, index=False)
            return True, f"Created Excel file: {output_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def convert_excel_to_csv(self, input_file, output_file=None):
        """Convert Excel to CSV"""
        if not PANDAS_AVAILABLE:
            return False, "pandas not installed"
            
        if not output_file:
            output_file = str(Path(input_file).with_suffix('.csv'))
        
        try:
            df = pd.read_excel(input_file)
            df.to_csv(output_file, index=False)
            return True, f"Created CSV file: {output_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def convert_json_to_csv(self, input_file, output_file=None):
        """Convert JSON to CSV"""
        if not PANDAS_AVAILABLE:
            return False, "pandas not installed"
            
        if not output_file:
            output_file = str(Path(input_file).with_suffix('.csv'))
        
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            df = pd.json_normalize(data)
            df.to_csv(output_file, index=False)
            return True, f"Created CSV file: {output_file}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    # ============= COMPRESSION FUNCTIONS =============
    
    def compress_file(self, input_file, output_file=None, method='zip'):
        """Compress a single file"""
        if not output_file:
            if method == 'zip':
                output_file = str(Path(input_file).with_suffix('.zip'))
            elif method in ['gz', 'bz2']:
                output_file = str(Path(input_file)) + f'.{method}'
            elif method == 'tar':
                output_file = str(Path(input_file).with_suffix('.tar'))
        
        try:
            if method == 'zip':
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(input_file, arcname=Path(input_file).name)
            
            elif method == 'tar':
                with tarfile.open(output_file, 'w') as tf:
                    tf.add(input_file, arcname=Path(input_file).name)
            
            elif method == 'gz':
                import gzip
                with open(input_file, 'rb') as f_in:
                    with gzip.open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            elif method == 'bz2':
                import bz2
                with open(input_file, 'rb') as f_in:
                    with bz2.open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            # Show compression ratio
            original_size = Path(input_file).stat().st_size
            compressed_size = Path(output_file).stat().st_size
            ratio = (1 - compressed_size/original_size) * 100
            
            return True, f"Compressed: {ratio:.1f}% reduction"
        except Exception as e:
            return False, f"Compression failed: {str(e)}"
    
    def compress_folder(self, folder_path, output_file=None, method='zip'):
        """Compress an entire folder"""
        folder = Path(folder_path)
        if not folder.is_dir():
            return False, "Not a valid folder"
        
        if not output_file:
            if method == 'zip':
                output_file = str(folder) + '.zip'
            elif method == 'tar':
                output_file = str(folder) + '.tar'
            elif method == 'targz':
                output_file = str(folder) + '.tar.gz'
        
        try:
            if method == 'zip':
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file in folder.rglob('*'):
                        if file.is_file():
                            arcname = file.relative_to(folder.parent)
                            zf.write(file, arcname)
            
            elif method == 'tar':
                with tarfile.open(output_file, 'w') as tf:
                    tf.add(folder, arcname=folder.name)
            
            elif method == 'targz':
                with tarfile.open(output_file, 'w:gz') as tf:
                    tf.add(folder, arcname=folder.name)
            
            return True, f"Folder compressed to: {output_file}"
        except Exception as e:
            return False, f"Compression failed: {str(e)}"
    
    def decompress_file(self, input_file, output_dir=None):
        """Decompress various archive formats"""
        if not output_dir:
            output_dir = str(Path(input_file).parent / Path(input_file).stem)
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            ext = Path(input_file).suffix.lower()
            
            if ext == '.zip':
                with zipfile.ZipFile(input_file, 'r') as zf:
                    zf.extractall(output_dir)
            
            elif ext in ['.tar', '.gz', '.bz2']:
                if input_file.endswith('.tar.gz') or input_file.endswith('.tgz'):
                    with tarfile.open(input_file, 'r:gz') as tf:
                        tf.extractall(output_dir)
                elif input_file.endswith('.tar.bz2'):
                    with tarfile.open(input_file, 'r:bz2') as tf:
                        tf.extractall(output_dir)
                elif ext == '.tar':
                    with tarfile.open(input_file, 'r') as tf:
                        tf.extractall(output_dir)
                elif ext == '.gz':
                    import gzip
                    output_file = Path(output_dir) / Path(input_file).stem
                    with gzip.open(input_file, 'rb') as f_in:
                        with open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif ext == '.bz2':
                    import bz2
                    output_file = Path(output_dir) / Path(input_file).stem
                    with bz2.open(input_file, 'rb') as f_in:
                        with open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
            
            return True, f"Extracted to: {output_dir}"
        except Exception as e:
            return False, f"Decompression failed: {str(e)}"
    
    # ============= PDF OPERATIONS =============
    
    def merge_pdfs(self, pdf_files, output_file):
        """Merge multiple PDF files"""
        if not PDF_AVAILABLE:
            return False, "PyPDF2 not installed"
        
        try:
            merger = PyPDF2.PdfMerger()
            for pdf in pdf_files:
                merger.append(pdf)
            merger.write(output_file)
            merger.close()
            return True, f"Merged {len(pdf_files)} PDFs into: {output_file}"
        except Exception as e:
            return False, f"Merge failed: {str(e)}"
    
    def split_pdf(self, input_file, output_dir=None, pages=None):
        """Split PDF into separate pages"""
        if not PDF_AVAILABLE:
            return False, "PyPDF2 not installed"
        
        if not output_dir:
            output_dir = str(Path(input_file).parent / f"{Path(input_file).stem}_split")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            with open(input_file, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pages:
                    # Split specific pages
                    for i in pages:
                        pdf_writer = PyPDF2.PdfWriter()
                        pdf_writer.add_page(pdf_reader.pages[i-1])
                        output_file = Path(output_dir) / f"page_{i}.pdf"
                        with open(output_file, 'wb') as out:
                            pdf_writer.write(out)
                else:
                    # Split all pages
                    for i, page in enumerate(pdf_reader.pages):
                        pdf_writer = PyPDF2.PdfWriter()
                        pdf_writer.add_page(page)
                        output_file = Path(output_dir) / f"page_{i+1}.pdf"
                        with open(output_file, 'wb') as out:
                            pdf_writer.write(out)
            
            return True, f"Split PDF into: {output_dir}"
        except Exception as e:
            return False, f"Split failed: {str(e)}"
    
    # ============= BATCH PROCESSING =============
    
    def batch_convert(self, input_folder, target_format, output_folder=None):
        """Convert all files in a folder to target format"""
        if not output_folder:
            output_folder = str(Path(input_folder) / f"converted_to_{target_format}")
        
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        results = []
        for file in Path(input_folder).iterdir():
            if file.is_file():
                ext = file.suffix.lower()
                output_file = Path(output_folder) / f"{file.stem}.{target_format}"
                
                # Determine conversion type
                if target_format == 'pdf':
                    if ext in ['.txt', '.md']:
                        success, msg = self.convert_text_to_pdf(file, output_file)
                    elif ext in ['.jpg', '.jpeg', '.png']:
                        success, msg = self.convert_image_to_pdf(file, output_file)
                    else:
                        success, msg = False, f"Unsupported conversion: {ext} to pdf"
                elif target_format == 'csv' and ext == '.xlsx':
                    success, msg = self.convert_excel_to_csv(file, output_file)
                elif target_format == 'xlsx' and ext == '.csv':
                    success, msg = self.convert_csv_to_excel(file, output_file)
                else:
                    success, msg = False, f"Unsupported conversion"
                
                results.append({
                    'file': str(file),
                    'success': success,
                    'message': msg
                })
        
        return results
    
    # ============= FILE CLEANUP & ORGANIZATION =============
    
    def organize_by_type(self, folder_path):
        """Organize files into folders by type"""
        folder = Path(folder_path)
        if not folder.is_dir():
            return False, "Not a valid folder"
        
        organized = 0
        for file in folder.iterdir():
            if file.is_file():
                ext = file.suffix.lower()
                # Determine category
                category = 'other'
                for cat, extensions in self.supported_formats.items():
                    if ext in extensions:
                        category = cat
                        break
                
                # Create category folder and move file
                cat_folder = folder / category
                cat_folder.mkdir(exist_ok=True)
                
                # Handle duplicates
                dest = cat_folder / file.name
                if dest.exists():
                    stem = dest.stem
                    dest = cat_folder / f"{stem}_duplicate{ext}"
                
                shutil.move(str(file), str(dest))
                organized += 1
        
        return True, f"Organized {organized} files into categories"
    
    def remove_duplicates(self, folder_path):
        """Find and remove duplicate files"""
        folder = Path(folder_path)
        if not folder.is_dir():
            return False, "Not a valid folder"
        
        hashes = {}
        duplicates = []
        
        for file in folder.rglob('*'):
            if file.is_file():
                file_hash = self._calculate_md5(file)
                if file_hash in hashes:
                    duplicates.append((str(file), hashes[file_hash]))
                else:
                    hashes[file_hash] = str(file)
        
        # Remove duplicates (keep first occurrence)
        removed = 0
        for dup, original in duplicates:
            print(f"Duplicate: {dup}")
            print(f"Original: {original}")
            response = input("Delete duplicate? (y/n): ").lower()
            if response == 'y':
                os.remove(dup)
                removed += 1
        
        return True, f"Removed {removed} duplicate files"


class DocumentConverterCLI:
    """Command-line interface for DocumentConverter"""
    
    def __init__(self):
        self.converter = DocumentConverter()
        self.parser = self._create_parser()
    
    def _create_parser(self):
        parser = argparse.ArgumentParser(
            description='Document Conversion and Compression Toolkit',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s info document.pdf
  %(prog)s convert document.docx --to pdf
  %(prog)s compress file.txt --method zip
  %(prog)s decompress archive.zip
  %(prog)s merge file1.pdf file2.pdf -o merged.pdf
  %(prog)s split document.pdf
  %(prog)s batch /path/to/folder --to pdf
  %(prog)s organize /path/to/folder
  %(prog)s clean /path/to/folder --find-duplicates
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Info command
        info_parser = subparsers.add_parser('info', help='Get file information')
        info_parser.add_argument('file', help='File to analyze')
        
        # Convert command
        convert_parser = subparsers.add_parser('convert', help='Convert file format')
        convert_parser.add_argument('file', help='Input file')
        convert_parser.add_argument('--to', '-t', required=True, 
                                   choices=['pdf', 'csv', 'xlsx', 'txt'],
                                   help='Target format')
        convert_parser.add_argument('--output', '-o', help='Output file path')
        
        # Compress command
        compress_parser = subparsers.add_parser('compress', help='Compress file/folder')
        compress_parser.add_argument('path', help='File or folder to compress')
        compress_parser.add_argument('--method', '-m', default='zip',
                                    choices=['zip', 'tar', 'gz', 'bz2', 'targz'],
                                    help='Compression method')
        compress_parser.add_argument('--output', '-o', help='Output file path')
        
        # Decompress command
        decompress_parser = subparsers.add_parser('decompress', help='Decompress archive')
        decompress_parser.add_argument('file', help='Archive to decompress')
        decompress_parser.add_argument('--output', '-o', help='Output directory')
        
        # PDF commands
        pdf_parser = subparsers.add_parser('pdf', help='PDF operations')
        pdf_subparsers = pdf_parser.add_subparsers(dest='pdf_command')
        
        # Merge PDFs
        merge_parser = pdf_subparsers.add_parser('merge', help='Merge PDFs')
        merge_parser.add_argument('files', nargs='+', help='PDF files to merge')
        merge_parser.add_argument('--output', '-o', required=True, help='Output file')
        
        # Split PDF
        split_parser = pdf_subparsers.add_parser('split', help='Split PDF')
        split_parser.add_argument('file', help='PDF to split')
        split_parser.add_argument('--pages', '-p', nargs='+', type=int,
                                 help='Page numbers to extract')
        split_parser.add_argument('--output', '-o', help='Output directory')
        
        # Batch convert
        batch_parser = subparsers.add_parser('batch', help='Batch convert files')
        batch_parser.add_argument('folder', help='Folder to process')
        batch_parser.add_argument('--to', required=True, help='Target format')
        batch_parser.add_argument('--output', '-o', help='Output folder')
        
        # Organize
        organize_parser = subparsers.add_parser('organize', help='Organize files by type')
        organize_parser.add_argument('folder', help='Folder to organize')
        
        # Clean
        clean_parser = subparsers.add_parser('clean', help='Clean up files')
        clean_parser.add_argument('folder', help='Folder to clean')
        clean_parser.add_argument('--find-duplicates', action='store_true',
                                 help='Find and remove duplicate files')
        
        return parser
    
    def run(self, args=None):
        """Run the CLI"""
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return
        
        # Execute command
        if parsed_args.command == 'info':
            info = self.converter.get_file_info(parsed_args.file)
            if info:
                print("\n📄 File Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print(f"File not found: {parsed_args.file}")
        
        elif parsed_args.command == 'convert':
            if parsed_args.to == 'pdf':
                ext = Path(parsed_args.file).suffix.lower()
                if ext in ['.txt', '.md']:
                    success, msg = self.converter.convert_text_to_pdf(
                        parsed_args.file, parsed_args.output)
                elif ext in ['.jpg', '.jpeg', '.png']:
                    success, msg = self.converter.convert_image_to_pdf(
                        parsed_args.file, parsed_args.output)
                elif ext == '.docx':
                    success, msg = self.converter.convert_docx_to_pdf(
                        parsed_args.file, parsed_args.output)
                else:
                    success, msg = False, f"Unsupported conversion to PDF from {ext}"
            
            elif parsed_args.to == 'csv':
                ext = Path(parsed_args.file).suffix.lower()
                if ext == '.xlsx':
                    success, msg = self.converter.convert_excel_to_csv(
                        parsed_args.file, parsed_args.output)
                elif ext == '.json':
                    success, msg = self.converter.convert_json_to_csv(
                        parsed_args.file, parsed_args.output)
                else:
                    success, msg = False, f"Unsupported conversion to CSV from {ext}"
            
            elif parsed_args.to == 'xlsx':
                ext = Path(parsed_args.file).suffix.lower()
                if ext == '.csv':
                    success, msg = self.converter.convert_csv_to_excel(
                        parsed_args.file, parsed_args.output)
                else:
                    success, msg = False, f"Unsupported conversion to Excel from {ext}"
            
            print("✅" if success else "❌", msg)
        
        elif parsed_args.command == 'compress':
            path = Path(parsed_args.path)
            if path.is_dir():
                success, msg = self.converter.compress_folder(
                    parsed_args.path, parsed_args.output, parsed_args.method)
            else:
                success, msg = self.converter.compress_file(
                    parsed_args.path, parsed_args.output, parsed_args.method)
            print("✅" if success else "❌", msg)
        
        elif parsed_args.command == 'decompress':
            success, msg = self.converter.decompress_file(
                parsed_args.file, parsed_args.output)
            print("✅" if success else "❌", msg)
        
        elif parsed_args.command == 'pdf':
            if parsed_args.pdf_command == 'merge':
                success, msg = self.converter.merge_pdfs(
                    parsed_args.files, parsed_args.output)
                print("✅" if success else "❌", msg)
            
            elif parsed_args.pdf_command == 'split':
                success, msg = self.converter.split_pdf(
                    parsed_args.file, parsed_args.output, parsed_args.pages)
                print("✅" if success else "❌", msg)
        
        elif parsed_args.command == 'batch':
            results = self.converter.batch_convert(
                parsed_args.folder, parsed_args.to, parsed_args.output)
            
            print(f"\nBatch conversion results:")
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            
            if failed > 0:
                print("\nFailed conversions:")
                for r in results:
                    if not r['success']:
                        print(f"  {r['file']}: {r['message']}")
        
        elif parsed_args.command == 'organize':
            success, msg = self.converter.organize_by_type(parsed_args.folder)
            print("✅" if success else "❌", msg)
        
        elif parsed_args.command == 'clean':
            if parsed_args.find_duplicates:
                success, msg = self.converter.remove_duplicates(parsed_args.folder)
                print("✅" if success else "❌", msg)


def main():
    """Main entry point"""
    cli = DocumentConverterCLI()
    cli.run()


if __name__ == "__main__":
    main()