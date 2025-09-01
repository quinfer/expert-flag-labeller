#!/bin/bash

# Context Ablation Study for RS5M Flag Classification
# Tests: Crop vs Crop+Context vs Full+BBox

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

echo "🔬 Starting Context Ablation Study"
echo "📊 Testing: Crop vs Crop+Context vs Full+BBox"
echo "🎯 Goal: Optimize input representation for flag classification"
echo "=" * 80

# Run context ablation study
python MSc-Themed-Research-Project/flag_classification_adaptation/train_rs5m_context_ablation.py \
    --data-root MSc-Themed-Research-Project/data \
    --checkpoint MSc-Themed-Research-Project/final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR/context_ablation_study" \
    --epochs 15 \
    --batch-size 4 \
    --lr 1e-4 \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --eval-freq 5 \
    --seed 42 \
    --context-modes crop crop_context full_bbox

echo "✅ Context Ablation Study Complete!"
echo "📊 Check results in: $EXP_DIR/context_ablation_study/"