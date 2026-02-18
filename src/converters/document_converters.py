#!/usr/bin/env python3
"""
Document Conversion and Compression Toolkit
Main entry point for the modular conversion system
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.converters.document_converters import DocumentConverter
from src.converters.image_converters import ImageConverter
from src.converters.audio_converters import AudioConverter
from src.compressors.zip_compressor import ZipCompressor
from src.compressors.tar_compressor import TarCompressor
from src.processors.batch_processor import BatchProcessor
from src.core.file_utils import FileUtils
from src.core.exceptions import *


class ConversionToolkit:
    """Main toolkit class that orchestrates all converters"""
    
    def __init__(self):
        self.document_converter = DocumentConverter()
        self.image_converter = ImageConverter()
        self.audio_converter = AudioConverter()
        self.zip_compressor = ZipCompressor()
        self.tar_compressor = TarCompressor()
        self.batch_processor = BatchProcessor()
        self.file_utils = FileUtils()
    
    def convert(self, input_file, output_format, **kwargs):
        """Intelligently route conversion to appropriate converter"""
        ext = Path(input_file).suffix.lower()
        
        # Document formats
        if ext in ['.txt', '.md', '.html', '.docx', '.odt', '.pdf', '.xml', '.json', '.yaml']:
            return self.document_converter.convert(input_file, output_format, **kwargs)
        
        # Image formats
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic']:
            return self.image_converter.convert(input_file, output_format, **kwargs)
        
        # Audio formats
        elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']:
            return self.audio_converter.convert(input_file, output_format, **kwargs)
        
        else:
            raise UnsupportedFormatError(f"No converter available for {ext}")


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Document Conversion and Compression Toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get file information')
    info_parser.add_argument('file', help='File to analyze')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert file format')
    convert_parser.add_argument('file', help='Input file')
    convert_parser.add_argument('--to', '-t', required=True, help='Target format')
    convert_parser.add_argument('--output', '-o', help='Output file path')
    convert_parser.add_argument('--quality', '-q', type=int, default=95, help='Quality (1-100)')
    convert_parser.add_argument('--resize', help='Resize dimensions (WxH, e.g., 800x600)')
    convert_parser.add_argument('--bitrate', help='Audio bitrate (e.g., 192k)')
    
    # Batch convert
    batch_parser = subparsers.add_parser('batch', help='Batch convert files')
    batch_parser.add_argument('folder', help='Folder to process')
    batch_parser.add_argument('--to', required=True, help='Target format')
    batch_parser.add_argument('--output', '-o', help='Output folder')
    batch_parser.add_argument('--recursive', '-r', action='store_true', help='Process subfolders')
    
    # Image specific commands
    image_parser = subparsers.add_parser('image', help='Image operations')
    image_subparsers = image_parser.add_subparsers(dest='image_command')
    
    # Image filter
    filter_parser = image_subparsers.add_parser('filter', help='Apply filter to image')
    filter_parser.add_argument('file', help='Image file')
    filter_parser.add_argument('--filter', '-f', required=True, 
                              choices=['blur', 'sharpen', 'contour', 'emboss', 
                                      'edge_enhance', 'find_edges', 'smooth', 
                                      'grayscale', 'invert'],
                              help='Filter to apply')
    filter_parser.add_argument('--output', '-o', help='Output file')
    
    # Create PDF from images
    pdf_parser = image_subparsers.add_parser('pdf', help='Create PDF from images')
    pdf_parser.add_argument('files', nargs='+', help='Image files')
    pdf_parser.add_argument('--output', '-o', required=True, help='Output PDF file')
    
    # Audio specific commands
    audio_parser = subparsers.add_parser('audio', help='Audio operations')
    audio_subparsers = audio_parser.add_subparsers(dest='audio_command')
    
    # Merge audio
    merge_parser = audio_subparsers.add_parser('merge', help='Merge audio files')
    merge_parser.add_argument('files', nargs='+', help='Audio files')
    merge_parser.add_argument('--output', '-o', required=True, help='Output file')
    
    # Audio metadata
    metadata_parser = audio_subparsers.add_parser('metadata', help='Extract audio metadata')
    metadata_parser.add_argument('file', help='Audio file')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    toolkit = ConversionToolkit()
    
    try:
        if args.command == 'info':
            info = toolkit.file_utils.get_file_info(args.file)
            if info:
                print("\n📄 File Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print(f"File not found: {args.file}")
        
        elif args.command == 'convert':
            kwargs = {'output_file': args.output} if args.output else {}
            if args.quality:
                kwargs['quality'] = args.quality
            if args.resize:
                w, h = map(int, args.resize.split('x'))
                kwargs['resize'] = {'width': w, 'height': h}
            if args.bitrate:
                kwargs['bitrate'] = args.bitrate
            
            result = toolkit.convert(args.file, args.to, **kwargs)
            
            if result['success']:
                print(f"✅ {result['message']}")
                print(f"   Output: {result['output_file']}")
                if 'new_size' in result:
                    ratio = (1 - result['new_size']/result['original_size']) * 100
                    print(f"   Size reduction: {ratio:.1f}%")
            else:
                print(f"❌ {result['message']}")
        
        elif args.command == 'batch':
            print(f"Starting batch conversion...")
            # Implement batch processing
        
        elif args.command == 'image':
            if args.image_command == 'filter':
                result = toolkit.image_converter.apply_filter(
                    args.file, args.filter, args.output
                )
                print(f"✅ {result['message']}" if result['success'] else f"❌ {result['message']}")
            
            elif args.image_command == 'pdf':
                result = toolkit.image_converter.create_pdf(args.files, args.output)
                print(f"✅ {result['message']}" if result['success'] else f"❌ {result['message']}")
        
        elif args.command == 'audio':
            if args.audio_command == 'merge':
                result = toolkit.audio_converter.merge_audio(args.files, args.output)
                print(f"✅ {result['message']}" if result['success'] else f"❌ {result['message']}")
            
            elif args.audio_command == 'metadata':
                metadata = toolkit.audio_converter.extract_metadata(args.file)
                if metadata:
                    print("\n🎵 Audio Metadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                else:
                    print("No metadata found")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())