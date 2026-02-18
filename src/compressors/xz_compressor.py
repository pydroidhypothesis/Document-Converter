"""XZ single-file compressor/decompressor."""

from pathlib import Path
from typing import Dict, Any, Union
import lzma
import shutil


class XzCompressor:
    """Utility for .xz compression and extraction."""

    def compress(self, input_file: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists() or not source.is_file():
            return {"success": False, "message": f"Input file not found: {source}"}

        output_path = Path(output_file) if output_file else source.with_suffix(source.suffix + ".xz")
        if output_path.suffix.lower() != ".xz":
            output_path = Path(f"{output_path}.xz")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with source.open("rb") as src, lzma.open(output_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": "XZ compression completed"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"XZ compression failed: {exc}", "error": str(exc)}

    def decompress(self, input_file: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists() or not source.is_file():
            return {"success": False, "message": f"Archive file not found: {source}"}

        default_output = source.with_suffix("") if source.suffix.lower() == ".xz" else source.parent / f"{source.name}.out"
        output_path = Path(output_file) if output_file else default_output
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with lzma.open(source, "rb") as src, output_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": "XZ extraction completed"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"XZ extraction failed: {exc}", "error": str(exc)}
