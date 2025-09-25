# Clean GitLab Submission Structure for MSc

Based on the paper requirements, here's what should be included:

## Essential Files for Paper Reproduction

### Core Training Pipeline
- `train.py` - Main training script (RS5M ViT-H-14)
- `requirements.txt` - Dependencies
- `datasets/NIFlagsV2/` - Dataset files (train.txt, val.txt, test.txt, classnames.txt)

### Model Architecture  
- `clip/` - CLIP implementation (for RS5M)
- `trainers/cocoop-final.py` - Main trainer implementation
- Key trainer files that support the paper

### Configuration
- `configs/datasets/` - Dataset configuration (NIFlagsV2 specific)
- `configs/trainers/` - Training configuration (CoCoOp specific)

### Evaluation & Figures
- `scripts/metrics.py` - Evaluation metrics
- Figure generation scripts that create paper figures
- `parse_test_res.py` - Results parsing

### Documentation
- `README.md` - Setup and reproduction instructions
- Key methodology documentation

## Files to REMOVE (Over-engineered)
- Most of `docs/` folder (keep only essential methodology)
- Archive folders
- Multiple experimental variants
- RAG instruction files
- Email drafts and progress tracking
- Duplicate configurations for other datasets
- ViTAEv2 implementation (not used in paper)
- Multiple trainer variants not used

## Target Size: ~500MB (vs current 3.7GB)
