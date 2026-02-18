"""Audio format converters"""
from typing import Dict, List, Any, Union
from pathlib import Path
import subprocess
import os

from ..core.base_converter import BaseConverter
from ..core.exceptions import *

try:
    import pydub
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class AudioConverter(BaseConverter):
    """Converter for audio formats"""
    
    def _get_supported_formats(self) -> Dict[str, List[str]]:
        return {
            'input': [
                '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma',
                '.opus', '.webm', '.aiff', '.au', '.raw', '.caf', '.ape',
                '.wv', '.tta', '.dts', '.ac3', '.eac3', '.mlp', '.truehd'
            ],
            'output': [
                '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.opus',
                '.aiff', '.wma'
            ]
        }
    
    def convert(self, input_file: Union[str, Path], output_format: str, **kwargs) -> Dict[str, Any]:
        """Main conversion method"""
        if not PYDUB_AVAILABLE:
            raise DependencyMissingError("pydub not installed")
        
        input_path = Path(input_file)
        self.validate_input(input_path)
        
        output_format = output_format.lower()
        if not output_format.startswith('.'):
            output_format = f'.{output_format}'
        
        output_file = kwargs.get('output_file', 
                                 input_path.parent / f"{input_path.stem}{output_format}")
        
        try:
            # Load audio file
            audio = AudioSegment.from_file(str(input_path))
            
            # Apply effects if specified
            if kwargs.get('volume_change'):
                audio = audio + kwargs['volume_change']  # dB
            
            if kwargs.get('fade_in'):
                audio = audio.fade_in(kwargs['fade_in'] * 1000)  # ms
            
            if kwargs.get('fade_out'):
                audio = audio.fade_out(kwargs['fade_out'] * 1000)  # ms
            
            if kwargs.get('speed'):
                speed = kwargs['speed']
                audio = audio.speedup(playback_speed=speed)
            
            if kwargs.get('start_time') or kwargs.get('end_time'):
                start = kwargs.get('start_time', 0) * 1000  # ms
                end = kwargs.get('end_time', len(audio)/1000) * 1000  # ms
                audio = audio[start:end]
            
            # Set bitrate if specified
            bitrate = kwargs.get('bitrate', '192k')
            
            # Export to target format
            export_kwargs = {}
            if output_format == '.mp3':
                export_kwargs['bitrate'] = bitrate
            elif output_format == '.ogg':
                export_kwargs['codec'] = 'libvorbis'
            elif output_format == '.flac':
                export_kwargs['compression_level'] = kwargs.get('compression_level', 5)
            
            audio.export(str(output_file), format=output_format[1:], **export_kwargs)
            
            # Get metadata if available
            metadata = self._get_metadata(input_path) if MUTAGEN_AVAILABLE else {}
            
            result = {
                'success': True,
                'input_file': str(input_path),
                'output_file': str(output_file),
                'format_from': input_path.suffix.lower(),
                'format_to': output_format,
                'original_size': input_path.stat().st_size,
                'new_size': output_file.stat().st_size,
                'duration': len(audio) / 1000,  # seconds
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'metadata': metadata,
                'message': f"Converted audio to {output_format}"
            }
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'input_file': str(input_path),
                'error': str(e),
                'message': f"Audio conversion failed: {str(e)}"
            }
    
    def _get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get audio metadata"""
        ext = file_path.suffix.lower()
        metadata = {}
        
        try:
            if ext == '.mp3':
                audio = MP3(file_path)
                metadata['title'] = audio.get('TIT2', [''])[0]
                metadata['artist'] = audio.get('TPE1', [''])[0]
                metadata['album'] = audio.get('TALB', [''])[0]
                metadata['year'] = audio.get('TDRC', [''])[0]
                metadata['genre'] = audio.get('TCON', [''])[0]
                metadata['track'] = audio.get('TRCK', [''])[0]
                metadata['bitrate'] = audio.info.bitrate
                metadata['sample_rate'] = audio.info.sample_rate
                
            elif ext == '.flac':
                audio = FLAC(file_path)
                metadata['title'] = audio.get('title', [''])[0]
                metadata['artist'] = audio.get('artist', [''])[0]
                metadata['album'] = audio.get('album', [''])[0]
                metadata['date'] = audio.get('date', [''])[0]
                metadata['genre'] = audio.get('genre', [''])[0]
                metadata['tracknumber'] = audio.get('tracknumber', [''])[0]
                metadata['bits_per_sample'] = audio.info.bits_per_sample
                metadata['sample_rate'] = audio.info.sample_rate
                
            elif ext == '.ogg':
                audio = OggVorbis(file_path)
                metadata['title'] = audio.get('title', [''])[0]
                metadata['artist'] = audio.get('artist', [''])[0]
                metadata['album'] = audio.get('album', [''])[0]
                metadata['date'] = audio.get('date', [''])[0]
                metadata['genre'] = audio.get('genre', [''])[0]
                metadata['tracknumber'] = audio.get('tracknumber', [''])[0]
                metadata['bitrate'] = audio.info.bitrate
                metadata['sample_rate'] = audio.info.sample_rate
                
        except Exception:
            pass
        
        return metadata
    
    def merge_audio(self, input_files: List[Union[str, Path]], output_file: Union[str, Path]) -> Dict[str, Any]:
        """Merge multiple audio files"""
        if not PYDUB_AVAILABLE:
            raise DependencyMissingError("pydub not installed")
        
        try:
            combined = AudioSegment.empty()
            files_info = []
            
            for input_file in input_files:
                path = Path(input_file)
                audio = AudioSegment.from_file(str(path))
                combined += audio
                files_info.append(str(path))
            
            combined.export(str(output_file), format=Path(output_file).suffix[1:])
            
            return {
                'success': True,
                'input_files': files_info,
                'output_file': str(output_file),
                'total_duration': len(combined) / 1000,
                'message': f"Merged {len(input_files)} audio files"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Merge failed: {str(e)}"
            }
    
    def extract_metadata(self, input_file: Union[str, Path]) -> Dict[str, Any]:
        """Extract metadata from audio file"""
        if not MUTAGEN_AVAILABLE:
            raise DependencyMissingError("mutagen not installed")
        
        input_path = Path(input_file)
        self.validate_input(input_path)
        
        return self._get_metadata(input_path)