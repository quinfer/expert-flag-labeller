### RS5M ViT-H-14 adaptation plan (paper-aligned)

Goal: Run the author-style RS5M ViT-H-14 baseline on NI flags and layer on hierarchical prompting and imbalance mitigation.

Prereqs
- Dataset in author format (images + classnames.txt + train/val/test)
- RS5M ViT-H-14 checkpoint (~3.8 GB)
- Author code available under `final_code/`

Steps
1) Export dataset (base labels recommended, e.g., `data/ni_flags_v2`):
   ```bash
   python flag_classification_adaptation/scripts/export_author_format.py \
     --source-dir MSc-Themed-Research-Project/data/ni_flags_v2 \
     --dest-dir   MSc-Themed-Research-Project/final_code/datasets/NIFlagsV2 \
     --images-subdir images
   ```

2) Download RS5M checkpoint:
   ```bash
   bash MSc-Themed-Research-Project/scripts/download_rs5m_checkpoint.sh
   ```
   - Fill the URL in the script before running.

3) Run author baseline (example, adjust config/checkpoint as needed):
   ```bash
   python flag_classification_adaptation/scripts/run_author_baseline.py \
     --dataset-root MSc-Themed-Research-Project/final_code/datasets/NIFlagsV2 \
     --output-dir   MSc-Themed-Research-Project/flag_classification_adaptation/experiments/author_vith14_baseline \
     --config-file  MSc-Themed-Research-Project/final_code/configs/trainers/CoCoOp/vit_h14.yaml \
     --trainer CoCoOp \
     --extra-args LOSS.NAME focal LOSS.ALPHA 0.25
   ```

4) Log metrics
- Save Top-1/Top-5, macro/micro F1, per-class PR, confusion matrix to `flag_classification_adaptation/experiments/author_vith14_baseline/` and copy plots to `docs/writeup_bundle/`.

Hierarchical prompting templates (adapting paper’s coarse→fine idea)
- Primary (category):
  - "a photo of a [flag], category: National/Fraternal/Proscribed/..."
- Secondary (context):
  - "mounted on lamppost/building/pole, window display, bunting, memorial"
- Specific (flag identity):
  - "Union Jack, Ulster Banner, Irish Tricolor, Scottish Saltire, ..."

Implementation options
- Multi-stage inference (coarse→fine) with confidence gating; or
- Single-stage prompts combining levels (e.g., "National-Lamppost-mounted-Union Jack").

Imbalance mitigation
- Compare: dynamic inverse-frequency weights, class-balanced sampler, focal loss (gamma 1.5–2.5) with capping on max class weight.

Notes
- ViT-H-14 is heavy; ensure enough VRAM/MPS memory; consider batch-size tuning.
- Keep all new runs in `flag_classification_adaptation/experiments/` to preserve history.
