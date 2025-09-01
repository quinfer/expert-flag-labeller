#!/usr/bin/env python3
"""
Export dataset to author-style format (images + classnames.txt + train/val/test txts).

Inputs:
  --source-dir: dataset root (expects either JSON annotations+images/ or split txts+classnames.txt)
  --dest-dir: destination root to place exported dataset files
  --images-subdir: subdir with images (default: images)

When split files exist (train/val/test), they are copied; otherwise, a single
train.txt is generated from annotations.json with dummy split.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def load_classnames_from_annotations(ann_path: Path) -> list[str]:
    with ann_path.open("r", encoding="utf-8") as f:
        annotations = json.load(f)
    classes = set()
    for _, ann in annotations.items():
        if isinstance(ann, dict):
            label = ann.get("hierarchical_classname") or ann.get("classname") or ann.get("label")
            if label:
                classes.add(str(label))
    return sorted(classes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--dest-dir", required=True)
    ap.add_argument("--images-subdir", default="images")
    args = ap.parse_args()

    src = Path(args.source_dir).resolve()
    dst = Path(args.dest_dir).resolve()
    img_sub = args.images_subdir

    dst.mkdir(parents=True, exist_ok=True)

    # 1) copy/rsync images tree
    src_images = src / img_sub
    dst_images = dst / img_sub
    dst_images.mkdir(parents=True, exist_ok=True)

    # shallow copy; user can rsync externally for speed if needed
    for p in src_images.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src_images)
            outp = dst_images / rel
            outp.parent.mkdir(parents=True, exist_ok=True)
            if not outp.exists():
                shutil.copy2(p, outp)

    # 2) classnames and splits
    src_classnames = src / "classnames.txt"
    if src_classnames.exists():
        shutil.copy2(src_classnames, dst / "classnames.txt")
    else:
        ann = src / "annotations.json"
        if ann.exists():
            names = load_classnames_from_annotations(ann)
            (dst / "classnames.txt").write_text("\n".join(names) + "\n", encoding="utf-8")

    for split in ("train.txt", "val.txt", "test.txt"):
        p = src / split
        if p.exists():
            shutil.copy2(p, dst / split)

    print(f"Exported to {dst}")


if __name__ == "__main__":
    main()

