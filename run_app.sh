#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Auto-detect conda
CONDA_CMD="$(command -v conda || true)"
if [ -z "$CONDA_CMD" ] && [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -z "$CONDA_CMD" ] && [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -n "$CONDA_CMD" ]; then
    # conda is on PATH already, good
    :
else
    echo "Conda not found. Install Miniconda or Anaconda first."
    exit 1
fi

ENV_NAME="${CONDA_DEFAULT_ENV:-voiceTyping}"

if conda env list | grep -q "$ENV_NAME"; then
    conda activate "$ENV_NAME"
else
    echo "Environment '$ENV_NAME' not found. Create it with: conda create -n $ENV_NAME python=3.11"
    exit 1
fi

python app.py