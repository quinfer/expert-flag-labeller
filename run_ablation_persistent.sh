#!/bin/bash

# Ablation Study - Persistent Session Runner
echo "🔬 Starting Oversampling Ablation Study in Screen Session"
echo "📅 Start time: $(date)"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate flag_classification

# Set environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export KMP_DUPLICATE_LIB_OK=TRUE

# Navigate to project directory
cd /Users/quinference/Documents/expert-flag-labeler/MSc-Themed-Research-Project

echo "🚀 Running ablation study..."
echo "⏱️  Expected runtime: ~6-8 hours"
echo "📊 Will test 5-6 different configurations"

# Run the ablation study
python flag_classification_adaptation/train_rs5m_oversampling_ablation.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --epochs 15 \
    --batch-size 8 \
    --lr 1e-4 \
    --output-dir flag_classification_adaptation/experiments/oversampling_ablation_$(date +%Y%m%d_%H%M%S) \
    --seed 42

echo "✅ Ablation study complete!"
echo "📅 End time: $(date)"
