#!/usr/bin/env python3
"""
Thin wrapper to run the author baseline (final_code/train.py) on an exported dataset.

Example:
  python scripts/run_author_baseline.py \
    --dataset-root ../../final_code/datasets/NIFlagsV2 \
    --output-dir ../experiments/author_vith14_baseline \
    --config-file ../../final_code/configs/trainers/CoCoOp/vit_h14.yaml \
    --trainer CoCoOp

Note: Provide the correct config file and checkpoint via the author's mechanisms.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", required=True, help="Path passed as --root to author train.py (folder with images/, classnames.txt, train/val/test.txt)")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config-file", required=True)
    ap.add_argument("--trainer", default="CoCoOp")
    ap.add_argument("--extra-args", nargs=argparse.REMAINDER, default=[], help="Additional args for author train.py")
    args = ap.parse_args()

    train_py = Path(__file__).resolve().parents[2] / "final_code" / "train.py"

    cmd = [
        "python", str(train_py),
        "--root", str(Path(args.dataset_root).resolve()),
        "--output-dir", str(Path(args.output_dir).resolve()),
        "--config-file", str(Path(args.config_file).resolve()),
        "--trainer", args.trainer,
    ] + args.extra_args

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

