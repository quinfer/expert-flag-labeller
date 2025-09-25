# ECS8056 Video Demo Script (6–8 minutes)

Purpose: Recorded screen‑capture demo to accompany supporting materials (30%).

Format: MP4/H.264, 1080p recommended. Test playback on multiple machines before upload.

Repo used: QUB EEECS GitLab mirror of the project (include URL + tag/commit in your supporting report).

---

## 0:00 – 0:20 Title & Identity
- Show title slide (thesis_demo_slides.qmd rendered to reveal.js) with module, title, name, student number, supervisor, second marker.
- Voice‑over: “Hello, I’m Barry Quinn (student 9207589). This video demonstrates my ECS8056 Themed Research Project on hierarchical flag classification.”

## 0:20 – 1:10 Problem & Contributions
- Slide: Problem & Contributions.
- Voice‑over: Briefly introduce the real‑world task (cultural symbol recognition), dataset (4,501 images), and hierarchical taxonomy (70 → 16 → 7). Emphasize practical framing and reproducibility.

## 1:10 – 1:50 Dataset & Task
- Slide: Dataset & Task.
- Voice‑over: Note licensing constraints (no redistribution), expert verification, and evaluation across semantic granularities. Clarify that scripts/metadata are provided.

## 1:50 – 2:40 Method (Hierarchy)
- Slide: Method with Figure 4 image.
- Voice‑over: Explain taxonomy design guided by economic domain knowledge; show the 4‑level prompting idea and learned fusion weights at a high level.

## 2:40 – 3:30 Results (Comparative)
- Slide: Results with Figure 2 image.
- Voice‑over: State numbers succinctly — 70‑class 40.8%, 16‑class 72.6%, 7‑class 94.78% — and mention multi‑seed + cross‑validation for robustness. Avoid any “solves imbalance” language.

## 3:30 – 5:30 Reproducibility Walkthrough
- Switch to terminal/IDE.
- Show repo root. Mention GitLab URL, branch, and submission tag/commit.
- Run quick checks (choose one present in repo):
  - `python verify_setup.py`  (external submission repo) or
  - `python qub-gitlab-submission/test_setup.py` (bundle)  
  Narrate what it verifies (split sizes and totals).
- Generate a non‑GPU heavy figure or run a metrics script briefly, e.g., `python scripts/compute_metrics.py --results-dir results/` (if results present), or show figure files already rendered.
- Demonstrate Quarto render of the paper: `./write-up/render_and_publish.sh`  
  Open the resulting PDF and briefly show the declaration page and a figure.

Notes: Do not attempt heavy training in the demo. Focus on quick, verifiable steps.

## 5:30 – 6:10 Ethics & AI Use
- Slide: Ethics & AI Use.
- Voice‑over: Acknowledge limited AI usage (docstrings/comments for own code only) and data licensing constraints.

## 6:10 – 6:40 Acknowledgements & Closing
- Slide: Acknowledgements.
- Voice‑over: Thank named contributors (PI/CI, PhD student, supervisor, second marker) and invite questions. Confirm that supporting materials (code + video + short report) are uploaded to Canvas.

---

## Recording Tips
- Use MP4/H.264 at 1080p; confirm audio levels and window text readability.
- Keep background processes to a minimum; pre‑open the repo and slides.
- Do a brief test export and play it on a different machine/user account.

## Rendering Slides
- From `MSc-Themed-Research-Project/write-up`:
  ```bash
  quarto render thesis_demo_slides.qmd
  # Output: thesis_demo_slides.html (open locally in a browser for the recording)
  ```

