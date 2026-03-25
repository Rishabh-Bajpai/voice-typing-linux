#!/bin/bash

# Configuration - update these for your machine
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_PATH="$HOME/miniconda3"
ENV_NAME="voiceTyping"

# Navigate to project directory
cd "$PROJECT_DIR"

# Initialize conda
if [ ! -f "$CONDA_PATH/etc/profile.d/conda.sh" ]; then
  echo "Could not find conda.sh at $CONDA_PATH/etc/profile.d/conda.sh"
  exit 1
fi

source "$CONDA_PATH/etc/profile.d/conda.sh"

# Activate environment and run the app
conda activate "$ENV_NAME"
python app.py
