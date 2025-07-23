#!/bin/bash

# Setup script for Docker Mount Consistency Tester

echo "Setting up Docker Mount Consistency Tester..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker first."
    
    # Provide platform-specific guidance
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo ""
        echo "On macOS:"
        echo "1. Open Docker Desktop application"
        echo "2. Wait for it to fully start (whale icon in menu bar)"
        echo "3. Try running 'docker info' to verify it's working"
        echo ""
        echo "If you're still having issues, try:"
        echo "- Restart Docker Desktop"
        echo "- Check if Docker Desktop is updated"
        echo "- Run: python3 docker_mount_tester.py --test-connection"
    fi
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Make the script executable
chmod +x docker_mount_tester.py

echo "Setup complete!"
echo ""
echo "Testing Docker connection..."
python3 docker_mount_tester.py --test-connection

echo ""
echo "Usage examples:"
echo "  Test Docker connection:"
echo "    python3 docker_mount_tester.py --test-connection"
echo ""
echo "  Run stress test with default settings:"
echo "    python3 docker_mount_tester.py"
echo ""
echo "  Run with custom parameters:"
echo "    python3 docker_mount_tester.py --samples 50 --timeout 10"
echo ""
echo "  Analyze existing report:"
echo "    python3 docker_mount_tester.py --analyze report_file.json"
echo ""
echo "  Save report with custom name:"
echo "    python3 docker_mount_tester.py --output my_test_report.json"