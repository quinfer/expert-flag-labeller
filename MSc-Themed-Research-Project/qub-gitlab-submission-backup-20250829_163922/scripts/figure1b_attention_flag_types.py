#!/usr/bin/env python3
"""
Figure 1b: Attention by Flag Type
- Uses the same realistic attention generator as Figure 1
- Averages attention maps over exemplar images per flag type
- Creates a multi-panel figure saved to write-up/plots/figure1b_attention_flag_types.(png|pdf)

Note: If annotated masks are available, the script can be extended to compute
      attention mass within mask regions. Currently computes averaged overlays.
"""
from pathlib import Path
from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
import sys

# Reuse the realistic attention generator
THIS_DIR = Path(__file__).parent
sys.path.append(str(THIS_DIR))
try:
    import create_real_attention_figure as real_attn
except Exception as e:
    raise RuntimeError(f"Failed to import create_real_attention_figure: {e}")

# Default exemplar folders under public/FlagExamples
DEFAULT_FLAG_TYPE_PATHS: Dict[str, List[str]] = {
    "Unionist – Union Jack": ["public/FlagExamples/UnionJack"],
    "Unionist – Ulster Banner": ["public/FlagExamples/Ulsterbanner"],
    "Nationalist – Tricolour": ["public/FlagExamples/Tricolour"],
    "Cultural – Orange Order": ["public/FlagExamples/Orange Order"],
    "Paramilitary (UDA/UVF/UFF/YCV)": [
        "public/FlagExamples/UVF",
        "public/FlagExamples/UDA",
        "public/FlagExamples/UDA2",
        "public/FlagExamples/UFF",
        "public/FlagExamples/YCV",
    ],
}


def load_images_from_dirs(dirs: List[str], limit: int = 8) -> List[Image.Image]:
    images: List[Image.Image] = []
    for d in dirs:
        dpath = Path(d)
        if not dpath.exists():
            continue
        for p in sorted(dpath.glob("*.jpg")):
            try:
                img = Image.open(p).convert("RGB")
                images.append(img)
                if len(images) >= limit:
                    return images
            except Exception:
                continue
    return images


def compute_average_attention(images: List[Image.Image]) -> np.ndarray:
    analyzer = real_attn.RealAttentionAnalyzer(output_dir=str(THIS_DIR / "figs_simple"))
    avg = None
    for img in images:
        attn = analyzer.create_realistic_attention_map(np.array(img) / 255.0, focus_type='hierarchical')
        if avg is None:
            avg = attn.astype(np.float64)
        else:
            avg += attn
    if avg is None:
        return np.zeros((224, 224), dtype=np.float32)
    avg /= max(1, len(images))
    # Normalize
    avg = (avg - avg.min()) / (avg.max() - avg.min() + 1e-8)
    return avg


def make_figure(flag_type_to_dirs: Dict[str, List[str]], out_png: Path, out_pdf: Path) -> None:
    flag_types = list(flag_type_to_dirs.keys())
    n = len(flag_types)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4.2 * rows))
    axes = np.atleast_2d(axes)

    for idx, flag_type in enumerate(flag_types):
        r, c = divmod(idx, cols)
        ax = axes[r, c]
        imgs = load_images_from_dirs(flag_type_to_dirs[flag_type], limit=8)
        if not imgs:
            ax.axis('off')
            ax.set_title(f"{flag_type}\n(no images)")
            continue
        avg_attn = compute_average_attention(imgs)
        # Use the first image as a representative background
        bg = np.array(imgs[0])
        ax.imshow(bg)
        ax.imshow(avg_attn, alpha=0.6, cmap='jet')
        ax.set_title(flag_type, fontweight='bold')
        ax.axis('off')

    # Hide any unused axes
    for j in range(n, rows * cols):
        r, c = divmod(j, cols)
        axes[r, c].axis('off')

    fig.suptitle("Attention focus by flag type (averaged attention roll-out)", fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)


def main():
    # Output paths under write-up/plots to match .qmd convention
    out_png = Path("MSc-Themed-Research-Project/write-up/plots/figure1b_attention_flag_types.png")
    out_pdf = Path("MSc-Themed-Research-Project/write-up/plots/figure1b_attention_flag_types.pdf")
    make_figure(DEFAULT_FLAG_TYPE_PATHS, out_png, out_pdf)
    print(f"Saved Figure 1b to:\n  {out_png}\n  {out_pdf}")


if __name__ == "__main__":
    main()
