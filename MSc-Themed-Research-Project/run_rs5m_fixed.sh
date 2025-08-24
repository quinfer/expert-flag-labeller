#!/bin/bash

# FIXED RS5M Flag Classification Training
# Addresses critical class mapping inconsistency and class imbalance

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

echo "🔧 Starting FIXED RS5M Training"
echo "🎯 Fixes Applied:"
echo "   ✅ Class mapping consistency"
echo "   ✅ Balanced sampling"
echo "   ✅ Class-weighted loss"
echo "   ✅ Fixed random seed"
echo "   ✅ Comprehensive evaluation"
echo "🚀 This will give us REAL results!"
echo "=" * 80

# Run FIXED RS5M training
python MSc-Themed-Research-Project/flag_classification_adaptation/train_rs5m_fixed.py \
    --data-root MSc-Themed-Research-Project/data \
    --checkpoint MSc-Themed-Research-Project/final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR" \
    --epochs 25 \
    --batch-size 4 \
    --lr 1e-4 \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --use-balanced-sampling \
    --use-class-weights \
    --eval-freq 5 \
    --seed 42

echo "✅ FIXED RS5M Training Complete!"
echo "🎉 Check results - this should be REAL performance!"