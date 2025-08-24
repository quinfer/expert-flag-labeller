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
