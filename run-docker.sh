#!/bin/bash

# Azure OpenAI Whisper Client - Docker Runner Script
# This script provides an easy way to run the containerized application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if environment file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning "No .env file found. Creating from template..."
        if [ -f .env.sample ]; then
            cp .env.sample .env
            print_warning "Please edit .env with your Azure OpenAI credentials before running the application."
            return 1
        else
            print_error ".env.sample not found. Please create .env file manually."
            exit 1
        fi
    fi
    return 0
}

# Enable GUI access (Linux/macOS)
enable_gui_access() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Enabling X11 access for GUI..."
        xhost +local:docker > /dev/null 2>&1 || print_warning "Could not enable X11 access. GUI may not work."
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "macOS detected. Make sure XQuartz is running and configured for network connections."
        if ! command -v xhost &> /dev/null; then
            print_warning "xhost not found. Install XQuartz for GUI support."
        fi
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  run         Run the application (default)"
    echo "  dev         Run in development mode with hot-reload"
    echo "  build       Build the Docker image"
    echo "  stop        Stop the running container"
    echo "  logs        Show application logs"
    echo "  shell       Open a shell in the container"
    echo "  test        Run tests in container"
    echo "  clean       Stop and remove containers and images"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Run the application"
    echo "  $0 dev          # Run in development mode"
    echo "  $0 logs         # View logs"
    echo "  $0 clean        # Clean up Docker resources"
}

# Main execution
main() {
    local command="${1:-run}"
    
    case $command in
        "run")
            print_status "Starting Azure OpenAI Whisper Client..."
            check_docker
            if check_env_file; then
                enable_gui_access
                docker compose up --build
            else
                print_error "Please configure .env file first."
                exit 1
            fi
            ;;
        "dev")
            print_status "Starting development environment..."
            check_docker
            if check_env_file; then
                enable_gui_access
                docker compose --profile dev up --build azure-whisper-client-dev
            else
                print_error "Please configure .env file first."
                exit 1
            fi
            ;;
        "build")
            print_status "Building Docker image..."
            check_docker
            docker compose build
            ;;
        "stop")
            print_status "Stopping containers..."
            docker compose down
            ;;
        "logs")
            print_status "Showing application logs..."
            docker compose logs -f azure-whisper-client
            ;;
        "shell")
            print_status "Opening shell in container..."
            docker compose run --rm azure-whisper-client bash
            ;;
        "test")
            print_status "Running tests..."
            docker compose run --rm azure-whisper-client python -m pytest tests/ -v
            ;;
        "clean")
            print_warning "Cleaning up Docker resources..."
            docker compose down -v
            docker system prune -f
            print_status "Cleanup complete."
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"