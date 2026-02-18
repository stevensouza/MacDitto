#!/bin/bash
# MacDitto Flask Web Interface Startup Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment should be used
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set Flask environment variables
export FLASK_APP=macditto.app
export FLASK_ENV=development
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "Starting MacDitto Web Interface..."
echo "Access at: http://localhost:5001"
echo "Press Ctrl+C to stop"
echo ""

# Run Flask app
python3 -m macditto.app
