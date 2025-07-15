"""
Data models for audio recording state and metadata.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime


class RecordingState(Enum):
    """Enumeration of possible recording states."""
    IDLE = "idle"
    RECORDING = "recording"
    STOPPING = "stopping"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AudioConfig:
    """Configuration for audio recording."""
    format: int = 8  # pyaudio.paInt16
    channels: int = 1
    rate: int = 44100
    frames_per_buffer: int = 1024
    
    def validate(self) -> bool:
        """Validate audio configuration."""
        return (self.channels > 0 and 
                self.rate > 0 and 
                self.frames_per_buffer > 0)


@dataclass
class RecordingSession:
    """Represents a recording session with metadata."""
    id: str
    state: RecordingState
    config: AudioConfig
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    file_path: Optional[str] = None
    frames: Optional[List[bytes]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.frames is None:
            self.frames = []
    
    @classmethod
    def create_new(cls, config: AudioConfig) -> 'RecordingSession':
        """Create a new recording session."""
        import uuid
        return cls(
            id=str(uuid.uuid4()),
            state=RecordingState.IDLE,
            config=config
        )
    
    def start(self) -> None:
        """Mark the recording as started."""
        self.state = RecordingState.RECORDING
        self.started_at = datetime.now()
        self.error_message = None
    
    def stop(self) -> None:
        """Mark the recording as stopping."""
        if self.state == RecordingState.RECORDING:
            self.state = RecordingState.STOPPING
    
    def complete(self, file_path: str) -> None:
        """Mark the recording as completed."""
        self.state = RecordingState.COMPLETED
        self.completed_at = datetime.now()
        self.file_path = file_path
        
        if self.started_at and self.completed_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def set_error(self, error_message: str) -> None:
        """Mark the recording as having an error."""
        self.state = RecordingState.ERROR
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def set_processing(self) -> None:
        """Mark the recording as being processed."""
        self.state = RecordingState.PROCESSING
    
    def add_frame(self, frame: bytes) -> None:
        """Add an audio frame to the recording."""
        if self.frames is not None:
            self.frames.append(frame)
    
    def clear_frames(self) -> None:
        """Clear the audio frames from memory."""
        self.frames = []
    
    def is_active(self) -> bool:
        """Check if the recording is currently active."""
        return self.state in [RecordingState.RECORDING, RecordingState.STOPPING, RecordingState.PROCESSING]
    
    def is_complete(self) -> bool:
        """Check if the recording is completed."""
        return self.state == RecordingState.COMPLETED
    
    def has_error(self) -> bool:
        """Check if the recording has an error."""
        return self.state == RecordingState.ERROR
    
    def get_duration_str(self) -> str:
        """Get a formatted duration string."""
        if self.duration_seconds is None:
            return "Unknown"
        
        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'state': self.state.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'file_path': self.file_path,
            'error_message': self.error_message,
            'config': {
                'format': self.config.format,
                'channels': self.config.channels,
                'rate': self.config.rate,
                'frames_per_buffer': self.config.frames_per_buffer
            }
        }
