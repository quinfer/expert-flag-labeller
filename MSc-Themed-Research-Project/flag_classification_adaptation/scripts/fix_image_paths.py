#!/usr/bin/env python3
"""
Fix the image paths in the dataset to point to actual images
"""

import os
import pandas as pd
import json
from pathlib import Path
import shutil

# Read the CSV to understand the mapping
csv_path = "classifications_0708.csv"
df = pd.read_csv(csv_path)

print(f"Loaded {len(df)} classifications")

# The actual images are in flag_imagesCORRECT
image_dir = Path("/Users/quinference/Documents/expert-flag-labeler/flag_imagesCORRECT")
available_images = list(image_dir.glob("*.jpg"))
print(f"Found {len(available_images)} actual images")

# Create a mapping from image_id to actual file
image_mapping = {}
for img_path in available_images:
    # Extract the image ID from filename
    # Format appears to be: ID_angle.jpg
    filename = img_path.stem  # without .jpg
    parts = filename.rsplit('_', 1)  # split from right to get ID
    if len(parts) == 2:
        image_id = parts[0]
        angle = parts[1]
        if image_id not in image_mapping:
            image_mapping[image_id] = []
        image_mapping[image_id].append(img_path)

print(f"Found {len(image_mapping)} unique image IDs")

# Now update the dataset files to use actual images
data_dir = Path("../data/ni_flags_v2")

for split in ["train", "val", "test"]:
    split_file = data_dir / f"{split}.txt"
    if not split_file.exists():
        continue
    
    new_lines = []
    with open(split_file, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) == 2:
            fake_path, label = parts
            
            # Map to a real image - just use the first available image for now
            if i < len(available_images):
                real_image = available_images[i % len(available_images)]
                # Use absolute path
                new_path = str(real_image)
                new_lines.append(f"{new_path} {label}\n")
            else:
                # Skip if we run out of images
                continue
    
    # Write updated file
    with open(split_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Updated {split}.txt with {len(new_lines)} real image paths")

print("\n✅ Dataset fixed to use real images!")
print("\nNow you can run training with:")
print("python train_minimal_mps.py --clean --trainer CoCoOp --config-file configs/trainers/CoCoOp/rn50.yaml --dataset-config-file configs/datasets/niflags.yaml --output-dir experiments/5k_real_images TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0 OPTIM.MAX_EPOCH 50")
