#!/usr/bin/env python3
import argparse
import json
import random
import shutil
from pathlib import Path


def create_subset(source_dir: Path, dest_dir: Path, num_classes: int, samples_per_class: int, seed: int = 1):
    rng = random.Random(seed)

    src_images = source_dir / "images"
    src_annotations = source_dir / "annotations.json"
    assert src_images.exists(), f"Missing images dir: {src_images}"
    assert src_annotations.exists(), f"Missing annotations.json: {src_annotations}"

    with open(src_annotations, "r") as f:
        annotations = json.load(f)

    # Group images by hierarchical_classname
    class_to_imgs = {}
    for fname, meta in annotations.items():
        cls = meta["hierarchical_classname"]
        class_to_imgs.setdefault(cls, []).append(fname)

    # Pick classes (top by count to ensure availability)
    sorted_classes = sorted(class_to_imgs.items(), key=lambda kv: len(kv[1]), reverse=True)
    chosen_classes = [c for c, _ in sorted_classes[:num_classes]]

    subset_annotations = {}
    dest_images = dest_dir / "images"
    dest_images.mkdir(parents=True, exist_ok=True)

    for cls in chosen_classes:
        imgs = class_to_imgs[cls]
        rng.shuffle(imgs)
        take = imgs[:samples_per_class]
        for fname in take:
            src_path = src_images / fname
            if not src_path.exists():
                continue
            shutil.copy2(src_path, dest_images / fname)
            subset_annotations[fname] = annotations[fname]

    # Write annotations and classnames
    with open(dest_dir / "annotations.json", "w") as f:
        json.dump(subset_annotations, f, indent=2)

    classnames = sorted({meta["hierarchical_classname"] for meta in subset_annotations.values()})
    with open(dest_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(name + "\n")

    # Basic stats
    total = len(subset_annotations)
    print(f"Created overfit subset at {dest_dir} with {total} images across {len(classnames)} classes")


def main():
    # repo_root/MSc-Themed-Research-Project/flag_classification_adaptation/scripts
    scripts_dir = Path(__file__).resolve().parent
    project_dir = scripts_dir.parents[1]

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default=str(project_dir / "data" / "ni_flags"), help="Path to source dataset root (contains images/ + annotations.json)")
    parser.add_argument("--dest", type=str, default=str(project_dir / "data" / "ni_flags_overfit"), help="Destination subset root (will create '<dest>/ni_flags')")
    parser.add_argument("--num-classes", type=int, default=3)
    parser.add_argument("--samples-per-class", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    # Conform to NIFlags loader which expects root/<dataset_dir> where dataset_dir is 'ni_flags'
    dest_root = Path(args.dest)
    dest_dataset = dest_root / "ni_flags"
    create_subset(Path(args.source), dest_dataset, args.num_classes, args.samples_per_class, seed=args.seed)
    print(f"Note: Set --root to '{dest_root}' when training (loader will find '{dest_dataset.name}')")


if __name__ == "__main__":
    main()

