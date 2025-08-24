#!/bin/bash

# Hierarchical Prompting for RS5M Flag Classification (FIXED)
# Uses the proven working RS5M approach + proper hierarchical prompting

set -e

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate flag_classification

# Set environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export KMP_DUPLICATE_LIB_OK=TRUE

# Create experiment directory
EXP_DIR="MSc-Themed-Research-Project/flag_classification_adaptation/experiments"
mkdir -p "$EXP_DIR"

echo "🚀 Starting Fixed Hierarchical Prompting Experiment"
echo "📊 Using proven RS5M approach + hierarchical prompts"
echo "🎯 Target: Beat 72.63% baseline with hierarchical understanding"
echo "=" * 80

# Run fixed hierarchical prompting experiment
python MSc-Themed-Research-Project/flag_classification_adaptation/train_rs5m_hierarchical_fixed.py \
    --data-root MSc-Themed-Research-Project/data \
    --checkpoint MSc-Themed-Research-Project/final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR" \
    --epochs 25 \
    --batch-size 4 \
    --lr 1e-4 \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --eval-freq 5 \
    --seed 42

echo "✅ Fixed Hierarchical Prompting Experiment Complete!"