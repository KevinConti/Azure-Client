# Developer Documentation

## Architecture Overview

The Whisper Client application follows a clean, layered architecture designed for maintainability, testability, and extensibility.

### Design Principles

1. **Separation of Concerns**: Each layer has a distinct responsibility
2. **Dependency Injection**: Services are injected rather than hard-coded
3. **Single Responsibility**: Each class/module has one primary purpose
4. **Interface Segregation**: Clean, minimal interfaces between components
5. **Testability**: All components can be unit tested in isolation

### Layer Details

#### UI Layer (`ui/`)
- **Purpose**: User interface components and event handling
- **Technologies**: Tkinter for desktop GUI
- **Key Classes**:
  - `MainWindow`: Primary application window
  - `RecordingTab`: Audio recording interface
  - `NotesTab`: Meeting notes and Q&A interface
  - `ThemeManager`: UI styling and theming

#### Controller Layer (`controllers/`)
- **Purpose**: Application orchestration and workflow management
- **Key Classes**:
  - `AppController`: Central coordinator for all services
  - `EventSystem`: Event dispatching and callback management

#### Service Layer (`services/`)
- **Purpose**: Business logic and external service integration
- **Key Services**:
  - `AudioService`: Microphone recording and audio processing
  - `TranscriptionService`: Azure OpenAI Whisper integration
  - `NotesService`: Azure OpenAI GPT for notes and Q&A
  - `FileService`: File operations and format conversions
  - `ConfigService`: Configuration and credential management

#### Model Layer (`models/`)
- **Purpose**: Data structures and business entities
- **Key Models**:
  - `Transcript`: Transcribed text with metadata
  - `RecordingSession`: Audio recording state and configuration
  - `AppState`: Central application state management

## Service Architecture

### Service Interface Pattern

All services follow a consistent pattern:

```python
class ServiceTemplate:
    def __init__(self, dependencies...):
        # Initialize service state
        pass
    
    def set_callbacks(self, **callbacks) -> None:
        # Configure event callbacks
        pass
    
    def primary_operation(self, input_data) -> bool:
        # Main service operation
        # Returns success/failure immediately
        # Actual results delivered via callbacks
        pass
    
    def cleanup(self) -> None:
        # Resource cleanup
        pass
```

### Callback System

Services communicate asynchronously through callbacks:

```python
# Setting up callbacks
service.set_callbacks(
    on_success=lambda result: handle_success(result),
    on_error=lambda error: handle_error(error),
    on_progress=lambda percent: update_progress(percent)
)

# Service calls callback when operation completes
if service.start_operation(data):
    # Operation started successfully
    # Wait for callback notification
```

### Error Handling Strategy

1. **Service Level**: Services validate inputs and handle API errors
2. **Controller Level**: Controller aggregates errors and updates app state
3. **UI Level**: UI displays errors from app state
4. **Global Level**: Unhandled exceptions caught at application level

## Development Workflows

### Adding a New Service

1. **Create Service Class** (`services/new_service.py`):
```python
from typing import Optional, Callable

class NewService:
    def __init__(self, dependencies):
        self._on_complete: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
    
    def set_callbacks(self, on_complete=None, on_error=None):
        self._on_complete = on_complete
        self._on_error = on_error
    
    def perform_operation(self, data) -> bool:
        # Implementation here
        pass
    
    def cleanup(self) -> None:
        # Cleanup resources
        pass
```

2. **Add to Controller** (`controllers/app_controller.py`):
```python
def _initialize(self):
    # Initialize new service
    self.new_service = NewService(dependencies)
    
    # Set up callbacks
    self.new_service.set_callbacks(
        on_complete=self._handle_new_service_complete,
        on_error=self._handle_error
    )
```

3. **Create Tests** (`tests/services/test_new_service.py`):
```python
import unittest
from unittest.mock import Mock, patch
from services.new_service import NewService

class TestNewService(unittest.TestCase):
    def setUp(self):
        self.service = NewService(mock_dependencies)
    
    def test_operation_success(self):
        # Test implementation
        pass
```

4. **Update Interface** (if UI changes needed)

### Adding New UI Components

1. **Create Component** (`ui/new_component.py`):
```python
import tkinter as tk
from typing import Callable

class NewComponent:
    def __init__(self, parent, controller):
        self.controller = controller
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Create UI elements
        pass
    
    def cleanup(self):
        # Cleanup if needed
        pass
```

2. **Integrate with MainWindow**
3. **Add Controller Methods** (if needed)
4. **Add Tests**

### Testing Strategy

#### Unit Tests
- **Service Tests**: Mock all external dependencies
- **Model Tests**: Test data validation and serialization
- **Controller Tests**: Mock services, test orchestration logic

#### Integration Tests
- **Service Integration**: Test service interactions
- **End-to-End Workflows**: Test complete user scenarios

#### Test Structure
```
tests/
├── services/
│   ├── test_audio_service.py
│   ├── test_transcription_service.py
│   └── ...
├── models/
│   ├── test_transcript.py
│   └── ...
├── controllers/
│   ├── test_app_controller.py
│   └── ...
└── integration/
    ├── test_recording_workflow.py
    └── ...
```

## Configuration Management

### Environment Variables

The application uses environment variables for configuration:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_WHISPER_API_KEY=your_key_here
AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper-1
AZURE_OPENAI_GPT_API_KEY=your_key_here
AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4
```

### Configuration Validation

The `ConfigService` provides:
- Environment variable loading and validation
- Configuration object creation and validation
- Sample configuration file generation
- Configuration summary for debugging

## Error Handling Patterns

### Service-Level Error Handling

```python
def service_operation(self, data):
    try:
        # Perform operation
        result = external_api_call(data)
        if self._on_complete:
            self._on_complete(result)
        return True
    except SpecificAPIError as e:
        if self._on_error:
            self._on_error(f"API Error: {str(e)}")
        return False
    except Exception as e:
        if self._on_error:
            self._on_error(f"Unexpected error: {str(e)}")
        return False
```

### Controller-Level Error Handling

```python
def _handle_service_error(self, error_message: str):
    self.app_state.set_error(error_message)
    self.logger.error(error_message)
    # Notify UI through state change
```

### UI-Level Error Display

```python
def update_from_state(self):
    if self.controller.app_state.error_message:
        self.show_error(self.controller.app_state.error_message)
```

## Performance Considerations

### Async Operations

- All potentially long-running operations use threading
- UI remains responsive during processing
- Progress updates provided through callbacks

### Memory Management

- Services clean up resources in `cleanup()` methods
- Large data objects released after processing
- Temporary files cleaned up automatically

### API Rate Limiting

- Retry logic with exponential backoff
- Configurable retry counts and delays
- Graceful degradation on API failures

## Security Best Practices

### Credential Management

- API keys stored in environment variables only
- No credentials in source code or logs
- Configuration validation prevents exposure

### Input Validation

- All user inputs validated before processing
- File uploads checked for size and format
- API responses validated before use

## Debugging and Logging

### Logging Configuration

The application uses Python's logging module:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Debug Tools

- `test_migration.py`: Validates architecture setup
- Application state inspection through controller
- Service-level debug information
- Comprehensive error messages with context

## Extension Points

### Adding New AI Models

1. Extend `TranscriptionService` or `NotesService`
2. Add new configuration options
3. Update UI to expose new features
4. Add appropriate tests

### Supporting New File Formats

1. Extend `FileService` with new parsers
2. Add format validation
3. Update UI file selection filters
4. Add format-specific tests

### Custom UI Themes

1. Extend `ThemeManager`
2. Add new color schemes
3. Support user theme selection
4. Persist theme preferences

This architecture provides a solid foundation for future enhancements while maintaining clean separation of concerns and comprehensive testing coverage.
