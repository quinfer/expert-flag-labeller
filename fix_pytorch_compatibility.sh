#!/bin/bash

echo "🔧 Fixing PyTorch compatibility issues..."

# Fix the LR scheduler to avoid PyTorch 2.7 API conflicts
sed -i '' 's/LR_SCHEDULER: "cosine"/LR_SCHEDULER: "single_step"/g' configs/trainers/CoCoOp/rn50.yaml

# Disable warmup to avoid scheduler API issues
sed -i '' 's/WARMUP_EPOCH: 1/WARMUP_EPOCH: 0/g' configs/trainers/CoCoOp/rn50.yaml

echo "✅ PyTorch compatibility fixes applied!"

# Verify the changes
echo "📋 Current config:"
cat configs/trainers/CoCoOp/rn50.yaml