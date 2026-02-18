"""BZip2 single-file compressor/decompressor."""

from pathlib import Path
from typing import Dict, Any, Union
import bz2
import shutil


class Bz2Compressor:
    """Utility for .bz2 compression and extraction."""

    def compress(self, input_file: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists() or not source.is_file():
            return {"success": False, "message": f"Input file not found: {source}"}

        output_path = Path(output_file) if output_file else source.with_suffix(source.suffix + ".bz2")
        if output_path.suffix.lower() != ".bz2":
            output_path = Path(f"{output_path}.bz2")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with source.open("rb") as src, bz2.open(output_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": "BZip2 compression completed"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"BZip2 compression failed: {exc}", "error": str(exc)}

    def decompress(self, input_file: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists() or not source.is_file():
            return {"success": False, "message": f"Archive file not found: {source}"}

        default_output = source.with_suffix("") if source.suffix.lower() == ".bz2" else source.parent / f"{source.name}.out"
        output_path = Path(output_file) if output_file else default_output
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with bz2.open(source, "rb") as src, output_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": "BZip2 extraction completed"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"BZip2 extraction failed: {exc}", "error": str(exc)}
