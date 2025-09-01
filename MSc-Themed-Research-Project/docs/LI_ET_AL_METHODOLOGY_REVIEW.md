# Li et al. 2023 Methodology Review: RS5M for Flag Classification

## Paper Context: Ship Classification with Remote Sensing

The Li et al. paper demonstrates using **RS5M (Remote Sensing 5 Million)** pretrained ViT-H/14 models for ship classification. Our goal is to adapt their methodology for Northern Ireland flag classification.

## Key Methodology Components

### 1. Model Architecture: RS5M ViT-H/14
- **Pretrained Model**: ViT-H/14 (Huge variant, 14x14 patch size)
- **Pretraining Dataset**: RS5M - 5 million remote sensing images
- **Checkpoint**: Available via HuggingFace (Zilun/GeoRSCLIP)
- **Size**: ~3.8GB checkpoint file

### 2. Training Framework: Dassl + CoCoOp
Based on the `final_code/` analysis:

**Base Framework**: 
- Uses Dassl (Domain Adaptation Semi-Supervised Learning) framework
- CoCoOp (Conditional Context Optimization) for prompt learning
- CLIP-style vision-language pretraining adaptation

**Key Configuration Parameters** (from `vit_b16_ep100.yaml`):
```yaml
DATALOADER:
  BATCH_SIZE: 16
  NUM_WORKERS: 8

INPUT:
  SIZE: (224, 224)
  INTERPOLATION: "bicubic"
  TRANSFORMS: ["random_resized_crop", "random_flip", "normalize"]

OPTIM:
  NAME: "sgd"
  LR: 0.001
  MAX_EPOCH: 50
  LR_SCHEDULER: "cosine"
  WARMUP_EPOCH: 1
  WARMUP_TYPE: "constant"
  WARMUP_CONS_LR: 1e-5

TRAINER:
  COCOOP:
    N_CTX: 16  # Number of context tokens
    CTX_INIT: True  # Initialize with text
```

### 3. Hierarchical Prompting Strategy
From `cocoop.py` analysis, the paper uses hierarchical prompts:

**Template Structure**:
- Primary: `"a photo of a ship, primary type is [CLASS]"`
- Secondary: `"econdary type is [CLASS]"` 
- Final: `"final type is [CLASS]"`

**For Flag Adaptation**:
- Primary: `"a photo of a flag, category: [National/Fraternal/Proscribed]"`
- Secondary: `"mounted on [lamppost/building/pole], [CLASS]"`
- Specific: `"[Union Jack/Ulster Banner/Irish Tricolor], [CLASS]"`

### 4. Training Procedure

**Data Requirements**:
- Images in standard format (224x224, normalized)
- `classnames.txt` with class labels
- `train.txt`, `val.txt`, `test.txt` with image paths and labels

**Training Process**:
1. Load RS5M ViT-H/14 checkpoint
2. Initialize CoCoOp prompt learner with hierarchical templates
3. Fine-tune on target dataset using SGD optimizer
4. Cosine LR scheduling with warmup
5. Standard data augmentation (random crop, flip, normalize)

### 5. Loss Functions and Metrics

**Standard Setup**:
- Cross-entropy loss (default)
- Top-1 and Top-5 accuracy
- Macro/Micro F1 scores

**For Imbalanced Data** (our case):
- Focal Loss (recommended: α=0.25, γ=1.5-2.5)
- Class-balanced sampling
- Inverse-frequency weighting

## Current Status: Zero-shot Results

**RS5M ViT-H/14 Zero-shot on NI Flags (16-class consolidated)**:
- **Top-1 Accuracy**: 1.96% (7/358 test images)
- **Macro F1**: 0.99%
- **Analysis**: Massive domain gap - remote sensing → flag classification

## Adaptation Strategy for Our Project

### Phase 1: Direct Fine-tuning
1. **Dataset**: Start with 16-class consolidated (`ni_flags_consolidated`)
2. **Architecture**: RS5M ViT-H/14 + CoCoOp prompt learning
3. **Training**: 50 epochs, SGD, cosine LR, focal loss
4. **Evaluation**: Top-1/5 accuracy, macro F1, per-class metrics

### Phase 2: Hierarchical Enhancement
1. **Prompts**: Implement flag-specific hierarchical templates
2. **Multi-stage**: Coarse→fine classification pipeline
3. **Context**: Add mounting context (lamppost, building, etc.)

### Phase 3: Imbalance Mitigation
1. **Loss**: Focal loss with class-balanced sampling
2. **Weights**: Dynamic inverse-frequency weighting
3. **Metrics**: Emphasize macro F1, per-class precision/recall

## Implementation Plan

### Next Steps:
1. **Create RS5M fine-tuning script** - Adapt `train_minimal_mps.py` for RS5M
2. **Configure hierarchical prompts** - Flag-specific template design
3. **Run baseline fine-tuning** - 16-class consolidated dataset
4. **Compare with CoCoOp results** - Validate improvement over prompt-only

### Expected Improvements:
- **Zero-shot**: 1.96% → **Fine-tuned**: 40-60% (based on domain adaptation literature)
- **Domain gap**: RS5M pretraining should provide better visual features than standard CLIP
- **Hierarchical prompts**: Should improve fine-grained flag distinction

## Technical Considerations

### Hardware Requirements:
- **Memory**: ViT-H/14 requires significant VRAM/MPS memory
- **Batch Size**: May need to reduce from 16 to 8 or 4
- **Training Time**: Expect 2-4 hours per 50-epoch run

### Integration with Existing Code:
- **Preserve**: Current `train_minimal_mps.py` workflow
- **Extend**: Add RS5M checkpoint loading
- **Maintain**: Existing experiment logging and metrics

This methodology review provides the foundation for implementing RS5M adaptation for flag classification, building on the Li et al. ship classification approach.