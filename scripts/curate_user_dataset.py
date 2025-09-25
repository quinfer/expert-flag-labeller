#!/usr/bin/env python3
"""
Curate a user-specific static image set from an existing classification queue.

This script:
- Loads a classification queue (JSON produced by prepare_images_for_classification.py)
- Optionally filters by minimum confidence
- Excludes any filenames present in a provided static-images JSON (e.g., Pat's set)
- Optionally downsamples to a target sample size
- Verifies files exist in the public directory (copying from data/cropped_images if needed)
- Emits a static-images-{user}.json for the frontend/API to serve

Usage:
  python scripts/curate_user_dataset.py \
    --user Mai \
    --input-queue data/classification_queue_mai.json \
    --output-json src/data/static-images-mai.json \
    --exclude-json src/data/static-images-pat.json \
    --min-confidence 0.8 \
    --sample-size 2000 \
    --public-dir public/images-mai \
    --web-path /images-mai

Notes:
- This script is non-destructive. It only copies missing files if needed.
- It expects the queue entries to have web-paths for cropped/composite images.
"""

import argparse
import json
import os
import random
import shutil
from typing import List, Dict, Any, Set


def parse_args():
    p = argparse.ArgumentParser(description='Curate user-specific static image set')
    p.add_argument('--user', required=True, help='User identifier (e.g., Mai)')
    p.add_argument('--input-queue', required=True, help='Path to classification queue JSON')
    p.add_argument('--output-json', required=True, help='Output static-images-<user>.json path')
    p.add_argument('--exclude-json', help='Path to static-images JSON whose filenames to exclude (e.g., Pat)')
    p.add_argument('--min-confidence', type=float, default=0.8, help='Minimum confidence filter')
    p.add_argument('--sample-size', type=int, default=2000, help='Target number of images')
    p.add_argument('--public-dir', default='public/images-<user>', help='Public dir to verify/copy files')
    p.add_argument('--web-path', default='/images-<user>', help='Web path base for the curated files')
    p.add_argument('--exclude-classifications-csv', help='CSV export of prior classifications to exclude')
    p.add_argument('--exclude-classified-by', default='any', help='Username to exclude (e.g., May), or "any"')
    return p.parse_args()


def load_queue(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)


def load_exclude_filenames(path: str) -> Set[str]:
    """Load filenames to exclude from a static-images JSON list.
    Returns an empty set if path missing or unreadable.
    """
    excluded: Set[str] = set()
    if not path or not os.path.exists(path):
        return excluded
    try:
        data = json.load(open(path, 'r'))
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    fn = item.get('filename')
                    if fn:
                        excluded.add(fn)
    except Exception:
        # Fall back to empty set on any error
        return excluded
    return excluded

def load_classified_filenames_from_csv(path: str, only_user: str) -> Set[str]:
    excluded: Set[str] = set()
    if not path or not os.path.exists(path):
        return excluded
    try:
        import csv
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fn = row.get('image_id')
                expert = (row.get('expert_id') or '').strip()
                if not fn:
                    continue
                if only_user == 'any' or expert.lower() == only_user.lower():
                    excluded.add(fn)
    except Exception:
        pass
    return excluded


def ensure_file_exists(web_path: str, public_dir: str) -> bool:
    """Ensure web_path (e.g., /images-mai/TOWN/file.jpg) exists under public_dir.
    If missing in public_dir, try to copy from data/cropped_images_for_classification.
    """
    # Convert web_path to filesystem path under public_dir
    # web_path looks like /images-mai/TOWN/filename
    parts = web_path.strip('/').split('/')
    if len(parts) < 2:
        return False
    town = parts[-2]
    filename = parts[-1]
    dest_dir = os.path.join(public_dir, town)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path):
        return True

    # Attempt to copy from data/cropped_images_for_classification/{TOWN}/{filename}
    src_path = os.path.join('data', 'cropped_images_for_classification', town, filename)
    if os.path.exists(src_path):
        try:
            shutil.copy2(src_path, dest_path)
            return True
        except Exception:
            return False
    return False


def main():
    args = parse_args()

    public_dir = args.public_dir.replace('<user>', args.user.lower())
    web_path_base = args.web_path.replace('<user>', args.user.lower())

    os.makedirs(public_dir, exist_ok=True)

    queue = load_queue(args.input_queue)
    images: List[Dict[str, Any]] = queue.get('images', [])

    exclude_fns = load_exclude_filenames(args.exclude_json)
    classified_exclude = load_classified_filenames_from_csv(
        args.exclude_classifications_csv, args.exclude_classified_by.strip().lower()
    )

    # Filter by min confidence and exclusion set
    candidates = []
    for img in images:
        fn = img.get('filename')
        conf = float(img.get('confidence', 0.0))
        if not fn or conf < args.min_confidence:
            continue
        if fn in exclude_fns:
            continue
        if classified_exclude and fn in classified_exclude:
            continue
        candidates.append(img)

    if not candidates:
        print('No candidates after filtering; nothing to do.')
        return

    random.shuffle(candidates)
    selected = candidates[: args.sample_size]

    # Verify files exist (copy if needed)
    curated: List[Dict[str, Any]] = []
    for img in selected:
        town = img.get('town')
        cropped_web = img.get('cropped_image')
        comp_web = img.get('composite_image')
        filename = img.get('filename')

        # Normalize to this user's web path base
        # Replace any leading '/images' or custom path with our web_path_base
        # Keep town and filename segments
        if cropped_web and isinstance(cropped_web, str):
            parts = cropped_web.strip('/').split('/')
            if len(parts) >= 2:
                cropped_web = f"{web_path_base}/{parts[-2]}/{parts[-1]}"
        if comp_web and isinstance(comp_web, str):
            parts = comp_web.strip('/').split('/')
            if len(parts) >= 2:
                comp_web = f"{web_path_base}/{parts[-2]}/{parts[-1]}"

        # Ensure files exist under our public_dir
        ok1 = ensure_file_exists(cropped_web, public_dir) if cropped_web else False
        ok2 = ensure_file_exists(comp_web, public_dir) if comp_web else False

        curated.append({
            'town': town,
            'path': cropped_web,
            'filename': filename,
            'composite_image': comp_web if ok2 else None,
            'has_composite': bool(comp_web) and ok2
        })

    # Write static-images-<user>.json
    with open(args.output_json, 'w') as f:
        json.dump(curated, f, indent=2)

    print(f"Curated {len(curated)} images to {args.output_json}")
    print(f"Public directory: {public_dir}")


if __name__ == '__main__':
    main()
