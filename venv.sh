#!/bin/bash
# To activate the venv in your current shell, run: source venv.sh

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If arguments are given, run the Python file inside the venv
if [ $# -gt 0 ]; then
  python "$@"
fi