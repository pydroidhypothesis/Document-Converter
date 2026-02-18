"""ZIP archive compressor/decompressor."""

from pathlib import Path
from typing import Dict, Any, Union
import zipfile


class ZipCompressor:
    """Utility for ZIP compression and extraction."""

    def compress(self, input_path: Union[str, Path], output_file: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_path)
        if not source.exists():
            return {"success": False, "message": f"Input not found: {source}"}

        output_path = Path(output_file) if output_file else source.with_suffix(".zip")
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                if source.is_dir():
                    root = source.parent
                    for item in source.rglob("*"):
                        if item.is_file():
                            archive.write(item, arcname=str(item.relative_to(root)))
                else:
                    archive.write(source, arcname=source.name)

            return {
                "success": True,
                "input_file": str(source),
                "output_file": str(output_path),
                "message": "ZIP archive created successfully"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"ZIP compression failed: {exc}", "error": str(exc)}

    def decompress(self, input_file: Union[str, Path], output_dir: Union[str, Path, None] = None) -> Dict[str, Any]:
        source = Path(input_file)
        if not source.exists():
            return {"success": False, "message": f"Archive not found: {source}"}

        extract_dir = Path(output_dir) if output_dir else source.with_suffix("")
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(source, "r") as archive:
                archive.extractall(extract_dir)

            return {
                "success": True,
                "input_file": str(source),
                "output_dir": str(extract_dir),
                "message": "ZIP archive extracted successfully"
            }
        except Exception as exc:
            return {"success": False, "input_file": str(source), "message": f"ZIP extraction failed: {exc}", "error": str(exc)}
