#!/bin/bash

# Quick test of ablation study setup
echo "🧪 Testing Oversampling Ablation Study Setup"
echo "============================================="

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate flag_classification

# Set environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export KMP_DUPLICATE_LIB_OK=TRUE

# Navigate to project directory
cd /Users/quinference/Documents/expert-flag-labeler/MSc-Themed-Research-Project

echo "📋 Checking requirements..."

# Check if checkpoint exists
if [ -f "final_code/checkpoints/RS5M_ViT-H-14.pt" ]; then
    echo "✅ RS5M checkpoint found"
else
    echo "❌ RS5M checkpoint missing: final_code/checkpoints/RS5M_ViT-H-14.pt"
fi

# Check if dataset exists
if [ -d "data" ]; then
    echo "✅ Data directory found"
else
    echo "❌ Data directory missing"
fi

# Check if dataset classes exist
if [ -f "flag_classification_adaptation/datasets/ni_flags_super_consolidated.py" ]; then
    echo "✅ Super-consolidated dataset found"
else
    echo "❌ Super-consolidated dataset missing"
fi

echo ""
echo "🧪 Testing script syntax..."
python -m py_compile flag_classification_adaptation/train_rs5m_oversampling_ablation.py

if [ $? -eq 0 ]; then
    echo "✅ Script compiles successfully"
else
    echo "❌ Script has syntax errors"
    exit 1
fi

echo ""
echo "🔬 Testing imports..."
python -c "
import sys
sys.path.append('.')
try:
    from flag_classification_adaptation.datasets.ni_flags_super_consolidated import NIFlagsSuperConsolidated
    print('✅ Dataset import successful')
except Exception as e:
    print(f'❌ Dataset import failed: {e}')

try:
    import torch
    import open_clip
    from imblearn.over_sampling import RandomOverSampler, SMOTE
    print('✅ All required packages available')
except Exception as e:
    print(f'❌ Missing packages: {e}')
"

echo ""
echo "🎯 Ready to run ablation study!"
echo ""
echo "To start the experiment:"
echo "1. Using screen (recommended):"
echo "   screen -S ablation"
echo "   ./run_ablation_persistent.sh"
echo "   # Press Ctrl+A, then D to detach"
echo ""
echo "2. Using nohup:"
echo "   ./run_with_nohup.sh"
echo ""
echo "Expected runtime: ~6-8 hours"
echo "Expected configurations: 6 different ablations"
