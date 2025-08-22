# Azure OpenAI Whisper Client

A modern, scalable Python application for audio transcription and meeting notes generation using Azure OpenAI's Whisper and GPT models. Built with a clean service-oriented architecture for maintainability and extensibility.

## 🏗️ Architecture

This application follows a layered architecture with clear separation of concerns:

```
┌─────────────────┐
│   UI Layer      │  (Tkinter components)
├─────────────────┤
│  Controller     │  (Application orchestration)
├─────────────────┤
│   Services      │  (Business logic)
├─────────────────┤
│    Models       │  (Data structures)
└─────────────────┘
```

### Key Components

- **UI Layer**: Tkinter-based user interface with tabbed design
- **Controller**: Central orchestration of services and application state
- **Services**: Specialized services for audio, transcription, notes, files, and configuration
- **Models**: Data structures for transcripts, recordings, and application state

## 🚀 Features

- **Audio Recording**: Real-time microphone recording with configurable settings
- **File Upload**: Support for various audio formats and VTT transcript files
- **Transcription**: Azure OpenAI Whisper integration with retry logic and error handling
- **Meeting Notes**: Automated meeting notes generation using GPT models
- **Q&A System**: Interactive question answering based on transcript content
- **Export Options**: Multiple output formats (TXT, VTT, SRT)
- **Modern UI**: Clean, responsive interface with progress indicators

## 📋 Prerequisites

- Python 3.8 or higher (for local installation)
- **OR** Docker and Docker Compose (for containerized deployment)
- Azure OpenAI account with Whisper and GPT deployments
- Microphone access (for recording features)

## 🛠️ Setup

### Option 1: Docker Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Azure-Client
   ```

2. **Quick start with Docker:**
   
   **Linux/macOS:**
   ```bash
   # Copy environment template
   cp .env.sample .env
   
   # Edit .env with your Azure OpenAI credentials
   nano .env
   
   # Run the application (this will build and start the container)
   ./run-docker.sh
   ```
   
   **Windows (PowerShell):**
   ```powershell
   # Copy environment template
   Copy-Item .env.sample .env
   
   # Edit .env with your Azure OpenAI credentials
   notepad .env
   
   # Run the application (this will build and start the container)
   .\run-docker.ps1
   ```

3. **Alternative Docker commands:**
   ```bash
   # Manual setup
   docker compose up --build
   
   # Development mode with hot-reload
   docker compose --profile dev up --build azure-whisper-client-dev
   
   # Production deployment
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

4. **Enable GUI access (Linux/macOS):**
   ```bash
   # Allow Docker to access X11 display
   xhost +local:docker
   
   # Run the application
   docker-compose up
   ```

### Option 2: Local Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Azure-Client
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your credentials:**
   Create a `.env` file in the project root with your Azure OpenAI credentials:
   ```env
   AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key_here
   AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_WHISPER_DEPLOYMENT=your_whisper_deployment_name
   AZURE_OPENAI_GPT_API_KEY=your_gpt_api_key_here
   AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_GPT_DEPLOYMENT=your_gpt_deployment_name
   ```

## 🎯 Usage

### Starting the Application

#### With Docker:

**Linux/macOS:**
```bash
# Using helper script - Production mode
./run-docker.sh

# Using helper script - Development mode
./run-docker.sh dev

# Manual commands
docker-compose up                                              # Production
docker-compose --profile dev up azure-whisper-client-dev     # Development
```

**Windows (PowerShell):**
```powershell
# Using helper script - Production mode
.\run-docker.ps1

# Using helper script - Development mode
.\run-docker.ps1 dev

# Manual commands
docker-compose up                                              # Production
docker-compose --profile dev up azure-whisper-client-dev     # Development
```

#### Local Installation:
```bash
python main.py
```

### Docker Environment Configuration

Create a `.env` file in the project root with your Azure OpenAI credentials:
```env
AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key_here
AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_WHISPER_DEPLOYMENT=your_whisper_deployment_name
AZURE_OPENAI_GPT_API_KEY=your_gpt_api_key_here
AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=your_gpt_deployment_name
```

### GUI Access for Docker

#### Linux:
```bash
# Allow Docker containers to access the display
xhost +local:docker

# Run the application
docker-compose up
```

#### macOS:
```bash
# Install XQuartz if not already installed
brew install --cask xquartz

# Start XQuartz and allow network connections
open -a XQuartz
# In XQuartz preferences, enable "Allow connections from network clients"

# Get your IP address
export DISPLAY=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}'):0

# Run the application
docker-compose up
```

#### Windows:
```powershell
# Install and run an X11 server like VcXsrv, Xming, or X410
# For VcXsrv: Download from https://sourceforge.net/projects/vcxsrv/
# For X410: Available in Microsoft Store

# Set the DISPLAY environment variable
$env:DISPLAY = "host.docker.internal:0"

# Using PowerShell helper script (recommended)
.\run-docker.ps1

# Or using manual Docker commands
docker-compose up
```

**Note for Windows users:** The PowerShell script (`run-docker.ps1`) provides the same functionality as the bash script for Linux/macOS users, including GUI access setup reminders and environment file management.

### Application Features

### Recording Tab
1. Click "Start Recording" to begin audio capture
2. Click "Stop Recording" to end and automatically transcribe
3. Use "Copy to Clipboard" to copy the transcript text

### Meeting Notes Tab
1. Upload a VTT transcript file using "Browse"
2. Click "Generate Meeting Notes" for AI-powered summaries
3. Use the Q&A section to ask questions about the content

## 🏛️ Architecture Details

### Services

- **AudioService**: Handles microphone recording and audio file operations
- **TranscriptionService**: Manages Azure OpenAI Whisper API interactions
- **NotesService**: Generates meeting notes and handles Q&A using GPT
- **FileService**: Processes VTT files and handles exports
- **ConfigService**: Manages application configuration and credentials

### Models

- **Transcript**: Represents transcribed text with segments and metadata
- **RecordingSession**: Manages audio recording state and configuration
- **AppState**: Central application state management

### Controller

- **AppController**: Orchestrates all services and manages application flow

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run service tests only
python -m pytest tests/services/ -v

# Test the migration architecture
python test_migration.py
```

## 🔧 Development

### Project Structure

```
Azure-Client/
├── controllers/          # Application controllers
│   ├── app_controller.py
│   └── event_system.py
├── models/              # Data models
│   ├── app_state.py
│   ├── recording.py
│   └── transcript.py
├── services/            # Business logic services
│   ├── audio_service.py
│   ├── config_service.py
│   ├── file_service.py
│   ├── notes_service.py
│   └── transcription_service.py
├── ui/                  # User interface components
│   ├── main_window.py
│   ├── notes_tab.py
│   ├── recording_tab.py
│   └── theme.py
├── tests/               # Test suites
│   ├── controllers/
│   ├── models/
│   ├── services/
│   └── ui/
├── Dockerfile           # Docker container configuration
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker ignore patterns
├── main.py              # Application entry point
└── requirements.txt     # Dependencies
```

### Docker Development Workflow

#### Development Environment Setup
```bash
# Clone and setup
git clone <repository-url>
cd Azure-Client

# Create environment file
cp .env.sample .env
# Edit .env with your credentials

# Enable GUI access (Linux/macOS)
xhost +local:docker

# Start development environment
docker-compose --profile dev up --build azure-whisper-client-dev
```

#### Development Commands
```bash
# Build container
docker-compose build

# Run tests in container
docker-compose run azure-whisper-client python -m pytest tests/ -v

# Access container shell
docker-compose run azure-whisper-client bash

# View container logs
docker-compose logs azure-whisper-client

# Stop all containers
docker-compose down
```

#### Production Deployment
```bash
# Build and run production container
docker-compose up --build -d

# Monitor application
docker-compose logs -f azure-whisper-client

# Update application
docker-compose pull
docker-compose up -d
```

### Adding New Features

1. **Services**: Implement business logic in appropriate service classes
2. **Models**: Define data structures in the models package
3. **UI**: Add interface components in the ui package
4. **Tests**: Write comprehensive tests for all new functionality
5. **Docker**: Update Dockerfile if new system dependencies are needed

## 📝 Configuration

### Azure OpenAI Setup

Before using this application, you need to set up Azure OpenAI services:

1. **Create Azure OpenAI Resource**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new Azure OpenAI resource
   - Note the endpoint URL and API keys

2. **Deploy Models**:
   - Deploy a Whisper model (e.g., `whisper-1`)
   - Deploy a GPT model (e.g., `gpt-35-turbo` or `gpt-4`)
   - Note the deployment names

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `AZURE_OPENAI_WHISPER_API_KEY` | Azure OpenAI API key for Whisper | Yes | `abc123...` |
| `AZURE_OPENAI_WHISPER_ENDPOINT` | Azure OpenAI endpoint URL | Yes | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_WHISPER_DEPLOYMENT` | Whisper deployment name | Yes | `whisper-1` |
| `AZURE_OPENAI_GPT_API_KEY` | Azure OpenAI API key for GPT | Yes | `def456...` |
| `AZURE_OPENAI_GPT_ENDPOINT` | Azure OpenAI endpoint URL | Yes | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_GPT_DEPLOYMENT` | GPT deployment name | Yes | `gpt-35-turbo` |

### Configuration Setup

#### Option 1: Environment Variables (Recommended)
Set environment variables in your system or virtual environment:

**Windows (Command Prompt)**:
```cmd
set AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key
set AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource.openai.azure.com/
set AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper-1
set AZURE_OPENAI_GPT_API_KEY=your_gpt_api_key
set AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
set AZURE_OPENAI_GPT_DEPLOYMENT=gpt-35-turbo
```

**Windows (PowerShell)**:
```powershell
$env:AZURE_OPENAI_WHISPER_API_KEY="your_whisper_api_key"
$env:AZURE_OPENAI_WHISPER_ENDPOINT="https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_WHISPER_DEPLOYMENT="whisper-1"
$env:AZURE_OPENAI_GPT_API_KEY="your_gpt_api_key"
$env:AZURE_OPENAI_GPT_ENDPOINT="https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_GPT_DEPLOYMENT="gpt-35-turbo"
```

**Linux/macOS**:
```bash
export AZURE_OPENAI_WHISPER_API_KEY="your_whisper_api_key"
export AZURE_OPENAI_WHISPER_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_WHISPER_DEPLOYMENT="whisper-1"
export AZURE_OPENAI_GPT_API_KEY="your_gpt_api_key"
export AZURE_OPENAI_GPT_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_GPT_DEPLOYMENT="gpt-35-turbo"
```

#### Option 2: .env File
Create a `.env` file in the project root:

```bash
# Generate a sample .env file
python -c "from services.config_service import ConfigService; ConfigService().create_sample_env_file()"
```

Edit the generated `.env.sample` file and rename it to `.env`:
```env
AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key
AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper-1
AZURE_OPENAI_GPT_API_KEY=your_gpt_api_key
AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-35-turbo
```

### Configuration Validation

Validate your configuration before running the application:

```bash
python -c "from services.config_service import ConfigService; cs = ConfigService(); is_valid, errors = cs.validate_configuration(); print('✅ Configuration is valid!' if is_valid else f'❌ Configuration errors: {errors}')"
```

### Configuration Requirements

- **API Keys**: Must be valid Azure OpenAI API keys
- **Endpoints**: Must include the full URL with trailing slash
- **Deployments**: Must match the exact deployment names in your Azure OpenAI resource
- **Permissions**: Ensure API keys have access to the specified deployments

## 🐛 Troubleshooting

### Quick Diagnostics

Before diving into specific issues, run these quick checks:

```bash
# Validate configuration
python -c "from services.config_service import ConfigService; cs = ConfigService(); print('✅ Valid' if cs.validate_configuration()[0] else '❌ Invalid')"

# Test application import
python -c "import main; print('✅ Application imports successfully')"

# Run migration tests
python test_migration.py
```

### Common Issues

1. **Configuration Errors**: 
   - Ensure all environment variables are set correctly
   - Verify API keys and deployment names match your Azure OpenAI resource
   - Check endpoint URLs include trailing slash

2. **API Issues**: 
   - Check Azure OpenAI quotas and rate limits in Azure Portal
   - Verify your Azure subscription is active
   - Ensure deployments exist and are running

3. **Audio Issues**: 
   - Verify microphone permissions and availability
   - Check Windows audio settings and default recording device
   - Test microphone in other applications

4. **Import Errors**: 
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify Python version is 3.8 or higher
   - Check virtual environment is activated

5. **Docker Issues**:
   - Ensure Docker is running and accessible
   - For GUI access, verify X11 forwarding is enabled
   - Check audio device permissions: `ls -la /dev/snd`
   - Verify environment file (.env) is properly configured

### Docker Troubleshooting

#### GUI Not Displaying
```bash
# Linux: Enable X11 forwarding
xhost +local:docker

# Check DISPLAY variable
echo $DISPLAY

# Test X11 access
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro alpine sh -c "apk add --no-cache xeyes && xeyes"
```

#### Audio Not Working
```bash
# Check audio devices
ls -la /dev/snd

# Verify Docker has audio access
docker run --rm --device /dev/snd -it alpine sh -c "apk add --no-cache alsa-utils && arecord -l"
```

#### Container Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check container logs
docker-compose logs azure-whisper-client
```

### Detailed Troubleshooting

For comprehensive troubleshooting information, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Getting Help

- Check the logs for detailed error messages
- Run `python test_migration.py` to validate your setup
- Review the test files for usage examples
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting guide

## 📚 Additional Documentation

- **[DEVELOPER_DOCS.md](DEVELOPER_DOCS.md)**: Comprehensive developer guide and architecture documentation
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Detailed troubleshooting guide for common issues
- **[MAINTENANCE.md](MAINTENANCE.md)**: Maintenance procedures and best practices
- **[refactor.md](refactor.md)**: Complete refactoring checklist and progress tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass with `python -m pytest tests/ -v`
5. Follow code quality standards with `black .` and `flake8 .`
6. Update documentation as needed
7. Submit a pull request

## 📚 Development Setup

For development work:

### Local Development
```bash
# Install development dependencies
pip install pytest black flake8 coverage

# Run tests
python -m pytest tests/ -v

# Check code quality
black .
flake8 .

# Generate coverage report
coverage run -m pytest tests/
coverage report
```

### Docker Development
```bash
# Development environment with hot-reload
docker-compose --profile dev up --build azure-whisper-client-dev

# Run tests in container
docker-compose run azure-whisper-client python -m pytest tests/ -v

# Code quality checks in container
docker-compose run azure-whisper-client black --check .
docker-compose run azure-whisper-client flake8 .

# Access development container shell
docker-compose run azure-whisper-client bash
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
