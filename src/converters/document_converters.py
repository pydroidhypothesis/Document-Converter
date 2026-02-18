"""Document format converters powered by LibreOffice."""
from typing import Dict, List, Any, Union
from pathlib import Path
import shutil
import subprocess

from ..core.base_converter import BaseConverter
from ..core.exceptions import DependencyMissingError, UnsupportedFormatError


class DocumentConverter(BaseConverter):
    """Converter for document, spreadsheet, presentation and publisher formats."""

    def _get_supported_formats(self) -> Dict[str, List[str]]:
        return {
            'input': [
                '.txt', '.rtf', '.doc', '.docx', '.odt', '.ott', '.sxw',
                '.xls', '.xlsx', '.ods', '.ots', '.csv',
                '.ppt', '.pptx', '.odp', '.otp',
                '.pub', '.html', '.htm', '.xml', '.epub',
                '.fodt', '.fods', '.fodp'
            ],
            'output': [
                '.pdf', '.txt', '.rtf', '.doc', '.docx', '.odt', '.html', '.xml',
                '.xls', '.xlsx', '.ods', '.csv', '.ppt', '.pptx', '.odp', '.epub'
            ]
        }

    def _resolve_convert_target(self, output_format: str) -> str:
        """Map extension to LibreOffice convert target/filter."""
        target_map = {
            '.pdf': 'pdf',
            '.txt': 'txt:Text',
            '.rtf': 'rtf',
            '.doc': 'doc:MS Word 97',
            '.docx': 'docx:MS Word 2007 XML',
            '.odt': 'odt',
            '.html': 'html:XHTML Writer File',
            '.xml': 'xml',
            '.xls': 'xls:MS Excel 97',
            '.xlsx': 'xlsx:Calc MS Excel 2007 XML',
            '.ods': 'ods',
            '.csv': 'csv:Text - txt - csv (StarCalc)',
            '.ppt': 'ppt:MS PowerPoint 97',
            '.pptx': 'pptx:Impress MS PowerPoint 2007 XML',
            '.odp': 'odp',
            '.epub': 'epub'
        }
        return target_map.get(output_format, output_format[1:])

    def _find_generated_file(self, output_dir: Path, stem: str, output_format: str) -> Path:
        preferred_suffixes = [output_format]
        if output_format == '.html':
            preferred_suffixes.append('.htm')

        for suffix in preferred_suffixes:
            candidate = output_dir / f"{stem}{suffix}"
            if candidate.exists():
                return candidate

        matches = sorted(output_dir.glob(f"{stem}.*"))
        if not matches:
            raise FileNotFoundError("LibreOffice did not generate an output file")

        return matches[0]

    def convert(self, input_file: Union[str, Path], output_format: str, **kwargs) -> Dict[str, Any]:
        """Convert using LibreOffice CLI."""
        soffice_path = shutil.which('soffice')
        if not soffice_path:
            raise DependencyMissingError(
                "LibreOffice not found. Install LibreOffice and ensure 'soffice' is in PATH."
            )

        input_path = Path(input_file)
        self.validate_input(input_path)

        source_ext = input_path.suffix.lower()
        if source_ext not in self.supported_formats['input']:
            raise UnsupportedFormatError(f"Unsupported input format: {source_ext}")

        output_format = output_format.lower()
        if not output_format.startswith('.'):
            output_format = f'.{output_format}'

        if output_format not in self.supported_formats['output']:
            raise UnsupportedFormatError(f"Unsupported output format: {output_format}")

        output_file = kwargs.get('output_file')
        if output_file:
            output_file = Path(output_file)
            output_dir = output_file.parent
        else:
            output_dir = input_path.parent
            output_file = output_dir / f"{input_path.stem}{output_format}"

        output_dir.mkdir(parents=True, exist_ok=True)

        convert_target = self._resolve_convert_target(output_format)
        cmd = [
            soffice_path,
            '--headless',
            '--convert-to',
            convert_target,
            '--outdir',
            str(output_dir),
            str(input_path)
        ]

        try:
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if process.returncode != 0:
                error_message = process.stderr.strip() or process.stdout.strip() or 'unknown error'
                return {
                    'success': False,
                    'input_file': str(input_path),
                    'error': error_message,
                    'message': f"Document conversion failed: {error_message}"
                }

            generated = self._find_generated_file(output_dir, input_path.stem, output_format)
            if generated.resolve() != output_file.resolve():
                if output_file.exists():
                    output_file.unlink()
                generated.replace(output_file)

            result = {
                'success': True,
                'input_file': str(input_path),
                'output_file': str(output_file),
                'format_from': source_ext,
                'format_to': output_format,
                'original_size': input_path.stat().st_size,
                'new_size': output_file.stat().st_size,
                'message': f"Converted {source_ext} to {output_format} using LibreOffice"
            }

            self.add_to_history(result)
            return result

        except Exception as exc:
            return {
                'success': False,
                'input_file': str(input_path),
                'error': str(exc),
                'message': f"Document conversion failed: {exc}"
            }
