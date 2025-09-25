# Reproducibility Progress Log

Date: 2025-09-18

This log records the latest changes and build steps to ensure the write-up is reproducible.

## Summary of Changes

- Reframed thesis to “new task + hierarchical taxonomy” per supervisor guidance (Dr. Shuyan Li).
- Updated title, abstract, keywords, introduction, methodology, results framing, and conclusion in the Quarto source.
- Corrected supervisor name occurrences (“Wang” → “Li”) in supervisor update docs.

## Files Modified

- Write-up source updated:
  - `MSc-Themed-Research-Project/write-up/complete_quarto_paper.qmd`
    - Title: “Hierarchical Flag Classification through Economic Domain Knowledge: A Vision Transformer Approach for Cultural Symbol Recognition”
    - Abstract: new task, dataset (4,501 images: 2,030 train / 2,471 test), hierarchical framework (70→16→7), baselines (40.8%, 72.6%, 94.78%).
    - Keywords: focus on hierarchical classification and dataset contribution.
    - Introduction: reframed to cultural symbol recognition task; removed imbalance “breakthrough” claims.
    - Methodology: “Economic Taxonomy (Hierarchical Grouping)” — taxonomy design, not imbalance fix.
    - Experiments/Results: comparative granularity study (70/16/7) without claiming to solve 70-class.
    - Conclusion: dataset + hierarchical framework + practical applications.

- Supervisor naming corrections:
  - `MSc-Themed-Research-Project/docs/SUPERVISOR_UPDATE_JANUARY_2025.md`
  - `MSc-Themed-Research-Project/qub-gitlab-submission-backup-20250829_163922/docs/SUPERVISOR_UPDATE_JANUARY_2025.md`

## Build Details

- Tooling: Quarto 1.5.52; PDF engine: XeLaTeX (TeX Live 2024).
- Command (run from `MSc-Themed-Research-Project/write-up`):
  - `quarto render complete_quarto_paper.qmd --to pdf`
- Output:
  - `MSc-Themed-Research-Project/write-up/complete_quarto_paper.pdf` (size ~1.786 MB)
- Destination copy (default):
  - `docs/thesis_paper.pdf` (copied by render_and_publish.sh)

### Video Demo Slides & Script

- Slides (Quarto reveal.js): `write-up/thesis_demo_slides.qmd`
  - Render: `quarto render thesis_demo_slides.qmd` → `thesis_demo_slides.html`
  - Content aligns with ECS8056 supporting materials guidance (video demo requirement)
- Video script: `write-up/video_demo_script.md` (6–8 minutes plan)
  - MP4/H.264 recommended; test playback on multiple machines before Canvas upload

### Automated Render & Publish Script

To make rendering and publishing repeatable, use the helper script:

- Script path: `MSc-Themed-Research-Project/write-up/render_and_publish.sh`
- What it does:
  - Renders `complete_quarto_paper.qmd` to PDF using Quarto
  - Creates a timestamped backup of the destination PDF if it exists
  - Copies the newly rendered PDF to the submission folder
- Prerequisites: Quarto ≥ 1.5 and a working LaTeX engine (XeLaTeX)

Usage:

```
# Default (uses the standard source and destination paths)
./render_and_publish.sh

# Custom source/destination (optional)
./render_and_publish.sh path/to/source.qmd /absolute/path/to/destination.pdf
```

Defaults baked into the script:

- Source QMD: `MSc-Themed-Research-Project/write-up/complete_quarto_paper.qmd`
- Destination PDF: `docs/thesis_paper.pdf`

## 2025-09-19 Update

- Updated `render_and_publish.sh` to publish the paper PDF to the repository’s `docs/thesis_paper.pdf` by default (to match supporting materials).

## Backups

- Pre-reframe source (from git HEAD) saved as:
  - `MSc-Themed-Research-Project/write-up/complete_quarto_paper_pre-reframe_20250918_081441.qmd`

## Data Curation (for downstream training reproducibility)

- New classifications vs previous export (diff at repo root):
  - `classifications_new_rows_since_prev.csv` — 4,413 rows (new classification IDs)
  - `classifications_new_images_since_prev.csv` — 1,890 rows (new image_ids)

## Notes

- All changes are uncommitted; re-run the render command above to reproduce the PDF.
- No additional environment changes required beyond Quarto + TeX.
