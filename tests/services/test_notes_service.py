"""
Unit tests for NotesService.
"""
import unittest
from unittest.mock import Mock, patch, ANY
import tempfile
import os

from services.notes_service import NotesService
from models.transcript import Transcript


class TestNotesService(unittest.TestCase):
    """Test cases for NotesService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Azure OpenAI client
        self.mock_client = Mock()
        self.deployment_name = "gpt-4"
        
        self.notes_service = NotesService(
            client=self.mock_client,
            deployment_name=self.deployment_name
        )
        
        self.mock_on_notes_started = Mock()
        self.mock_on_notes_complete = Mock()
        self.mock_on_question_started = Mock()
        self.mock_on_question_complete = Mock()
        self.mock_on_error = Mock()
        
        # Set up callbacks
        self.notes_service.set_callbacks(
            on_notes_started=self.mock_on_notes_started,
            on_notes_complete=self.mock_on_notes_complete,
            on_question_started=self.mock_on_question_started,
            on_question_complete=self.mock_on_question_complete,
            on_error=self.mock_on_error
        )
        
        # Create test transcript
        self.test_transcript = Transcript.from_text(
            "This is a meeting about project planning. We discussed the timeline and budget.",
            source_file="test.txt"
        )
    
    @patch('services.notes_service.threading.Thread')
    def test_generate_notes_success(self, mock_thread):
        """Test successful notes generation start."""
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Generate notes
        result = self.notes_service.generate_notes(self.test_transcript)
        
        # Verify success
        self.assertTrue(result)
        self.mock_on_notes_started.assert_called_once()
        
        # Verify thread was started
        mock_thread_instance.start.assert_called_once()
    
    def test_generate_notes_already_processing(self):
        """Test generating notes when already in progress."""
        # Set processing flag
        self.notes_service._is_processing = True
        
        # Try to generate notes
        result = self.notes_service.generate_notes(self.test_transcript)
        
        # Verify failed to start
        self.assertFalse(result)
        self.mock_on_error.assert_called_with("Notes generation already in progress")
    
    def test_generate_notes_invalid_transcript(self):
        """Test generating notes with invalid transcript."""
        # Create invalid transcript
        invalid_transcript = Transcript.from_text("", source_file="empty.txt")
        
        # Try to generate notes
        result = self.notes_service.generate_notes(invalid_transcript)
        
        # Verify failed due to validation
        self.assertFalse(result)
        self.mock_on_error.assert_called_with("Invalid transcript provided")
    
    @patch('services.notes_service.threading.Thread')
    def test_answer_question_success(self, mock_thread):
        """Test successful question answering start."""
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Ask question
        result = self.notes_service.answer_question(
            "What was discussed in the meeting?",
            self.test_transcript
        )
        
        # Verify success
        self.assertTrue(result)
        self.mock_on_question_started.assert_called_once_with("What was discussed in the meeting?")
        
        # Verify thread was started
        mock_thread_instance.start.assert_called_once()
    
    def test_answer_question_already_processing(self):
        """Test answering question when already processing."""
        # Set processing flag
        self.notes_service._is_processing = True
        
        # Try to answer question
        result = self.notes_service.answer_question(
            "Test question?",
            self.test_transcript
        )
        
        # Verify failed to start
        self.assertFalse(result)
        self.mock_on_error.assert_called_with("Question processing already in progress")
    
    def test_answer_question_empty_question(self):
        """Test answering empty question."""
        # Try to answer empty question
        result = self.notes_service.answer_question("", self.test_transcript)
        
        # Verify failed due to validation
        self.assertFalse(result)
        self.mock_on_error.assert_called_with("Question cannot be empty")
    
    def test_answer_question_invalid_transcript(self):
        """Test answering question with invalid transcript."""
        # Create invalid transcript
        invalid_transcript = Transcript.from_text("", source_file="empty.txt")
        
        # Try to answer question
        result = self.notes_service.answer_question("Test question?", invalid_transcript)
        
        # Verify failed due to validation
        self.assertFalse(result)
        self.mock_on_error.assert_called_with("Invalid transcript provided")
    
    @patch('prompts.get_meeting_notes_prompt')
    @patch('prompts.MEETING_NOTES_SYSTEM_MESSAGE', "System message")
    def test_generate_meeting_notes_success(self, mock_prompt):
        """Test successful meeting notes generation."""
        # Mock prompt function
        mock_prompt.return_value = "Generate notes for this meeting"
        
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated meeting notes content"
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Generate notes
        result = self.notes_service._generate_meeting_notes(self.test_transcript)
        
        # Verify success
        self.assertEqual(result, "Generated meeting notes content")
        
        # Verify API was called
        self.mock_client.chat.completions.create.assert_called_once()
        call_args = self.mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], self.deployment_name)
        self.assertEqual(call_args['temperature'], self.notes_service.notes_temperature)
        self.assertEqual(call_args['max_tokens'], self.notes_service.notes_max_tokens)
    
    @patch('prompts.get_question_answering_prompt')
    @patch('prompts.QUESTION_ANSWERING_SYSTEM_MESSAGE', "System message")
    def test_process_question_success(self, mock_prompt):
        """Test successful question processing."""
        # Mock prompt function
        mock_prompt.return_value = "Answer this question about the meeting"
        
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Answer to the question"
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # Process question
        result = self.notes_service._process_question(
            "What was discussed?", 
            self.test_transcript
        )
        
        # Verify success
        self.assertEqual(result, "Answer to the question")
        
        # Verify API was called
        self.mock_client.chat.completions.create.assert_called_once()
        call_args = self.mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], self.deployment_name)
        self.assertEqual(call_args['temperature'], self.notes_service.question_temperature)
        self.assertEqual(call_args['max_tokens'], self.notes_service.question_max_tokens)
    
    def test_generate_meeting_notes_api_error(self):
        """Test notes generation with API error."""
        # Mock API to raise exception
        self.mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Verify exception is raised
        with self.assertRaises(Exception) as context:
            self.notes_service._generate_meeting_notes(self.test_transcript)
        
        self.assertIn("GPT API call failed", str(context.exception))
    
    def test_process_question_api_error(self):
        """Test question processing with API error."""
        # Mock API to raise exception
        self.mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Verify exception is raised
        with self.assertRaises(Exception) as context:
            self.notes_service._process_question("Test question?", self.test_transcript)
        
        self.assertIn("GPT API call failed", str(context.exception))
    
    def test_is_processing(self):
        """Test processing status check."""
        # Initially not processing
        self.assertFalse(self.notes_service.is_processing())
        
        # Set processing flag
        self.notes_service._is_processing = True
        self.assertTrue(self.notes_service.is_processing())
    
    def test_set_configuration(self):
        """Test setting configuration parameters."""
        # Set new configuration
        self.notes_service.set_configuration(
            notes_temperature=0.5,
            notes_max_tokens=1500,
            question_temperature=0.1,
            question_max_tokens=1000,
            max_retries=3,
            retry_delay=1.5
        )
        
        # Verify configuration was updated
        self.assertEqual(self.notes_service.notes_temperature, 0.5)
        self.assertEqual(self.notes_service.notes_max_tokens, 1500)
        self.assertEqual(self.notes_service.question_temperature, 0.1)
        self.assertEqual(self.notes_service.question_max_tokens, 1000)
        self.assertEqual(self.notes_service.max_retries, 3)
        self.assertEqual(self.notes_service.retry_delay, 1.5)
    
    def test_set_configuration_bounds_checking(self):
        """Test configuration bounds checking."""
        # Set values outside valid ranges
        self.notes_service.set_configuration(
            notes_temperature=-1.0,  # Should be clamped to 0.0
            notes_max_tokens=5000,   # Should be clamped to 4000
            question_temperature=3.0,  # Should be clamped to 2.0
            question_max_tokens=0,   # Should be clamped to 1
            max_retries=10,          # Should be clamped to 5
            retry_delay=15.0         # Should be clamped to 10.0
        )
        
        # Verify values were clamped
        self.assertEqual(self.notes_service.notes_temperature, 0.0)
        self.assertEqual(self.notes_service.notes_max_tokens, 4000)
        self.assertEqual(self.notes_service.question_temperature, 2.0)
        self.assertEqual(self.notes_service.question_max_tokens, 1)
        self.assertEqual(self.notes_service.max_retries, 5)
        self.assertEqual(self.notes_service.retry_delay, 10.0)
    
    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        estimates = self.notes_service.estimate_processing_time(self.test_transcript)
        
        # Verify estimates are returned
        self.assertIsInstance(estimates, dict)
        self.assertIn("notes_generation", estimates)
        self.assertIn("question_answering", estimates)
        
        # Verify estimates are reasonable
        self.assertIsInstance(estimates["notes_generation"], (int, float))
        self.assertIsInstance(estimates["question_answering"], (int, float))
        self.assertTrue(estimates["notes_generation"] >= 10.0)
        self.assertTrue(estimates["question_answering"] >= 5.0)
    
    def test_validate_transcript_length_valid(self):
        """Test transcript length validation with valid transcript."""
        is_valid, message = self.notes_service.validate_transcript_length(self.test_transcript)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Transcript length is valid")
    
    def test_validate_transcript_length_too_short(self):
        """Test transcript length validation with short transcript."""
        short_transcript = Transcript.from_text("Hi", source_file="short.txt")
        
        is_valid, message = self.notes_service.validate_transcript_length(short_transcript)
        
        self.assertFalse(is_valid)
        self.assertIn("Transcript too short", message)
    
    def test_validate_transcript_length_too_long(self):
        """Test transcript length validation with long transcript."""
        # Create very long transcript
        long_text = "word " * 5000  # Much longer than limit
        long_transcript = Transcript.from_text(long_text, source_file="long.txt")
        
        is_valid, message = self.notes_service.validate_transcript_length(long_transcript)
        
        self.assertFalse(is_valid)
        self.assertIn("Transcript too long", message)
    
    def test_set_callbacks(self):
        """Test setting callback functions."""
        new_notes_started = Mock()
        new_notes_complete = Mock()
        new_question_started = Mock()
        new_question_complete = Mock()
        new_error = Mock()
        
        self.notes_service.set_callbacks(
            on_notes_started=new_notes_started,
            on_notes_complete=new_notes_complete,
            on_question_started=new_question_started,
            on_question_complete=new_question_complete,
            on_error=new_error
        )
        
        # Verify callbacks were set
        self.assertEqual(self.notes_service._on_notes_started, new_notes_started)
        self.assertEqual(self.notes_service._on_notes_complete, new_notes_complete)
        self.assertEqual(self.notes_service._on_question_started, new_question_started)
        self.assertEqual(self.notes_service._on_question_complete, new_question_complete)
        self.assertEqual(self.notes_service._on_error, new_error)
    
    def test_cleanup(self):
        """Test service cleanup."""
        # Set processing flag
        self.notes_service._is_processing = True
        
        # Call cleanup
        self.notes_service.cleanup()
        
        # Verify flag was reset
        self.assertFalse(self.notes_service._is_processing)


if __name__ == '__main__':
    unittest.main()
