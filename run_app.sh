#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Auto-detect conda
CONDA_CMD="$(command -v conda || true)"
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    . "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    . "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -n "$CONDA_CMD" ]; then
    # conda is on PATH (e.g. micromamba, Miniforge, custom installs) — locate conda.sh
    CONDA_BASE="$(conda info --base 2>/dev/null || true)"
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        . "$CONDA_BASE/etc/profile.d/conda.sh"
    else
        echo "Conda found but conda.sh not found. Run: conda shell.bash hook"
        exit 1
    fi
else
    echo "Conda not found. Install Miniconda or Anaconda first."
    exit 1
fi

ENV_NAME="voiceTyping"

if conda env list | grep -q "$ENV_NAME"; then
    conda activate "$ENV_NAME"
else
    echo "Environment '$ENV_NAME' not found. Create it with: conda create -n $ENV_NAME python=3.11"
    exit 1
fi

python app.py