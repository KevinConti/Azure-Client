"""
Data models for application state management.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

from .transcript import Transcript
from .recording import RecordingSession


class AppMode(Enum):
    """Application operation modes."""
    RECORDING = "recording"
    NOTES = "notes"
    QUESTION_ANSWERING = "question_answering"


class ProcessingState(Enum):
    """States for processing operations."""
    IDLE = "idle"
    TRANSCRIBING = "transcribing"
    GENERATING_NOTES = "generating_notes"
    ANSWERING_QUESTION = "answering_question"
    ERROR = "error"


@dataclass
class AppConfig:
    """Application configuration settings."""
    whisper_deployment: str
    gpt_deployment: str
    temp_file_path: str = "temp_recording.wav"
    output_file_path: str = "out.txt"
    max_tokens: int = 2000
    temperature: float = 0.3
    question_temperature: float = 0.2
    question_max_tokens: int = 1500
    
    def validate(self) -> bool:
        """Validate configuration."""
        return (bool(self.whisper_deployment) and 
                bool(self.gpt_deployment) and
                self.max_tokens > 0 and
                0.0 <= self.temperature <= 2.0 and
                0.0 <= self.question_temperature <= 2.0)


@dataclass
class AppState:
    """Central application state management."""
    mode: AppMode = AppMode.RECORDING
    processing_state: ProcessingState = ProcessingState.IDLE
    status_message: str = "Ready"
    current_transcript: Optional[Transcript] = None
    current_recording: Optional[RecordingSession] = None
    selected_file_path: Optional[str] = None
    last_question: Optional[str] = None
    last_response: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.now)
    
    def set_status(self, message: str) -> None:
        """Update status message."""
        self.status_message = message
        self.updated_at = datetime.now()
    
    def set_processing_state(self, state: ProcessingState) -> None:
        """Update processing state."""
        self.processing_state = state
        self.updated_at = datetime.now()
    
    def set_mode(self, mode: AppMode) -> None:
        """Change application mode."""
        self.mode = mode
        self.updated_at = datetime.now()
    
    def set_transcript(self, transcript: Transcript) -> None:
        """Set the current transcript."""
        self.current_transcript = transcript
        self.updated_at = datetime.now()
    
    def set_recording(self, recording: RecordingSession) -> None:
        """Set the current recording session."""
        self.current_recording = recording
        self.updated_at = datetime.now()
    
    def set_selected_file(self, file_path: str) -> None:
        """Set the selected VTT file path."""
        self.selected_file_path = file_path
        # Clear previous transcript when new file is selected
        self.current_transcript = None
        self.updated_at = datetime.now()
    
    def set_question_response(self, question: str, response: str) -> None:
        """Set the last question and response."""
        self.last_question = question
        self.last_response = response
        self.updated_at = datetime.now()
    
    def set_error(self, error_message: str) -> None:
        """Set error state."""
        self.error_message = error_message
        self.processing_state = ProcessingState.ERROR
        self.status_message = "Error occurred."
        self.updated_at = datetime.now()
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.error_message = None
        if self.processing_state == ProcessingState.ERROR:
            self.processing_state = ProcessingState.IDLE
        self.updated_at = datetime.now()
    
    def is_busy(self) -> bool:
        """Check if the application is currently processing."""
        return self.processing_state in [
            ProcessingState.TRANSCRIBING,
            ProcessingState.GENERATING_NOTES,
            ProcessingState.ANSWERING_QUESTION
        ]
    
    def can_record(self) -> bool:
        """Check if recording is possible."""
        return (self.mode == AppMode.RECORDING and 
                not self.is_busy() and
                (self.current_recording is None or not self.current_recording.is_active()))
    
    def can_generate_notes(self) -> bool:
        """Check if notes generation is possible."""
        return (self.mode == AppMode.NOTES and 
                not self.is_busy() and
                self.selected_file_path is not None)
    
    def can_ask_question(self) -> bool:
        """Check if question asking is possible."""
        return (self.mode == AppMode.QUESTION_ANSWERING and 
                not self.is_busy() and
                self.selected_file_path is not None)
    
    def reset(self) -> None:
        """Reset application state to initial values."""
        self.processing_state = ProcessingState.IDLE
        self.status_message = "Ready"
        self.current_transcript = None
        self.current_recording = None
        self.selected_file_path = None
        self.last_question = None
        self.last_response = None
        self.error_message = None
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for debugging/logging."""
        return {
            'mode': self.mode.value,
            'processing_state': self.processing_state.value,
            'status_message': self.status_message,
            'has_transcript': self.current_transcript is not None,
            'has_recording': self.current_recording is not None,
            'selected_file_path': self.selected_file_path,
            'last_question': self.last_question,
            'has_response': self.last_response is not None,
            'error_message': self.error_message,
            'updated_at': self.updated_at.isoformat(),
            'is_busy': self.is_busy(),
            'can_record': self.can_record(),
            'can_generate_notes': self.can_generate_notes(),
            'can_ask_question': self.can_ask_question()
        }
