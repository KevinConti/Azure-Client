"""
File processing service for handling various file operations.
"""
import os
import re
from typing import Optional, Callable
from datetime import datetime

from models.transcript import Transcript


class FileService:
    """Service for handling file operations and format conversions."""
    
    def __init__(self):
        # Callbacks
        self._on_file_processed: Optional[Callable[[str, Transcript], None]] = None
        self._on_file_exported: Optional[Callable[[str], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
    
    def set_callbacks(self,
                     on_file_processed: Optional[Callable[[str, Transcript], None]] = None,
                     on_file_exported: Optional[Callable[[str], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None):
        """Set callback functions for file operations."""
        self._on_file_processed = on_file_processed
        self._on_file_exported = on_file_exported
        self._on_error = on_error
    
    def parse_vtt_file(self, file_path: str) -> Optional[Transcript]:
        """Parse a VTT file and return a Transcript object."""
        try:
            if not self.validate_file_exists(file_path):
                if self._on_error:
                    self._on_error(f"VTT file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            transcript = Transcript.from_vtt_content(content, source_file=file_path)
            
            if not transcript.validate():
                if self._on_error:
                    self._on_error("Invalid VTT file format or empty content")
                return None
            
            if self._on_file_processed:
                self._on_file_processed(file_path, transcript)
            
            return transcript
            
        except UnicodeDecodeError:
            if self._on_error:
                self._on_error("VTT file encoding error. Please ensure the file is UTF-8 encoded.")
            return None
        except Exception as e:
            if self._on_error:
                self._on_error(f"Error parsing VTT file: {str(e)}")
            return None
    
    def export_transcript(self, transcript: Transcript, output_path: str, format_type: str = "txt") -> bool:
        """Export transcript to various formats."""
        try:
            if format_type.lower() == "txt":
                return self._export_as_text(transcript, output_path)
            elif format_type.lower() == "vtt":
                return self._export_as_vtt(transcript, output_path)
            elif format_type.lower() == "srt":
                return self._export_as_srt(transcript, output_path)
            else:
                if self._on_error:
                    self._on_error(f"Unsupported export format: {format_type}")
                return False
                
        except Exception as e:
            if self._on_error:
                self._on_error(f"Export failed: {str(e)}")
            return False
    
    def _export_as_text(self, transcript: Transcript, output_path: str) -> bool:
        """Export transcript as plain text."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcript.to_plain_text())
            
            if self._on_file_exported:
                self._on_file_exported(output_path)
            
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to export as text: {str(e)}")
            return False
    
    def _export_as_vtt(self, transcript: Transcript, output_path: str) -> bool:
        """Export transcript as VTT format."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for i, segment in enumerate(transcript.segments, 1):
                    f.write(f"{i}\n")
                    
                    if segment.start_time is not None and segment.end_time is not None:
                        start_time = self._format_timestamp(segment.start_time)
                        end_time = self._format_timestamp(segment.end_time)
                        f.write(f"{start_time} --> {end_time}\n")
                    else:
                        f.write("00:00:00.000 --> 00:00:10.000\n")
                    
                    f.write(f"{segment.text}\n\n")
            
            if self._on_file_exported:
                self._on_file_exported(output_path)
            
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to export as VTT: {str(e)}")
            return False
    
    def _export_as_srt(self, transcript: Transcript, output_path: str) -> bool:
        """Export transcript as SRT format."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(transcript.segments, 1):
                    f.write(f"{i}\n")
                    
                    if segment.start_time is not None and segment.end_time is not None:
                        start_time = self._format_timestamp_srt(segment.start_time)
                        end_time = self._format_timestamp_srt(segment.end_time)
                        f.write(f"{start_time} --> {end_time}\n")
                    else:
                        f.write("00:00:00,000 --> 00:00:10,000\n")
                    
                    f.write(f"{segment.text}\n\n")
            
            if self._on_file_exported:
                self._on_file_exported(output_path)
            
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to export as SRT: {str(e)}")
            return False
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for VTT format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def _format_timestamp_srt(self, seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        milliseconds = int((secs % 1) * 1000)
        secs = int(secs)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def validate_file_exists(self, file_path: str) -> bool:
        """Validate that a file exists."""
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    def validate_vtt_file(self, file_path: str) -> tuple[bool, str]:
        """Validate a VTT file format and content."""
        if not self.validate_file_exists(file_path):
            return False, "File does not exist"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for WEBVTT header
            if not content.strip().startswith('WEBVTT'):
                return False, "Invalid VTT file: missing WEBVTT header"
            
            # Check if there's any transcript content
            lines = content.split('\n')
            has_content = False
            
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.startswith('WEBVTT') and 
                    not re.match(r'^\d+$', line) and 
                    not re.match(r'^[\d:.,\s-]+-->', line)):
                    has_content = True
                    break
            
            if not has_content:
                return False, "VTT file contains no transcript text"
            
            return True, "VTT file is valid"
            
        except UnicodeDecodeError:
            return False, "File encoding error. Please ensure the file is UTF-8 encoded."
        except Exception as e:
            return False, f"Error validating VTT file: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get information about a file."""
        try:
            if not self.validate_file_exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': os.path.splitext(file_path)[1].lower()
            }
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Error getting file info: {str(e)}")
            return None
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup copy of a file."""
        try:
            if not self.validate_file_exists(file_path):
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(file_path)
            backup_path = f"{base_name}_backup_{timestamp}{ext}"
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to create backup: {str(e)}")
            return None
    
    def cleanup_temp_files(self, file_paths: list[str]) -> int:
        """Clean up temporary files."""
        cleaned_count = 0
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_count += 1
            except Exception as e:
                if self._on_error:
                    self._on_error(f"Failed to clean up {file_path}: {str(e)}")
        
        return cleaned_count
    
    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported file formats for import and export."""
        return {
            'import': ['vtt'],
            'export': ['txt', 'vtt', 'srt'],
            'audio': ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm', 'flac']
        }
