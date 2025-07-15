"""
Transcription service for handling Azure OpenAI Whisper API calls.
"""
import threading
import time
from typing import Callable, Optional
from openai import AzureOpenAI

from models.transcript import Transcript


class TranscriptionService:
    """Service for handling audio transcription using Azure OpenAI Whisper."""
    
    def __init__(self, client: AzureOpenAI, deployment_name: str):
        self.client = client
        self.deployment_name = deployment_name
        self._is_transcribing = False
        
        # Callbacks
        self._on_transcription_started: Optional[Callable[[str], None]] = None
        self._on_transcription_complete: Optional[Callable[[Transcript], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    def set_callbacks(self,
                     on_transcription_started: Optional[Callable[[str], None]] = None,
                     on_transcription_complete: Optional[Callable[[Transcript], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None):
        """Set callback functions for transcription events."""
        self._on_transcription_started = on_transcription_started
        self._on_transcription_complete = on_transcription_complete
        self._on_error = on_error
    
    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> bool:
        """Start transcription of an audio file."""
        if self._is_transcribing:
            if self._on_error:
                self._on_error("Transcription already in progress")
            return False
        
        try:
            # Validate file exists
            import os
            if not os.path.exists(file_path):
                if self._on_error:
                    self._on_error(f"Audio file not found: {file_path}")
                return False
            
            # Start transcription in separate thread
            transcribe_thread = threading.Thread(
                target=self._transcribe_with_retry, 
                args=(file_path, language)
            )
            transcribe_thread.start()
            
            if self._on_transcription_started:
                self._on_transcription_started(file_path)
            
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to start transcription: {str(e)}")
            return False
    
    def _transcribe_with_retry(self, file_path: str, language: Optional[str] = None):
        """Internal method to transcribe with retry logic."""
        self._is_transcribing = True
        
        for attempt in range(self.max_retries):
            try:
                result = self._transcribe_audio(file_path, language)
                
                if result:
                    # Create transcript object
                    transcript = Transcript.from_text(result, source_file=file_path)
                    if language:
                        transcript.language = language
                    
                    if self._on_transcription_complete:
                        self._on_transcription_complete(transcript)
                    
                    self._is_transcribing = False
                    return
                    
            except Exception as e:
                error_msg = f"Transcription attempt {attempt + 1} failed: {str(e)}"
                
                if attempt < self.max_retries - 1:
                    # Wait before retrying
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    # Final attempt failed
                    if self._on_error:
                        self._on_error(f"Transcription failed after {self.max_retries} attempts: {str(e)}")
        
        self._is_transcribing = False
    
    def _transcribe_audio(self, file_path: str, language: Optional[str] = None) -> str:
        """Internal method to call Azure OpenAI Whisper API."""
        try:
            with open(file_path, "rb") as audio_file:
                # Prepare API parameters
                api_params = {
                    "model": self.deployment_name,
                    "file": audio_file
                }
                
                # Add language parameter if specified
                if language:
                    api_params["language"] = language
                
                # Call the API
                result = self.client.audio.transcriptions.create(**api_params)
                
                if result and hasattr(result, 'text'):
                    return result.text
                else:
                    raise Exception("Invalid response from transcription API")
                    
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
    
    def transcribe_vtt_file(self, vtt_file_path: str) -> Optional[Transcript]:
        """Parse and create transcript from a VTT file."""
        try:
            with open(vtt_file_path, 'r', encoding='utf-8') as file:
                vtt_content = file.read()
            
            transcript = Transcript.from_vtt_content(vtt_content, source_file=vtt_file_path)
            
            if not transcript.validate():
                if self._on_error:
                    self._on_error("Invalid VTT file format or empty content")
                return None
            
            return transcript
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to parse VTT file: {str(e)}")
            return None
    
    def is_transcribing(self) -> bool:
        """Check if transcription is currently in progress."""
        return self._is_transcribing
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported audio formats."""
        return [
            "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm",
            "flac", "3gp", "aac", "ogg", "oga", "opus"
        ]
    
    def validate_audio_file(self, file_path: str) -> tuple[bool, str]:
        """Validate an audio file for transcription."""
        import os
        
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if file_ext not in self.get_supported_formats():
            return False, f"Unsupported file format: {file_ext}"
        
        # Check file size (Azure OpenAI has a 25MB limit)
        file_size = os.path.getsize(file_path)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max 25MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, "File is valid"
    
    def estimate_transcription_time(self, file_path: str) -> Optional[float]:
        """Estimate transcription time based on file size."""
        try:
            import os
            file_size = os.path.getsize(file_path)
            # Rough estimate: 1MB takes about 10-30 seconds
            estimated_seconds = (file_size / (1024 * 1024)) * 20
            return max(5.0, min(estimated_seconds, 300.0))  # Between 5s and 5min
        except Exception:
            return None
    
    def cleanup(self):
        """Clean up resources and cancel ongoing operations."""
        # Note: Azure OpenAI doesn't provide a way to cancel ongoing API calls
        # This is a placeholder for future implementation if needed
        self._is_transcribing = False
