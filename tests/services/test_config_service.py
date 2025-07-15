"""
Unit tests for ConfigService.
"""
import unittest
from unittest.mock import Mock, patch, mock_open
import os
import tempfile

from services.config_service import ConfigService, AzureConfig


class TestConfigService(unittest.TestCase):
    """Test cases for ConfigService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temp .env file for testing
        self.temp_env_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env_file.close()
        
        self.config_service = ConfigService(env_file_path=self.temp_env_file.name)
        
        # Test environment variables
        self.test_env_vars = {
            'AZURE_OPENAI_WHISPER_API_KEY': 'test_whisper_key',
            'AZURE_OPENAI_WHISPER_ENDPOINT': 'https://test-whisper.openai.azure.com/',
            'AZURE_OPENAI_WHISPER_DEPLOYMENT': 'whisper-1',
            'AZURE_OPENAI_GPT_API_KEY': 'test_gpt_key',
            'AZURE_OPENAI_GPT_ENDPOINT': 'https://test-gpt.openai.azure.com/',
            'AZURE_OPENAI_GPT_DEPLOYMENT': 'gpt-4'
        }
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_env_file.name):
            os.unlink(self.temp_env_file.name)
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_WHISPER_API_KEY': 'test_whisper_key',
        'AZURE_OPENAI_WHISPER_ENDPOINT': 'https://test-whisper.openai.azure.com/',
        'AZURE_OPENAI_WHISPER_DEPLOYMENT': 'whisper-1',
        'AZURE_OPENAI_GPT_API_KEY': 'test_gpt_key',
        'AZURE_OPENAI_GPT_ENDPOINT': 'https://test-gpt.openai.azure.com/',
        'AZURE_OPENAI_GPT_DEPLOYMENT': 'gpt-4'
    }, clear=True)
    def test_get_azure_config_success(self):
        """Test getting Azure configuration from environment variables."""
        config = self.config_service.get_azure_config()
        
        # Verify config was loaded
        self.assertIsNotNone(config)
        self.assertIsInstance(config, AzureConfig)
        self.assertEqual(config.whisper_api_key, 'test_whisper_key')
        self.assertEqual(config.whisper_endpoint, 'https://test-whisper.openai.azure.com/')
        self.assertEqual(config.whisper_deployment, 'whisper-1')
        self.assertEqual(config.gpt_api_key, 'test_gpt_key')
        self.assertEqual(config.gpt_endpoint, 'https://test-gpt.openai.azure.com/')
        self.assertEqual(config.gpt_deployment, 'gpt-4')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_azure_config_missing_env_vars(self):
        """Test getting Azure configuration with missing environment variables."""
        config = self.config_service.get_azure_config()
        
        # Should return None due to missing variables
        self.assertIsNone(config)
    
    def test_get_app_config(self):
        """Test getting application configuration."""
        app_config = self.config_service.get_app_config()
        
        # Should always return a config (with defaults if needed)
        self.assertIsNotNone(app_config)
        self.assertTrue(hasattr(app_config, 'whisper_deployment'))
        self.assertTrue(hasattr(app_config, 'gpt_deployment'))
    
    def test_azure_config_validate_success(self):
        """Test Azure configuration validation with valid config."""
        config = AzureConfig(
            whisper_api_key='sk-test123',
            whisper_endpoint='https://test-whisper.openai.azure.com/',
            whisper_deployment='whisper-1',
            gpt_api_key='sk-test456',
            gpt_endpoint='https://test-gpt.openai.azure.com/',
            gpt_deployment='gpt-4'
        )
        
        is_valid, message = config.validate()
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Configuration is valid")
    
    def test_azure_config_validate_missing_required(self):
        """Test Azure configuration validation with missing required fields."""
        config = AzureConfig(
            whisper_api_key='',  # Empty key
            whisper_endpoint='https://test.openai.azure.com/',
            whisper_deployment='whisper-1',
            gpt_api_key='sk-test456',
            gpt_endpoint='https://test.openai.azure.com/',
            gpt_deployment='gpt-4'
        )
        
        is_valid, message = config.validate()
        
        self.assertFalse(is_valid)
        self.assertIn('whisper_api_key', message)
    
    def test_azure_config_validate_invalid_url(self):
        """Test Azure configuration validation with invalid URL."""
        config = AzureConfig(
            whisper_api_key='sk-test123',
            whisper_endpoint='not_a_valid_url',  # Invalid URL
            whisper_deployment='whisper-1',
            gpt_api_key='sk-test456',
            gpt_endpoint='https://test.openai.azure.com/',
            gpt_deployment='gpt-4'
        )
        
        is_valid, message = config.validate()
        
        self.assertFalse(is_valid)
        self.assertIn('endpoint URL format', message)
    
    def test_validate_configuration_success(self):
        """Test overall configuration validation with valid config."""
        with patch.object(self.config_service, 'get_azure_config') as mock_azure:
            mock_azure.return_value = AzureConfig(
                whisper_api_key='sk-test123',
                whisper_endpoint='https://test.openai.azure.com/',
                whisper_deployment='whisper-1',
                gpt_api_key='sk-test456',
                gpt_endpoint='https://test.openai.azure.com/',
                gpt_deployment='gpt-4'
            )
            
            # Create the env file
            with open(self.temp_env_file.name, 'w') as f:
                f.write("# Test env file\n")
            
            is_valid, errors = self.config_service.validate_configuration()
            
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
    
    def test_validate_configuration_missing_azure(self):
        """Test configuration validation with missing Azure config."""
        with patch.object(self.config_service, 'get_azure_config') as mock_azure:
            mock_azure.return_value = None
            
            is_valid, errors = self.config_service.validate_configuration()
            
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
            self.assertTrue(any('Azure OpenAI configuration' in error for error in errors))
    
    def test_get_required_env_vars(self):
        """Test getting list of required environment variables."""
        required_vars = self.config_service.get_required_env_vars()
        
        # Verify required variables are listed
        self.assertIsInstance(required_vars, list)
        self.assertIn('AZURE_OPENAI_WHISPER_API_KEY', required_vars)
        self.assertIn('AZURE_OPENAI_WHISPER_ENDPOINT', required_vars)
        self.assertIn('AZURE_OPENAI_WHISPER_DEPLOYMENT', required_vars)
        self.assertIn('AZURE_OPENAI_GPT_API_KEY', required_vars)
        self.assertIn('AZURE_OPENAI_GPT_ENDPOINT', required_vars)
        self.assertIn('AZURE_OPENAI_GPT_DEPLOYMENT', required_vars)
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_WHISPER_API_KEY': 'test_key',
        # Missing other required vars
    }, clear=True)
    def test_get_missing_env_vars(self):
        """Test getting list of missing environment variables."""
        missing_vars = self.config_service.get_missing_env_vars()
        
        # Should include missing variables
        self.assertIsInstance(missing_vars, list)
        self.assertIn('AZURE_OPENAI_WHISPER_ENDPOINT', missing_vars)
        self.assertIn('AZURE_OPENAI_GPT_API_KEY', missing_vars)
        # Should not include the one that's set
        self.assertNotIn('AZURE_OPENAI_WHISPER_API_KEY', missing_vars)
    
    def test_create_sample_env_file(self):
        """Test creating sample .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.sample', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create sample env file
            success = self.config_service.create_sample_env_file(temp_path)
            
            # Verify file was created
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify content
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn('AZURE_OPENAI_WHISPER_API_KEY', content)
                self.assertIn('AZURE_OPENAI_GPT_API_KEY', content)
                self.assertIn('your_whisper_api_key_here', content)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_create_sample_env_file_error(self):
        """Test creating sample .env file with write error."""
        # Try to write to invalid path
        success = self.config_service.create_sample_env_file('/invalid/path/.env.sample')
        
        # Verify failure
        self.assertFalse(success)
    
    def test_reload_configuration(self):
        """Test reloading configuration."""
        # Get initial config
        initial_config = self.config_service.get_azure_config()
        
        # Reload configuration
        success = self.config_service.reload_configuration()
        
        # Verify reload succeeded
        self.assertTrue(success)
    
    def test_get_config_summary(self):
        """Test getting configuration summary."""
        summary = self.config_service.get_config_summary()
        
        # Verify summary structure
        self.assertIsInstance(summary, dict)
        self.assertIn('environment_file', summary)
        self.assertIn('environment_file_exists', summary)
        self.assertIn('azure_config_loaded', summary)
        self.assertIn('app_config_loaded', summary)
        self.assertIn('missing_env_vars', summary)
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_WHISPER_API_KEY': 'test_whisper_key',
        'AZURE_OPENAI_WHISPER_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_WHISPER_DEPLOYMENT': 'whisper-1',
        'AZURE_OPENAI_GPT_API_KEY': 'test_gpt_key',
        'AZURE_OPENAI_GPT_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_GPT_DEPLOYMENT': 'gpt-4'
    }, clear=True)
    def test_get_config_summary_with_azure_config(self):
        """Test getting configuration summary with Azure config loaded."""
        summary = self.config_service.get_config_summary()
        
        # Should include Azure config details
        self.assertIn('azure', summary)
        azure_summary = summary['azure']
        self.assertIn('whisper_endpoint', azure_summary)
        self.assertIn('gpt_endpoint', azure_summary)
        self.assertIn('has_whisper_key', azure_summary)
        self.assertIn('has_gpt_key', azure_summary)
        
        # Sensitive flags should be boolean
        self.assertTrue(azure_summary['has_whisper_key'])
        self.assertTrue(azure_summary['has_gpt_key'])
    
    def test_mask_sensitive_value(self):
        """Test masking sensitive configuration values."""
        # Test normal case
        sensitive_value = 'sk-very-secret-key-12345'
        masked_value = self.config_service.mask_sensitive_value(sensitive_value)
        
        # Verify value is masked
        self.assertNotEqual(masked_value, sensitive_value)
        self.assertIn('*', masked_value)
        self.assertTrue(masked_value.startswith('sk-v'))
        self.assertTrue(masked_value.endswith('2345'))
        
        # Test short value
        short_value = 'short'
        masked_short = self.config_service.mask_sensitive_value(short_value)
        self.assertEqual(masked_short, '*****')
        
        # Test empty value
        empty_masked = self.config_service.mask_sensitive_value('')
        self.assertEqual(empty_masked, '')


if __name__ == '__main__':
    unittest.main()
