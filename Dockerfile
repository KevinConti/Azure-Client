# Use Python 3.12 with Ubuntu base for GUI support
FROM python:3.12-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0

# Install system dependencies for GUI and audio
RUN apt-get update && apt-get install -y \
    python3-tk \
    portaudio19-dev \
    libportaudio2 \
    libasound2-dev \
    xvfb \
    x11-apps \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose any ports if needed (none for this desktop app)
# EXPOSE 8080

# Set default command
CMD ["python", "main.py"]