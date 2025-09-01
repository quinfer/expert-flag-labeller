#!/bin/bash

# RS5M Fine-tuning - 16-Class Economic Consolidation Scale-Up Test
# Tests if consolidation principles that achieved 94.57% on 7-class scale to 16-class

echo "🎯 Starting 16-CLASS ECONOMIC CONSOLIDATION SCALE-UP TEST"
echo "📊 Strategy: Apply same economic principles that achieved 94.57% on 7-class"
echo "🔬 Goal: Validate consolidation universality across problem scales"
echo "📈 Baseline: 0.56% (16-class with all strategies failed)"
echo "⏱️  Expected time: ~30 minutes"

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
echo "🚀 Running 16-Class Economic Consolidation Test..."
echo "📅 Start time: $(date)"

python flag_classification_adaptation/train_rs5m_16class_consolidation.py \
    --data-root data \
    --checkpoint final_code/checkpoints/RS5M_ViT-H-14.pt \
    --epochs 20 \
    --batch-size 8 \
    --lr 1e-4 \
    --num-workers 4 \
    --seed 42

echo ""
echo "✅ 16-Class Consolidation Test complete!"
echo "📅 End time: $(date)"
echo ""

echo "🔍 SCALE-UP ANALYSIS:"
echo "   If accuracy >80%: Consolidation scales successfully"
echo "   If accuracy 20-80%: Partial scaling, may need more aggressive consolidation"  
echo "   If accuracy <20%: Consolidation limited to super-consolidated problems"
echo ""
echo "📊 Next: Compare with 7-class results (94.57%) to assess scaling effectiveness"