"""
Unit tests for AudioService.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
import tempfile
import os

from services.audio_service import AudioService
from models.recording import AudioConfig, RecordingState


class TestAudioService(unittest.TestCase):
    """Test cases for AudioService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_service = AudioService()
        self.mock_on_recording_started = Mock()
        self.mock_on_recording_stopped = Mock()
        self.mock_on_recording_complete = Mock()
        self.mock_on_error = Mock()
        
        # Set up callbacks
        self.audio_service.set_callbacks(
            on_recording_started=self.mock_on_recording_started,
            on_recording_stopped=self.mock_on_recording_stopped,
            on_recording_complete=self.mock_on_recording_complete,
            on_error=self.mock_on_error
        )
        
    def tearDown(self):
        """Clean up after tests."""
        if self.audio_service.is_recording():
            self.audio_service.stop_recording()
    
    @patch('services.audio_service.threading.Thread')
    def test_start_recording_success(self, mock_thread):
        """Test successful recording start."""
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Start recording
        config = AudioConfig()
        result = self.audio_service.start_recording(config, "test.wav")
        
        # Verify recording started
        self.assertTrue(result)
        self.assertTrue(self.audio_service.is_recording())
        self.assertIsNotNone(self.audio_service.current_session)
        
        # Verify callback was called
        self.mock_on_recording_started.assert_called_once()
        
        # Verify thread was started
        mock_thread_instance.start.assert_called_once()
    
    def test_start_recording_already_recording(self):
        """Test starting recording when already recording."""
        # Create a mock session that's already active
        mock_session = Mock()
        mock_session.is_active.return_value = True
        self.audio_service.current_session = mock_session
        
        # Try to start recording
        config = AudioConfig()
        result = self.audio_service.start_recording(config, "test.wav")
        
        # Verify recording failed to start
        self.assertFalse(result)
        self.mock_on_recording_started.assert_not_called()
    
    def test_start_recording_invalid_config(self):
        """Test starting recording with invalid config."""
        # Create invalid config
        config = AudioConfig(channels=0)  # Invalid channel count
        
        # Try to start recording
        result = self.audio_service.start_recording(config, "test.wav")
        
        # Verify recording failed and error callback called
        self.assertFalse(result)
        self.mock_on_error.assert_called_with("Invalid audio configuration")
    
    def test_stop_recording_success(self):
        """Test successful recording stop."""
        # Create a mock active session
        mock_session = Mock()
        mock_session.is_active.return_value = True
        self.audio_service.current_session = mock_session
        
        # Stop recording
        result = self.audio_service.stop_recording()
        
        # Verify recording stopped
        self.assertTrue(result)
        mock_session.stop.assert_called_once()
        self.mock_on_recording_stopped.assert_called_once_with(mock_session)
    
    def test_stop_recording_not_recording(self):
        """Test stopping recording when not recording."""
        # Ensure no current session
        self.audio_service.current_session = None
        
        # Try to stop recording
        result = self.audio_service.stop_recording()
        
        # Verify stop failed
        self.assertFalse(result)
        self.mock_on_recording_stopped.assert_not_called()
    
    def test_stop_recording_inactive_session(self):
        """Test stopping recording with inactive session."""
        # Create inactive session
        mock_session = Mock()
        mock_session.is_active.return_value = False
        self.audio_service.current_session = mock_session
        
        # Try to stop recording
        result = self.audio_service.stop_recording()
        
        # Verify stop failed
        self.assertFalse(result)
        self.mock_on_recording_stopped.assert_not_called()
    
    @patch('services.audio_service.pyaudio.PyAudio')
    def test_record_audio_success(self, mock_pyaudio):
        """Test successful audio recording thread."""
        # Mock PyAudio
        mock_pa_instance = Mock()
        mock_pyaudio.return_value = mock_pa_instance
        mock_stream = Mock()
        mock_pa_instance.open.return_value = mock_stream
        
        # Create a session
        config = AudioConfig()
        self.audio_service.current_session = Mock()
        self.audio_service.current_session.config = config
        self.audio_service.current_session.state = RecordingState.RECORDING
        
        # Mock stream.read to return data once then stop
        mock_stream.read.side_effect = [b'audio_data', Exception("Stop")]
        
        # Run recording method
        self.audio_service._record_audio()
        
        # Verify PyAudio was set up correctly
        mock_pa_instance.open.assert_called_once_with(
            format=config.format,
            channels=config.channels,
            rate=config.rate,
            input=True,
            frames_per_buffer=config.frames_per_buffer
        )
        
        # Verify audio data was added to session
        self.audio_service.current_session.add_frame.assert_called_with(b'audio_data')
    
    @patch('services.audio_service.pyaudio.PyAudio')
    def test_record_audio_pyaudio_error(self, mock_pyaudio):
        """Test recording with PyAudio initialization error."""
        # Mock PyAudio to raise exception
        mock_pyaudio.side_effect = Exception("PyAudio init failed")
        
        # Create a session
        config = AudioConfig()
        self.audio_service.current_session = Mock()
        self.audio_service.current_session.config = config
        
        # Run recording method
        self.audio_service._record_audio()
        
        # Verify error was handled
        self.audio_service.current_session.set_error.assert_called()
        self.mock_on_error.assert_called()
    
    @patch('services.audio_service.wave.open')
    def test_save_audio_file_success(self, mock_wave_open):
        """Test successful audio file saving."""
        # Mock wave file
        mock_wf = Mock()
        mock_wave_open.return_value.__enter__.return_value = mock_wf
        
        # Create session with frames
        config = AudioConfig()
        self.audio_service.current_session = Mock()
        self.audio_service.current_session.config = config
        self.audio_service.current_session.file_path = "test.wav"
        self.audio_service.current_session.frames = [b'frame1', b'frame2']
        
        # Save audio file
        self.audio_service._save_audio_file()
        
        # Verify wave file was configured correctly
        mock_wf.setnchannels.assert_called_with(config.channels)
        mock_wf.setframerate.assert_called_with(config.rate)
        mock_wf.writeframes.assert_called_with(b'frame1frame2')
        
        # Verify session was updated
        self.audio_service.current_session.clear_frames.assert_called_once()
        self.audio_service.current_session.complete.assert_called_once()
        self.mock_on_recording_complete.assert_called_once()
    
    def test_get_current_session(self):
        """Test getting current session."""
        # Test with no session
        self.assertIsNone(self.audio_service.get_current_session())
        
        # Test with session
        mock_session = Mock()
        self.audio_service.current_session = mock_session
        self.assertEqual(self.audio_service.get_current_session(), mock_session)
    
    def test_is_recording_true(self):
        """Test is_recording when actively recording."""
        mock_session = Mock()
        mock_session.state = RecordingState.RECORDING
        self.audio_service.current_session = mock_session
        
        self.assertTrue(self.audio_service.is_recording())
    
    def test_is_recording_false(self):
        """Test is_recording when not recording."""
        # Test with no session
        self.assertFalse(self.audio_service.is_recording())
        
        # Test with completed session
        mock_session = Mock()
        mock_session.state = RecordingState.COMPLETED
        self.audio_service.current_session = mock_session
        self.assertFalse(self.audio_service.is_recording())
    
    @patch('services.audio_service.os.path.exists')
    @patch('services.audio_service.os.remove')
    def test_cleanup_temp_files_success(self, mock_remove, mock_exists):
        """Test successful temp file cleanup."""
        mock_exists.return_value = True
        
        result = self.audio_service.cleanup_temp_files("temp.wav")
        
        self.assertTrue(result)
        mock_remove.assert_called_once_with("temp.wav")
    
    @patch('services.audio_service.os.path.exists')
    def test_cleanup_temp_files_not_exists(self, mock_exists):
        """Test cleanup when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.audio_service.cleanup_temp_files("temp.wav")
        
        self.assertFalse(result)
    
    @patch('services.audio_service.pyaudio.PyAudio')
    def test_get_audio_devices_success(self, mock_pyaudio):
        """Test getting audio devices list."""
        # Mock PyAudio
        mock_pa_instance = Mock()
        mock_pyaudio.return_value = mock_pa_instance
        mock_pa_instance.get_device_count.return_value = 2
        
        # Mock device info
        mock_pa_instance.get_device_info_by_index.side_effect = [
            {'name': 'Device 1', 'maxInputChannels': 2, 'defaultSampleRate': 44100},
            {'name': 'Device 2', 'maxInputChannels': 1, 'defaultSampleRate': 48000}
        ]
        
        devices = self.audio_service.get_audio_devices()
        
        # Verify devices were returned correctly
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['name'], 'Device 1')
        self.assertEqual(devices[0]['channels'], 2)
        self.assertEqual(devices[1]['name'], 'Device 2')
        self.assertEqual(devices[1]['channels'], 1)
    
    @patch('services.audio_service.pyaudio.PyAudio')
    def test_validate_audio_config_valid(self, mock_pyaudio):
        """Test audio config validation with valid config."""
        # Mock PyAudio
        mock_pa_instance = Mock()
        mock_pyaudio.return_value = mock_pa_instance
        mock_stream = Mock()
        mock_pa_instance.open.return_value = mock_stream
        
        config = AudioConfig()
        is_valid, message = self.audio_service.validate_audio_config(config)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Audio configuration is valid")
        mock_stream.close.assert_called_once()
        mock_pa_instance.terminate.assert_called_once()
    
    @patch('services.audio_service.pyaudio.PyAudio')
    def test_validate_audio_config_invalid(self, mock_pyaudio):
        """Test audio config validation with invalid config."""
        # Mock PyAudio to raise exception
        mock_pa_instance = Mock()
        mock_pyaudio.return_value = mock_pa_instance
        mock_pa_instance.open.side_effect = Exception("Invalid config")
        
        config = AudioConfig()
        is_valid, message = self.audio_service.validate_audio_config(config)
        
        self.assertFalse(is_valid)
        self.assertIn("Audio configuration test failed", message)
    
    def test_set_callbacks(self):
        """Test setting callback functions."""
        new_started = Mock()
        new_stopped = Mock()
        new_complete = Mock()
        new_error = Mock()
        
        self.audio_service.set_callbacks(
            on_recording_started=new_started,
            on_recording_stopped=new_stopped,
            on_recording_complete=new_complete,
            on_error=new_error
        )
        
        # Verify callbacks were set
        self.assertEqual(self.audio_service._on_recording_started, new_started)
        self.assertEqual(self.audio_service._on_recording_stopped, new_stopped)
        self.assertEqual(self.audio_service._on_recording_complete, new_complete)
        self.assertEqual(self.audio_service._on_error, new_error)


if __name__ == '__main__':
    unittest.main()
