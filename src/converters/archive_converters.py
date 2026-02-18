"""Archive converter for zip/tar/gz/bz2/xz/7z workflows."""

from pathlib import Path
import re
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Union

from ..core.base_converter import BaseConverter
from ..core.exceptions import UnsupportedFormatError
from ..compressors import (
    Bz2Compressor,
    GzCompressor,
    SevenZCompressor,
    TarCompressor,
    XzCompressor,
    ZipCompressor,
)


class ArchiveConverter(BaseConverter):
    """Convert to archive formats and convert archives between formats."""

    ARCHIVE_FORMATS = [
        ".tar.gz",
        ".tar.bz2",
        ".tar.xz",
        ".tgz",
        ".tbz2",
        ".txz",
        ".tar",
        ".zip",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
    ]

    def __init__(self, input_file: Union[str, Path] = None, output_dir: Union[str, Path] = None):
        super().__init__(input_file=input_file, output_dir=output_dir)
        self.zip = ZipCompressor()
        self.tar = TarCompressor()
        self.gz = GzCompressor()
        self.bz2 = Bz2Compressor()
        self.xz = XzCompressor()
        self.seven_z = SevenZCompressor()

    def _get_supported_formats(self) -> Dict[str, List[str]]:
        return {
            "input": self.ARCHIVE_FORMATS,
            "output": self.ARCHIVE_FORMATS,
        }

    def _normalize_output_format(self, output_format: str) -> str:
        fmt = output_format.strip().lower()
        if not fmt:
            raise UnsupportedFormatError("Missing output archive format")
        if not fmt.startswith("."):
            fmt = f".{fmt}"
        if fmt not in self.ARCHIVE_FORMATS:
            raise UnsupportedFormatError(f"Unsupported archive output format: {fmt}")
        return fmt

    def _parse_output_chain(self, output_format: str) -> List[str]:
        raw = (output_format or "").strip().lower()
        if not raw:
            raise UnsupportedFormatError("Missing output archive format")

        parts = [part.strip() for part in re.split(r"\s*(?:->|=>|>|,|\|)\s*", raw) if part.strip()]
        if not parts:
            raise UnsupportedFormatError("Missing output archive format")

        return [self._normalize_output_format(part) for part in parts]

    def _detect_archive_format(self, path: Path) -> Union[str, None]:
        name = path.name.lower()
        for fmt in sorted(self.ARCHIVE_FORMATS, key=len, reverse=True):
            if name.endswith(fmt):
                return fmt
        return None

    def _base_stem(self, path: Path) -> str:
        fmt = self._detect_archive_format(path)
        if not fmt:
            return path.stem
        return path.name[: -len(fmt)] or path.stem

    def _compress_to_format(self, source_path: Path, target_format: str, output_file: Path) -> Dict[str, Any]:
        if target_format == ".zip":
            return self.zip.compress(source_path, output_file)
        if target_format in {".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"}:
            return self.tar.compress(source_path, output_file)
        if target_format == ".gz":
            if source_path.is_dir():
                return {"success": False, "message": "GZIP supports single files only. Use tar.gz for folders."}
            return self.gz.compress(source_path, output_file)
        if target_format == ".bz2":
            if source_path.is_dir():
                return {"success": False, "message": "BZip2 supports single files only. Use tar.bz2 for folders."}
            return self.bz2.compress(source_path, output_file)
        if target_format == ".xz":
            if source_path.is_dir():
                return {"success": False, "message": "XZ supports single files only. Use tar.xz for folders."}
            return self.xz.compress(source_path, output_file)
        if target_format == ".7z":
            return self.seven_z.compress(source_path, output_file)
        return {"success": False, "message": f"Unsupported target archive format: {target_format}"}

    def _extract_archive(self, archive_path: Path, output_dir: Path) -> Dict[str, Any]:
        source_format = self._detect_archive_format(archive_path)
        if not source_format:
            return {"success": False, "message": f"Input is not a recognized archive: {archive_path.name}"}

        output_dir.mkdir(parents=True, exist_ok=True)

        if source_format == ".zip":
            return self.zip.decompress(archive_path, output_dir)
        if source_format in {".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"}:
            return self.tar.decompress(archive_path, output_dir)
        if source_format == ".gz":
            out_file = output_dir / self._base_stem(archive_path)
            return self.gz.decompress(archive_path, out_file)
        if source_format == ".bz2":
            out_file = output_dir / self._base_stem(archive_path)
            return self.bz2.decompress(archive_path, out_file)
        if source_format == ".xz":
            out_file = output_dir / self._base_stem(archive_path)
            return self.xz.decompress(archive_path, out_file)
        if source_format == ".7z":
            return self.seven_z.decompress(archive_path, output_dir)

        return {"success": False, "message": f"Unsupported input archive format: {source_format}"}

    def _convert_single(self, input_path: Path, target_format: str, output_path: Path) -> Dict[str, Any]:
        source_format = self._detect_archive_format(input_path)
        if source_format:
            with TemporaryDirectory(prefix="archive_convert_") as temp_dir:
                extracted_dir = Path(temp_dir) / "extracted"
                extract_result = self._extract_archive(input_path, extracted_dir)
                if not extract_result.get("success"):
                    return {
                        "success": False,
                        "input_file": str(input_path),
                        "format_from": source_format,
                        "format_to": target_format,
                        "message": extract_result.get("message", "Archive extraction failed"),
                        "error": extract_result.get("error"),
                    }

                children = [item for item in extracted_dir.iterdir()]
                source_payload = children[0] if len(children) == 1 else extracted_dir
                compress_result = self._compress_to_format(source_payload, target_format, output_path)
        else:
            compress_result = self._compress_to_format(input_path, target_format, output_path)

        if not compress_result.get("success"):
            return {
                "success": False,
                "input_file": str(input_path),
                "format_from": source_format or input_path.suffix.lower() or "(folder)",
                "format_to": target_format,
                "message": compress_result.get("message", "Archive conversion failed"),
                "error": compress_result.get("error"),
            }

        return {
            "success": True,
            "input_file": str(input_path),
            "output_file": str(output_path),
            "format_from": source_format or input_path.suffix.lower() or "(folder)",
            "format_to": target_format,
        }

    def convert(self, input_file: Union[str, Path], output_format: str, **kwargs) -> Dict[str, Any]:
        """Convert archives between formats, or package file/folder into archive format.

        Supports multi-step targets, e.g.:
        - zip
        - tar.gz
        - zip->tar.xz
        - tar,zip,7z
        """
        input_path = Path(input_file)
        if not input_path.exists():
            return {"success": False, "message": f"Input not found: {input_path}", "input_file": str(input_path)}

        target_chain = self._parse_output_chain(output_format)
        output_file = kwargs.get("output_file")
        final_output_path = Path(output_file) if output_file else input_path.parent / f"{self._base_stem(input_path)}{target_chain[-1]}"
        final_output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            steps = []
            current_input = input_path
            with TemporaryDirectory(prefix="archive_chain_") as temp_dir:
                temp_root = Path(temp_dir)
                for index, target_format in enumerate(target_chain):
                    is_last = index == len(target_chain) - 1
                    step_output = final_output_path if is_last else temp_root / f"step_{index + 1}{target_format}"
                    step_output.parent.mkdir(parents=True, exist_ok=True)

                    step_result = self._convert_single(current_input, target_format, step_output)
                    if not step_result.get("success"):
                        return {
                            **step_result,
                            "chain": target_chain,
                            "failed_step": index + 1,
                        }

                    steps.append({
                        "step": index + 1,
                        "from": step_result["format_from"],
                        "to": step_result["format_to"],
                        "output_file": step_result["output_file"],
                    })
                    current_input = Path(step_result["output_file"])

            result = {
                "success": True,
                "input_file": str(input_path),
                "output_file": str(final_output_path),
                "format_from": self._detect_archive_format(input_path) or input_path.suffix.lower() or "(folder)",
                "format_to": target_chain[-1],
                "original_size": input_path.stat().st_size if input_path.is_file() else 0,
                "new_size": final_output_path.stat().st_size if final_output_path.exists() else 0,
                "chain": target_chain,
                "steps": steps,
                "message": f"Archive conversion completed: {input_path.name} -> {final_output_path.name} via {' -> '.join(target_chain)}",
            }
            self.add_to_history(result)
            return result
        except Exception as exc:
            return {
                "success": False,
                "input_file": str(input_path),
                "format_to": target_chain[-1] if target_chain else "",
                "message": f"Archive conversion failed: {exc}",
                "error": str(exc),
            }
