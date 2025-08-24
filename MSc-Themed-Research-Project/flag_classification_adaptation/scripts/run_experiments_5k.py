#!/usr/bin/env python3
"""
Quick test script to compare different loss configurations
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

experiments = [
    {
        "name": "standard_ce",
        "description": "Standard Cross-Entropy (no weights)",
        "command": """python train_minimal_mps.py \\
    --clean \\
    --trainer CoCoOp \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --dataset-config-file configs/datasets/niflags_v2.yaml \\
    --output-dir experiments/5k_standard_ce \\
    TRAINER.COCOOP.PREC fp32 \\
    DATALOADER.NUM_WORKERS 0 \\
    OPTIM.MAX_EPOCH 30 \\
    DATASET.NAME NIFlagsV2 \\
    LOSS.USE_WEIGHTS False"""
    },
    {
        "name": "weighted_ce",
        "description": "Weighted Cross-Entropy",
        "command": """python train_minimal_mps.py \\
    --clean \\
    --trainer CoCoOp \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --dataset-config-file configs/datasets/niflags_v2.yaml \\
    --output-dir experiments/5k_weighted_ce \\
    TRAINER.COCOOP.PREC fp32 \\
    DATALOADER.NUM_WORKERS 0 \\
    OPTIM.MAX_EPOCH 30 \\
    DATASET.NAME NIFlagsV2 \\
    LOSS.USE_WEIGHTS True"""
    },
    {
        "name": "vit_model",
        "description": "ViT-B/32 instead of RN50",
        "command": """python train_minimal_mps.py \\
    --clean \\
    --trainer CoCoOp \\
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \\
    --dataset-config-file configs/datasets/niflags_v2.yaml \\
    --output-dir experiments/5k_vit_b32 \\
    TRAINER.COCOOP.PREC fp32 \\
    DATALOADER.NUM_WORKERS 0 \\
    OPTIM.MAX_EPOCH 30 \\
    DATASET.NAME NIFlagsV2 \\
    MODEL.BACKBONE.NAME ViT-B/32"""
    }
]

print("\n" + "="*60)
print("🔬 EXPERIMENT CONFIGURATIONS")
print("="*60)

for i, exp in enumerate(experiments, 1):
    print(f"\n{i}. {exp['name'].upper()}")
    print(f"   {exp['description']}")
    print(f"\n   Command:")
    print(f"   {exp['command']}")
    print()

print("\n" + "="*60)
print("💡 RECOMMENDATIONS")
print("="*60)
print("1. Start with standard_ce to establish baseline")
print("2. Then try weighted_ce to see if it helps")
print("3. If performance is poor, try ViT-B/32 model")
print("4. Monitor category-level accuracy, not just overall")
