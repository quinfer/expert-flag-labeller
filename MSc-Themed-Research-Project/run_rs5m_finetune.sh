#!/bin/bash
# RS5M ViT-H-14 Fine-tuning Script
# Run this from the expert-flag-labeler directory

set -e

# Navigate to project root
cd MSc-Themed-Research-Project

# Initialize conda for bash scripts
eval "$(conda shell.bash hook)"

# Activate conda environment
conda activate flag_classification

# Set environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export KMP_DUPLICATE_LIB_OK=TRUE

# Create output directory
EXP_DIR="flag_classification_adaptation/experiments/rs5m_finetune_consolidated_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXP_DIR"

echo "🚀 Starting RS5M ViT-H-14 fine-tuning..."
echo "📁 Output directory: $EXP_DIR"
echo "📊 Dataset: 16-class consolidated"
echo "🎯 Expected improvement: 1.96% → 40-60% accuracy"
echo ""

# Run fine-tuning
python flag_classification_adaptation/train_rs5m_finetune.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR" \
    --epochs 50 \
    --batch-size 4 \
    --lr 1e-4 \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --eval-freq 5 \
    --seed 42 \
    2>&1 | tee "$EXP_DIR/training.log"

echo ""
echo "🎉 Training complete! Results in: $EXP_DIR"
echo "📊 Check best_results.json for final metrics"
echo "📈 Check training_log.json for training progress"