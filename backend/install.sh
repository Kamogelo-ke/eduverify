# install.sh
#!/bin/bash

# EduVerify Backend Installation Script

echo "Installing EduVerify Backend Dependencies..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# For development environment
if [ "$1" == "--dev" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Download AI models
echo "Downloading AI models..."
python scripts/download_models.py

# Setup pre-commit hooks
if [ "$1" == "--dev" ]; then
    pre-commit install
fi

echo "Installation complete!"