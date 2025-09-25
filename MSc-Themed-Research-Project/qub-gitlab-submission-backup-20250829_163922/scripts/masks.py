import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import numpy as np
from PIL import Image

MASK_SUFFIXES = ["_mask.png", "_seg.png", "_mask.jpg"]


def _find_mask_path(image_path: str) -> Optional[Path]:
    p = Path(image_path)
    stem = p.stem
    for suf in MASK_SUFFIXES:
        cand = p.with_name(stem + suf)
        if cand.exists():
            return cand
    # Also support sibling 'masks' dir
    masks_dir = p.parent / "masks"
    for suf in MASK_SUFFIXES:
        cand = masks_dir / (stem + suf)
        if cand.exists():
            return cand
    return None


def _load_bbox_data() -> Dict[str, List]:
    """Load all bounding box data from JSON files."""
    bbox_data = {}
    
    # Find all bbox JSON files
    data_dir = Path("/Users/quinference/Documents/expert-flag-labeler/data/true_positive_images")
    for json_file in data_dir.glob("*/true_positive_bboxes_hf_*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Data structure: {filename: [bbox_objects]}
                for filename, bbox_list in data.items():
                    bbox_data[filename] = bbox_list
        except Exception as e:
            print(f"⚠️  Error loading {json_file}: {e}")
    
    return bbox_data


def _create_mask_from_bbox(image_path: str, target_size: Tuple[int, int] = (224, 224)) -> Optional[np.ndarray]:
    """
    Create a mask from bounding box data for cropped images.
    
    Args:
        image_path: Path to the cropped image (e.g., "image_240_box0.jpg")
        target_size: Target mask size (height, width)
        
    Returns:
        Boolean mask array or None if no bbox data found
    """
    path_obj = Path(image_path)
    filename = path_obj.name
    
    # Extract original filename and box info from cropped filename
    # Format: "originalname_size_boxN.jpg"
    if "_box" not in filename:
        return None
    
    # Parse filename to get original image name and box number
    parts = filename.split("_")
    if len(parts) < 3:
        return None
    
    # Reconstruct original filename (everything before the boxN part)
    original_parts = parts[:-1]  # Remove only boxN part, keep size
    original_name = "_".join(original_parts) + ".jpg"
    
    # Get box number
    try:
        box_part = parts[-1]  # e.g., "box0.jpg"
        box_num = int(box_part.replace("box", "").replace(".jpg", ""))
    except (ValueError, IndexError):
        return None
    
    # Load bbox data
    bbox_data = _load_bbox_data()
    
    if original_name not in bbox_data:
        return None
    
    bboxes = bbox_data[original_name]
    
    if box_num >= len(bboxes):
        return None
    
    # Get the specific bounding box
    bbox = bboxes[box_num]
    
    # Create mask - for cropped images, the entire crop is essentially the "flag area"
    # So we create a central mask that covers most of the cropped region
    mask = np.zeros(target_size, dtype=bool)
    
    # Create a central region mask (80% of the image, centered)
    h, w = target_size
    margin_h, margin_w = int(h * 0.1), int(w * 0.1)
    mask[margin_h:h-margin_h, margin_w:w-margin_w] = True
    
    return mask


def load_mask(image_path: str) -> np.ndarray:
    """
    Load a boolean mask for the given image_path.
    For cropped images, creates mask from bounding box data.
    If no mask exists, returns an all-False mask with same HxW as a 224x224 default.
    """
    # First try to find existing mask files
    mask_path = _find_mask_path(image_path)
    if mask_path and mask_path.exists():
        m = Image.open(mask_path).convert("L")
        arr = np.array(m)
        # Nonzero considered mask True
        mask = arr > 0
        return mask
    
    # For cropped images (_box0, _box1, etc.), create mask from bbox data
    if "_box" in str(image_path):
        bbox_mask = _create_mask_from_bbox(image_path)
        if bbox_mask is not None:
            return bbox_mask
    
    # Default fallback size (224x224) if not available
    return np.zeros((224, 224), dtype=bool)


def on_mask_attention(attn: np.ndarray, mask: np.ndarray) -> float:
    """
    Compute proportion of attention mass on-mask: sum(attn[mask]) / sum(attn)
    Safeguards for zero sums and shape mismatches (resizes mask if needed).
    """
    if attn.ndim != 2:
        raise ValueError("attn must be 2D")
    if mask.shape != attn.shape:
        # naive resize using nearest neighbor
        from PIL import Image
        mask_img = Image.fromarray(mask.astype(np.uint8) * 255)
        mask_resized = mask_img.resize((attn.shape[1], attn.shape[0]), Image.NEAREST)
        mask = np.array(mask_resized) > 0
    total = float(attn.sum())
    if total <= 0:
        return 0.0
    onmask = float(attn[mask].sum())
    return onmask / total
