"""
Data models for transcript handling.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class TranscriptSegment:
    """Represents a single segment of a transcript with timing information."""
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class Transcript:
    """Represents a complete transcript with metadata."""
    segments: List[TranscriptSegment]
    full_text: str
    source_file: Optional[str] = None
    created_at: Optional[datetime] = None
    language: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @classmethod
    def from_text(cls, text: str, source_file: Optional[str] = None) -> 'Transcript':
        """Create a transcript from plain text."""
        segment = TranscriptSegment(text=text)
        return cls(
            segments=[segment],
            full_text=text,
            source_file=source_file
        )
    
    @classmethod
    def from_vtt_content(cls, vtt_content: str, source_file: Optional[str] = None) -> 'Transcript':
        """Create a transcript from VTT file content."""
        import re
        
        lines = vtt_content.split('\n')
        transcript_lines = []
        segments = []
        
        current_segment_text = ""
        current_start = None
        current_end = None
        
        for line in lines:
            line = line.strip()
            # Skip VTT header, empty lines, and cue numbers
            if (line and 
                not line.startswith('WEBVTT') and 
                not re.match(r'^\d+$', line)):
                
                # Check if it's a timestamp line
                timestamp_match = re.match(r'^([\d:.,]+)\s*-->\s*([\d:.,]+)', line)
                if timestamp_match:
                    # Save previous segment if exists
                    if current_segment_text.strip():
                        segments.append(TranscriptSegment(
                            text=current_segment_text.strip(),
                            start_time=current_start,
                            end_time=current_end
                        ))
                        transcript_lines.append(current_segment_text.strip())
                    
                    # Parse new timestamp
                    current_start = cls._parse_timestamp(timestamp_match.group(1))
                    current_end = cls._parse_timestamp(timestamp_match.group(2))
                    current_segment_text = ""
                else:
                    # It's transcript text
                    if current_segment_text:
                        current_segment_text += " " + line
                    else:
                        current_segment_text = line
        
        # Add the last segment
        if current_segment_text.strip():
            segments.append(TranscriptSegment(
                text=current_segment_text.strip(),
                start_time=current_start,
                end_time=current_end
            ))
            transcript_lines.append(current_segment_text.strip())
        
        full_text = ' '.join(transcript_lines)
        
        return cls(
            segments=segments,
            full_text=full_text,
            source_file=source_file
        )
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> float:
        """Parse VTT timestamp to seconds."""
        try:
            # Remove any extra whitespace and handle both comma and dot for milliseconds
            timestamp_str = timestamp_str.strip().replace(',', '.')
            
            # Split by colon to get time components
            parts = timestamp_str.split(':')
            
            if len(parts) == 3:  # HH:MM:SS.mmm
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:  # MM:SS.mmm
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            else:  # SS.mmm
                return float(parts[0])
        except (ValueError, IndexError):
            return 0.0
    
    def get_segment_at_time(self, timestamp: float) -> Optional[TranscriptSegment]:
        """Get the transcript segment at a specific timestamp."""
        for segment in self.segments:
            if (segment.start_time is not None and segment.end_time is not None and
                segment.start_time <= timestamp <= segment.end_time):
                return segment
        return None
    
    def to_plain_text(self) -> str:
        """Convert transcript to plain text."""
        return self.full_text
    
    def validate(self) -> bool:
        """Validate the transcript structure."""
        if not self.segments:
            return False
        
        if not self.full_text.strip():
            return False
        
        # Check that all segments have text
        for segment in self.segments:
            if not segment.text.strip():
                return False
        
        return True
