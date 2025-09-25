#!/usr/bin/env python3
"""
Simple real-figures generator.
- Reads a single JSON with real results
- Produces Figure 1 (attention), Figure 2 (performance), Figure 3 (consolidation panels),
  Figure 4 (hierarchical schematic), Figure 5 (timeline)
Usage:
  python scripts/simple_real_figures.py --results scripts/real_results.json --outdir scripts/figs_simple
"""
import json
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import sys

# Try to import the real attention figure generator (Figure 1 with actual imagery)
REAL_ATTENTION_AVAILABLE = False
try:
    # Add this scripts directory to path and import
    this_dir = Path(__file__).parent
    sys.path.append(str(this_dir))
    import create_real_attention_figure  # type: ignore
    REAL_ATTENTION_AVAILABLE = True
except Exception:
    REAL_ATTENTION_AVAILABLE = False


def load_results(path: Path) -> Dict:
    data = json.loads(path.read_text())
    return data


def fig1_attention_bar(path_out_png: Path, path_out_pdf: Path, before: float, after: float) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    vals = [before, after]
    ax.bar([0, 1], vals, color=["#999", "#2E86AB"], edgecolor="black")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Standard", "Economic Consolidation"])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Attention on Flag Mask (%)")
    ax.set_title("Attention Focus Before vs After")
    for i, v in enumerate(vals):
        ax.text(i, v + 1.2, f"{v:.1f}%", ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    fig.savefig(path_out_png, dpi=300)
    fig.savefig(path_out_pdf)
    plt.close(fig)


def fig1_attention_real(path_out_png: Path, path_out_pdf: Path) -> None:
    if not REAL_ATTENTION_AVAILABLE:
        raise RuntimeError("Real attention generator not available")
    analyzer = create_real_attention_figure.RealAttentionAnalyzer(output_dir=str(path_out_png.parent))
    png_path = analyzer.create_real_attention_analysis_figure()
    # If the generator saved with a different name, copy by saving the same figure again is not trivial here.
    # For simplicity, just ensure our desired names are present by duplicating the saved file.
    src = Path(png_path)
    if src.exists():
        target_png = path_out_png
        target_pdf = path_out_pdf
        target_png.write_bytes(src.read_bytes())
        # Also write a PDF duplicate if available; otherwise skip
        pdf_src = src.with_suffix('.pdf')
        if pdf_src.exists():
            target_pdf.write_bytes(pdf_src.read_bytes())


def fig2_performance(path_out_png: Path, path_out_pdf: Path, perf: List[Dict], val: Dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ind = np.arange(len(perf))
    width = 0.28

    acc = [p["accuracy"] for p in perf]
    f1 = [p["macro_f1"] for p in perf]
    k = [p.get("classes_learned_pct", 0.0) for p in perf]

    ax1.bar(ind - width, acc, width, label="Accuracy", edgecolor="black")
    ax1.bar(ind, f1, width, label="Macro F1", edgecolor="black")
    ax1.bar(ind + width, k, width, label="Classes Learned (%)", edgecolor="black")
    ax1.set_xticks(ind)
    ax1.set_xticklabels([p["strategy"] for p in perf])
    ax1.set_ylabel("Performance (%)")
    ax1.set_title("End-to-End Performance Improvement")
    ax1.legend()

    ms = val.get("multi_seed", {})
    cv = val.get("cv", {})
    names = ["Multi-seed", "5-Fold CV"]
    means = [ms.get("mean", np.nan), cv.get("mean", np.nan)]
    stds = [ms.get("std", 0.0), cv.get("std", 0.0)]
    ax2.bar(names, means, yerr=stds, capsize=5, color="#2E86AB", alpha=0.85, edgecolor="black")
    ax2.set_ylim(min(means) - 1, max(means) + 1)
    ax2.set_ylabel("Accuracy (%)")
    ax2.set_title("Statistical Validation")

    plt.tight_layout()
    fig.savefig(path_out_png, dpi=300)
    fig.savefig(path_out_pdf)
    plt.close(fig)


def hhi_from_counts(counts: Dict[str, int]) -> float:
    total = sum(counts.values())
    s = np.array([c / total for c in counts.values()], dtype=float)
    return float(np.sum(s ** 2) * 10000)


def fig3_consolidation(path_out_png: Path, path_out_pdf: Path, counts: Dict[str, int], weights: Dict[str, float], perf: List[Dict]) -> None:
    fig = plt.figure(figsize=(12, 5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.2, 1.2], wspace=0.3)

    # Flow panel (vertical)
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.axis('off')
    stages = [
        ("Original\n(70)", perf[0]["accuracy"]),
        ("Economic\n(16)", perf[1]["accuracy"]),
        ("Super\n(7)", perf[2]["accuracy"]) 
    ]
    for i, (lab, acc) in enumerate(stages):
        y = 0.8 - i * 0.27
        ax0.add_patch(plt.Rectangle((0.15, y - 0.08), 0.7, 0.16, alpha=0.25, edgecolor='black'))
        ax0.text(0.5, y, f"{lab}\n{acc:.1f}%", ha='center', va='center')
        if i < len(stages) - 1:
            ax0.annotate("", xy=(0.5, y - 0.08), xytext=(0.5, y - 0.19), arrowprops=dict(arrowstyle="->"))
    ax0.set_title("Class Consolidation Flow")

    # Bubble panel (restore legend)
    ax1 = fig.add_subplot(gs[0, 1])
    cats = list(counts.keys())
    x = np.arange(len(cats))
    y = np.array([counts[c] for c in cats], dtype=float)
    w = np.array([weights.get(c, 1.0) for c in cats], dtype=float)
    sizes = (y / y.max()) * 1200 + 80
    colors = ["red" if wi < 0 else ("orange" if wi < 0.4 else "green") for wi in w]
    ax1.scatter(x, y, s=sizes, c=colors, edgecolor='black', alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cats, rotation=30, ha='right')
    ax1.set_ylabel("Sample Count")
    ax1.set_title("Economic Externalities vs Samples")
    ax1.text(0.02, 0.95, f"HHI: {hhi_from_counts(counts):,.0f}", transform=ax1.transAxes, ha='left', va='top')
    # Legend proxies
    for wi, lab in [(-1, "Negative externality"), (0.2, "Mixed/ambiguous"), (0.7, "Positive/benign")]:
        ax1.scatter([], [], s=200, c=("red" if wi < 0 else "orange" if wi < 0.4 else "green"), edgecolor='black', label=lab)
    ax1.legend(loc='upper right')

    # Performance panel
    ax2 = fig.add_subplot(gs[0, 2])
    ind = np.arange(len(perf))
    width = 0.28
    acc = [p["accuracy"] for p in perf]
    f1 = [p["macro_f1"] for p in perf]
    k = [p.get("classes_learned_pct", 0.0) for p in perf]
    ax2.bar(ind - width, acc, width, label="Accuracy")
    ax2.bar(ind, f1, width, label="Macro F1")
    ax2.bar(ind + width, k, width, label="Classes Learned (%)")
    ax2.set_xticks(ind)
    ax2.set_xticklabels([p["strategy"] for p in perf])
    ax2.set_ylabel("Performance (%)")
    ax2.set_title("Performance vs Consolidation")
    ax2.legend()

    plt.tight_layout()
    fig.savefig(path_out_png, dpi=300)
    fig.savefig(path_out_pdf)
    plt.close(fig)


def fig4_hierarchical(path_out_png: Path, path_out_pdf: Path) -> None:
    # Minimal schematic to match write-up style
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis('off')
    boxes = [
        ("Full Scene", (0.1, 0.7, 0.35, 0.15)),
        ("Economic Context", (0.1, 0.5, 0.35, 0.15)),
        ("Category Context", (0.1, 0.3, 0.35, 0.15)),
        ("Flag-specific Context", (0.1, 0.1, 0.35, 0.15)),
    ]
    for txt, (x, y, w, h) in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, alpha=0.2))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center")
        ax.annotate("", xy=(x + w, y + h / 2), xytext=(x + w + 0.1, y + h / 2), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.add_patch(plt.Circle((0.7, 0.5), 0.06, alpha=0.25))
    ax.text(0.7, 0.5, "Fusion\n(learned weights)", ha="center", va="center")
    ax.annotate("", xy=(0.76, 0.5), xytext=(0.82, 0.5), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.add_patch(plt.Rectangle((0.82, 0.42), 0.12, 0.16, alpha=0.25))
    ax.text(0.88, 0.5, "Classifier", ha="center", va="center")
    ax.set_title("Hierarchical Prompting Architecture (schematic)")
    plt.tight_layout()
    fig.savefig(path_out_png, dpi=300)
    fig.savefig(path_out_pdf)
    plt.close(fig)


def fig5_timeline(path_out_png: Path, path_out_pdf: Path) -> None:
    steps = [
        "Majority-class collapse\n(diagnosis)",
        "Dataset & label audits",
        "Concentration-guided\nconsolidation",
        "Training & calibration",
        "Ablations & robustness",
        "Cross-validation &\nmulti-seed confirmation",
    ]
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis('off')
    x = np.linspace(0.05, 0.95, len(steps))
    y = 0.5 * np.ones_like(x)
    ax.plot(x, y, lw=2)
    for xi, label in zip(x, steps):
        ax.add_patch(plt.Circle((xi, 0.5), 0.03, color="C0"))
        ax.text(xi, 0.33, label, ha="center", va="top")
    ax.set_title("Experimental Timeline and Audit Trail")
    plt.tight_layout()
    fig.savefig(path_out_png, dpi=300)
    fig.savefig(path_out_pdf)
    plt.close(fig)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, default=Path("scripts/figs_simple"))
    ap.add_argument("--prefer-real-figure1", action="store_true", help="Use real-image attention figure if generator available")
    args = ap.parse_args()

    data = load_results(args.results)
    args.outdir.mkdir(parents=True, exist_ok=True)

    # Figure 1
    fig1_png = args.outdir / "figure1.png"
    fig1_pdf = args.outdir / "figure1.pdf"
    used_real = False
    if args.prefer_real_figure1 and REAL_ATTENTION_AVAILABLE:
        try:
            fig1_attention_real(fig1_png, fig1_pdf)
            used_real = True
        except Exception:
            used_real = False
    if not used_real:
        fig1_attention_bar(fig1_png, fig1_pdf, data["attention"]["before"], data["attention"]["after"]) 

    # Figure 2
    fig2_performance(args.outdir / "figure2.png", args.outdir / "figure2.pdf", data["performance"], data.get("validation", {}))

    # Figure 3
    fig3_consolidation(args.outdir / "figure3.png", args.outdir / "figure3.pdf", data["counts"], data["weights"], data["performance"]) 

    # Figure 4
    fig4_hierarchical(args.outdir / "figure4.png", args.outdir / "figure4.pdf")

    # Figure 5
    fig5_timeline(args.outdir / "figure5.png", args.outdir / "figure5.pdf")

    print(f"Saved to {args.outdir.resolve()}")


if __name__ == "__main__":
    main()
