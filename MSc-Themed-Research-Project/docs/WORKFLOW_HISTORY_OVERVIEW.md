### Project Workflow History Overview (Hand‑over Guide)

This document summarizes the complete workflow of the Expert Flag Labeler project and the MSc classifier work. It is designed as a single hand‑over reference for another AI assistant.

---

### At a glance
- **Part 1 – Detection + Expert correction (GroundingDINO → True Positives)**
- **Part 2 – Expert Labeler App (Next.js) with stratified sampling**
- **Part 3 – MSc Classifier (RS5M ViT‑H‑14) with economic consolidation and validated results**

---

### End‑to‑end data flow
1) Street‑level images (≈1.9M) per town → GroundingDINO prompt "flag"
2) GroundingDINO outputs candidates (`flags=1`) → Expert review creates `flags_correct` and `indicator`
3) Expert‑confirmed true positives feed the labeling app (composites/crops, stratified sampling)
4) Expert annotations/splits feed the MSc classifier (70 → 16 → 7 classes); results and figures generated

---

### Part 1 – GroundingDINO detection and expert‑confirmed true positives
- Key docs: `docs/false-positive-filtering-logic.md`, `docs/false-positive-filtering.md`, `docs/expert-confirmed-curation.md`
- Core files (per town; see `false_positive_checks/`):
  - `{TOWN}list.pickle`: all image paths processed
  - `{TOWN}results.pickle`: GroundingDINO raw results
  - `{TOWN}resultsCORRECT.pickle`: expert‑corrected results (authoritative)
- Correct logic:
  - True positives: `(flags==1) & (flags_correct==1)`
  - False positives: `(flags==1) & (flags_correct==0)`
- Bounding boxes/masks for exemplars: see `scripts/create_masked_images.py` (reads per‑town bbox JSONs), used for visual QA and can be used to compute attention‑mass within flag regions.

---

### Part 2 – Expert Labeler App (Next.js)
- Key docs: `Expert_Flag_Labeller_User_Guide.md`, `docs/image_processing_guide.md`, `docs/deployment_instructions.md`
- Purpose: serve side‑by‑side composites (crop + context) to experts with a stratified sample (by town, complexity, context). Pat‑only curated sets and confidence‑based sampling described in `MSc-Themed-Research-Project/docs/EMAIL_SHUYAN_DRAFT.md`.
- Filtering and serving logic integrates the false‑positive curation so experts see only high‑quality images.

---

### Part 3 – MSc Classifier (RS5M ViT‑H‑14)
- Key docs: `MSc-Themed-Research-Project/docs/COMPLETE_EXPERIMENTAL_WORKFLOW.md`, `MSc-Themed-Research-Project/flag_classification_adaptation/WORKFLOW_DOCUMENTATION.md`, `MSc-Themed-Research-Project/docs/standardized-numbers-ref.md`
- Data consolidation:
  - 70 original labels → 16 economic groups → 7 super‑consolidated categories
- Critical bug discovery:
  - 72.63% (16‑class) was an artifact: majority‑class collapse + mapping bug
  - Fixed baseline is 0.56% (after corrections)
- Validated breakthrough results:
  - 7‑class consolidation: 94.78% (multi‑seed 94.57% ± 0.22; 5‑fold CV 93.23% ± 0.34)
  - 16‑class scaling: 83.24% (separate config)
- Repro quick start (examples):
  - Activate env: `conda activate flag_classification`
  - Multi‑seed 7‑class: `./MSc-Themed-Research-Project/run_multi_seed_validation.sh`
  - 16‑class scaling: `./MSc-Themed-Research-Project/run_16class_consolidation_test.sh`

---

### Figures and generation
- Primary scripts (current):
  - `MSc-Themed-Research-Project/scripts/create_thesis_visualizations.py` (rich, thesis set)
  - `MSc-Themed-Research-Project/scripts/create_real_attention_figure.py` (Figure 1 real imagery)
  - `MSc-Themed-Research-Project/scripts/simple_real_figures.py` + `scripts/real_results.json` (lightweight 5‑figure generator)
  - New: `MSc-Themed-Research-Project/scripts/figure1b_attention_flag_types.py` (attention by flag type)
- Write‑up targets (`MSc-Themed-Research-Project/write-up/plots/`):
  - `figure1_real_attention_analysis.(png|pdf)` – attention, real imagery
  - `figure1b_attention_flag_types.(png|pdf)` – attention by flag type
  - `figure2_performance_breakthrough.(png|pdf)` – performance + validation
  - `figure3_economic_consolidation.(png|pdf)` – consolidation flow + bubble + performance
  - `figure4_hierarchical_prompting.(png|pdf)` – schematic
  - `figure5_complete_results_summary.(png|pdf)` – summary/timeline

---

### Suggested alignment for attention figures (consistency across parts)
- Source images: sample only expert‑confirmed true positives from Part 1; persist deterministic lists per type.
- Attention maps: compute ViT attention roll‑out with RS5M ViT‑H‑14 (Part 3 model) and report attention‑mass within annotated flag masks (from Part 1 bbox/masks) per type.
- Outputs: keep Quarto paths under `write-up/plots/` with sequential numbering.

---

### Key directories and artifacts
- Detection/curation: `false_positive_checks/`, `scripts/create_masked_images.py`
- App (Next.js): `src/app/`, `src/data/`, `src/lib/false-positive-filter.ts`
- MSc training: `MSc-Themed-Research-Project/flag_classification_adaptation/`
- Figures: `MSc-Themed-Research-Project/scripts/` and `MSc-Themed-Research-Project/write-up/plots/`

---

### Hand‑off checklist
- Environment: `conda activate flag_classification`
- Verify town pickles present; ensure bbox JSONs accessible if computing attention‑mass
- Generate/update figures using the simple or full script suites
- Use standardized numbers only (`MSc-Themed-Research-Project/docs/standardized-numbers-ref.md`)

---

### Pointers for another AI assistant
- If asked to regenerate figures: prefer `simple_real_figures.py` (5 figures) or `create_thesis_visualizations.py` (full thesis set); write to `write-up/plots/`.
- If asked to align attention with true positives: build a small index from `{TOWN}resultsCORRECT.pickle` and bboxes; sample deterministically; run ViT roll‑out; compute attention‑mass within masks.
- If asked to reproduce results: use the run scripts in the MSc project and report validated metrics from the standardized numbers reference.
