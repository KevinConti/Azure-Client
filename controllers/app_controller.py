"""
Main application controller for orchestrating services and managing application state.
"""
import logging
from typing import Optional, Callable, Dict, Any
from openai import AzureOpenAI

from models import AppState, AppConfig, AppMode, ProcessingState, AudioConfig, RecordingState
from services import (
    AudioService, 
    TranscriptionService, 
    NotesService, 
    FileService, 
    ConfigService
)


class AppController:
    """
    Central controller for orchestrating services and managing application flow.
    
    The AppController serves as the central nervous system of the application,
    coordinating between all services and managing the overall application state.
    It follows the Controller pattern to decouple the UI from business logic.
    
    Key Responsibilities:
    - Service lifecycle management and orchestration
    - Application state management and synchronization
    - Error handling and propagation across layers
    - Event coordination between services and UI
    - Configuration management and validation
    
    Architecture:
    - Initializes and manages all service instances
    - Provides high-level workflow methods for common operations
    - Handles cross-service communication and data flow
    - Maintains centralized error handling and logging
    
    Attributes:
        app_state: Central application state object
        config_service: Configuration and credential management
        audio_service: Audio recording and device management
        file_service: File operations and format handling
        transcription_service: Azure OpenAI Whisper integration
        notes_service: Azure OpenAI GPT integration for notes and Q&A
        whisper_client: Azure OpenAI client for transcription
        gpt_client: Azure OpenAI client for text generation
    """
    
    def __init__(self):
        # Initialize state
        self.app_state = AppState()
        
        # Initialize services
        self.config_service = ConfigService()
        self.audio_service = AudioService()
        self.file_service = FileService()
        
        # These will be initialized after configuration is loaded
        self.transcription_service: Optional[TranscriptionService] = None
        self.notes_service: Optional[NotesService] = None
        
        # OpenAI clients (initialized after config)
        self.whisper_client: Optional[AzureOpenAI] = None
        self.gpt_client: Optional[AzureOpenAI] = None
        
        # UI callbacks
        self._ui_callbacks: Dict[str, Callable] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize the application
        self._initialize()
    
    def _initialize(self):
        """Initialize the controller and services."""
        try:
            # Load configuration
            if not self._setup_configuration():
                return
            
            # Setup Azure clients
            if not self._setup_azure_clients():
                return
            
            # Initialize AI services
            self._setup_ai_services()
            
            # Setup service callbacks
            self._setup_service_callbacks()
            
            self.app_state.set_status("Ready")
            self.logger.info("Application controller initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize application: {str(e)}"
            self.app_state.set_error(error_msg)
            self.logger.error(error_msg)
    
    def _setup_configuration(self) -> bool:
        """Setup application configuration."""
        try:
            is_valid, errors = self.config_service.validate_configuration()
            if not is_valid:
                error_msg = "Configuration validation failed: " + "; ".join(errors)
                self.app_state.set_error(error_msg)
                self.logger.error(error_msg)
                return False
            
            app_config = self.config_service.get_app_config()
            if not app_config.validate():
                self.app_state.set_error("Invalid application configuration")
                return False
            
            return True
            
        except Exception as e:
            self.app_state.set_error(f"Configuration setup failed: {str(e)}")
            return False
    
    def _setup_azure_clients(self) -> bool:
        """Setup Azure OpenAI clients."""
        try:
            azure_config = self.config_service.get_azure_config()
            if not azure_config:
                self.app_state.set_error("Azure configuration not available")
                return False
            
            # Create Whisper client
            self.whisper_client = AzureOpenAI(
                api_key=azure_config.whisper_api_key,
                azure_endpoint=azure_config.whisper_endpoint,
                api_version=azure_config.api_version_whisper
            )
            
            # Create GPT client
            self.gpt_client = AzureOpenAI(
                api_key=azure_config.gpt_api_key,
                azure_endpoint=azure_config.gpt_endpoint,
                api_version=azure_config.api_version_gpt
            )
            
            return True
            
        except Exception as e:
            self.app_state.set_error(f"Failed to setup Azure clients: {str(e)}")
            return False
    
    def _setup_ai_services(self):
        """Initialize AI services with clients."""
        azure_config = self.config_service.get_azure_config()
        
        if self.whisper_client and azure_config:
            self.transcription_service = TranscriptionService(
                self.whisper_client, 
                azure_config.whisper_deployment
            )
        
        if self.gpt_client and azure_config:
            self.notes_service = NotesService(
                self.gpt_client, 
                azure_config.gpt_deployment
            )
    
    def _setup_service_callbacks(self):
        """Setup callbacks for all services."""
        # Audio service callbacks
        self.audio_service.set_callbacks(
            on_recording_started=self._on_recording_started,
            on_recording_stopped=self._on_recording_stopped,
            on_recording_complete=self._on_recording_complete,
            on_error=self._on_audio_error
        )
        
        # Transcription service callbacks
        if self.transcription_service:
            self.transcription_service.set_callbacks(
                on_transcription_started=self._on_transcription_started,
                on_transcription_complete=self._on_transcription_complete,
                on_error=self._on_transcription_error
            )
        
        # Notes service callbacks
        if self.notes_service:
            self.notes_service.set_callbacks(
                on_notes_started=self._on_notes_started,
                on_notes_complete=self._on_notes_complete,
                on_question_started=self._on_question_started,
                on_question_complete=self._on_question_complete,
                on_error=self._on_notes_error
            )
        
        # File service callbacks
        self.file_service.set_callbacks(
            on_file_processed=self._on_file_processed,
            on_file_exported=self._on_file_exported,
            on_error=self._on_file_error
        )
    
    # Public API methods
    
    def set_ui_callbacks(self, **callbacks):
        """Set UI callback functions."""
        self._ui_callbacks.update(callbacks)
    
    def start_recording(self) -> bool:
        """Start audio recording."""
        if not self.app_state.can_record():
            self._notify_ui('on_error', "Cannot start recording in current state")
            return False
        
        try:
            app_config = self.config_service.get_app_config()
            audio_config = AudioConfig()  # Use default audio config
            
            success = self.audio_service.start_recording(
                config=audio_config, 
                file_path=app_config.temp_file_path
            )
            
            if success:
                self.app_state.set_mode(AppMode.RECORDING)
                self.app_state.set_processing_state(ProcessingState.IDLE)
            
            return success
            
        except Exception as e:
            self.app_state.set_error(f"Failed to start recording: {str(e)}")
            return False
    
    def stop_recording(self) -> bool:
        """Stop audio recording."""
        if not self.audio_service.is_recording():
            return False
        
        try:
            return self.audio_service.stop_recording()
        except Exception as e:
            self.app_state.set_error(f"Failed to stop recording: {str(e)}")
            return False
    
    def select_vtt_file(self, file_path: str) -> bool:
        """Select a VTT file for processing."""
        try:
            # Validate the file
            is_valid, error_msg = self.file_service.validate_vtt_file(file_path)
            if not is_valid:
                self._notify_ui('on_error', f"Invalid VTT file: {error_msg}")
                return False
            
            # Update application state
            self.app_state.set_selected_file(file_path)
            self.app_state.set_mode(AppMode.NOTES)
            
            # Parse the file
            transcript = self.file_service.parse_vtt_file(file_path)
            if transcript:
                self.app_state.set_transcript(transcript)
                self._notify_ui('on_file_selected', file_path)
                return True
            
            return False
            
        except Exception as e:
            self.app_state.set_error(f"Failed to select VTT file: {str(e)}")
            return False
    
    def generate_meeting_notes(self) -> bool:
        """Generate meeting notes from current transcript."""
        if not self.app_state.can_generate_notes():
            self._notify_ui('on_error', "Cannot generate notes in current state")
            return False
        
        if not self.notes_service:
            self._notify_ui('on_error', "Notes service not available")
            return False
        
        try:
            transcript = self.app_state.current_transcript
            if not transcript:
                # Try to load from selected file
                if self.app_state.selected_file_path:
                    transcript = self.file_service.parse_vtt_file(self.app_state.selected_file_path)
                    if transcript:
                        self.app_state.set_transcript(transcript)
                
                if not transcript:
                    self._notify_ui('on_error', "No transcript available for notes generation")
                    return False
            
            self.app_state.set_processing_state(ProcessingState.GENERATING_NOTES)
            return self.notes_service.generate_notes(transcript)
            
        except Exception as e:
            self.app_state.set_error(f"Failed to generate notes: {str(e)}")
            return False
    
    def ask_question(self, question: str) -> bool:
        """Ask a question about the current transcript."""
        if not self.app_state.can_ask_question():
            self._notify_ui('on_error', "Cannot ask question in current state")
            return False
        
        if not self.notes_service:
            self._notify_ui('on_error', "Notes service not available")
            return False
        
        if not question.strip():
            self._notify_ui('on_error', "Question cannot be empty")
            return False
        
        try:
            # Switch to question answering mode
            self.app_state.set_mode(AppMode.QUESTION_ANSWERING)
            
            transcript = self.app_state.current_transcript
            if not transcript:
                # Try to load from selected file
                if self.app_state.selected_file_path:
                    transcript = self.file_service.parse_vtt_file(self.app_state.selected_file_path)
                    if transcript:
                        self.app_state.set_transcript(transcript)
                
                if not transcript:
                    self._notify_ui('on_error', "No transcript available for question answering")
                    return False
            
            self.app_state.set_processing_state(ProcessingState.ANSWERING_QUESTION)
            return self.notes_service.answer_question(question, transcript)
            
        except Exception as e:
            self.app_state.set_error(f"Failed to process question: {str(e)}")
            return False
    
    def export_transcript(self, file_path: str, format_type: str = "txt") -> bool:
        """Export current transcript to file."""
        try:
            transcript = self.app_state.current_transcript
            if not transcript:
                self._notify_ui('on_error', "No transcript available for export")
                return False
            
            return self.file_service.export_transcript(transcript, file_path, format_type)
            
        except Exception as e:
            self.app_state.set_error(f"Failed to export transcript: {str(e)}")
            return False
    
    def get_app_state(self) -> AppState:
        """Get current application state."""
        return self.app_state
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging."""
        return self.config_service.get_config_summary()
    
    def reload_configuration(self) -> bool:
        """Reload configuration from environment."""
        try:
            success = self.config_service.reload_configuration()
            if success:
                self._initialize()
            return success
        except Exception as e:
            self.app_state.set_error(f"Failed to reload configuration: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up resources and stop any ongoing operations."""
        try:
            # Stop recording if active
            if self.audio_service.is_recording():
                self.audio_service.stop_recording()
            
            # Clean up temporary files
            app_config = self.config_service.get_app_config()
            self.audio_service.cleanup_temp_files(app_config.temp_file_path)
            
            # Reset application state
            self.app_state.reset()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    # Internal callback methods
    
    def _on_recording_started(self, session):
        """Handle recording started event."""
        self.app_state.set_recording(session)
        self.app_state.set_status("Recording...")
        self._notify_ui('on_recording_started', session)
    
    def _on_recording_stopped(self, session):
        """Handle recording stopped event."""
        self.app_state.set_status("Finished recording. Transcribing...")
        self._notify_ui('on_recording_stopped', session)
    
    def _on_recording_complete(self, session, file_path):
        """Handle recording complete event."""
        self.app_state.set_processing_state(ProcessingState.TRANSCRIBING)
        
        if self.transcription_service:
            self.transcription_service.transcribe_file(file_path)
        else:
            self.app_state.set_error("Transcription service not available")
    
    def _on_transcription_started(self, file_path):
        """Handle transcription started event."""
        self.app_state.set_status("Transcribing audio...")
        self._notify_ui('on_transcription_started', file_path)
    
    def _on_transcription_complete(self, transcript):
        """Handle transcription complete event."""
        self.app_state.set_transcript(transcript)
        self.app_state.set_processing_state(ProcessingState.IDLE)
        self.app_state.set_status("Transcription complete.")
        
        # Export transcript to file
        app_config = self.config_service.get_app_config()
        self.file_service.export_transcript(transcript, app_config.output_file_path, "txt")
        
        # Clean up temp audio file
        self.audio_service.cleanup_temp_files(app_config.temp_file_path)
        
        self._notify_ui('on_transcription_complete', transcript)
    
    def _on_notes_started(self):
        """Handle notes generation started event."""
        self.app_state.set_status("Generating meeting notes...")
        self._notify_ui('on_notes_started')
    
    def _on_notes_complete(self, notes):
        """Handle notes generation complete event."""
        self.app_state.set_processing_state(ProcessingState.IDLE)
        self.app_state.set_status("Meeting notes generated successfully.")
        self._notify_ui('on_notes_complete', notes)
    
    def _on_question_started(self, question):
        """Handle question processing started event."""
        self.app_state.set_status("Processing your question...")
        self._notify_ui('on_question_started', question)
    
    def _on_question_complete(self, question, answer):
        """Handle question processing complete event."""
        self.app_state.set_question_response(question, answer)
        self.app_state.set_processing_state(ProcessingState.IDLE)
        self.app_state.set_status("Question answered successfully.")
        self._notify_ui('on_question_complete', question, answer)
    
    def _on_file_processed(self, file_path, transcript):
        """Handle file processing complete event."""
        self._notify_ui('on_file_processed', file_path, transcript)
    
    def _on_file_exported(self, file_path):
        """Handle file export complete event."""
        self._notify_ui('on_file_exported', file_path)
    
    def _on_audio_error(self, error_msg):
        """Handle audio service error."""
        self.app_state.set_error(f"Audio error: {error_msg}")
        self._notify_ui('on_error', error_msg)
    
    def _on_transcription_error(self, error_msg):
        """Handle transcription service error."""
        self.app_state.set_error(f"Transcription error: {error_msg}")
        self._notify_ui('on_error', error_msg)
    
    def _on_notes_error(self, error_msg):
        """Handle notes service error."""
        self.app_state.set_error(f"Notes error: {error_msg}")
        self._notify_ui('on_error', error_msg)
    
    def _on_file_error(self, error_msg):
        """Handle file service error."""
        self.app_state.set_error(f"File error: {error_msg}")
        self._notify_ui('on_error', error_msg)
    
    def _notify_ui(self, callback_name: str, *args, **kwargs):
        """Notify UI of events through callbacks."""
        try:
            callback = self._ui_callbacks.get(callback_name)
            if callback and callable(callback):
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in UI callback {callback_name}: {str(e)}")
