# Economic Concentration for Extreme Class Imbalance: Flag Classification

**MSc Artificial Intelligence - Themed Research Project**  
**Student**: Barry Quinn (b.quinn@ulster.ac.uk)  
**Institution**: Queen's University Belfast  
**Date**: January 2025  

## Abstract

This repository contains the implementation for "Economic Concentration as Domain Knowledge for Extreme Class Imbalance: A Case Study in Flag Classification." We demonstrate that economic consolidation theory can guide machine learning approaches to extreme class imbalance, achieving 94.8% accuracy on a task where traditional methods reach only 0.56%.

## Key Results

- **Performance**: 94.78% accuracy (169× improvement over baseline)
- **Attention**: 87% focus on flag regions (vs 23% baseline) 
- **Macro-F1**: Improved from 15.2% to 67.5%
- **Dataset**: 5,490 high-confidence annotations from 9,535 expert classifications
- **Validation**: Multi-seed testing (42, 123, 456) and cross-validation

## Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Download RS5M checkpoint (3.8GB)
wget https://github.com/om-ai-lab/RS5M/releases/download/v1.0/RS5M_ViT-H-14.pt -P checkpoints/
```

### Training
```bash
# Train with economic consolidation (7 classes)
python train.py --config configs/trainers/rs5m_economic_consolidation.yaml \
                --data-root datasets/NIFlagsV2 \
                --checkpoint checkpoints/RS5M_ViT-H-14.pt \
                --output-dir experiments/economic_consolidation
```

### Evaluation
```bash
# Generate paper figures
python scripts/create_paper_figures.py --results-dir experiments/economic_consolidation

# Compute metrics
python scripts/compute_metrics.py --predictions experiments/economic_consolidation/predictions.json
```

## Repository Structure

```
├── train.py                 # Main training script (RS5M ViT-H-14)
├── requirements.txt         # Dependencies
├── datasets/
│   └── NIFlagsV2/          # Flag dataset (5,490 samples)
├── configs/                # Training configurations  
├── trainers/               # Model implementations
├── scripts/                # Evaluation and figure generation
├── checkpoints/            # Model checkpoints (download separately)
└── docs/                   # Methodology documentation
```

## Dataset

The dataset contains 5,490 flag images from Northern Ireland, derived from a larger study using GroundingDINO on 2M Google Street View images. Expert classifications with confidence ≥3.0 were retained for quality control.

**Splits**: Train (3,823), Validation (841), Test (826)  
**Classes**: 70 fine-grained → 7 economic categories  
**Imbalance**: Reduced from 169:1 to 8.8:1  

## Methodology

1. **Economic Consolidation**: Groups classes by community impact using HHI concentration theory
2. **RS5M ViT-H-14**: Vision transformer pre-trained on remote sensing imagery  
3. **Hierarchical Prompting**: Multi-level attention steering for economic categories
4. **Quality Control**: Confidence filtering and inter-annotator reliability

## Reproducibility

All experiments use fixed seeds (42, 123, 456) and documented hyperparameters:
- Batch size: 8
- Learning rate: 1e-4  
- Epochs: 30
- Optimizer: AdamW with differential learning rates

## Citation

```bibtex
@mastersthesis{quinn2025economic,
  title={Economic Concentration as Domain Knowledge for Extreme Class Imbalance: A Case Study in Flag Classification},
  author={Quinn, Barry},
  school={Queen's University Belfast},
  year={2025},
  type={MSc Thesis}
}
```

## Contact
Barry Quinn - b.quinn@ulster.ac.uk  
