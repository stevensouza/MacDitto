#!/bin/bash
# MacDitto Flask Web Interface Startup Script

# Check if virtual environment should be used
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set Flask environment variables
export FLASK_APP=macditto.app
export FLASK_ENV=development

echo "Starting MacDitto Web Interface..."
echo "Access at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

# Run Flask app
python -m macditto.app
