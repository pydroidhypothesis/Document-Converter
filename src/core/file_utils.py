"""File utility functions"""
import os
import shutil
from pathlib import Path
from typing import List, Union, Optional
import tempfile
import hashlib


class FileUtils:
    """Utility class for file operations"""
    
    @staticmethod
    def ensure_dir(directory: Union[str, Path]) -> Path:
        """Ensure directory exists, create if it doesn't"""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_unique_filename(file_path: Union[str, Path]) -> Path:
        """Get a unique filename by adding numbers if file exists"""
        path = Path(file_path)
        if not path.exists():
            return path
        
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    @staticmethod
    def safe_move(src: Union[str, Path], dst: Union[str, Path]) -> Path:
        """Safely move file with unique name if destination exists"""
        src_path = Path(src)
        dst_path = Path(dst)
        
        if dst_path.exists():
            dst_path = FileUtils.get_unique_filename(dst_path)
        
        shutil.move(str(src_path), str(dst_path))
        return dst_path
    
    @staticmethod
    def get_temp_file(suffix: str = None) -> Path:
        """Create a temporary file"""
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return Path(path)
    
    @staticmethod
    def clean_temp_files(pattern: str = None) -> int:
        """Clean temporary files"""
        temp_dir = Path(tempfile.gettempdir())
        count = 0
        for file in temp_dir.glob('tmp*' if not pattern else pattern):
            try:
                file.unlink()
                count += 1
            except (OSError, PermissionError):
                pass
        return count
    
    @staticmethod
    def split_file(file_path: Union[str, Path], chunk_size_mb: int = 10) -> List[Path]:
        """Split file into chunks"""
        path = Path(file_path)
        chunk_size = chunk_size_mb * 1024 * 1024
        chunks = []
        
        with open(path, 'rb') as f:
            chunk_num = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_path = path.parent / f"{path.stem}_part{chunk_num:03d}{path.suffix}"
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunks.append(chunk_path)
                chunk_num += 1
        
        return chunks
    
    @staticmethod
    def merge_files(file_parts: List[Union[str, Path]], output_file: Union[str, Path]) -> Path:
        """Merge file parts"""
        output_path = Path(output_file)
        
        with open(output_path, 'wb') as outfile:
            for part in sorted(file_parts):
                with open(part, 'rb') as infile:
                    outfile.write(infile.read())
        
        return output_path