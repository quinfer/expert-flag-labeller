# Slides Speaking Notes (6–8 minutes, detailed)

These notes align to `thesis_demo_slides.qmd`. Aim for a clear, confident tempo; trim as needed to stay under 10 minutes.

00:00 – 00:15 Title
- Show the Title slide; keep Loom camera pop‑in visible.
- Say: “I’m Barry Quinn, student 9207589. This is my ECS8056 Themed Research Project: Hierarchical Flag Classification through Economic Domain Knowledge.”

00:15 – 00:35 Submission Compliance
- Say: “In this demo I’ll briefly cover the problem, dataset and task, the model and results, and show quick reproducibility checks and the code. I’ll link the GitLab repo/tag and acknowledge limited AI assistance per the declaration.”

00:35 – 01:15 Problem & Contributions
- Context: “We frame cultural symbol recognition in Northern Ireland as a hierarchical classification task. The core contribution is a new dataset (4,501 images), a principled taxonomy (70 → 16 → 7 categories) guided by economic domain knowledge, and strong baselines with a ViT backbone.”
- Emphasize reframing: “We do not claim to ‘solve’ 70‑class imbalance; we define a tractable, meaningful task, then evaluate at three granularities.”

01:15 – 01:55 Dataset & Task
- Source: “Images are from Google Street View (2022–2023) with expert verification. Licensing prevents redistribution; the repo ships scripts/metadata only.”
- Evaluation: “The paper compares 70, 16, and 7 classes to show how hierarchy affects learnability. The clean submission repo includes NIFlagsV2 splits used by the verification scripts (Train 3823 / Val 841 / Test 826 = 5,490 samples) with 90 fine‑grained classes. In the demo, I verify those NIFlagsV2 splits for reproducibility.”

01:55 – 02:15 Flag Exemplars
- Show the exemplars slide: “These examples illustrate the diversity of symbols and contexts we target (demo/allowlisted imagery only).”

02:15 – 03:10 Model Overview (ViT + Hierarchy)
- ViT recap (intuitive): “A Vision Transformer splits the image into fixed‑size patches (e.g., 14×14 for ViT‑H‑14), flattens and linearly projects each into a patch embedding, then adds positional encodings and processes the sequence with transformer layers.”
- MHSA (Multi‑Head Self‑Attention): “Each transformer block uses MHSA, which lets each token attend to all others. ‘Multi‑head’ means we compute attention in several parallel subspaces: for each head we compute Queries, Keys, and Values via learned linear maps; we score attention with scaled dot‑products (Q·Kᵀ/√dₖ), softmax to get weights, and use them to mix Values. Heads are concatenated and projected, giving rich, global context.”
- [CLS] token / head: “We either use a special [CLS] token or pooled representations; a linear head maps to class logits.”
- Our backbone: “We use ViT‑H‑14 pre‑trained on the RS5M remote‑sensing corpus [Zhang et al. 2024], which provides strong spatial priors for scenes with buildings, poles, and environment — relevant to flags in context.”
- Prompting/hierarchy: “We inject hierarchical signals (category/flag/context/full) to guide features, inspired by CLIP and prompt‑tuning work [Radford et al. 2021; Li et al. 2023]. This helps the model weigh symbol vs. mounting context appropriately.”

03:10 – 03:40 Method (Hierarchy)
- “Our taxonomy groups fine‑grained labels into economically meaningful categories; the 4‑level prompting (Category, Flag, Context, Full) provides multi‑granularity cues. This is principled label engineering, not an imbalance ‘fix’.”

03:40 – 04:20 Results (Comparative)
- “On 70 classes: 40.8% accuracy; 16 classes: 72.6%; 7 economic categories: 94.78%. Robust to multi‑seed and cross‑validation. The performance trend supports the value of taxonomy design for practical decision‑support.”

04:20 – 06:10 Live Demo (Reproducibility)
- Open the clean submission repo (QUB EEECS GitLab mirror) at the repository root and show README: “The repository documents setup and reproduction.”
- Quick verification (preferred, from repo root):
  - `python verify_setup.py` — shows split sizes and totals.
  - Alternative (only if your docs say so): `python qub-gitlab-submission/test_setup.py` — prints Train/Val/Test counts and totals.

- Commands you will run in sequence:
  ```bash
  # 1) Verify setup
  python verify_setup.py

  # 2) Quick expected metrics (stub prints targets/usage)
  python scripts/compute_metrics.py

  # 3) Generate simple figures from summary results JSON (fast)
  python scripts/simple_real_figures.py \
    --results results/real_results.json \
    --outdir figures/demo

  # Optional: show saved predictions exist (no need to recompute)
  ls -1 results/rs5m_ablation_consolidation_only_*/preds.parquet
  ```
- Show a lightweight figure or results table (no heavy training): “We provide scripts to regenerate figures and recompute metrics from saved predictions.”
- Run a short evaluation or inference step (no heavy training): e.g., compute metrics from saved predictions or run a tiny batch through the model; then show a metrics table or a pre-rendered figure.

06:10 – 06:20 Annotation App (Link Only)
- “We collected expert labels with a small Next.js + Supabase app used within the larger project. The live URL and demo credentials are in the supporting report on Canvas. Skipping a live demo to conserve time.”

06:50 – 07:20 Reproducibility & GitLab
- “The QUB EEECS GitLab mirror URL and submission tag/commit are in the supporting report. No raw imagery is shipped; scripts/metadata enable reproduction.”

07:20 – 07:40 Ethics & AI Use
- “AI assistance was limited to docstrings/comments for code I authored and non‑substantive UI scaffolding in the annotation app. All task logic, curation, ML experiments, and manuscript text are my own.”

07:40 – 08:00 Acknowledgements & Thank You
- “Thanks to Prof. Declan French and Prof. Dominic Bryan (PI/CI), Brandon Cochrane (PhD), my supervisor Dr. Shuyan Li, and second marker Prof. Yang Hua. Thank you.”

---

## Mini‑reference summaries (plain‑English, 1–2 lines each)

- Radford et al. (CLIP, 2021) [@radford2021learning]: Contrastive pre‑training on image–text pairs learns powerful visual features; prompt‑based classification uses text embeddings as label prototypes.
- Zhang et al. (RS5M, 2024) [@zhang2024rs5m]: Large‑scale remote‑sensing pre‑training for ViT (incl. ViT‑H‑14) yields strong spatial priors for scenes — helpful for flags embedded in streetscapes.
- Li et al. (Efficient prompt tuning, 2023) [@li2023efficient]: Parameter‑efficient prompt‑tuning mechanisms inject task semantics (e.g., hierarchical cues) without heavy fine‑tuning.

Intuition link to our work: CLIP-style prompting motivates our hierarchy cues; RS5M’s pre‑training matches our scene‑level patterns; prompt‑tuning ideas explain how small learned signals can improve recognition.
