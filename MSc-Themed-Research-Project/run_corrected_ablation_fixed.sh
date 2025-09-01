#!/bin/bash

# Corrected Ablation Study - Fixed Version
# Tests economic consolidation vs traditional oversampling techniques

echo "🔬 Starting CORRECTED ABLATION STUDY (FIXED VERSION)"
echo "📊 Testing: Economic consolidation vs oversampling techniques"
echo "🎯 Hypothesis: Oversampling techniques are counterproductive"
echo "⏱️  Expected total time: ~6-8 hours"
echo ""

# Set up environment
cd "$(dirname "$0")"
export PYTHONPATH="$PYTHONPATH:$(pwd)"
export KMP_DUPLICATE_LIB_OK=TRUE

# Activate the correct conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate flag_classification

# Create output directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="flag_classification_adaptation/experiments/corrected_ablation_fixed_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

# Log file
LOG_FILE="corrected_ablation_fixed_${TIMESTAMP}.log"

echo "📁 Output directory: $OUTPUT_DIR"
echo "📝 Log file: $LOG_FILE"
echo ""

# Run the ablation study with nohup for persistence
nohup python flag_classification_adaptation/train_rs5m_oversampling_ablation.py \
    --data-root "data" \
    --output-dir "$OUTPUT_DIR" \
    --epochs 15 \
    --batch-size 8 \
    --seed 42 \
    > "$LOG_FILE" 2>&1 &

# Get the process ID
PID=$!
echo "🚀 Ablation study started with PID: $PID"
echo "📊 Monitor progress: tail -f $LOG_FILE"
echo "⏹️  Stop experiment: kill $PID"
echo ""
echo "🔍 Expected results:"
echo "   1. Consolidation Only: ~94% (best performance)"
echo "   2. Smart Augmentation: ~90% (original multi-strategy)"  
echo "   3. Random Oversampling: <90% (hypothesis: worse)"
echo "   4. SMOTE Oversampling: <85% (hypothesis: worse)"
echo "   5. Class Weights: <85% (hypothesis: worse)"
echo "   6. Focal Loss: ~87% (hypothesis: moderate)"
echo ""
echo "🎉 This will provide final methodological validation for thesis!"
