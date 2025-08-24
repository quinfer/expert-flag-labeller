#!/bin/bash

# RS5M Fine-tuning - ABLATION STUDY: Consolidation Only
# Tests ONLY economic super-consolidation (16→7 classes) without other balancing strategies

echo "🔬 Starting ABLATION STUDY: Consolidation Only"
echo "📊 Strategy: Economic super-consolidation (16→7 classes) ONLY"
echo "❌ No oversampling, no focal loss, no weighted sampling"

# Ensure conda environment is activated
eval "$(conda shell.bash hook)"
conda activate flag_classification

# Set PYTHONPATH to include the project root
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Export MKL setting for compatibility
export KMP_DUPLICATE_LIB_OK=TRUE

# Run the consolidation-only ablation
cd MSc-Themed-Research-Project

python flag_classification_adaptation/train_rs5m_ablation_consolidation_only.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --epochs 20 \
    --batch-size 8 \
    --lr 1e-4 \
    --num-workers 4

echo ""
echo "✅ Consolidation-only ablation complete!"
echo "📊 This isolates the contribution of economic super-consolidation"
echo "🔍 Compare results with full improved method (90.22%) to measure consolidation impact"