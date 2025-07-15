"""
Audio recording service for handling microphone input and file operations.
"""
import os
import wave
import threading
import pyaudio
from typing import Callable, Optional

from models.recording import RecordingSession, AudioConfig, RecordingState


class AudioService:
    """Service for handling audio recording operations."""
    
    def __init__(self):
        self.current_session: Optional[RecordingSession] = None
        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream = None
        self._record_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._on_recording_started: Optional[Callable[[RecordingSession], None]] = None
        self._on_recording_stopped: Optional[Callable[[RecordingSession], None]] = None
        self._on_recording_complete: Optional[Callable[[RecordingSession, str], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        
    def set_callbacks(self, 
                     on_recording_started: Optional[Callable[[RecordingSession], None]] = None,
                     on_recording_stopped: Optional[Callable[[RecordingSession], None]] = None,
                     on_recording_complete: Optional[Callable[[RecordingSession, str], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None):
        """Set callback functions for recording events."""
        self._on_recording_started = on_recording_started
        self._on_recording_stopped = on_recording_stopped
        self._on_recording_complete = on_recording_complete
        self._on_error = on_error
    
    def start_recording(self, config: Optional[AudioConfig] = None, file_path: Optional[str] = None) -> bool:
        """Start a new recording session."""
        if self.current_session and self.current_session.is_active():
            return False
        
        if config is None:
            config = AudioConfig()
        
        if not config.validate():
            if self._on_error:
                self._on_error("Invalid audio configuration")
            return False
        
        if file_path is None:
            file_path = "temp_recording.wav"
        
        try:
            self.current_session = RecordingSession.create_new(config)
            self.current_session.file_path = file_path
            self.current_session.start()
            
            # Start recording in a separate thread
            self._record_thread = threading.Thread(target=self._record_audio)
            self._record_thread.start()
            
            if self._on_recording_started:
                self._on_recording_started(self.current_session)
            
            return True
            
        except Exception as e:
            if self.current_session:
                self.current_session.set_error(str(e))
            if self._on_error:
                self._on_error(f"Failed to start recording: {str(e)}")
            return False
    
    def stop_recording(self) -> bool:
        """Stop the current recording session."""
        if not self.current_session or not self.current_session.is_active():
            return False
        
        try:
            self.current_session.stop()
            
            if self._on_recording_stopped:
                self._on_recording_stopped(self.current_session)
            
            return True
            
        except Exception as e:
            if self.current_session:
                self.current_session.set_error(str(e))
            if self._on_error:
                self._on_error(f"Failed to stop recording: {str(e)}")
            return False
    
    def _record_audio(self):
        """Internal method to handle audio recording."""
        if not self.current_session:
            return
        
        try:
            config = self.current_session.config
            self._audio = pyaudio.PyAudio()
            
            # Open audio stream
            self._stream = self._audio.open(
                format=config.format,
                channels=config.channels,
                rate=config.rate,
                input=True,
                frames_per_buffer=config.frames_per_buffer
            )
            
            # Record audio frames
            while (self.current_session and 
                   self.current_session.state == RecordingState.RECORDING):
                try:
                    data = self._stream.read(config.frames_per_buffer)
                    self.current_session.add_frame(data)
                except Exception as e:
                    if self._on_error:
                        self._on_error(f"Error reading audio data: {str(e)}")
                    break
            
            # Clean up audio resources
            self._cleanup_audio()
            
            # Save the recorded audio to file
            if (self.current_session and 
                self.current_session.state == RecordingState.STOPPING):
                self._save_audio_file()
            
        except Exception as e:
            if self.current_session:
                self.current_session.set_error(str(e))
            if self._on_error:
                self._on_error(f"Recording error: {str(e)}")
            self._cleanup_audio()
    
    def _cleanup_audio(self):
        """Clean up PyAudio resources."""
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            
            if self._audio:
                self._audio.terminate()
                self._audio = None
        except Exception as e:
            if self._on_error:
                self._on_error(f"Error cleaning up audio resources: {str(e)}")
    
    def _save_audio_file(self):
        """Save recorded audio frames to a WAV file."""
        if not self.current_session or not self.current_session.file_path:
            return
        
        try:
            self.current_session.set_processing()
            
            with wave.open(self.current_session.file_path, 'wb') as wf:
                wf.setnchannels(self.current_session.config.channels)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.current_session.config.format))
                wf.setframerate(self.current_session.config.rate)
                if self.current_session.frames:
                    wf.writeframes(b''.join(self.current_session.frames))
            
            # Clear frames from memory
            self.current_session.clear_frames()
            self.current_session.complete(self.current_session.file_path)
            
            if self._on_recording_complete:
                self._on_recording_complete(self.current_session, self.current_session.file_path)
                
        except Exception as e:
            error_msg = f"Failed to save audio file: {str(e)}"
            if self.current_session:
                self.current_session.set_error(error_msg)
            if self._on_error:
                self._on_error(error_msg)
    
    def get_current_session(self) -> Optional[RecordingSession]:
        """Get the current recording session."""
        return self.current_session
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return (self.current_session is not None and 
                self.current_session.state == RecordingState.RECORDING)
    
    def cleanup_temp_files(self, file_path: str) -> bool:
        """Clean up temporary audio files."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to cleanup temp file: {str(e)}")
            return False
    
    def get_audio_devices(self) -> list:
        """Get list of available audio input devices."""
        devices = []
        try:
            audio = pyaudio.PyAudio()
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                max_channels = device_info.get('maxInputChannels', 0)
                if isinstance(max_channels, (int, float)) and max_channels > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': max_channels,
                        'sample_rate': device_info.get('defaultSampleRate', 0)
                    })
            audio.terminate()
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to get audio devices: {str(e)}")
        
        return devices
    
    def validate_audio_config(self, config: AudioConfig) -> tuple[bool, str]:
        """Validate an audio configuration."""
        if not config.validate():
            return False, "Invalid audio configuration parameters"
        
        try:
            # Test if we can create an audio stream with this config
            audio = pyaudio.PyAudio()
            test_stream = audio.open(
                format=config.format,
                channels=config.channels,
                rate=config.rate,
                input=True,
                frames_per_buffer=config.frames_per_buffer
            )
            test_stream.close()
            audio.terminate()
            return True, "Audio configuration is valid"
        except Exception as e:
            return False, f"Audio configuration test failed: {str(e)}"
