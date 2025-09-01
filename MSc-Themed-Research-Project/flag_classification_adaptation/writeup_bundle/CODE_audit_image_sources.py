#!/usr/bin/env python3
import os
import sys
import csv
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image


def main():
    # repo_root: .../expert-flag-labeler
    repo_root = Path(__file__).resolve().parents[3]
    # project_dir: .../expert-flag-labeler/MSc-Themed-Research-Project
    project_dir = repo_root / "MSc-Themed-Research-Project"

    # Paths
    dataset_images_dir = project_dir / "data" / "ni_flags" / "images"
    source_dirs = [
        repo_root / "public" / "images",
        repo_root / "data",
        repo_root / "flag_imagesCORRECT",
    ]

    # Safety checks
    if not dataset_images_dir.exists():
        print(f"Dataset images directory not found: {dataset_images_dir}")
        sys.exit(1)

    # Build quick filename lookup for sources
    print("Indexing source directories (by filename)...")
    filename_to_source_paths = defaultdict(list)
    for sdir in source_dirs:
        if not sdir.exists():
            print(f"  Skipping missing source dir: {sdir}")
            continue
        count = 0
        for root, _, files in os.walk(sdir):
            for fname in files:
                if not fname.lower().endswith('.jpg'):
                    continue
                filename_to_source_paths[fname].append(os.path.join(root, fname))
                count += 1
        print(f"  Indexed {count} images from {sdir}")

    # Iterate dataset images and infer chosen source (first match by priority)
    print("Scanning dataset images and inferring source...")
    source_priority = [str(p) for p in source_dirs]
    counts = Counter()
    multi_source = 0
    missing_in_sources = 0

    report_rows = []

    for fname in os.listdir(dataset_images_dir):
        if not fname.lower().endswith('.jpg'):
            continue
        dataset_path = dataset_images_dir / fname
        source_paths = filename_to_source_paths.get(fname, [])
        chosen_source = None
        chosen_path = None

        if len(source_paths) > 1:
            multi_source += 1

        # Choose by priority order
        for sdir in source_priority:
            for spath in source_paths:
                if spath.startswith(sdir):
                    chosen_source = sdir
                    chosen_path = spath
                    break
            if chosen_source:
                break

        if not chosen_source:
            missing_in_sources += 1
            chosen_source = "<not found in sources>"
            chosen_path = ""
        counts[chosen_source] += 1

        # Basic quality metrics
        try:
            with Image.open(dataset_path) as im:
                width, height = im.size
        except Exception:
            width, height = -1, -1

        file_size = dataset_path.stat().st_size if dataset_path.exists() else -1

        report_rows.append({
            "filename": fname,
            "chosen_source": chosen_source,
            "chosen_source_path": chosen_path,
            "also_found_in": ";".join(source_paths),
            "width": width,
            "height": height,
            "filesize_bytes": file_size,
        })

    # Print summary
    print("\nSource breakdown (inferred):")
    for src, cnt in counts.items():
        print(f"  {src}: {cnt}")
    print(f"  Multiple source candidates: {multi_source}")
    print(f"  Not found in any source dir: {missing_in_sources}")

    # Save CSV report next to dataset
    out_csv = project_dir / "data" / "ni_flags" / "image_sources_report.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(report_rows[0].keys()))
        writer.writeheader()
        writer.writerows(report_rows)
    print(f"\nReport written to: {out_csv}")

    # Simple quality flags
    low_res = sum(1 for r in report_rows if min(r["width"], r["height"]) != -1 and min(r["width"], r["height"]) < 128)
    tiny_file = sum(1 for r in report_rows if 0 < r["filesize_bytes"] < 10_000)  # <10KB
    print("\nQuality summary:")
    print(f"  Low-resolution images (min dim < 128px): {low_res}")
    print(f"  Very small files (<10KB): {tiny_file}")
    print("  Consider filtering or augmenting these before training.")


if __name__ == "__main__":
    main()

