### Experiments

- CLIP zero-shot/baseline: `data/test_baseline_clip.py`
- CoCoOp-style trainer: `data/cocoop_flags_trainer.py` with entrypoints `data/train.py`, `data/train_minimal*.py`, `data/direct_mps_train*.py`
- Loss/imbalance utilities: `data/focal_loss_validator.py`, `data/test_focal_loss.py`, `data/compare_losses.py`
- Monitoring/Hygiene: `data/training_monitor.py`, `data/monitor_training.sh`, `data/cleanup_training.py`
- Evaluation/compare: `data/evaluate_consolidated.py`, `data/compare_approaches.py`

#### Datasets
- Variants: `data/ni_flags*`, with overfit sanity sets: `data/ni_flags_overfit*`
- Stats: `data/detailed_class_statistics.json`
- Figures: `data/flag_class_distribution_analysis.png`, `data/class_distribution_confidence3.png`

#### Running
- Prepare data: `bash data/run_data_prep.sh`
- Train baseline: `python data/train.py`
- Evaluate: `python data/evaluate_consolidated.py`
- Outputs: `data/output/` (metrics, plots); archive older runs to `data/archive/`

#### Notes
- Use class-balanced sampling and focal loss for long-tail classes.
- Validate sanity on overfit subsets to ensure optimization is functioning.

### Label sanity check (manual)

- Generate an HTML gallery to verify labels match images:
  ```bash
  python scripts/label_sanity_check.py \
    --dataset-dir data/ni_flags_consolidated \
    --samples-per-class 12
  ```
- Open the generated HTML under `<dataset>/sanity_checks/` and visually confirm.
