#!/usr/bin/env python3
"""Document Conversion and Compression Toolkit entry point."""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.converters.document_converters import DocumentConverter
from src.converters.image_converters import ImageConverter
from src.converters.audio_converters import AudioConverter
from src.converters.archive_converters import ArchiveConverter
from src.core.file_utils import FileUtils
from src.core.exceptions import UnsupportedFormatError


class ConversionToolkit:
    """Main toolkit class that routes conversion to specific modules."""

    def __init__(self):
        self.document_converter = DocumentConverter()
        self.image_converter = ImageConverter()
        self.audio_converter = AudioConverter()
        self.archive_converter = ArchiveConverter()
        self.file_utils = FileUtils()

    def convert(self, input_file, output_format, **kwargs):
        ext = Path(input_file).suffix.lower()
        normalized_output = output_format.lower()
        if not normalized_output.startswith('.'):
            normalized_output = f'.{normalized_output}'

        document_exts = {
            '.txt', '.md', '.html', '.htm', '.doc', '.docx', '.odt', '.ott', '.rtf', '.pdf', '.xml', '.json', '.yaml',
            '.xls', '.xlsx', '.ods', '.csv', '.ppt', '.pptx', '.odp', '.pub', '.epub', '.fodt', '.fods', '.fodp'
        }
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic'}
        audio_exts = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}
        archive_exts = {
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z',
            '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz'
        }

        input_name = str(input_file).lower()
        input_is_archive = any(input_name.endswith(ext_name) for ext_name in archive_exts)
        output_is_archive = normalized_output in archive_exts

        if input_is_archive or output_is_archive:
            return self.archive_converter.convert(input_file, normalized_output, **kwargs)

        if ext in document_exts:
            return self.document_converter.convert(input_file, normalized_output, **kwargs)
        if ext in image_exts:
            return self.image_converter.convert(input_file, normalized_output, **kwargs)
        if ext in audio_exts:
            return self.audio_converter.convert(input_file, normalized_output, **kwargs)

        raise UnsupportedFormatError(f"No converter available for {ext}")


def create_parser():
    parser = argparse.ArgumentParser(
        description='Document Conversion and Compression Toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    info_parser = subparsers.add_parser('info', help='Get file information')
    info_parser.add_argument('file', help='File to analyze')

    convert_parser = subparsers.add_parser('convert', help='Convert file format')
    convert_parser.add_argument('file', help='Input file')
    convert_parser.add_argument('--to', '-t', required=True, help='Target format')
    convert_parser.add_argument('--output', '-o', help='Output file path')
    convert_parser.add_argument('--quality', '-q', type=int, default=95, help='Quality (1-100)')
    convert_parser.add_argument('--resize', help='Resize dimensions (WxH, e.g., 800x600)')
    convert_parser.add_argument('--bitrate', help='Audio bitrate (e.g., 192k)')

    batch_parser = subparsers.add_parser('batch', help='Batch convert files')
    batch_parser.add_argument('folder', help='Folder to process')
    batch_parser.add_argument('--to', required=True, help='Target format')
    batch_parser.add_argument('--output', '-o', help='Output folder')
    batch_parser.add_argument('--recursive', '-r', action='store_true', help='Process subfolders')

    image_parser = subparsers.add_parser('image', help='Image operations')
    image_subparsers = image_parser.add_subparsers(dest='image_command')

    filter_parser = image_subparsers.add_parser('filter', help='Apply filter to image')
    filter_parser.add_argument('file', help='Image file')
    filter_parser.add_argument(
        '--filter',
        '-f',
        required=True,
        choices=['blur', 'sharpen', 'contour', 'emboss', 'edge_enhance', 'find_edges', 'smooth', 'grayscale', 'invert'],
        help='Filter to apply'
    )
    filter_parser.add_argument('--output', '-o', help='Output file')

    pdf_parser = image_subparsers.add_parser('pdf', help='Create PDF from images')
    pdf_parser.add_argument('files', nargs='+', help='Image files')
    pdf_parser.add_argument('--output', '-o', required=True, help='Output PDF file')

    audio_parser = subparsers.add_parser('audio', help='Audio operations')
    audio_subparsers = audio_parser.add_subparsers(dest='audio_command')

    merge_parser = audio_subparsers.add_parser('merge', help='Merge audio files')
    merge_parser.add_argument('files', nargs='+', help='Audio files')
    merge_parser.add_argument('--output', '-o', required=True, help='Output file')

    metadata_parser = audio_subparsers.add_parser('metadata', help='Extract audio metadata')
    metadata_parser.add_argument('file', help='Audio file')

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    toolkit = ConversionToolkit()

    try:
        if args.command == 'info':
            info = toolkit.file_utils.get_file_info(args.file)
            if info:
                print("\nFile Information:")
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
                print(result['message'])
                print(f"Output: {result['output_file']}")
            else:
                print(result['message'])

        elif args.command == 'batch':
            print('Batch command placeholder.')

        elif args.command == 'image':
            if args.image_command == 'filter':
                result = toolkit.image_converter.apply_filter(args.file, args.filter, args.output)
                print(result['message'])
            elif args.image_command == 'pdf':
                result = toolkit.image_converter.create_pdf(args.files, args.output)
                print(result['message'])

        elif args.command == 'audio':
            if args.audio_command == 'merge':
                result = toolkit.audio_converter.merge_audio(args.files, args.output)
                print(result['message'])
            elif args.audio_command == 'metadata':
                metadata = toolkit.audio_converter.extract_metadata(args.file)
                if metadata:
                    print("\nAudio Metadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                else:
                    print('No metadata found')

    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
