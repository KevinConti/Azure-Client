# Azure OpenAI Whisper Client - Docker Runner Script (Windows PowerShell)
# This script provides an easy way to run the containerized application on Windows

param(
    [Parameter(Position=0)]
    [string]$Command = "run"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Docker is running
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    }
}

# Check if environment file exists
function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Warning "No .env file found. Creating from template..."
        if (Test-Path ".env.sample") {
            Copy-Item ".env.sample" ".env"
            Write-Warning "Please edit .env with your Azure OpenAI credentials before running the application."
            return $false
        }
        else {
            Write-Error ".env.sample not found. Please create .env file manually."
            exit 1
        }
    }
    return $true
}

# Enable GUI access (Windows)
function Enable-GuiAccess {
    Write-Status "Windows detected. Make sure you have an X server running (VcXsrv, Xming, or X410)."
    Write-Status "For GUI support, ensure your X server is configured to allow connections."
    Write-Warning "If you don't have an X server installed, the GUI features won't work."
    Write-Status "Recommended: Install VcXsrv or X410 from Microsoft Store."
}

# Show usage information
function Show-Usage {
    Write-Host "Usage: .\run-docker.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  run         Run the application (default)"
    Write-Host "  dev         Run in development mode with hot-reload"
    Write-Host "  build       Build the Docker image"
    Write-Host "  stop        Stop the running container"
    Write-Host "  logs        Show application logs"
    Write-Host "  shell       Open a shell in the container"
    Write-Host "  test        Run tests in container"
    Write-Host "  clean       Stop and remove containers and images"
    Write-Host "  help        Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\run-docker.ps1              # Run the application"
    Write-Host "  .\run-docker.ps1 dev          # Run in development mode"
    Write-Host "  .\run-docker.ps1 logs         # View logs"
    Write-Host "  .\run-docker.ps1 clean        # Clean up Docker resources"
}

# Main execution logic
switch ($Command.ToLower()) {
    "run" {
        Write-Status "Starting Azure OpenAI Whisper Client..."
        Test-Docker
        if (Test-EnvFile) {
            Enable-GuiAccess
            docker compose up --build
        }
        else {
            Write-Error "Please configure .env file first."
            exit 1
        }
    }
    "dev" {
        Write-Status "Starting development environment..."
        Test-Docker
        if (Test-EnvFile) {
            Enable-GuiAccess
            docker compose --profile dev up --build azure-whisper-client-dev
        }
        else {
            Write-Error "Please configure .env file first."
            exit 1
        }
    }
    "build" {
        Write-Status "Building Docker image..."
        Test-Docker
        docker compose build
    }
    "stop" {
        Write-Status "Stopping containers..."
        docker compose down
    }
    "logs" {
        Write-Status "Showing application logs..."
        docker compose logs -f azure-whisper-client
    }
    "shell" {
        Write-Status "Opening shell in container..."
        docker compose run --rm azure-whisper-client bash
    }
    "test" {
        Write-Status "Running tests..."
        docker compose run --rm azure-whisper-client python -m pytest tests/ -v
    }
    "clean" {
        Write-Warning "Cleaning up Docker resources..."
        docker compose down -v
        docker system prune -f
        Write-Status "Cleanup complete."
    }
    { $_ -in @("help", "--help", "-h") } {
        Show-Usage
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Usage
        exit 1
    }
}