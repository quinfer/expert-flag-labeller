Subject: Expert Flag Labeler – Pat-only gold-standard set (1995 images) now live

Hi Shuyan,

Quick update on the expert labeling app and the gold-standard curation for Pat.

Highlights
- Pat-only curated set deployed to production; Pat starts at Image 1.
- Production API currently serves 1,995 curated images (composite-first) from the high-confidence pool.
- Confidence-based selection ensures low label noise for the gold standard.

What we built
- Confidence distribution (GroundingDINO) over 96,128 detections:
  - Mean 0.631, Median 0.619; P90 0.842, P95 0.878, P97 0.896, P99 0.920
- Sampling strategy:
  - Cutoff ≥ 0.90 → 2,440 candidates
  - Stratified per town to sample exactly 2,000
  - Every item has a side-by-side composite (cropped + original context)
- Storage and metadata:
  - Uploaded all required files to Supabase Storage; populated `image_metadata` with 2,000 rows
  - Expert-confirmed curation filters 5 non-`_box0` items → final 1,995 in-app

User experience (Pat)
- Progress logic hardened for curated runs; Pat always starts at the first image (index 0) to avoid jumps caused by historic classifications.
- Composite images are prioritized automatically for better context.

Where to check
- App: https://expert-flag-labeller-production.up.railway.app
- Login (Pat):
  - Username: Pat
  - Password: 3fG7tHj9Ym1sK8pX
- API sanity: `GET /api/images-static` returns ~1995 images (metadata shows source/curation counts)

Notes
- One composite in LARNE failed upload (harmless); we will re-upload.
- Added a simple environment toggle (`NEXT_PUBLIC_PAT_ONLY`) to enable/disable curated Pat-only behavior in future runs.

Next steps
- Begin Pat’s gold-standard pass on the curated set.
- Optional: add API-level filtering for per-expert subsets when onboarding additional experts.
- Re-upload the single missing composite and add a small check to detect missing composites earlier.

Technical appendix (for reproducibility)
- Generation scripts and artifacts:
  - `scripts/prepare_images_for_classification.py` (now enforces `--min-confidence` and supports `--filter-by-confidence`, `--target-boxes-per-town`)
  - Queue merged at `data/classification_queue_PAT.json` (2,000 items)
  - App list written to `src/data/static-images-pat.json`; static fallback set to `src/data/static-images.json` for dev
- Upload + metadata:
  - `scripts/upload-images-to-supabase.js` (public uploads)
  - `scripts/populate-image-metadata.js` (2,000 rows)
- Production behavior:
  - API: `src/app/api/images-static/route.ts` (serves Supabase/metadata; applies expert-confirmed curation)
  - Curated result: 1,995 images (filters 5 non-`_box0` items)

Best,
Barry

Subject: Flag classification project: status, concerns, and requests for guidance

Hi Shuyan,

We’ve prepared multiple dataset variants and overfit subsets, analyzed class imbalance, designed a gold‑standard 3–5k labeling pipeline, and implemented CLIP/CoCoOp-style baselines with focal loss and monitoring. However, initial experiments haven’t yielded acceptable performance, likely due to severe class imbalance, domain shift, ambiguous classes, and insufficient hierarchical prompting.

We plan to run the upstream RS5M ViT‑H‑14 baseline (`final_code/`) on our dataset next, then perform prompt/imbalance/context ablations and consolidate results.

We would value your guidance on:
1) Dataset conventions to plug our data into `final_code/` and any RS5M-specific preprocessing
2) Effective prompt templates and hierarchical prompts for NI flags (handling synonyms/variants)
3) Multi‑label vs hierarchical single‑label setup and preferred loss design
4) Imbalance strategy (focal + sampling/weights) and preferred metrics (macro F1, hierarchical accuracy)
5) Evaluation protocol beyond Top‑1 and recommended visualizations (confusion matrices, PR curves)

If helpful, we’re happy to involve the original author as you suggested, especially while aligning our dataset interface with their code.

Thanks very much,
Barry
