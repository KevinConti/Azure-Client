# Troubleshooting Guide

This guide helps resolve common issues you might encounter when using the Azure OpenAI Whisper Client.

## 🔧 Quick Diagnostics

Before diving into specific issues, run these diagnostic commands:

1. **Validate Configuration**:
   ```bash
   python -c "from services.config_service import ConfigService; cs = ConfigService(); print('✅ Valid' if cs.validate_configuration()[0] else '❌ Invalid')"
   ```

2. **Test Application Import**:
   ```bash
   python -c "import main; print('✅ Application imports successfully')"
   ```

3. **Run Migration Tests**:
   ```bash
   python test_migration.py
   ```

4. **Check Dependencies**:
   ```bash
   pip check
   ```

5. **Docker Quick Check**:
   ```bash
   # Check if Docker is running
   docker --version && docker compose version
   
   # Test container build
   ./run-docker.sh build
   
   # Verify environment configuration
   ./run-docker.sh help
   ```

## 🐳 Docker Troubleshooting

### Docker Installation and Setup Issues

#### ❌ Docker Not Found
**Error**: `docker: command not found` or `docker compose: command not found`

**Solution**:
1. **Install Docker**: Visit [docker.com](https://docker.com) to install Docker Desktop
2. **Verify Installation**:
   ```bash
   docker --version
   docker compose version
   ```
3. **Start Docker**: Make sure Docker Desktop is running

#### ❌ Permission Denied (Linux)
**Error**: `permission denied while trying to connect to the Docker daemon`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify access
docker run hello-world
```

### GUI and Display Issues

#### ❌ GUI Not Displaying
**Error**: Application runs but no GUI appears

**Solutions by Operating System**:

**Linux**:
```bash
# Enable X11 forwarding
xhost +local:docker

# Check DISPLAY variable
echo $DISPLAY

# Test X11 connection
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro alpine sh -c "apk add --no-cache xeyes && xeyes"
```

**macOS**:
```bash
# Install XQuartz
brew install --cask xquartz

# Start XQuartz and enable network connections
open -a XQuartz
# In XQuartz preferences: Security tab > "Allow connections from network clients"

# Set DISPLAY variable
export DISPLAY=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}'):0

# Test connection
./run-docker.sh run
```

**Windows**:
```powershell
# Install X server (VcXsrv, Xming, or X410)
# Configure X server to allow connections

# Set DISPLAY variable
$env:DISPLAY = "host.docker.internal:0"

# Run application
./run-docker.sh run
```

### Audio Issues

#### ❌ No Audio Access
**Error**: Audio recording not working in container

**Solution**:
```bash
# Check audio devices
ls -la /dev/snd

# Verify Docker has audio access
docker run --rm --device /dev/snd -it alpine sh -c "apk add --no-cache alsa-utils && arecord -l"

# Run with proper audio permissions
docker compose up  # Already configured in docker-compose.yml
```

#### ❌ Audio Permission Denied
**Error**: `Permission denied: '/dev/snd/controlC0'`

**Solution**:
```bash
# Add user to audio group (Linux)
sudo usermod -aG audio $USER

# Check audio group membership
groups $USER

# Restart Docker container
docker compose restart azure-whisper-client
```

### Container Build and Runtime Issues

#### ❌ Build Fails with SSL Errors
**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
- The Dockerfile includes SSL trust configuration
- If issues persist, check corporate firewall/proxy settings
- Use `--build-arg` to pass proxy settings if needed

#### ❌ Python Dependencies Fail to Install
**Error**: `Failed building wheel for pyaudio`

**Solution**:
- The Dockerfile includes necessary build tools (gcc, python3-dev)
- If issues persist, try building with `--no-cache`:
  ```bash
  docker compose build --no-cache
  ```

#### ❌ Container Memory Issues
**Error**: Container runs out of memory during processing

**Solution**:
```bash
# Check container memory usage
docker stats azure-whisper-client

# Increase Docker memory limits (Docker Desktop settings)
# Or modify docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

### Environment Configuration Issues

#### ❌ Environment Variables Not Loading
**Error**: Configuration validation fails in container

**Solution**:
1. **Check .env file exists**:
   ```bash
   ls -la .env
   ```

2. **Verify .env format**:
   ```bash
   cat .env
   # Should contain:
   # AZURE_OPENAI_WHISPER_API_KEY=your_key
   # No spaces around = signs
   # No quotes needed
   ```

3. **Test environment loading**:
   ```bash
   docker compose run --rm azure-whisper-client env | grep AZURE
   ```

#### ❌ Invalid Azure OpenAI Configuration
**Error**: API calls fail from container

**Solution**:
1. **Test configuration locally first**
2. **Verify network connectivity**:
   ```bash
   docker compose run --rm azure-whisper-client curl -I https://your-resource.openai.azure.com/
   ```
3. **Check API key format and permissions**

### Development and Debugging

#### ❌ Hot Reload Not Working
**Error**: Code changes not reflected in development container

**Solution**:
```bash
# Use development profile
docker compose --profile dev up azure-whisper-client-dev

# Verify volume mounts
docker compose run --rm azure-whisper-client-dev ls -la /app
```

#### ❌ Can't Access Container Shell
**Error**: Need to debug inside container

**Solution**:
```bash
# Access running container
docker compose exec azure-whisper-client bash

# Or start new container with shell
docker compose run --rm azure-whisper-client bash

# Use convenience script
./run-docker.sh shell
```

### Performance Issues

#### ❌ Slow Container Performance
**Error**: Application runs slowly in container

**Solutions**:
1. **Increase Docker resources** (CPU, Memory in Docker Desktop)
2. **Check host system resources**:
   ```bash
   docker stats azure-whisper-client
   htop  # or top
   ```
3. **Optimize Docker settings** for your platform

#### ❌ Large Image Size
**Error**: Docker image too large

**Solution**:
```bash
# Check image size
docker images azure-whisper-client

# Clean up unused images
docker image prune -f

# Use multi-stage builds (future optimization)
```

## 🚨 Common Issues and Solutions

### Configuration Issues

#### ❌ Missing Environment Variables
**Error**: `Configuration validation failed: Missing required environment variables`

**Solution**:
1. Create a `.env` file in the project root:
   ```bash
   python -c "from services.config_service import ConfigService; ConfigService().create_sample_env_file()"
   ```
2. Edit the generated `.env.sample` file with your Azure OpenAI credentials
3. Rename it to `.env`

**Environment Variables Required**:
```env
AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key
AZURE_OPENAI_WHISPER_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_WHISPER_DEPLOYMENT=your_whisper_deployment_name
AZURE_OPENAI_GPT_API_KEY=your_gpt_api_key
AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=your_gpt_deployment_name
```

#### ❌ Invalid API Endpoints
**Error**: `Invalid Azure OpenAI endpoint URL`

**Solution**:
- Ensure endpoints follow the format: `https://your-resource.openai.azure.com/`
- Include the trailing slash (`/`)
- Verify the resource name matches your Azure OpenAI resource

#### ❌ API Key Authentication Failures
**Error**: `Authentication failed` or `401 Unauthorized`

**Solution**:
1. Verify API keys are correct and not expired
2. Check that the API keys match the correct Azure OpenAI resource
3. Ensure the deployment names exist in your Azure OpenAI resource
4. Verify your Azure subscription is active

### Audio Recording Issues

#### ❌ No Microphone Detected
**Error**: `No audio input devices found`

**Solution**:
1. Check microphone is connected and recognized by Windows
2. Verify microphone permissions in Windows Settings
3. Test microphone in other applications
4. Restart the application after connecting microphone

#### ❌ Audio Recording Fails
**Error**: `Failed to start recording` or `PyAudio error`

**Solution**:
1. Close other applications using the microphone
2. Check Windows audio settings:
   - Right-click speaker icon → "Sounds" → "Recording" tab
   - Ensure microphone is enabled and set as default
3. Try different audio devices:
   ```python
   from services.audio_service import AudioService
   service = AudioService()
   devices = service.get_audio_devices()
   print(devices)  # Shows available devices
   ```

#### ❌ Poor Audio Quality
**Symptoms**: Transcription accuracy is low

**Solution**:
1. Check microphone positioning (6-12 inches from mouth)
2. Reduce background noise
3. Verify audio levels in Windows recording settings
4. Test with a different microphone if available

### Transcription Issues

#### ❌ Transcription API Failures
**Error**: `Transcription failed` or `Azure OpenAI API error`

**Solution**:
1. Check Azure OpenAI service status
2. Verify quota limits in Azure portal
3. Ensure audio file is supported format (wav, mp3, m4a, etc.)
4. Check file size limits (< 25MB for Azure OpenAI)

#### ❌ Slow Transcription
**Symptoms**: Transcription takes very long

**Solution**:
1. Check your Azure OpenAI pricing tier and quotas
2. Verify network connectivity
3. Consider shorter audio segments (< 10 minutes)
4. Check Azure OpenAI service region latency

#### ❌ Inaccurate Transcriptions
**Symptoms**: Poor transcription quality

**Solution**:
1. Ensure clear audio with minimal background noise
2. Try specifying language in transcription settings
3. Use higher quality audio formats (wav preferred)
4. Verify speaker distance from microphone

### File Processing Issues

#### ❌ VTT File Import Errors
**Error**: `Invalid VTT file format` or `Failed to parse VTT`

**Solution**:
1. Verify VTT file starts with `WEBVTT` header
2. Check file encoding (should be UTF-8)
3. Validate VTT format with online validators
4. Example valid VTT format:
   ```vtt
   WEBVTT

   00:00:00.000 --> 00:00:05.000
   This is the first subtitle.

   00:00:05.000 --> 00:00:10.000
   This is the second subtitle.
   ```

#### ❌ Audio File Format Issues
**Error**: `Unsupported audio format`

**Solution**:
1. Convert audio to supported formats: wav, mp3, m4a, flac, ogg
2. Use tools like FFmpeg for conversion:
   ```bash
   ffmpeg -i input.format output.wav
   ```
3. Verify file isn't corrupted by playing in media player

### UI Issues

#### ❌ Application Won't Start
**Error**: `Tkinter import error` or UI crashes

**Solution**:
1. Verify Python Tkinter installation:
   ```bash
   python -c "import tkinter; print('✅ Tkinter available')"
   ```
2. On Ubuntu/Debian: `sudo apt-get install python3-tk`
3. On macOS: Install Python from python.org (includes Tkinter)
4. Check display environment on Linux systems

#### ❌ UI Freezing During Processing
**Symptoms**: Interface becomes unresponsive

**Solution**:
1. This is expected during transcription/notes generation
2. Look for progress indicators in the status bar
3. Avoid clicking buttons repeatedly during processing
4. Large files may take several minutes to process

### Import and Dependency Issues

#### ❌ Module Import Errors
**Error**: `ModuleNotFoundError: No module named 'xyz'`

**Solution**:
1. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify virtual environment is activated
3. Check Python version compatibility (3.8+)
4. For development dependencies:
   ```bash
   pip install pytest black flake8 coverage
   ```

#### ❌ Package Version Conflicts
**Error**: `VersionConflict` or dependency warnings

**Solution**:
1. Create fresh virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Update pip: `python -m pip install --upgrade pip`
3. Check for conflicting global packages

## 🔍 Advanced Debugging

### Enable Debug Logging

Add this to the beginning of `main.py` for detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components

Test services independently:
```python
# Test Configuration
from services.config_service import ConfigService
config = ConfigService()
print(config.get_config_summary())

# Test Audio Service
from services.audio_service import AudioService
audio = AudioService()
print(audio.get_audio_devices())

# Test Transcription Service
from services.transcription_service import TranscriptionService
transcription = TranscriptionService()
# Configure with your settings...
```

### Check System Resources

Monitor system performance during processing:
- Task Manager (Windows) or Activity Monitor (macOS)
- Check CPU, memory, and network usage
- Ensure sufficient disk space for temporary files

## 📞 Getting Additional Help

### Before Requesting Support

1. **Check logs**: Look for error messages in the console output
2. **Run diagnostics**: Use the quick diagnostic commands above
3. **Review documentation**: Check README.md and DEVELOPER_DOCS.md
4. **Test with sample data**: Verify with known good audio files

### Reporting Issues

When reporting issues, include:
1. **Environment information**:
   ```bash
   python --version
   pip list | grep -E "(azure|openai|tkinter|pyaudio)"
   ```
2. **Configuration**: Sanitized configuration (without API keys)
3. **Error messages**: Full error traces and logs
4. **Steps to reproduce**: Detailed reproduction steps
5. **Expected vs actual behavior**: Clear description of the issue

### Useful Log Files

- Application logs: Console output
- Test results: `python test_migration.py` output
- Coverage reports: Generated by coverage tools

## 🛠️ Maintenance Commands

Regular maintenance commands for optimal performance:

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run full test suite
python -m pytest tests/ -v

# Check code quality
black .
flake8 .

# Generate coverage report
coverage run -m pytest tests/
coverage report
coverage html  # Generates HTML report
```
