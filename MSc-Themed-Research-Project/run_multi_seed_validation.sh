#!/bin/bash

# Multi-Seed Validation for Consolidation-Only Ablation
# Validates that 93.48% accuracy is reproducible across different data splits

echo "🔬 Starting MULTI-SEED VALIDATION: Consolidation Only"
echo "🎯 Testing reproducibility of 93.48% accuracy breakthrough"
echo "⏱️  Expected time: ~50 minutes total"

# Ensure conda environment is activated
eval "$(conda shell.bash hook)"
conda activate flag_classification

# Set PYTHONPATH to include the project root
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Export MKL setting for compatibility
export KMP_DUPLICATE_LIB_OK=TRUE

# Navigate to project directory
cd MSc-Themed-Research-Project

echo ""
echo "📊 VALIDATION PLAN:"
echo "   Seed 42:  ✅ COMPLETED (93.48% accuracy, 67.78% Macro F1)"
echo "   Seed 123: 🔄 RUNNING..."
echo "   Seed 456: ⏳ PENDING"
echo ""

# Run Seed 123
echo "🚀 Running Consolidation-Only with Seed 123..."
echo "📅 Start time: $(date)"

python flag_classification_adaptation/train_rs5m_ablation_consolidation_only.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --epochs 20 \
    --batch-size 8 \
    --lr 1e-4 \
    --num-workers 4 \
    --seed 123

echo ""
echo "✅ Seed 123 complete!"
echo "📅 Time: $(date)"
echo ""

# Run Seed 456
echo "🚀 Running Consolidation-Only with Seed 456..."
echo "📅 Start time: $(date)"

python flag_classification_adaptation/train_rs5m_ablation_consolidation_only.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --epochs 20 \
    --batch-size 8 \
    --lr 1e-4 \
    --num-workers 4 \
    --seed 456

echo ""
echo "✅ Seed 456 complete!"
echo "📅 End time: $(date)"
echo ""

echo "🎉 MULTI-SEED VALIDATION COMPLETE!"
echo "📊 Analyzing results across all seeds..."

# Run analysis script
python flag_classification_adaptation/analyze_multi_seed_results.py

echo ""
echo "📈 Next step: Review multi-seed analysis for breakthrough validation"