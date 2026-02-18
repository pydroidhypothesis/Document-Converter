"""Image format converters"""
from typing import Dict, List, Any, Union, Optional
from pathlib import Path
import shutil

from ..core.base_converter import BaseConverter
from ..core.exceptions import *

try:
    from PIL import Image
    from PIL import ImageOps
    from PIL import ImageFilter
    from PIL import ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

try:
    import pyheif
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False


class ImageConverter(BaseConverter):
    """Converter for image formats"""
    
    def _get_supported_formats(self) -> Dict[str, List[str]]:
        return {
            'input': [
                '.jpg', '.jpeg', '.jpe', '.jfif', '.png', '.gif', '.bmp',
                '.tiff', '.tif', '.webp', '.ico', '.icns', '.psd', '.eps',
                '.raw', '.cr2', '.nef', '.arw', '.dng', '.heic', '.heif',
                '.avif', '.jp2', '.j2k', '.pcx', '.tga', '.xbm', '.xpm',
                '.svg', '.svgz'
            ],
            'output': [
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
                '.ico', '.pdf', '.eps', '.svg'
            ]
        }
    
    def convert(self, input_file: Union[str, Path], output_format: str, **kwargs) -> Dict[str, Any]:
        """Main conversion method"""
        if not PIL_AVAILABLE:
            raise DependencyMissingError("Pillow not installed")
        
        input_path = Path(input_file)
        self.validate_input(input_path)
        
        output_format = output_format.lower()
        if not output_format.startswith('.'):
            output_format = f'.{output_format}'
        
        output_file = kwargs.get('output_file', 
                                 input_path.parent / f"{input_path.stem}{output_format}")
        
        try:
            # Handle special formats
            if input_path.suffix.lower() in ['.heic', '.heif']:
                if not HEIF_AVAILABLE:
                    raise DependencyMissingError("pyheif not installed")
                image = self._read_heif(input_path)
            else:
                image = Image.open(input_path)
            
            # Apply preprocessing if specified
            if kwargs.get('resize'):
                width = kwargs['resize'].get('width')
                height = kwargs['resize'].get('height')
                if width and height:
                    image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            if kwargs.get('crop'):
                left = kwargs['crop'].get('left', 0)
                top = kwargs['crop'].get('top', 0)
                right = kwargs['crop'].get('right', image.width)
                bottom = kwargs['crop'].get('bottom', image.height)
                image = image.crop((left, top, right, bottom))
            
            if kwargs.get('rotate'):
                image = image.rotate(kwargs['rotate'], expand=True)
            
            if kwargs.get('flip'):
                if kwargs['flip'] == 'horizontal':
                    image = ImageOps.mirror(image)
                elif kwargs['flip'] == 'vertical':
                    image = ImageOps.flip(image)
            
            if kwargs.get('grayscale'):
                image = ImageOps.grayscale(image)
            
            if kwargs.get('quality'):
                quality = kwargs['quality']
            else:
                quality = 95
            
            # Convert to RGB if necessary for JPEG
            if output_format in ['.jpg', '.jpeg'] and image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Save with appropriate parameters
            save_kwargs = {}
            if output_format in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_format == '.png':
                save_kwargs['optimize'] = True
                if kwargs.get('compress_level'):
                    save_kwargs['compress_level'] = kwargs['compress_level']
            elif output_format == '.webp':
                save_kwargs['quality'] = quality
                if kwargs.get('method'):
                    save_kwargs['method'] = kwargs['method']
            
            image.save(output_file, **save_kwargs)
            
            result = {
                'success': True,
                'input_file': str(input_path),
                'output_file': str(output_file),
                'format_from': input_path.suffix.lower(),
                'format_to': output_format,
                'original_size': input_path.stat().st_size,
                'new_size': output_file.stat().st_size,
                'dimensions': f"{image.width}x{image.height}",
                'message': f"Converted image to {output_format}"
            }
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'input_file': str(input_path),
                'error': str(e),
                'message': f"Image conversion failed: {str(e)}"
            }
    
    def _read_heif(self, file_path: Path):
        """Read HEIF/HEIC image"""
        import pyheif
        heif_file = pyheif.read(str(file_path))
        return Image.frombytes(
            heif_file.mode, 
            heif_file.size, 
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )
    
    def convert_multiple(self, input_files: List[Union[str, Path]], output_format: str, 
                        output_dir: Optional[Union[str, Path]] = None, **kwargs) -> List[Dict[str, Any]]:
        """Convert multiple images"""
        results = []
        output_path = Path(output_dir) if output_dir else Path.cwd()
        output_path.mkdir(parents=True, exist_ok=True)
        
        for input_file in input_files:
            input_path = Path(input_file)
            output_file = output_path / f"{input_path.stem}{output_format}"
            result = self.convert(input_path, output_format, output_file=output_file, **kwargs)
            results.append(result)
        
        return results
    
    def create_pdf(self, input_files: List[Union[str, Path]], output_file: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """Create PDF from multiple images"""
        if not PIL_AVAILABLE:
            raise DependencyMissingError("Pillow not installed")
        
        output_path = Path(output_file)
        images = []
        
        try:
            for input_file in input_files:
                img = Image.open(input_file)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                images.append(img)
            
            if images:
                images[0].save(
                    output_path, 
                    'PDF', 
                    save_all=True, 
                    append_images=images[1:],
                    quality=kwargs.get('quality', 95)
                )
            
            result = {
                'success': True,
                'input_files': [str(f) for f in input_files],
                'output_file': str(output_path),
                'num_pages': len(images),
                'message': f"Created PDF with {len(images)} pages"
            }
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'input_files': [str(f) for f in input_files],
                'error': str(e),
                'message': f"PDF creation failed: {str(e)}"
            }
    
    def apply_filter(self, input_file: Union[str, Path], filter_name: str, 
                    output_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Apply filter to image"""
        if not PIL_AVAILABLE:
            raise DependencyMissingError("Pillow not installed")
        
        input_path = Path(input_file)
        if not output_file:
            output_file = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"
        
        filters = {
            'blur': ImageFilter.BLUR,
            'contour': ImageFilter.CONTOUR,
            'detail': ImageFilter.DETAIL,
            'edge_enhance': ImageFilter.EDGE_ENHANCE,
            'emboss': ImageFilter.EMBOSS,
            'find_edges': ImageFilter.FIND_EDGES,
            'sharpen': ImageFilter.SHARPEN,
            'smooth': ImageFilter.SMOOTH
        }
        
        try:
            image = Image.open(input_path)
            if filter_name in filters:
                image = image.filter(filters[filter_name])
            elif filter_name == 'grayscale':
                image = ImageOps.grayscale(image)
            elif filter_name == 'invert':
                if image.mode == 'RGBA':
                    r, g, b, a = image.split()
                    rgb_image = Image.merge('RGB', (r, g, b))
                    inverted_rgb = ImageOps.invert(rgb_image)
                    r2, g2, b2 = inverted_rgb.split()
                    image = Image.merge('RGBA', (r2, g2, b2, a))
                else:
                    image = ImageOps.invert(image)
            else:
                return {
                    'success': False,
                    'input_file': str(input_path),
                    'error': f"Unknown filter: {filter_name}",
                    'message': f"Filter '{filter_name}' not found"
                }
            
            image.save(output_file)
            
            return {
                'success': True,
                'input_file': str(input_path),
                'output_file': str(output_file),
                'filter': filter_name,
                'message': f"Applied {filter_name} filter"
            }
            
        except Exception as e:
            return {
                'success': False,
                'input_file': str(input_path),
                'error': str(e),
                'message': f"Filter application failed: {str(e)}"
            }