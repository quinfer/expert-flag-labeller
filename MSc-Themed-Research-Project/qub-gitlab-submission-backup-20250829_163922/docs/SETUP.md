### Environment setup

- Python 3.10+
- Recommended: conda env `flag_classification`
- Install core deps:
  ```bash
  pip install -r data/requirements.txt
  ```
- macOS MPS (optional): see `data/fixed_environment_setup.sh` and `data/m4_device_utils.py`.

### Data preparation

- Prepare datasets and splits:
  ```bash
  bash data/run_data_prep.sh
  ```
- Inspect distribution figures in `data/flag_class_distribution_analysis.png` and `data/class_distribution_confidence3.png`.

### Upstream baseline (author code)

- Use `final_code/` with RS5M ViT-H-14 checkpoint as advised; format our dataset to match the author’s `datasets/` conventions. 
- After wiring the dataset, run training via `final_code/train.py` using the provided configs.

### Local baselines

- CLIP zero-shot/baseline:
  ```bash
  python data/test_baseline_clip.py
  ```
- CoCoOp-style training:
  ```bash
  python data/train.py
  ```
- Minimal/MPS variants exist under `data/train_minimal*.py` and `data/direct_mps_train*.py`.
