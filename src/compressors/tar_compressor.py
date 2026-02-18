"""TAR archive compressor/decompressor (tar, tar.gz, tar.bz2, tar.xz)."""

from pathlib import Path
from typing import Dict, Any, Union
import tarfile


class TarCompressor:
    """Utility for TAR-family archive compression and extraction."""

    _WRITE_MODES = {
        ".tar": "w",
        ".tar.gz": "w:gz",
        ".tgz": "w:gz",
        ".tar.bz2": "w:bz2",
        ".tbz2": "w:bz2",
        ".tar.xz": "w:xz",
        ".txz": "w:xz",
    }

    def _detect_tar_suffix(self, path: Path) -> str:
        name = path.name.lower()
        for suffix in sorted(self._WRITE_MODES.keys(), key=len, reverse=True):
            if name.endswith(suffix):
                return suffix
        return ".tar"

    def compress(self, input_path: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_path)
        if not source.exists():
            return {"success": False, "message": f"Input not found: {source}"}

        output_path = Path(output_file) if output_file else source.with_suffix(".tar")
        suffix = self._detect_tar_suffix(output_path)
        mode = self._WRITE_MODES[suffix]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(output_path, mode) as archive:
                archive.add(source, arcname=source.name)

            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": f"TAR archive ({suffix}) created successfully"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"TAR compression failed: {exc}", "error": str(exc)}

    def decompress(self, input_file: Union[str, Path], output_dir: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists():
            return {"success": False, "message": f"Archive not found: {source}"}

        extract_dir = Path(output_dir) if output_dir else source.parent / source.stem
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(source, "r:*") as archive:
                archive.extractall(extract_dir)

            return {
                "success": True,
                "input_file": str(source),
                "output_dir": str(extract_dir),
                "message": "TAR archive extracted successfully"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"TAR extraction failed: {exc}", "error": str(exc)}
