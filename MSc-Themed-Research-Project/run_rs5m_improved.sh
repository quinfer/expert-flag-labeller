#!/bin/bash

# IMPROVED RS5M Flag Classification Training
# Multiple strategies to handle extreme class imbalance:
# 1. Economic super-consolidation (16 → 7 classes)
# 2. Smart oversampling with augmentation
# 3. Gentler focal loss
# 4. Improved model architecture

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

echo "🚀 Starting IMPROVED RS5M Training"
echo "🎯 Advanced Strategies for Extreme Class Imbalance:"
echo "   ✅ Economic super-consolidation (16 → 7 classes)"
echo "   ✅ Smart oversampling with data augmentation"
echo "   ✅ Gentler focal loss (less aggressive)"
echo "   ✅ Improved model architecture with dropout"
echo "   ✅ Different learning rates for pretrained vs new layers"
echo "🔬 This should achieve meaningful performance!"
echo "=" * 80

# Run IMPROVED RS5M training
python MSc-Themed-Research-Project/flag_classification_adaptation/train_rs5m_improved.py \
    --data-root MSc-Themed-Research-Project/data \
    --checkpoint MSc-Themed-Research-Project/final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR" \
    --epochs 30 \
    --batch-size 4 \
    --lr 1e-4 \
    --use-super-consolidation \
    --use-oversampling \
    --focal-alpha 0.5 \
    --focal-gamma 1.0 \
    --eval-freq 5 \
    --seed 42

echo "✅ IMPROVED RS5M Training Complete!"
echo "🎉 This should show real learning with multiple balancing strategies!"