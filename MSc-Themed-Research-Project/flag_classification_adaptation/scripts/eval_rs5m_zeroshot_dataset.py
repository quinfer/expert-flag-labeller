#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import torch
import open_clip
from PIL import Image
from tqdm import tqdm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True, help="Root folder that contains ni_flags_consolidated/")
    ap.add_argument("--ckpt", required=True, help="Path to RS5M_ViT-H-14.pt")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    # Build a minimal cfg-like object
    class _DS:
        ROOT: str = str(Path(args.data_root).resolve())

    class _Cfg:
        DATASET = _DS()

    # Import the training dataset class to reuse split logic
    from flag_classification_adaptation.datasets.ni_flags_consolidated import NIFlagsConsolidated

    dataset = NIFlagsConsolidated(_Cfg)
    test_items = dataset.test  # list of Datum with .impath and .label
    num_classes = len({d.label for d in (dataset.train_x + dataset.val + dataset.test)})

    device = torch.device(args.device)
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-H-14", pretrained="laion2b_s32b_b79k")
    ckpt = torch.load(args.ckpt, map_location="cpu")
    model.load_state_dict(ckpt, strict=False)
    model = model.to(device).eval()
    tokenizer = open_clip.get_tokenizer("ViT-H-14")

    # Build class prompts from dataset classnames if available
    # Try to read classnames.txt under data/ni_flags_consolidated
    classnames_path = Path(args.data_root).resolve() / "ni_flags_consolidated" / "classnames.txt"
    if classnames_path.exists():
        classnames = [l.strip() for l in classnames_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        # Fallback to numeric labels
        classnames = [str(i) for i in range(num_classes)]

    prompts = [f"a photo of {name}" for name in classnames]
    text_tokens = tokenizer(prompts).to(device)
    with torch.no_grad():
        text_feats = model.encode_text(text_tokens)
        text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)

    y_true: List[int] = []
    y_pred: List[int] = []

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    with torch.no_grad():
        for batch in tqdm(chunks(test_items, args.batch_size), total=(len(test_items)+args.batch_size-1)//args.batch_size, desc="Zero-shot eval (consolidated)"):
            imgs = []
            labels = []
            for d in batch:
                img = Image.open(d.impath).convert("RGB")
                imgs.append(preprocess(img))
                labels.append(int(d.label))
            image_tensor = torch.stack(imgs, dim=0).to(device)
            img_feats = model.encode_image(image_tensor)
            img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)
            logits = 100.0 * img_feats @ text_feats.T
            preds = logits.argmax(dim=-1).tolist()
            y_pred.extend(preds)
            y_true.extend(labels)

    import numpy as np
    from sklearn.metrics import f1_score
    acc = float((np.array(y_pred) == np.array(y_true)).mean())
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))

    out = {
        "dataset": "ni_flags_consolidated",
        "num_classes": len(classnames),
        "num_test": len(test_items),
        "top1_accuracy": acc,
        "macro_f1": macro_f1,
    }
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "zero_shot_metrics_consolidated.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

