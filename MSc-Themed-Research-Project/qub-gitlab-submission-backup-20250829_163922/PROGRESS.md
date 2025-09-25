### Progress to date

- Dataset engineering and analysis
  - Built multiple dataset variants and overfit splits (`data/ni_flags*`)
  - Generated distribution figures and stats (`flag_class_distribution_analysis.png`, `class_distribution_confidence3.png`, `detailed_class_statistics.json`)
  - Gold-standard labeling plan and artifacts (`gold_standard_to_label.csv`, `gold_standard_selection.py`, `implement_multi_expert.py`)

- Baselines and training infra
  - CLIP baseline (`test_baseline_clip.py`), CoCoOp-style trainer (`cocoop_flags_trainer.py`, `train.py`, `train_minimal*.py`, `direct_mps_train*.py`)
  - Focal loss and monitoring utilities (`focal_loss_validator.py`, `test_focal_loss.py`, `training_monitor.py`)
  - Setup scripts: `complete_setup_script.py`, `setup_environment.sh`, `fixed_environment_setup.sh`, `m4_device_utils.py`

- Upstream baseline code
  - `final_code/` aligned with author’s pipeline; to be run with RS5M ViT-H-14 checkpoint

### Current issues

- Performance poor/unstable despite multiple attempts (likely due to long-tail imbalance, domain shift, prompt mismatch)
- Need a solid upstream baseline run and hierarchical prompting
- Gold-standard 3–5k labeling needs completion for strong supervision

### Planned next steps (1–2 weeks)

- Run upstream `final_code/` baseline on our dataset and export full metrics
- Implement hierarchical prompts and evaluation; combine focal loss with class-balanced sampling
- Context ablations (crop vs crop+context vs full image with bbox mask)

### Requests for supervision input

- Dataset interface to `final_code/` (folder/file conventions, preprocessing)
- Prompt templates and hierarchical design for flags; synonyms/variants handling
- Multi-label vs hierarchical classification setup and loss choice
- Imbalance recipe (focal vs weights vs sampler) and recommended metrics
- Evaluation beyond Top-1 (hierarchical accuracy, macro F1, confusion matrices)
