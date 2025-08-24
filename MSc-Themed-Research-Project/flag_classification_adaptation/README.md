# NI Flags Dataset Preparation and Training Workflow

This document records the end-to-end workflow for preparing the dataset and training models for the MSc project and downstream production use.

## Data sources and priorities
- Preferred: clean, uncropped originals `<id>_NNN.jpg` (no overlays), sourced from `public/images` and `data/true_positive_images`.
- Fallback: clean crops `<id>_NNN_box0.jpg` (no overlays) if originals are missing.
- Excluded by default: decorated images such as `composite_*`, `masked_*`, and `*_boxed.jpg`.

## Preparation script
- Script: `final_data_setup.py`
- Key options:
  - `--prefer-uncropped-originals` (default on): Prefer originals over `_box0` crops.
  - `--exclude-decorated` (default on): Skip files with overlays.
  - `--min-side INT` (default 224): Ensure the shorter side is at least this many pixels (0 to disable upscaling).

### Steps
1. Place `classifications.csv` in `flag_classification_adaptation/` with columns:
   `image_id, primary_category, display_context, specific_flag, confidence`.
2. Run the setup:
   ```bash
   conda activate flag_classification
   cd MSc-Themed-Research-Project/flag_classification_adaptation
   python final_data_setup.py --prefer-uncropped-originals --exclude-decorated --min-side 224
   ```
3. Outputs:
   - `../data/ni_flags/images/` (prepared images)
   - `../data/ni_flags/annotations.json`
   - `../data/ni_flags/classnames.txt`
   - `../data/ni_flags/dataset_stats.json`
   - `configs/datasets/niflags.yaml`

## Audit and quality checks
- Script: `scripts/audit_image_sources.py`
- Produces `../data/ni_flags/image_sources_report.csv` with per-image source and basic quality stats.

## Training
- Use `train_minimal_mps.py` with MPS acceleration.
- Ensure dataset registration imports `datasets.ni_flags` if using annotations, and config `configs/datasets/niflags.yaml` (DATASET.NAME: "NIFlags").
```bash
python train_minimal_mps.py \
  --clean \
  --trainer CoCoOp \
  --config-file configs/trainers/CoCoOp/rn50.yaml \
  --dataset-config-file configs/datasets/niflags.yaml \
  --output-dir experiments/niflags_rn50_full \
  TRAINER.COCOOP.PREC fp32 \
  DATALOADER.NUM_WORKERS 0 \
  OPTIM.MAX_EPOCH 50
```

## Rationale
- Prefer highest-fidelity inputs within CLIP constraints; avoid decorated overlays to reduce bias.
- Upscale tiny images to meet the model’s input size when necessary.

## Folder structure
- Core entrypoints (stay in this folder):
  - `final_data_setup.py`, `train_minimal_mps.py`, `train.py`, `configs/`, `datasets/`, `experiments/`
- Utility scripts (moved to `scripts/`):
  - `analyze_class_distribution.py`, `create_distribution_plots.py`, `monitor_logs.py`, `mps_verification_script.py`, `fix_openmp.sh`, `supabase_data_export.py`
- Tip: scripts now resolve paths relative to their own location; you can run them from anywhere.

# Flag Classification Adaptation

This directory contains the adaptation of Li et al.'s hierarchical prompt tuning for Northern Ireland flag classification.

## Quick Start

1. **Setup Environment:**
   ```bash
   ./setup_environment.sh
   conda activate flag_classification
   ```

2. **Test Setup:**
   ```bash
   python quick_test.py
   ```

3. **Prepare Data:**
   ```bash
   python scripts/prepare_flag_data.py
   ```

4. **Train Model:**
   ```bash
   python train.py \
     --trainer CoCoOpFlags \
     --dataset-config-file configs/datasets/ni_flags.yaml \
     --config-file configs/trainers/CoCoOpFlags/rn50_ep50.yaml \
     --output-dir experiments/week9_tests
   ```

## Directory Structure

- `datasets/` - Custom dataset classes
- `trainers/` - Modified trainers for flag classification  
- `configs/` - Configuration files for training
- `utils/` - Utility functions (M4 Max compatibility, etc.)
- `scripts/` - Data preparation and analysis scripts
- `experiments/` - Training outputs and results

## Key Adaptations

1. **Hierarchical Prompts:** Adapted from ship classification to flag categories
2. **M4 Max Compatibility:** MPS support for Apple Silicon
3. **Expert Annotations:** Integration with your existing 8,204 classifications
