"""
Unit tests for TranscriptionService.
"""
import unittest
from unittest.mock import Mock, patch, mock_open, ANY
import threading
import tempfile
import os

from services.transcription_service import TranscriptionService
from models.transcript import Transcript


class TestTranscriptionService(unittest.TestCase):
    """Test cases for TranscriptionService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Azure OpenAI client
        self.mock_client = Mock()
        self.deployment_name = "whisper-deployment"
        
        self.transcription_service = TranscriptionService(
            client=self.mock_client,
            deployment_name=self.deployment_name
        )
        
        self.mock_on_transcription_started = Mock()
        self.mock_on_transcription_complete = Mock()
        self.mock_on_error = Mock()
        
        # Set up callbacks
        self.transcription_service.set_callbacks(
            on_transcription_started=self.mock_on_transcription_started,
            on_transcription_complete=self.mock_on_transcription_complete,
            on_error=self.mock_on_error
        )
        
        # Create temp audio file for testing
        self.temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.temp_audio_file.write(b'fake_audio_data')
        self.temp_audio_file.close()
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_audio_file.name):
            os.unlink(self.temp_audio_file.name)
    
    @patch('services.transcription_service.threading.Thread')
    def test_transcribe_file_success(self, mock_thread):
        """Test successful file transcription start."""
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Start transcription
        result = self.transcription_service.transcribe_file(self.temp_audio_file.name)
        
        # Verify transcription started
        self.assertTrue(result)
        self.mock_on_transcription_started.assert_called_once_with(self.temp_audio_file.name)
        
        # Verify thread was started
        mock_thread_instance.start.assert_called_once()
    
    def test_transcribe_file_already_transcribing(self):
        """Test starting transcription when already in progress."""
        # Set transcribing flag
        self.transcription_service._is_transcribing = True
        
        # Try to start transcription
        result = self.transcription_service.transcribe_file(self.temp_audio_file.name)
        
        # Verify transcription failed to start
        self.assertFalse(result)
        self.mock_on_error.assert_called_once_with("Transcription already in progress")
    
    def test_transcribe_file_not_found(self):
        """Test transcription with non-existent file."""
        # Try to transcribe non-existent file
        result = self.transcription_service.transcribe_file("nonexistent.wav")
        
        # Verify error handling
        self.assertFalse(result)
        self.mock_on_error.assert_called()
        error_message = self.mock_on_error.call_args[0][0]
        self.assertIn("Audio file not found", error_message)
    
    def test_transcribe_audio_success(self):
        """Test successful API transcription call."""
        # Mock API response
        mock_response = Mock()
        mock_response.text = "This is a test transcription."
        self.mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Call transcription method
        result = self.transcription_service._transcribe_audio(self.temp_audio_file.name)
        
        # Verify successful transcription
        self.assertEqual(result, "This is a test transcription.")
        
        # Verify API was called correctly
        self.mock_client.audio.transcriptions.create.assert_called_once()
        call_args = self.mock_client.audio.transcriptions.create.call_args[1]
        self.assertEqual(call_args['model'], self.deployment_name)
    
    def test_transcribe_audio_with_language(self):
        """Test transcription with language parameter."""
        # Mock API response
        mock_response = Mock()
        mock_response.text = "Spanish transcription"
        self.mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Call transcription with language
        result = self.transcription_service._transcribe_audio(self.temp_audio_file.name, language="es")
        
        # Verify language was passed to API
        call_args = self.mock_client.audio.transcriptions.create.call_args[1]
        self.assertEqual(call_args['language'], "es")
    
    def test_transcribe_audio_api_error(self):
        """Test transcription with API error."""
        # Mock API to raise exception
        self.mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        # Verify exception is raised
        with self.assertRaises(Exception) as context:
            self.transcription_service._transcribe_audio(self.temp_audio_file.name)
        
        self.assertIn("API call failed", str(context.exception))
    
    def test_transcribe_with_retry_success_on_retry(self):
        """Test transcription success on retry."""
        # Mock API to fail first time, succeed second time
        mock_response = Mock()
        mock_response.text = "Success on retry"
        self.mock_client.audio.transcriptions.create.side_effect = [
            Exception("Temporary failure"),
            mock_response
        ]
        
        # Run transcription with retry
        self.transcription_service._transcribe_with_retry(self.temp_audio_file.name)
        
        # Verify success callback was called
        self.mock_on_transcription_complete.assert_called_once()
        
        # Verify the transcript was created correctly
        transcript_arg = self.mock_on_transcription_complete.call_args[0][0]
        self.assertIsInstance(transcript_arg, Transcript)
    
    def test_transcribe_with_retry_max_retries_exceeded(self):
        """Test transcription when max retries exceeded."""
        # Mock API to always fail
        self.mock_client.audio.transcriptions.create.side_effect = Exception("Persistent failure")
        
        # Set low retry count for faster test
        self.transcription_service.max_retries = 2
        
        # Run transcription with retry
        self.transcription_service._transcribe_with_retry(self.temp_audio_file.name)
        
        # Verify error callback was called
        self.mock_on_error.assert_called_once()
        error_message = self.mock_on_error.call_args[0][0]
        self.assertIn("failed after 2 attempts", error_message)
    
    def test_transcribe_vtt_file_success(self):
        """Test successful VTT file parsing."""
        vtt_content = """WEBVTT

00:00.000 --> 00:05.000
This is a test transcription.

00:05.000 --> 00:10.000
With multiple segments.
"""
        
        # Create temp VTT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False, encoding='utf-8') as vtt_file:
            vtt_file.write(vtt_content)
            vtt_file_path = vtt_file.name
        
        try:
            # Parse VTT file
            transcript = self.transcription_service.transcribe_vtt_file(vtt_file_path)
            
            # Verify transcript was created
            self.assertIsNotNone(transcript)
            self.assertIsInstance(transcript, Transcript)
            # Note: Actual segment count depends on Transcript.from_vtt_content implementation
        finally:
            os.unlink(vtt_file_path)
    
    def test_transcribe_vtt_file_not_found(self):
        """Test VTT file parsing with non-existent file."""
        # Try to parse non-existent file
        transcript = self.transcription_service.transcribe_vtt_file("nonexistent.vtt")
        
        # Verify error handling
        self.assertIsNone(transcript)
        self.mock_on_error.assert_called()
    
    def test_is_transcribing(self):
        """Test transcription status check."""
        # Initially not transcribing
        self.assertFalse(self.transcription_service.is_transcribing())
        
        # Set transcribing flag
        self.transcription_service._is_transcribing = True
        self.assertTrue(self.transcription_service.is_transcribing())
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        formats = self.transcription_service.get_supported_formats()
        
        # Verify common audio formats are supported
        self.assertIn('wav', formats)
        self.assertIn('mp3', formats)
        self.assertIn('m4a', formats)
        self.assertIn('flac', formats)
        self.assertIsInstance(formats, list)
    
    def test_validate_audio_file_valid(self):
        """Test validation of valid audio file."""
        is_valid, message = self.transcription_service.validate_audio_file(self.temp_audio_file.name)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "File is valid")
    
    def test_validate_audio_file_not_found(self):
        """Test validation of non-existent audio file."""
        is_valid, message = self.transcription_service.validate_audio_file("nonexistent.wav")
        
        self.assertFalse(is_valid)
        self.assertIn("File does not exist", message)
    
    def test_validate_audio_file_unsupported_format(self):
        """Test validation of file with unsupported extension."""
        # Create temp file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'not audio data')
            temp_file_path = temp_file.name
        
        try:
            is_valid, message = self.transcription_service.validate_audio_file(temp_file_path)
            
            self.assertFalse(is_valid)
            self.assertIn("Unsupported file format", message)
        finally:
            os.unlink(temp_file_path)
    
    def test_validate_audio_file_empty(self):
        """Test validation of empty audio file."""
        # Create empty temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            is_valid, message = self.transcription_service.validate_audio_file(temp_file_path)
            
            self.assertFalse(is_valid)
            self.assertIn("File is empty", message)
        finally:
            os.unlink(temp_file_path)
    
    @patch('os.path.getsize')
    def test_validate_audio_file_too_large(self, mock_getsize):
        """Test validation of file that's too large."""
        # Mock file size to be larger than 25MB
        mock_getsize.return_value = 30 * 1024 * 1024  # 30MB
        
        is_valid, message = self.transcription_service.validate_audio_file(self.temp_audio_file.name)
        
        self.assertFalse(is_valid)
        self.assertIn("File too large", message)
    
    def test_estimate_transcription_time(self):
        """Test transcription time estimation."""
        # Mock file size (1 MB)
        with patch('os.path.getsize', return_value=1024*1024):
            estimated_time = self.transcription_service.estimate_transcription_time(self.temp_audio_file.name)
            
            # Verify estimation is reasonable
            self.assertIsNotNone(estimated_time)
            self.assertIsInstance(estimated_time, (int, float))
            if estimated_time is not None:
                self.assertTrue(estimated_time > 0.0)
                self.assertTrue(estimated_time <= 300.0)  # Max 5 minutes
    
    def test_estimate_transcription_time_error(self):
        """Test transcription time estimation with file error."""
        # Mock getsize to raise exception
        with patch('os.path.getsize', side_effect=OSError("File error")):
            estimated_time = self.transcription_service.estimate_transcription_time("invalid.wav")
            
            self.assertIsNone(estimated_time)
    
    def test_set_callbacks(self):
        """Test setting callback functions."""
        new_started = Mock()
        new_complete = Mock()
        new_error = Mock()
        
        self.transcription_service.set_callbacks(
            on_transcription_started=new_started,
            on_transcription_complete=new_complete,
            on_error=new_error
        )
        
        # Verify callbacks were set
        self.assertEqual(self.transcription_service._on_transcription_started, new_started)
        self.assertEqual(self.transcription_service._on_transcription_complete, new_complete)
        self.assertEqual(self.transcription_service._on_error, new_error)
    
    def test_cleanup(self):
        """Test service cleanup."""
        # Set transcribing flag
        self.transcription_service._is_transcribing = True
        
        # Call cleanup
        self.transcription_service.cleanup()
        
        # Verify flag was reset
        self.assertFalse(self.transcription_service._is_transcribing)


if __name__ == '__main__':
    unittest.main()
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_audio_with_vtt_format(self, mock_openai):
        """Test audio transcription with VTT format."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = """WEBVTT

00:00.000 --> 00:05.000
This is a test transcription.

00:05.000 --> 00:10.000
With multiple segments.
"""
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Set up service with client
        self.transcription_service.client = mock_client
        
        # Transcribe audio with VTT format
        result = self.transcription_service.transcribe_audio(
            self.temp_audio_file.name, 
            response_format="vtt"
        )
        
        # Verify transcription success and format
        self.assertIsNotNone(result)
        self.assertIn("WEBVTT", result.text)
        
        # Verify correct format was requested
        mock_client.audio.transcriptions.create.assert_called_once_with(
            model="whisper-1",
            file=unittest.mock.ANY,
            response_format="vtt"
        )
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_audio_file_not_found(self, mock_openai):
        """Test transcription with non-existent file."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        self.transcription_service.client = mock_client
        
        # Try to transcribe non-existent file
        result = self.transcription_service.transcribe_audio("nonexistent.wav")
        
        # Verify error handling
        self.assertIsNone(result)
        self.mock_on_error.assert_called()
        error_message = self.mock_on_error.call_args[0][0]
        self.assertIn("File not found", error_message)
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_audio_api_error(self, mock_openai):
        """Test transcription with API error."""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        # Set up service with client
        self.transcription_service.client = mock_client
        
        # Try to transcribe audio
        result = self.transcription_service.transcribe_audio(self.temp_audio_file.name)
        
        # Verify error handling
        self.assertIsNone(result)
        self.mock_on_error.assert_called()
        error_message = self.mock_on_error.call_args[0][0]
        self.assertIn("Transcription failed", error_message)
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_audio_with_retry(self, mock_openai):
        """Test transcription with retry on failure."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock first call to fail, second to succeed
        mock_response = Mock()
        mock_response.text = "Success on retry"
        mock_client.audio.transcriptions.create.side_effect = [
            Exception("Temporary failure"),
            mock_response
        ]
        
        # Set up service with client and retry enabled
        self.transcription_service.client = mock_client
        self.transcription_service.max_retries = 2
        
        # Transcribe audio
        result = self.transcription_service.transcribe_audio(self.temp_audio_file.name)
        
        # Verify success on retry
        self.assertIsNotNone(result)
        self.assertEqual(result.text, "Success on retry")
        
        # Verify multiple calls were made
        self.assertEqual(mock_client.audio.transcriptions.create.call_count, 2)
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_audio_max_retries_exceeded(self, mock_openai):
        """Test transcription when max retries exceeded."""
        # Mock OpenAI client to always fail
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("Persistent failure")
        
        # Set up service with client and retry enabled
        self.transcription_service.client = mock_client
        self.transcription_service.max_retries = 2
        
        # Try to transcribe audio
        result = self.transcription_service.transcribe_audio(self.temp_audio_file.name)
        
        # Verify failure after retries
        self.assertIsNone(result)
        self.assertEqual(mock_client.audio.transcriptions.create.call_count, 2)
        self.mock_on_error.assert_called()
    
    def test_validate_audio_file_valid(self):
        """Test validation of valid audio file."""
        is_valid, message = self.transcription_service.validate_audio_file(self.temp_audio_file.name)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Audio file is valid")
    
    def test_validate_audio_file_not_found(self):
        """Test validation of non-existent audio file."""
        is_valid, message = self.transcription_service.validate_audio_file("nonexistent.wav")
        
        self.assertFalse(is_valid)
        self.assertIn("File not found", message)
    
    def test_validate_audio_file_invalid_extension(self):
        """Test validation of file with invalid extension."""
        # Create temp file with invalid extension
        temp_invalid = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_invalid.close()
        
        try:
            is_valid, message = self.transcription_service.validate_audio_file(temp_invalid.name)
            
            self.assertFalse(is_valid)
            self.assertIn("Unsupported file format", message)
        finally:
            os.unlink(temp_invalid.name)
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        formats = self.transcription_service.get_supported_formats()
        
        # Verify common audio formats are supported
        self.assertIn('wav', formats)
        self.assertIn('mp3', formats)
        self.assertIn('m4a', formats)
        self.assertIn('flac', formats)
    
    def test_estimate_transcription_cost(self):
        """Test transcription cost estimation."""
        # Mock file size (1 MB = 1 minute audio approximately)
        with patch('os.path.getsize', return_value=1024*1024):  # 1 MB
            cost = self.transcription_service.estimate_transcription_cost(self.temp_audio_file.name)
            
            # Verify cost is calculated (should be > 0)
            self.assertGreater(cost, 0)
            self.assertIsInstance(cost, (int, float))
    
    def test_set_callbacks(self):
        """Test setting callback functions."""
        new_started = Mock()
        new_completed = Mock()
        new_error = Mock()
        
        self.transcription_service.set_callbacks(
            on_transcription_started=new_started,
            on_transcription_completed=new_completed,
            on_error=new_error
        )
        
        # Verify callbacks were set
        self.assertEqual(self.transcription_service._on_transcription_started, new_started)
        self.assertEqual(self.transcription_service._on_transcription_completed, new_completed)
        self.assertEqual(self.transcription_service._on_error, new_error)
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_with_custom_model(self, mock_openai):
        """Test transcription with custom model."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.text = "Custom model transcription"
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Set up service with client
        self.transcription_service.client = mock_client
        
        # Transcribe with custom model
        result = self.transcription_service.transcribe_audio(
            self.temp_audio_file.name,
            model="whisper-large"
        )
        
        # Verify custom model was used
        mock_client.audio.transcriptions.create.assert_called_once_with(
            model="whisper-large",
            file=unittest.mock.ANY,
            response_format="text"
        )
    
    @patch('services.transcription_service.openai.OpenAI')
    def test_transcribe_with_language_hint(self, mock_openai):
        """Test transcription with language hint."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.text = "Transcription in Spanish"
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Set up service with client
        self.transcription_service.client = mock_client
        
        # Transcribe with language hint
        result = self.transcription_service.transcribe_audio(
            self.temp_audio_file.name,
            language="es"
        )
        
        # Verify language hint was used
        mock_client.audio.transcriptions.create.assert_called_once_with(
            model="whisper-1",
            file=unittest.mock.ANY,
            response_format="text",
            language="es"
        )
    
    def test_get_transcription_status_no_session(self):
        """Test getting transcription status when no active session."""
        status = self.transcription_service.get_transcription_status()
        
        self.assertEqual(status['status'], 'idle')
        self.assertIsNone(status['file_path'])
        self.assertIsNone(status['progress'])


if __name__ == '__main__':
    unittest.main()
