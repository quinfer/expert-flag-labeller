#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List, Tuple

import torch
import open_clip
from PIL import Image
from tqdm import tqdm
from sklearn.metrics import f1_score


def load_classnames(root: Path) -> List[str]:
    lines = (root / "classnames.txt").read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip()]


def load_split(split_file: Path) -> Tuple[List[str], List[int]]:
    img_paths: List[str] = []
    labels: List[int] = []
    with split_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            img_paths.append(parts[0])
            labels.append(int(parts[1]))
    return img_paths, labels


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", required=True, help="Path to author-format dataset root (images/, classnames.txt, test.txt)")
    ap.add_argument("--ckpt", required=True, help="Path to RS5M_ViT-H-14.pt")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--out-dir", default="")
    args = ap.parse_args()

    dataset_root = Path(args.dataset_root).resolve()
    images_dir = dataset_root / "images"
    classnames = load_classnames(dataset_root)
    test_imgs, test_labels = load_split(dataset_root / "test.txt")

    device = torch.device(args.device)

    model, _, preprocess = open_clip.create_model_and_transforms("ViT-H-14", pretrained="laion2b_s32b_b79k")
    # Load RS5M checkpoint
    ckpt = torch.load(args.ckpt, map_location="cpu")
    model.load_state_dict(ckpt, strict=False)
    model = model.to(device).eval()

    tokenizer = open_clip.get_tokenizer("ViT-H-14")
    # Use class names directly as prompts
    prompts = [f"a photo of {name}" for name in classnames]
    text_tokens = tokenizer(prompts)
    text_tokens = text_tokens.to(device)
    text_feats = model.encode_text(text_tokens)
    text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)

    y_true: List[int] = []
    y_pred: List[int] = []

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    for batch_paths, batch_labels in tqdm(zip(chunks(test_imgs, args.batch_size), chunks(test_labels, args.batch_size)), total=(len(test_imgs)+args.batch_size-1)//args.batch_size, desc="Zero-shot eval"):
        imgs = []
        for rel in batch_paths:
            rel_path = Path(rel)
            # Handle entries that already include the leading 'images/' segment
            if len(rel_path.parts) > 0 and rel_path.parts[0] == "images":
                rel_path = Path(*rel_path.parts[1:])
            img_path = images_dir / rel_path
            img = Image.open(img_path).convert("RGB")
            imgs.append(preprocess(img))
        image_tensor = torch.stack(imgs, dim=0).to(device)
        img_feats = model.encode_image(image_tensor)
        img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)
        logits = 100.0 * img_feats @ text_feats.T
        preds = logits.argmax(dim=-1).tolist()
        y_pred.extend(preds)
        y_true.extend(batch_labels)

    # Metrics
    import numpy as np
    acc = float((np.array(y_pred) == np.array(y_true)).mean())
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))

    out = {
        "num_classes": len(classnames),
        "num_test": len(test_imgs),
        "top1_accuracy": acc,
        "macro_f1": macro_f1,
    }

    out_dir = Path(args.out_dir) if args.out_dir else (Path(__file__).resolve().parents[1] / "experiments" / "author_vith14_baseline")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "zero_shot_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

