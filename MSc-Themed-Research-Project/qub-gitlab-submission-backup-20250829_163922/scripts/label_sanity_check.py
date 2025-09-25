#!/usr/bin/env python3
"""
Label Sanity Check

Purpose:
  Quickly sample images per class and generate an HTML gallery to manually verify
  that labels describe the underlying images in a dataset.

Supported dataset layouts:
  1) JSON annotations (default):
     <dataset_dir>/annotations.json with keys = image relative paths and values containing
     a class field (tries hierarchical_classname, classname, label).
     Images are expected under <dataset_dir>/images/.

  2) Folder-per-class fallback:
     <dataset_dir>/<images_subdir>/<class_name>/*.jpg

Usage:
  python scripts/label_sanity_check.py \
    --dataset-dir data/ni_flags_consolidated \
    --samples-per-class 12

Outputs:
  - <dataset_dir>/sanity_checks/label_sanity_<dataset>_<timestamp>.html
  - <dataset_dir>/sanity_checks/label_sanity_<dataset>_<timestamp>.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


CLASS_FIELD_CANDIDATES = [
    "hierarchical_classname",
    "classname",
    "class_name",
    "label",
]


@dataclass
class SampledItem:
    image_path: Path  # absolute path to image file
    rel_path: str     # relative path from images root
    class_name: str


def infer_base_label(annotation: dict) -> str:
    # Prefer explicit base fields if present
    if "original_classname" in annotation and annotation["original_classname"]:
        return str(annotation["original_classname"]) or "unknown"
    cat = str(annotation.get("category", "nan"))
    ctx = str(annotation.get("context", "nan"))
    flag = str(annotation.get("specific_flag", "nan"))
    base = f"{cat}-{ctx}-{flag}"
    if base != "nan-nan-nan":
        return base
    # Fallback to any known class field
    for key in CLASS_FIELD_CANDIDATES:
        if key in annotation:
            return str(annotation[key])
    return "unknown"


def infer_consolidated_label(annotation: dict) -> str:
    for key in CLASS_FIELD_CANDIDATES:
        if key in annotation:
            return str(annotation[key])
    # Fallback to base format if consolidated not present
    return infer_base_label(annotation)


def load_from_annotations(dataset_dir: Path, images_subdir: str, annotations_file: str, label_mode: str) -> Dict[str, List[SampledItem]]:
    ann_path = dataset_dir / annotations_file
    if not ann_path.exists():
        return {}

    images_root = dataset_dir / images_subdir
    with ann_path.open("r") as f:
        annotations = json.load(f)

    class_to_items: Dict[str, List[SampledItem]] = {}
    for rel_img_path, ann in annotations.items():
        if not isinstance(ann, dict):
            # Some formats might store label inline
            ann = {"label": ann}
        if label_mode == "base":
            class_name = infer_base_label(ann)
        elif label_mode == "consolidated":
            class_name = infer_consolidated_label(ann)
        else:  # auto
            # Prefer base if fields exist
            if any(k in ann for k in ("original_classname", "category", "context", "specific_flag")):
                class_name = infer_base_label(ann)
            else:
                class_name = infer_consolidated_label(ann)
        abs_path = images_root / rel_img_path
        item = SampledItem(image_path=abs_path, rel_path=rel_img_path, class_name=class_name)
        class_to_items.setdefault(class_name, []).append(item)
    return class_to_items


def load_from_folder_structure(dataset_dir: Path, images_subdir: str) -> Dict[str, List[SampledItem]]:
    images_root = dataset_dir / images_subdir
    if not images_root.exists():
        return {}

    class_to_items: Dict[str, List[SampledItem]] = {}
    for class_dir in sorted([p for p in images_root.glob("*") if p.is_dir()]):
        class_name = class_dir.name
        for img_path in sorted(class_dir.rglob("*")):
            if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                rel_path = img_path.relative_to(images_root).as_posix()
                class_to_items.setdefault(class_name, []).append(
                    SampledItem(image_path=img_path, rel_path=rel_path, class_name=class_name)
                )
    return class_to_items


def load_from_splits(dataset_dir: Path, images_subdir: str) -> Dict[str, List[SampledItem]]:
    """Load class labels from train/val/test split files and classnames.txt.
    Expected format (per line): "images/xxx.jpg <class_index>"
    Class names loaded from classnames.txt (one per line).
    """
    classnames_path = dataset_dir / "classnames.txt"
    train_path = dataset_dir / "train.txt"
    val_path = dataset_dir / "val.txt"
    test_path = dataset_dir / "test.txt"

    if not (classnames_path.exists() and (train_path.exists() or val_path.exists() or test_path.exists())):
        return {}

    # Load class names
    with classnames_path.open("r", encoding="utf-8") as f:
        classnames = [line.strip() for line in f if line.strip()]

    def read_split_file(p: Path) -> List[Tuple[str, int]]:
        pairs: List[Tuple[str, int]] = []
        if not p.exists():
            return pairs
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                img_rel, idx_str = parts[0], parts[1]
                try:
                    class_idx = int(idx_str)
                except ValueError:
                    continue
                pairs.append((img_rel, class_idx))
        return pairs

    images_root = dataset_dir / images_subdir
    all_pairs = read_split_file(train_path) + read_split_file(val_path) + read_split_file(test_path)

    class_to_items: Dict[str, List[SampledItem]] = {}
    for rel_img_path, class_idx in all_pairs:
        if 0 <= class_idx < len(classnames):
            class_name = classnames[class_idx]
        else:
            class_name = f"class_{class_idx}"
        abs_path = images_root / rel_img_path
        item = SampledItem(image_path=abs_path, rel_path=rel_img_path, class_name=class_name)
        class_to_items.setdefault(class_name, []).append(item)
    return class_to_items


def sample_items(class_to_items: Dict[str, List[SampledItem]], samples_per_class: int, seed: int) -> Dict[str, List[SampledItem]]:
    rng = random.Random(seed)
    sampled: Dict[str, List[SampledItem]] = {}
    for class_name, items in class_to_items.items():
        if not items:
            continue
        if len(items) <= samples_per_class:
            chosen = list(items)
        else:
            chosen = rng.sample(items, samples_per_class)
        sampled[class_name] = chosen
    return sampled


def write_csv(sampled: Dict[str, List[SampledItem]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class_name", "relative_image_path", "absolute_image_path"])
        for class_name in sorted(sampled.keys()):
            for item in sampled[class_name]:
                writer.writerow([class_name, item.rel_path, str(item.image_path)])


def write_html(sampled: Dict[str, List[SampledItem]], dataset_dir: Path, out_html: Path) -> None:
    out_html.parent.mkdir(parents=True, exist_ok=True)
    html_dir = out_html.parent

    def escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    parts: List[str] = []
    parts.append("<!doctype html>")
    parts.append("<meta charset=\"utf-8\">")
    parts.append("<title>Label Sanity Check</title>")
    parts.append(
        """
<style>
body{font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;}
.class-block{margin: 18px 0;}
.class-title{font-weight: 600; font-size: 16px; margin-bottom: 8px;}
.grid{display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 8px;}
.card{border: 1px solid #ddd; border-radius: 8px; padding: 6px;}
.cap{font-size: 12px; color: #333; margin-top: 4px; word-break: break-all;}
img{width: 100%; height: 140px; object-fit: cover; border-radius: 4px; background: #f5f5f5;}
</style>
        """.strip()
    )
    parts.append("<h2>Label Sanity Check</h2>")
    parts.append(f"<p>Dataset: {escape(str(dataset_dir))}</p>")

    for class_name in sorted(sampled.keys()):
        parts.append("<div class=\"class-block\">")
        parts.append(f"<div class=\"class-title\">Class: {escape(class_name)} (n={len(sampled[class_name])})</div>")
        parts.append("<div class=\"grid\">")
        for item in sampled[class_name]:
            # Compute path relative to the HTML file location
            try:
                rel_src = os.path.relpath(str(item.image_path), start=str(html_dir))
            except (ValueError, OSError):
                # Fallback to absolute file URL
                rel_src = str(item.image_path)
            parts.append("<div class=\"card\">")
            parts.append(f"<a href=\"{escape(rel_src)}\" target=\"_blank\"><img src=\"{escape(rel_src)}\" loading=\"lazy\"></a>")
            parts.append(f"<div class=\"cap\">{escape(item.rel_path)}</div>")
            parts.append("</div>")
        parts.append("</div>")
        parts.append("</div>")

    out_html.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an HTML gallery to sanity-check labels vs images.")
    parser.add_argument("--dataset-dir", required=True, help="Path to the dataset directory (e.g., data/ni_flags_consolidated)")
    parser.add_argument("--annotations", default="annotations.json", help="Annotations filename to look for (default: annotations.json)")
    parser.add_argument("--images-subdir", default="images", help="Subdirectory containing images (default: images)")
    parser.add_argument("--samples-per-class", type=int, default=12, help="Number of images to sample per class (default: 12)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--label-mode", choices=["auto", "base", "consolidated"], default="base", help="Labeling mode for JSON annotations (default: base)")

    args = parser.parse_args()
    dataset_dir = Path(args.dataset_dir).resolve()

    # Load class -> items mapping
    # Prefer split files + classnames when present (e.g., ni_flags_v2)
    class_to_items = load_from_splits(dataset_dir, args.images_subdir)
    if not class_to_items:
        class_to_items = load_from_annotations(dataset_dir, args.images_subdir, args.annotations, args.label_mode)
    if not class_to_items:
        class_to_items = load_from_folder_structure(dataset_dir, args.images_subdir)
    if not class_to_items:
        raise SystemExit(f"Could not locate annotations or folder-per-class images under: {dataset_dir}")

    # Sample
    sampled = sample_items(class_to_items, args.samples_per_class, args.seed)

    # Outputs
    dataset_name = dataset_dir.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = dataset_dir / "sanity_checks"
    out_html = out_dir / f"label_sanity_{dataset_name}_{timestamp}.html"
    out_csv = out_dir / f"label_sanity_{dataset_name}_{timestamp}.csv"

    write_csv(sampled, out_csv)
    write_html(sampled, dataset_dir, out_html)

    print(f"Wrote HTML: {out_html}")
    print(f"Wrote CSV:  {out_csv}")
    print("Open the HTML in a browser and visually confirm label correctness.")


if __name__ == "__main__":
    main()

