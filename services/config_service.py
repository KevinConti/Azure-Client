"""
Configuration service for managing application settings and credentials.
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from models.app_state import AppConfig


@dataclass
class AzureConfig:
    """Configuration for Azure OpenAI services."""
    whisper_api_key: str
    whisper_endpoint: str
    whisper_deployment: str
    gpt_api_key: str
    gpt_endpoint: str
    gpt_deployment: str
    api_version_whisper: str = "2024-12-01-preview"
    api_version_gpt: str = "2025-01-01-preview"
    
    def validate(self) -> tuple[bool, str]:
        """Validate Azure configuration."""
        required_fields = [
            ('whisper_api_key', self.whisper_api_key),
            ('whisper_endpoint', self.whisper_endpoint),
            ('whisper_deployment', self.whisper_deployment),
            ('gpt_api_key', self.gpt_api_key),
            ('gpt_endpoint', self.gpt_endpoint),
            ('gpt_deployment', self.gpt_deployment)
        ]
        
        for field_name, field_value in required_fields:
            if not field_value or not field_value.strip():
                return False, f"Missing or empty {field_name}"
        
        # Validate endpoint URLs
        if not (self.whisper_endpoint.startswith('https://') or self.whisper_endpoint.startswith('http://')):
            return False, "Invalid whisper endpoint URL format"
        
        if not (self.gpt_endpoint.startswith('https://') or self.gpt_endpoint.startswith('http://')):
            return False, "Invalid GPT endpoint URL format"
        
        return True, "Configuration is valid"


class ConfigService:
    """Service for managing application configuration and credentials."""
    
    def __init__(self, env_file_path: Optional[str] = None):
        self.env_file_path = env_file_path or ".env"
        self._azure_config: Optional[AzureConfig] = None
        self._app_config: Optional[AppConfig] = None
        self._environment_variables: Dict[str, str] = {}
        
        # Load environment variables
        self._load_environment()
    
    def _load_environment(self) -> bool:
        """Load environment variables from .env file."""
        try:
            # Load from .env file if it exists
            if os.path.exists(self.env_file_path):
                load_dotenv(self.env_file_path)
            
            # Store current environment variables
            self._environment_variables = dict(os.environ)
            return True
            
        except Exception as e:
            print(f"Warning: Failed to load environment file: {e}")
            return False
    
    def get_azure_config(self) -> Optional[AzureConfig]:
        """Get Azure OpenAI configuration."""
        if self._azure_config is None:
            self._azure_config = self._load_azure_config()
        
        return self._azure_config
    
    def _load_azure_config(self) -> Optional[AzureConfig]:
        """Load Azure configuration from environment variables."""
        try:
            config = AzureConfig(
                whisper_api_key=os.getenv("AZURE_OPENAI_WHISPER_API_KEY", ""),
                whisper_endpoint=os.getenv("AZURE_OPENAI_WHISPER_ENDPOINT", ""),
                whisper_deployment=os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT", ""),
                gpt_api_key=os.getenv("AZURE_OPENAI_GPT_API_KEY", ""),
                gpt_endpoint=os.getenv("AZURE_OPENAI_GPT_ENDPOINT", ""),
                gpt_deployment=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT", ""),
                api_version_whisper=os.getenv("AZURE_OPENAI_API_VERSION_WHISPER", "2024-12-01-preview"),
                api_version_gpt=os.getenv("AZURE_OPENAI_API_VERSION_GPT", "2025-01-01-preview")
            )
            
            is_valid, error_message = config.validate()
            if not is_valid:
                print(f"Azure configuration validation failed: {error_message}")
                return None
            
            return config
            
        except Exception as e:
            print(f"Failed to load Azure configuration: {e}")
            return None
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration."""
        if self._app_config is None:
            self._app_config = self._load_app_config()
        
        return self._app_config
    
    def _load_app_config(self) -> AppConfig:
        """Load application configuration."""
        azure_config = self.get_azure_config()
        
        if not azure_config:
            # Return default config if Azure config is not available
            return AppConfig(
                whisper_deployment="whisper",
                gpt_deployment="gpt-4"
            )
        
        return AppConfig(
            whisper_deployment=azure_config.whisper_deployment,
            gpt_deployment=azure_config.gpt_deployment,
            temp_file_path=os.getenv("TEMP_AUDIO_FILE", "temp_recording.wav"),
            output_file_path=os.getenv("OUTPUT_FILE", "out.txt"),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
            temperature=float(os.getenv("TEMPERATURE", "0.3")),
            question_temperature=float(os.getenv("QUESTION_TEMPERATURE", "0.2")),
            question_max_tokens=int(os.getenv("QUESTION_MAX_TOKENS", "1500"))
        )
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """Validate all configuration settings."""
        errors = []
        
        # Validate Azure configuration
        azure_config = self.get_azure_config()
        if not azure_config:
            errors.append("Azure OpenAI configuration is missing or invalid")
        else:
            is_valid, error_message = azure_config.validate()
            if not is_valid:
                errors.append(f"Azure configuration error: {error_message}")
        
        # Validate app configuration
        app_config = self.get_app_config()
        if not app_config.validate():
            errors.append("Application configuration is invalid")
        
        # Check .env file existence
        if not os.path.exists(self.env_file_path):
            errors.append(f"Environment file not found: {self.env_file_path}")
        
        return len(errors) == 0, errors
    
    def get_required_env_vars(self) -> list[str]:
        """Get list of required environment variables."""
        return [
            "AZURE_OPENAI_WHISPER_API_KEY",
            "AZURE_OPENAI_WHISPER_ENDPOINT", 
            "AZURE_OPENAI_WHISPER_DEPLOYMENT",
            "AZURE_OPENAI_GPT_API_KEY",
            "AZURE_OPENAI_GPT_ENDPOINT",
            "AZURE_OPENAI_GPT_DEPLOYMENT"
        ]
    
    def get_missing_env_vars(self) -> list[str]:
        """Get list of missing required environment variables."""
        required_vars = self.get_required_env_vars()
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        return missing_vars
    
    def create_sample_env_file(self, file_path: Optional[str] = None) -> bool:
        """Create a sample .env file with required variables."""
        if file_path is None:
            file_path = ".env.sample"
        
        try:
            sample_content = """# Azure OpenAI Configuration for Whisper
AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key_here
AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_WHISPER_DEPLOYMENT=your_whisper_deployment_name

# Azure OpenAI Configuration for GPT
AZURE_OPENAI_GPT_API_KEY=your_gpt_api_key_here
AZURE_OPENAI_GPT_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=your_gpt_deployment_name

# Optional: API Versions (use defaults if not specified)
# AZURE_OPENAI_API_VERSION_WHISPER=2024-12-01-preview
# AZURE_OPENAI_API_VERSION_GPT=2025-01-01-preview

# Optional: Application Settings
# TEMP_AUDIO_FILE=temp_recording.wav
# OUTPUT_FILE=out.txt
# MAX_TOKENS=2000
# TEMPERATURE=0.3
# QUESTION_TEMPERATURE=0.2
# QUESTION_MAX_TOKENS=1500
"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            return True
            
        except Exception as e:
            print(f"Failed to create sample .env file: {e}")
            return False
    
    def reload_configuration(self) -> bool:
        """Reload configuration from environment."""
        try:
            self._load_environment()
            self._azure_config = None
            self._app_config = None
            return True
        except Exception as e:
            print(f"Failed to reload configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)."""
        azure_config = self.get_azure_config()
        app_config = self.get_app_config()
        
        summary = {
            "environment_file": self.env_file_path,
            "environment_file_exists": os.path.exists(self.env_file_path),
            "azure_config_loaded": azure_config is not None,
            "app_config_loaded": app_config is not None,
            "missing_env_vars": self.get_missing_env_vars()
        }
        
        if azure_config:
            summary["azure"] = {
                "whisper_endpoint": azure_config.whisper_endpoint,
                "whisper_deployment": azure_config.whisper_deployment,
                "gpt_endpoint": azure_config.gpt_endpoint,
                "gpt_deployment": azure_config.gpt_deployment,
                "api_version_whisper": azure_config.api_version_whisper,
                "api_version_gpt": azure_config.api_version_gpt,
                "has_whisper_key": bool(azure_config.whisper_api_key),
                "has_gpt_key": bool(azure_config.gpt_api_key)
            }
        
        if app_config:
            summary["app"] = {
                "temp_file_path": app_config.temp_file_path,
                "output_file_path": app_config.output_file_path,
                "max_tokens": app_config.max_tokens,
                "temperature": app_config.temperature,
                "question_temperature": app_config.question_temperature,
                "question_max_tokens": app_config.question_max_tokens
            }
        
        return summary
    
    def mask_sensitive_value(self, value: str) -> str:
        """Mask sensitive values for logging/display."""
        if not value:
            return ""
        
        if len(value) <= 8:
            return "*" * len(value)
        
        return value[:4] + "*" * (len(value) - 8) + value[-4:]
