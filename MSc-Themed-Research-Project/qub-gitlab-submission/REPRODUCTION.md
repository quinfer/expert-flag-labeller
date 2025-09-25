# Reproduction Instructions

## Quick Start

### 1. Environment Setup
```bash
# Create conda environment
conda create -n flag_classification python=3.9
conda activate flag_classification

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Model Checkpoint
```bash
# Download RS5M ViT-H-14 (3.8GB)
wget https://github.com/om-ai-lab/RS5M/releases/download/v1.0/RS5M_ViT-H-14.pt
mv RS5M_ViT-H-14.pt checkpoints/
```

### 3. Reproduce Paper Results

#### Main Result (94.78% accuracy)
```bash
python train_economic_consolidation.py --seed 42 --output-dir results/seed_42
```

#### Multi-seed Validation  
```bash
python train_economic_consolidation.py --seed 42 --output-dir results/seed_42
python train_economic_consolidation.py --seed 123 --output-dir results/seed_123  
python train_economic_consolidation.py --seed 456 --output-dir results/seed_456
```

#### Compute Aggregated Metrics
```bash
python scripts/compute_metrics.py --results-dir results/
```

### 4. Generate Paper Figures
```bash
python scripts/create_paper_figures.py --results-dir results/ --output-dir figures/
```

## Expected Results

### Performance Metrics
- **Accuracy**: 94.78% (±0.22% across seeds)
- **Macro-F1**: 67.45% 
- **Baseline**: 0.56% accuracy (169× improvement)

### Dataset Validation
- **Total Samples**: 5,490 (after confidence filtering ≥3.0)
- **Original Classifications**: 9,535 expert annotations
- **Unique Images**: 3,354
- **Quality Control**: High-confidence annotations only

### Attention Analysis
- **Baseline Attention**: 23% on flag regions
- **Consolidated Attention**: 87% on flag regions  
- **Mechanism**: Structural dominance reduction

## Troubleshooting

### Common Issues
1. **GPU Memory**: Reduce batch size to 4 if OOM errors
2. **MPS Issues**: Set `PYTORCH_ENABLE_MPS_FALLBACK=1` on Apple Silicon
3. **Missing Checkpoint**: Download RS5M checkpoint as shown above

### Verification
Run the test script to verify setup:
```bash
python test_setup.py
```

Expected output should show dataset sizes matching paper claims.
