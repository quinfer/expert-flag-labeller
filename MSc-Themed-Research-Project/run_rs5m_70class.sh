#!/bin/bash
# RS5M ViT-H-14 Fine-tuning on Original 70-Class Dataset
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
EXP_DIR="flag_classification_adaptation/experiments/rs5m_70class_original_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXP_DIR"

echo "🚀 Starting RS5M ViT-H-14 fine-tuning on 70-class original dataset..."
echo "📁 Output directory: $EXP_DIR"
echo "📊 Dataset: 70-class original (before consolidation)"
echo "🎯 Expected performance: 25-35% accuracy (vs 18% CoCoOp baseline)"
echo ""

# Run fine-tuning with original classes
python flag_classification_adaptation/train_rs5m_finetune.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR" \
    --epochs 30 \
    --batch-size 4 \
    --lr 1e-4 \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --eval-freq 5 \
    --seed 42 \
    --use-original-classes \
    2>&1 | tee "$EXP_DIR/training.log"

echo ""
echo "🎉 Training complete! Results in: $EXP_DIR"
echo "📊 Check best_results.json for final metrics"
echo "📈 Check training_log.json for training progress"
echo ""
echo "📋 Performance Comparison:"
echo "  CoCoOp (70-class): 18.0% accuracy"
echo "  RS5M (16-class):   72.63% accuracy" 
echo "  RS5M (70-class):   [CHECK RESULTS] accuracy"