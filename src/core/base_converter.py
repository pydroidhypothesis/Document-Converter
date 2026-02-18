"""Base converter class that all converters inherit from"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
import hashlib
import mimetypes
from datetime import datetime


class BaseConverter(ABC):
    """Abstract base class for all converters"""
    
    def __init__(self, input_file: Union[str, Path] = None, output_dir: Union[str, Path] = None):
        self.input_file = Path(input_file) if input_file else None
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.supported_formats = self._get_supported_formats()
        self.conversion_history = []
        
    @abstractmethod
    def _get_supported_formats(self) -> Dict[str, List[str]]:
        """Return dictionary of supported input/output formats"""
        pass
    
    @abstractmethod
    def convert(self, input_file: Union[str, Path], output_format: str, **kwargs) -> Dict[str, Any]:
        """Main conversion method to be implemented by subclasses"""
        pass
    
    def validate_input(self, file_path: Union[str, Path]) -> bool:
        """Validate input file exists and is readable"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        return True
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get detailed file information"""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        stats = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            'name': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': stats.st_size,
            'size_readable': self._bytes_to_readable(stats.st_size),
            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stats.st_atime).isoformat(),
            'path': str(path.absolute()),
            'mime_type': mime_type or 'application/octet-stream',
            'md5_hash': self._calculate_md5(file_path),
            'is_binary': self._is_binary(file_path)
        }
    
    def _bytes_to_readable(self, bytes_size: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} EB"
    
    def _calculate_md5(self, file_path: Union[str, Path], chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of a file"""
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception:
            return "N/A"
    
    def _is_binary(self, file_path: Union[str, Path]) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, 'tr') as f:
                f.read(1024)
            return False
        except UnicodeDecodeError:
            return True
    
    def add_to_history(self, conversion_data: Dict[str, Any]) -> None:
        """Add conversion to history"""
        conversion_data['timestamp'] = datetime.now().isoformat()
        self.conversion_history.append(conversion_data)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversion history"""
        return self.conversion_history
    
    def clear_history(self) -> None:
        """Clear conversion history"""
        self.conversion_history = []