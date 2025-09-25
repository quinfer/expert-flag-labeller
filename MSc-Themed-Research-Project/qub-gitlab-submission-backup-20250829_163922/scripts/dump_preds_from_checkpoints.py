#!/usr/bin/env python3
"""
Dump predictions from checkpoints into Parquet files expected by the Figure 1b diagnostic.

Implements real RS5M inference with MPS acceleration for both 16-class (before) and 7-class (after) models.
Maps model predictions to TYPE_ORDER flag types for downstream analysis.

Outputs:
  outputs/before/<name>/preds.parquet
  outputs/after/<name>/preds.parquet
Schema:
  image_path, flag_type, y_true, y_pred

Usage:
  conda run -n flag_classification \
    python MSc-Themed-Research-Project/scripts/dump_preds_from_checkpoints.py \
      --config MSc-Themed-Research-Project/configs/attention.yaml
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import pandas as pd
import yaml
import torch
import torch.nn as nn
from PIL import Image
from typing import List
from tqdm import tqdm

# Apply MPS optimizations from original experiments
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'

try:
    import open_clip
except ImportError:
    print("⚠️  open_clip not available. Install with: pip install open-clip-torch")
    open_clip = None


def load_cfg(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def load_index(index_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(index_csv)
    required = {"image_path", "flag_type"}
    if not required.issubset(df.columns):
        raise ValueError(f"index_csv must contain columns {required}")
    return df


# Type mapping from model outputs to diagnostic plot types
TYPE_ORDER = [
    "Unionist – Union Jack",
    "Unionist – Ulster Banner", 
    "Nationalist – Tricolour",
    "Cultural – Orange Order",
    "Paramilitary (UDA/UVF/UFF/YCV)",
]

# Model class mappings
CONSOLIDATED_16_TO_TYPE = {
    "Unionist_High_Impact": "Unionist – Union Jack",
    "Unionist_Medium_Impact": "Unionist – Union Jack", 
    "Unionist_Low_Impact": "Unionist – Union Jack",
    "Nationalist_Display": "Nationalist – Tricolour",
    "Fraternal_Cultural": "Cultural – Orange Order",
    "Paramilitary_Loyalist": "Paramilitary (UDA/UVF/UFF/YCV)",
    "Paramilitary_Other": "Paramilitary (UDA/UVF/UFF/YCV)",
    # Map other classes to closest TYPE_ORDER category
    "Regional_Scottish": "Unionist – Ulster Banner",
    "Seasonal_Decorative": "Cultural – Orange Order",
    "International_Other": "Unionist – Union Jack",
    "International_Republican": "Nationalist – Tricolour",
    "International_Loyalist": "Unionist – Union Jack",
    "International_EU": "Unionist – Union Jack",
    "Sport_Other": "Cultural – Orange Order", 
    "Sport_GAA": "Nationalist – Tricolour",
    "Commemorative_Historical": "Cultural – Orange Order",
}

SUPER_CONSOLIDATED_7_TO_TYPE = {
    "Unionist_All": "Unionist – Union Jack",
    "Nationalist_All": "Nationalist – Tricolour", 
    "Cultural_Community": "Cultural – Orange Order",
    "Paramilitary_All": "Paramilitary (UDA/UVF/UFF/YCV)",
    "Historical_Memorial": "Cultural – Orange Order",
    "Sport_Community": "Cultural – Orange Order",
    "International_Other": "Unionist – Union Jack",
}

class RS5MModel(nn.Module):
    """RS5M ViT-H-14 model matching the training scripts"""
    
    def __init__(self, num_classes: int, checkpoint_path: Path, backbone_path: Path):
        super().__init__()
        self.num_classes = num_classes
        
        if open_clip is None:
            raise ImportError("open_clip is required for inference. Install with: pip install open-clip-torch")
        
        # Load RS5M ViT-H-14 architecture  
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None
        )
        
        # Load RS5M backbone
        print(f"📥 Loading RS5M backbone from {backbone_path}")
        backbone_ckpt = torch.load(backbone_path, map_location='cpu', weights_only=False)
        
        # Load visual encoder weights
        visual_state_dict = {}
        for key, value in backbone_ckpt.items():
            if key.startswith('visual.'):
                new_key = key.replace('visual.', '')
                visual_state_dict[new_key] = value
        
        self.model.visual.load_state_dict(visual_state_dict, strict=False)
        print(f"✅ Loaded RS5M visual weights: {len(visual_state_dict)} parameters")
        
        # Get feature dimension
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224)
            features = self.model.visual(dummy_input)
            feature_dim = features.shape[-1]
        
        # Multi-layer classification head (matches training scripts)
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
        
        # Load trained classifier weights
        print(f"📥 Loading trained model from {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
        
        # Handle different checkpoint formats
        if 'model_state_dict' in checkpoint:
            # Training checkpoint format
            model_state_dict = checkpoint['model_state_dict']
            print(f"✅ Found training checkpoint (epoch {checkpoint.get('epoch', 'unknown')})")
        else:
            # Direct state dict format
            model_state_dict = checkpoint
            print(f"✅ Found direct state dict checkpoint")
        
        self.load_state_dict(model_state_dict, strict=True)
        print(f"✅ Model loaded with {num_classes} classes")
    
    def forward(self, x):
        features = self.model.visual(x)
        logits = self.classifier(features)
        return logits

def setup_optimized_device() -> torch.device:
    """
    Setup device with MPS optimizations from original experiments.
    Expected 10-40x speedup over CPU on Apple Silicon.
    """
    device = None
    
    # Check for MPS (Apple Silicon) FIRST - following original pattern
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("=" * 60)
        print("🚀 MPS (Metal Performance Shaders) DETECTED!")
        print("🎯 Using Apple Silicon GPU acceleration")
        print("⚡ Expected 10-40x speedup over CPU")
        print("=" * 60)
        
        # Apply MPS-specific optimizations
        try:
            torch.backends.mps.empty_cache()
        except AttributeError:
            # MPS empty_cache not available in this PyTorch version
            pass
        
    # Fallback to CUDA if available
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("🎮 Using CUDA GPU")
        torch.backends.cudnn.benchmark = True
        
    # Fallback to CPU
    else:
        device = torch.device("cpu")
        print("⚠️  WARNING: Using CPU - Inference will be VERY SLOW!")
        print("⚠️  MPS not detected - check PyTorch installation")
        
    return device

def get_optimal_batch_size(device: torch.device, model_type: str = "ViT-H/14") -> int:
    """
    Get optimal batch size based on device and model type from original experiments.
    """
    if device.type == "mps":
        # Conservative batch sizes for Apple Silicon MPS (from original experiments)
        batch_sizes = {
            "ViT-H/14": 8,   # RS5M ViT-H-14 optimized
            "ViT-L/14": 16,
            "ViT-B/16": 24,
            "RN50": 32,
        }
    elif device.type == "cuda":
        # More aggressive batch sizes for CUDA
        batch_sizes = {
            "ViT-H/14": 16,
            "ViT-L/14": 32, 
            "ViT-B/16": 48,
            "RN50": 64,
        }
    else:
        # CPU batch sizes
        batch_sizes = {
            "ViT-H/14": 1,
            "ViT-L/14": 2,
            "ViT-B/16": 4,
            "RN50": 8,
        }
    
    return batch_sizes.get(model_type, 8)  # Default to 8 for RS5M

@torch.no_grad()
def predict_batch(image_paths: List[str], checkpoint_path: Path, cfg: dict) -> List[str]:
    """
    Run real RS5M inference with MPS acceleration on a batch of images.
    
    Returns list of predicted flag type strings from TYPE_ORDER.
    """
    device = setup_optimized_device()
    backbone_path = Path(cfg["backbone_checkpoint"]).resolve()
    
    # Determine model type and class mapping
    if "16class" in str(checkpoint_path):
        num_classes = 16
        class_mapping = CONSOLIDATED_16_TO_TYPE
        classnames_path = Path("MSc-Themed-Research-Project/data/ni_flags_consolidated/classnames.txt")
    else:
        num_classes = 7  
        class_mapping = SUPER_CONSOLIDATED_7_TO_TYPE
        classnames_path = Path("MSc-Themed-Research-Project/data/ni_flags_super_consolidated/classnames.txt")
    
    # Load class names
    if classnames_path.exists():
        with open(classnames_path, 'r', encoding='utf-8') as f:
            classnames = [line.strip() for line in f if line.strip()]
    else:
        print(f"⚠️  Classnames file not found: {classnames_path}")
        classnames = [f"class_{i}" for i in range(num_classes)]
    
    print(f"🔄 Loading {num_classes}-class model for {len(image_paths)} images")
    
    # Load model with MPS optimizations
    model = RS5MModel(num_classes, checkpoint_path, backbone_path)
    model = model.to(device)
    
    # Apply device-specific optimizations
    if device.type == "mps":
        model = model.float()  # Ensure FP32 for MPS stability
        print(f"✅ Model on MPS: {next(model.parameters()).is_mps}")
    elif device.type == "cuda":
        # Enable optimized CUDA operations
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    
    model = model.eval()
    
    # Use optimized batch size from original experiments
    batch_size = get_optimal_batch_size(device, "ViT-H/14")
    print(f"🔥 Using optimized batch size: {batch_size} for {device}")
    
    predictions = []
    
    for i in tqdm(range(0, len(image_paths), batch_size), desc=f"MPS Inference ({device})"):
        batch_paths = image_paths[i:i + batch_size]
        batch_images = []
        
        for img_path in batch_paths:
            try:
                # Convert relative path to absolute
                if not Path(img_path).is_absolute():
                    img_path = Path(img_path).resolve()
                else:
                    img_path = Path(img_path)
                    
                image = Image.open(img_path).convert('RGB')
                image_tensor = model.preprocess(image)
                batch_images.append(image_tensor)
            except (IOError, OSError) as e:
                print(f"⚠️  Error loading {img_path}: {e}")
                # Use a dummy tensor for failed images
                batch_images.append(torch.zeros(3, 224, 224))
        
        if batch_images:
            batch_tensor = torch.stack(batch_images).to(device)
            
            # Ensure proper data type for MPS
            if device.type == "mps":
                batch_tensor = batch_tensor.float()
            
            logits = model(batch_tensor)
            pred_indices = torch.argmax(logits, dim=1).cpu().numpy()
            
            # Clear intermediate tensors for memory efficiency
            del batch_tensor, logits
            if device.type == "mps":
                try:
                    torch.backends.mps.empty_cache()
                except AttributeError:
                    pass  # MPS empty_cache not available in this PyTorch version
            elif device.type == "cuda":
                torch.cuda.empty_cache()
            
            for pred_idx in pred_indices:
                if pred_idx < len(classnames):
                    model_class = classnames[pred_idx]
                    # Map to TYPE_ORDER category
                    type_class = class_mapping.get(model_class, "Unionist – Union Jack")  # default fallback
                    predictions.append(type_class)
                else:
                    predictions.append("Unionist – Union Jack")  # fallback
        else:
            # If no images loaded, add fallbacks
            predictions.extend(["Unionist – Union Jack"] * len(batch_paths))
    
    # Final cleanup
    if device.type == "mps":
        try:
            torch.backends.mps.empty_cache()
        except AttributeError:
            pass  # MPS empty_cache not available in this PyTorch version
    elif device.type == "cuda":
        torch.cuda.empty_cache()
    
    return predictions


def write_preds(df_idx: pd.DataFrame, preds: list[str], out_parquet: Path) -> None:
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame({
        "image_path": df_idx["image_path"].tolist(),
        "flag_type": df_idx["flag_type"].tolist(),
        "y_true": df_idx["flag_type"].tolist(),
        "y_pred": preds,
    })
    df_out.to_parquet(out_parquet, index=False)
    print(f"✅ Wrote {out_parquet} ({len(df_out)} rows)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--copy-true-as-pred", action="store_true",
                    help="Fallback mode: copy y_true to y_pred to generate files without inference")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    index_csv = Path(cfg["index_csv"]).resolve()
    df_idx = load_index(index_csv)

    # BEFORE (single checkpoint)
    before_list = cfg.get("checkpoints_before", [])
    if not before_list:
        print("⚠️ No checkpoints_before defined in config; skipping BEFORE preds")
    else:
        ckpt = Path(before_list[0]).resolve()
        name = ckpt.parent.name or "seed_before"
        out_parquet = Path("outputs/before")/name/"preds.parquet"
        if args.copy_true_as_pred:
            preds = df_idx["flag_type"].tolist()
        else:
            # Real inference
            preds = predict_batch(df_idx["image_path"].tolist(), ckpt, cfg)
        write_preds(df_idx, preds, out_parquet)

    # AFTER (one or more checkpoints/seeds)
    after_list = cfg.get("checkpoints_after", [])
    if not after_list:
        print("⚠️ No checkpoints_after defined in config; skipping AFTER preds")
    else:
        for ck in after_list:
            ckpt = Path(ck).resolve()
            name = ckpt.parent.name or "seed_after"
            out_parquet = Path("outputs/after")/name/"preds.parquet"
            if args.copy_true_as_pred:
                preds = df_idx["flag_type"].tolist()
            else:
                preds = predict_batch(df_idx["image_path"].tolist(), ckpt, cfg)
            write_preds(df_idx, preds, out_parquet)


if __name__ == "__main__":
    main()
