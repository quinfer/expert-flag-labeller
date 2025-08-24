#!/bin/bash
# Manual RS5M ViT-H-14 Zero-shot Evaluation Script
# Run this from the expert-flag-labeler directory

set -e

# Navigate to project root
#cd MSc-Themed-Research-Project

# Activate conda environment
conda activate flag_classification

# Set environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export KMP_DUPLICATE_LIB_OK=TRUE

# Create output directory
EXP_DIR="flag_classification_adaptation/experiments/author_vith14_consolidated_zeroshot"
mkdir -p "$EXP_DIR"

# Run the evaluation
python flag_classification_adaptation/scripts/eval_rs5m_zeroshot_dataset.py \
    --data-root data \
    --ckpt final_code/checkpoints/RS5M_ViT-H-14.pt \
    --out-dir "$EXP_DIR" \
    2>&1 | tee "$EXP_DIR/run.log"

echo "Evaluation complete. Results in: $EXP_DIR"