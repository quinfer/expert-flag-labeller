# Figure 1b Diagnostic Workflow

## Overview

This workflow generates Figure 1b (type-specific attention analysis) for the MSc thesis. It involves:
1. **Dumping predictions** from trained checkpoints to Parquet files
2. **Generating diagnostic plots** with attention roll-outs, on-mask metrics, and concentration statistics

## Prerequisites

1. **Conda environment**: Ensure `flag_classification` environment is activated
2. **Dependencies**: `open-clip-torch`, `torch`, `pandas`, `matplotlib`, `pillow`, `tqdm`
3. **Checkpoints**: RS5M backbone and trained model checkpoints must exist
4. **Test data**: `index_test.csv` with test images and flag types

## Step 1: Dump Model Predictions

### Real Inference (Recommended)
```bash
# Activate conda environment
conda activate flag_classification

# Run real inference with MPS acceleration
python MSc-Themed-Research-Project/scripts/dump_preds_from_checkpoints.py \
  --config MSc-Themed-Research-Project/configs/attention.yaml
```

**MPS Acceleration Features**:
- **10-40x speedup** over CPU on Apple Silicon
- **Optimized batch sizes**: 8 for ViT-H/14 on MPS (vs 16 on CUDA)
- **Memory management**: Automatic cache clearing between batches
- **Environment optimizations**: OpenMP fixes and MPS fallback enabled

This will:
- Load RS5M backbone from `MSc-Themed-Research-Project/final_code/checkpoints/RS5M_ViT-H-14.pt`
- Load trained models:
  - **Before**: 16-class consolidation model (`rs5m_16class_consolidation_seed42_20250814_201544/best_model.pt`)
  - **After**: 7-class consolidation models (3 seeds: `rs5m_ablation_consolidation_only_*/best_model.pt`)
- Run inference on test images from `index_test.csv`
- Map predictions to TYPE_ORDER categories:
  - Unionist – Union Jack
  - Unionist – Ulster Banner
  - Nationalist – Tricolour
  - Cultural – Orange Order
  - Paramilitary (UDA/UVF/UFF/YCV)
- Output Parquet files:
  - `outputs/before/rs5m_16class_consolidation_seed42_20250814_201544/preds.parquet`
  - `outputs/after/rs5m_ablation_consolidation_only_*/preds.parquet` (3 files)

### Fallback Mode (Testing Only)
```bash
# For testing without real inference
python MSc-Themed-Research-Project/scripts/dump_preds_from_checkpoints.py \
  --config MSc-Themed-Research-Project/configs/attention.yaml \
  --copy-true-as-pred
```

## Step 2: Generate Figure 1b

```bash
# Generate diagnostic figure with attention analysis
python MSc-Themed-Research-Project/scripts/figure1b_diagnostic.py \
  --config MSc-Themed-Research-Project/configs/attention.yaml
```

This will:
- Load predictions from Step 1 Parquet files
- Compute per-type on-mask attention metrics (before/after)
- Generate attention roll-out heatmaps for exemplar images
- Create bar chart showing attention concentration by flag type
- Calculate concentration metrics ($N_{\text{eff}}^{\text{attn}}$, $HHI_w^{\text{attn}}$)
- Save figure to `MSc-Themed-Research-Project/write-up/plots/figure1b_attention_flag_types.png`

## Expected Outputs

### Files Generated
```
outputs/
├── before/
│   └── rs5m_16class_consolidation_seed42_20250814_201544/
│       └── preds.parquet
└── after/
    ├── rs5m_ablation_consolidation_only_20250814_141925/
    │   └── preds.parquet
    ├── rs5m_ablation_consolidation_only_seed123_20250814_162946/
    │   └── preds.parquet
    └── rs5m_ablation_consolidation_only_seed456_20250814_181814/
        └── preds.parquet

MSc-Themed-Research-Project/write-up/plots/
└── figure1b_attention_flag_types.png
```

### Figure 1b Structure
- **Top panels**: Attention roll-out heatmaps for each flag type (before/after)
- **Bottom panel**: Bar chart showing on-mask attention shares by type
- **Metrics**: $N_{\text{eff}}^{\text{attn}}$ and $HHI_w^{\text{attn}}$ for before/after conditions
- **Styling**: Fixed color scales, single colorbar, consistent formatting

## Troubleshooting

### Common Issues

1. **Missing checkpoints**:
   ```
   FileNotFoundError: [checkpoint path]
   ```
   - Verify checkpoint paths in `configs/attention.yaml`
   - Ensure RS5M backbone exists at specified location

2. **CUDA/MPS errors**:
   ```
   RuntimeError: MPS backend out of memory
   ```
   - **MPS optimized**: Batch size auto-adjusted to 8 for ViT-H/14
   - Memory management: Automatic cache clearing enabled
   - Use CPU fallback: `device = torch.device("cpu")`

3. **Import errors**:
   ```
   ImportError: No module named 'open_clip'
   ```
   - Install dependencies: `pip install open-clip-torch`
   - Activate correct conda environment

4. **Empty/zero attention**:
   - Check that test images exist and are readable
   - Verify mask loading logic in `scripts/masks.py`
   - Ensure bounding box JSONs are available for mask generation

### Verification Commands

```bash
# Check prediction files were generated
ls -la outputs/before/*/preds.parquet
ls -la outputs/after/*/preds.parquet

# Verify prediction contents
python -c "import pandas as pd; print(pd.read_parquet('outputs/before/rs5m_16class_consolidation_seed42_20250814_201544/preds.parquet').head())"

# Check figure output
ls -la MSc-Themed-Research-Project/write-up/plots/figure1b_attention_flag_types.png
```

## Configuration

Key settings in `configs/attention.yaml`:
- `seeds`: [0, 1, 2] - Random seeds for reproducibility
- `global_vmin/vmax`: 0.0/0.95 - Attention heatmap color scale
- `n_images_per_type`: 8 - Number of exemplar images per flag type
- `index_csv`: Path to test set CSV
- `backbone_checkpoint`: RS5M ViT-H-14 backbone path
- `checkpoints_before/after`: Trained model checkpoint paths

## Integration with Thesis

The generated `figure1b_attention_flag_types.png` should be:
1. Copied to the thesis write-up plots directory
2. Referenced in `complete_quarto_paper.qmd` 
3. Accompanied by appropriate caption describing the diagnostic analysis

## Performance Notes

### **MPS-Optimized Performance** *(Apple Silicon)*
- **Runtime**: ~8-15 minutes *(10-40x faster than CPU)*
- **Memory**: ~4-6GB GPU memory with automatic cache management
- **Batch size**: Optimized to 8 for ViT-H/14 models
- **Environment**: OpenMP conflicts resolved, MPS fallback enabled

### **CUDA Performance** *(NVIDIA GPUs)*
- **Runtime**: ~10-20 minutes
- **Memory**: ~6-8GB GPU memory
- **Batch size**: 16 for ViT-H/14 models

### **CPU Fallback**
- **Runtime**: ~30-45 minutes *(significantly slower)*
- **Memory**: ~2-4GB RAM
- **Batch size**: 1 for memory efficiency

### **Storage Requirements**
- **Prediction files**: ~50-100MB for Parquet files
- **Model checkpoints**: ~36GB total (4 models × 9GB each)
