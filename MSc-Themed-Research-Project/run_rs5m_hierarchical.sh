#!/bin/bash
# RS5M ViT-H-14 Hierarchical Prompting Experiment
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
EXP_DIR="flag_classification_adaptation/experiments/rs5m_hierarchical_prompting_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXP_DIR"

echo "🏗️ Starting RS5M ViT-H-14 Hierarchical Prompting Experiment..."
echo "📁 Output directory: $EXP_DIR"
echo "🎯 Innovation: Multi-level prompts (Category → Flag → Context)"
echo "📊 Expected: 5-10% improvement over baseline RS5M (72.63% → 77-80%)"
echo ""
echo "🏗️ Hierarchical Structure:"
echo "  Level 1: Category (Unionist, Nationalist, Paramilitary, etc.)"
echo "  Level 2: Flag Type (Union Jack, Ulster Banner, Irish Tricolor, etc.)" 
echo "  Level 3: Context (Building mounted, Lamppost mounted, etc.)"
echo ""
echo "🔬 Technical Innovation:"
echo "  - Learnable fusion weights for prompt levels"
echo "  - Economic hierarchy integration"
echo "  - Multi-scale semantic understanding"
echo ""

# Run hierarchical prompting experiment
python flag_classification_adaptation/train_rs5m_hierarchical.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --output-dir "$EXP_DIR" \
    --epochs 20 \
    --batch-size 4 \
    --lr 1e-4 \
    --focal-alpha 0.25 \
    --focal-gamma 2.0 \
    --eval-freq 5 \
    --seed 42 \
    2>&1 | tee "$EXP_DIR/training.log"

echo ""
echo "🎉 Hierarchical training complete! Results in: $EXP_DIR"
echo "📊 Check best_results.json for final metrics"
echo "📈 Check training_log.json for training progress"
echo ""
echo "📋 Expected Performance Comparison:"
echo "  RS5M Baseline (16-class):     72.63% accuracy"
echo "  RS5M Hierarchical (16-class): [CHECK RESULTS] accuracy"
echo "  Expected Improvement:         +5-10 percentage points"
echo ""
echo "🏆 If successful, this represents a novel contribution to hierarchical vision-language models!"