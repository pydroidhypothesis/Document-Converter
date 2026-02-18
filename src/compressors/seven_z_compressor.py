"""7z archive compressor/decompressor via external 7z binary."""

from pathlib import Path
from typing import Dict, Any, Union
import shutil
import subprocess

from ..core.exceptions import DependencyMissingError


class SevenZCompressor:
    """Utility for .7z compression and extraction."""

    def _binary(self) -> str:
        seven_z = shutil.which("7z") or shutil.which("7za")
        if not seven_z:
            raise DependencyMissingError("7z binary not found. Install p7zip/7zip.")
        return seven_z

    def compress(self, input_path: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_path)
        if not source.exists():
            return {"success": False, "message": f"Input not found: {source}"}

        output_path = Path(output_file) if output_file else source.with_suffix(".7z")
        if output_path.suffix.lower() != ".7z":
            output_path = output_path.with_suffix(".7z")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cmd = [self._binary(), "a", "-t7z", str(output_path), str(source)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                error_message = result.stderr.strip() or result.stdout.strip() or "unknown error"
                return {"success": False, "input_file": str(source), "message": f"7z compression failed: {error_message}", "error": error_message}

            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": "7z archive created successfully"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"7z compression failed: {exc}", "error": str(exc)}

    def decompress(self, input_file: Union[str, Path], output_dir: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists():
            return {"success": False, "message": f"Archive not found: {source}"}

        extract_dir = Path(output_dir) if output_dir else source.with_suffix("")
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            cmd = [self._binary(), "x", str(source), f"-o{extract_dir}", "-y"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                error_message = result.stderr.strip() or result.stdout.strip() or "unknown error"
                return {"success": False, "input_file": str(source), "message": f"7z extraction failed: {error_message}", "error": error_message}

            return {
                "success": True,
                "input_file": str(source),
                "output_dir": str(extract_dir),
                "message": "7z archive extracted successfully"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"7z extraction failed: {exc}", "error": str(exc)}
