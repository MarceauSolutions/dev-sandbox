#!/bin/bash
# Start AutoInsure Saver
cd "$(dirname "$0")"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
pip install -r requirements.txt --quiet

# Run the app
echo "Starting AutoInsure Saver on http://localhost:8080"
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
