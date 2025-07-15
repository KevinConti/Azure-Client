"""
Unit tests for FileService.
"""
import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

from services.file_service import FileService
from models.transcript import Transcript


class TestFileService(unittest.TestCase):
    """Test cases for FileService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.file_service = FileService()
        self.mock_on_file_processed = Mock()
        self.mock_on_file_exported = Mock()
        self.mock_on_error = Mock()
        
        # Set up callbacks
        self.file_service.set_callbacks(
            on_file_processed=self.mock_on_file_processed,
            on_file_exported=self.mock_on_file_exported,
            on_error=self.mock_on_error
        )
        
        # Create test transcript
        self.test_transcript = Transcript.from_text(
            "This is a test transcript content.",
            source_file="test.txt"
        )
    
    def test_parse_vtt_file_success(self):
        """Test successful VTT file parsing."""
        # Create temp VTT file
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:05.000
This is a test transcript.

2
00:05.000 --> 00:10.000
Second segment of text.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(vtt_content)
            temp_path = temp_file.name
        
        try:
            # Parse VTT file
            transcript = self.file_service.parse_vtt_file(temp_path)
            
            # Verify success
            self.assertIsNotNone(transcript)
            self.assertIsInstance(transcript, Transcript)
            self.mock_on_file_processed.assert_called_once_with(temp_path, transcript)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_parse_vtt_file_not_found(self):
        """Test VTT file parsing with non-existent file."""
        # Try to parse non-existent file
        transcript = self.file_service.parse_vtt_file("nonexistent.vtt")
        
        # Verify failure
        self.assertIsNone(transcript)
        self.mock_on_error.assert_called()
        error_message = self.mock_on_error.call_args[0][0]
        self.assertIn("VTT file not found", error_message)
    
    def test_parse_vtt_file_encoding_error(self):
        """Test VTT file parsing with encoding error."""
        # Create temp file with invalid encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.vtt', delete=False) as temp_file:
            temp_file.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            temp_path = temp_file.name
        
        try:
            # Try to parse file
            transcript = self.file_service.parse_vtt_file(temp_path)
            
            # Verify error handling
            self.assertIsNone(transcript)
            self.mock_on_error.assert_called()
            error_message = self.mock_on_error.call_args[0][0]
            self.assertIn("encoding error", error_message)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_transcript_txt_format(self):
        """Test exporting transcript in TXT format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export transcript
            result = self.file_service.export_transcript(
                self.test_transcript, 
                temp_path, 
                format_type='txt'
            )
            
            # Verify success
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))
            self.mock_on_file_exported.assert_called_once_with(temp_path)
            
            # Verify content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("This is a test transcript content", content)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_transcript_vtt_format(self):
        """Test exporting transcript in VTT format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export transcript
            result = self.file_service.export_transcript(
                self.test_transcript, 
                temp_path, 
                format_type='vtt'
            )
            
            # Verify success
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))
            self.mock_on_file_exported.assert_called_once_with(temp_path)
            
            # Verify VTT format
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("WEBVTT", content)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_transcript_srt_format(self):
        """Test exporting transcript in SRT format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export transcript
            result = self.file_service.export_transcript(
                self.test_transcript, 
                temp_path, 
                format_type='srt'
            )
            
            # Verify success
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))
            self.mock_on_file_exported.assert_called_once_with(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_transcript_unsupported_format(self):
        """Test exporting transcript with unsupported format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Try to export with unsupported format
            result = self.file_service.export_transcript(
                self.test_transcript, 
                temp_path, 
                format_type='xyz'
            )
            
            # Verify failure
            self.assertFalse(result)
            self.mock_on_error.assert_called()
            error_message = self.mock_on_error.call_args[0][0]
            self.assertIn("Unsupported export format", error_message)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_file_exists_true(self):
        """Test file existence validation with existing file."""
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Validate file exists
            exists = self.file_service.validate_file_exists(temp_path)
            self.assertTrue(exists)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_file_exists_false(self):
        """Test file existence validation with non-existent file."""
        exists = self.file_service.validate_file_exists("nonexistent.txt")
        self.assertFalse(exists)
    
    def test_validate_vtt_file_valid(self):
        """Test VTT file validation with valid file."""
        # Create valid VTT file
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:05.000
Valid VTT content.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(vtt_content)
            temp_path = temp_file.name
        
        try:
            # Validate VTT file
            is_valid, message = self.file_service.validate_vtt_file(temp_path)
            
            self.assertTrue(is_valid)
            self.assertEqual(message, "VTT file is valid")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_vtt_file_missing_header(self):
        """Test VTT file validation with missing WEBVTT header."""
        # Create VTT file without header
        vtt_content = """1
00:00:00.000 --> 00:05.000
Content without header.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(vtt_content)
            temp_path = temp_file.name
        
        try:
            # Validate VTT file
            is_valid, message = self.file_service.validate_vtt_file(temp_path)
            
            self.assertFalse(is_valid)
            self.assertIn("missing WEBVTT header", message)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_vtt_file_no_content(self):
        """Test VTT file validation with no content."""
        # Create VTT file with header only
        vtt_content = "WEBVTT\n\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(vtt_content)
            temp_path = temp_file.name
        
        try:
            # Validate VTT file
            is_valid, message = self.file_service.validate_vtt_file(temp_path)
            
            self.assertFalse(is_valid)
            self.assertIn("no transcript text", message)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_vtt_file_not_found(self):
        """Test VTT file validation with non-existent file."""
        is_valid, message = self.file_service.validate_vtt_file("nonexistent.vtt")
        
        self.assertFalse(is_valid)
        self.assertIn("File does not exist", message)
    
    def test_get_file_info_success(self):
        """Test getting file information."""
        # Create temp file with known content
        test_content = "Test file content for size calculation"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name
        
        try:
            # Get file info
            info = self.file_service.get_file_info(temp_path)
            
            # Verify info
            self.assertIsNotNone(info)
            self.assertIsInstance(info, dict)
            if info:  # Type guard
                self.assertIn('size', info)
                self.assertIn('extension', info)
                self.assertIn('name', info)
                self.assertIn('path', info)
                
                # Verify size is correct
                self.assertGreater(info['size'], 0)
                
                # Verify path
                self.assertEqual(info['path'], temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_file_info_not_found(self):
        """Test getting file info for non-existent file."""
        info = self.file_service.get_file_info("nonexistent.txt")
        
        # Verify None is returned
        self.assertIsNone(info)
    
    def test_create_backup_success(self):
        """Test creating file backup."""
        # Create original file
        test_content = "Original file content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            original_path = temp_file.name
        
        try:
            # Create backup
            backup_path = self.file_service.create_backup(original_path)
            
            # Verify backup was created
            self.assertIsNotNone(backup_path)
            if backup_path:
                self.assertTrue(os.path.exists(backup_path))
                
                # Verify backup content matches original
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                    self.assertEqual(backup_content, test_content)
                
                # Cleanup backup
                if os.path.exists(backup_path):
                    os.unlink(backup_path)
        finally:
            if os.path.exists(original_path):
                os.unlink(original_path)
    
    def test_create_backup_file_not_found(self):
        """Test creating backup for non-existent file."""
        backup_path = self.file_service.create_backup("nonexistent.txt")
        
        # Verify None is returned
        self.assertIsNone(backup_path)
    
    def test_cleanup_temp_files_success(self):
        """Test cleanup of temporary files."""
        # Create temp files
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_files.append(temp_file.name)
            temp_file.close()
        
        # Cleanup temp files
        cleaned = self.file_service.cleanup_temp_files(temp_files)
        
        # Verify cleanup
        self.assertEqual(cleaned, 3)
        for temp_path in temp_files:
            self.assertFalse(os.path.exists(temp_path))
    
    def test_cleanup_temp_files_partial_failure(self):
        """Test cleanup with some files missing."""
        # Create one real temp file and one fake path
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        
        temp_files = [temp_file.name, "nonexistent.tmp"]
        
        # Cleanup temp files
        cleaned = self.file_service.cleanup_temp_files(temp_files)
        
        # Verify partial cleanup
        self.assertEqual(cleaned, 1)
        self.assertFalse(os.path.exists(temp_file.name))
    
    def test_get_supported_formats(self):
        """Test getting supported file formats."""
        formats = self.file_service.get_supported_formats()
        
        # Verify formats are returned
        self.assertIsInstance(formats, dict)
        self.assertIn('import', formats)
        self.assertIn('export', formats)
        self.assertIn('audio', formats)
        
        # Verify format lists
        self.assertIn('vtt', formats['import'])
        self.assertIn('txt', formats['export'])
        self.assertIn('wav', formats['audio'])
    
    def test_format_timestamp_vtt(self):
        """Test VTT timestamp formatting."""
        # Test timestamp formatting
        formatted = self.file_service._format_timestamp(65.123)
        
        # Should be in HH:MM:SS.mmm format
        self.assertEqual(formatted, "00:01:05.123")
    
    def test_format_timestamp_srt(self):
        """Test SRT timestamp formatting."""
        # Test timestamp formatting
        formatted = self.file_service._format_timestamp_srt(65.123)
        
        # Should be in HH:MM:SS,mmm format
        self.assertEqual(formatted, "00:01:05,123")
    
    def test_set_callbacks(self):
        """Test setting callback functions."""
        new_processed = Mock()
        new_exported = Mock()
        new_error = Mock()
        
        self.file_service.set_callbacks(
            on_file_processed=new_processed,
            on_file_exported=new_exported,
            on_error=new_error
        )
        
        # Verify callbacks were set
        self.assertEqual(self.file_service._on_file_processed, new_processed)
        self.assertEqual(self.file_service._on_file_exported, new_exported)
        self.assertEqual(self.file_service._on_error, new_error)


if __name__ == '__main__':
    unittest.main()
