#!/usr/bin/env python3
"""
Context Ablation Study for RS5M Flag Classification
Tests: Crop vs Crop+Context vs Full+BBox to optimize input representation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import time
from datetime import datetime
from tqdm import tqdm
import random
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import json
import os
import argparse
import clip
import open_clip

# Add the flag_classification_adaptation directory to path for dataset imports
import sys
sys.path.append(str(Path(__file__).parent))

from dassl.data import DataManager
from dassl.utils import setup_logger, set_random_seed, collect_env_info
from dassl.config import get_cfg_default
from dassl.engine import TRAINER_REGISTRY, TrainerX
from dassl.data.datasets import DATASET_REGISTRY

# Import our custom datasets to register them
from datasets.ni_flags_consolidated import NIFlagsConsolidated

class ContextAblationDataset(Dataset):
    """Dataset for context ablation experiments with different input representations"""
    
    def __init__(self, data_items, context_mode="crop", preprocess=None):
        """
        Args:
            data_items: List of Dassl Datum objects
            context_mode: "crop", "crop_context", or "full_bbox"
            preprocess: Image preprocessing function
        """
        self.data_items = data_items
        self.context_mode = context_mode
        self.preprocess = preprocess
        
        print(f"📊 Context Ablation Dataset: {len(data_items)} samples, mode='{context_mode}'")
    
    def __len__(self):
        return len(self.data_items)
    
    def __getitem__(self, idx):
        item = self.data_items[idx]
        
        # Load original image
        img_path = Path(item.impath)
        image = Image.open(img_path).convert("RGB")
        
        if self.context_mode == "crop":
            # Current approach: Use cropped image as-is
            processed_image = image
            
        elif self.context_mode == "crop_context":
            # Extended context: Expand crop by 50% in each direction
            width, height = image.size
            expand_factor = 0.5
            
            # Calculate expanded dimensions (simulate expanding from original crop)
            new_width = int(width * (1 + expand_factor))
            new_height = int(height * (1 + expand_factor))
            
            # Create expanded image with padding
            expanded = Image.new("RGB", (new_width, new_height), (128, 128, 128))  # Gray padding
            
            # Center the original crop in expanded image
            offset_x = (new_width - width) // 2
            offset_y = (new_height - height) // 2
            expanded.paste(image, (offset_x, offset_y))
            
            processed_image = expanded
            
        elif self.context_mode == "full_bbox":
            # Full image with bounding box highlighting the flag region
            # Since we have cropped images, simulate bbox by adding border
            width, height = image.size
            
            # Create larger canvas simulating full image context
            full_width = int(width * 2.5)  # Simulate full image being 2.5x larger
            full_height = int(height * 2.5)
            
            # Create simulated full image with random background
            full_image = Image.new("RGB", (full_width, full_height), 
                                 (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
            
            # Place crop in random location
            bbox_x = random.randint(0, full_width - width)
            bbox_y = random.randint(0, full_height - height)
            full_image.paste(image, (bbox_x, bbox_y))
            
            # Draw bounding box around flag region
            draw = ImageDraw.Draw(full_image)
            bbox_coords = [bbox_x-2, bbox_y-2, bbox_x+width+2, bbox_y+height+2]
            draw.rectangle(bbox_coords, outline="red", width=3)
            
            processed_image = full_image
            
        else:
            raise ValueError(f"Unknown context_mode: {self.context_mode}")
        
        # Apply preprocessing
        if self.preprocess:
            processed_image = self.preprocess(processed_image)
        
        return processed_image, item.label

class RS5MContextAblationModel(nn.Module):
    """RS5M model for context ablation experiments"""
    
    def __init__(self, checkpoint_path, num_classes, device):
        super().__init__()
        self.device = device
        self.num_classes = num_classes
        
        # Load RS5M model using proven working approach
        print(f"🔄 Loading RS5M ViT-H-14 for context ablation...")
        
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None,  # Don't load default weights
            device=device
        )
        
        # Load RS5M checkpoint
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        missing_keys, unexpected_keys = self.model.load_state_dict(ckpt, strict=False)
        
        print(f"✅ Loaded RS5M weights: {len(ckpt)} total keys")
        
        # Get feature dimension
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224).to(device)
            features = self.model.encode_image(dummy_input)
            feature_dim = features.shape[-1]
        
        # Add classification head
        self.classifier = nn.Linear(feature_dim, num_classes).to(device)
        
        # Initialize classifier head
        nn.init.xavier_uniform_(self.classifier.weight)
        nn.init.zeros_(self.classifier.bias)
        
        print(f"✅ Context ablation model ready: {feature_dim}D → {num_classes} classes")
    
    def forward(self, images):
        # Extract image features from RS5M
        image_features = self.model.encode_image(images)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Classify
        logits = self.classifier(image_features)
        return logits

def setup_device():
    """Setup device with MPS support"""
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("=" * 60)
        print("🚀 MPS (Metal Performance Shaders) DETECTED!")
        print("🎯 Using M4 Max GPU acceleration")
        print("=" * 60)
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("🚀 CUDA GPU DETECTED!")
        print("🎯 Using NVIDIA GPU acceleration")
        print("=" * 60)
    else:
        device = torch.device("cpu")
        print("💻 Using CPU")
        print("=" * 60)

    return device

def create_data_loaders(data_root, batch_size=8, num_workers=4):
    """Create train/test data loaders using Dassl dataset"""
    print(f"Creating data loaders from {data_root}")

    # Create minimal config for dataset
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = str(Path(data_root).resolve())
    cfg.DATASET.NAME = "NIFlagsConsolidated"

    # Use Dassl dataset registry
    dataset = DATASET_REGISTRY.get("NIFlagsConsolidated")(cfg=cfg)

    # Get train/test splits
    train_items = dataset.train_x
    test_items = dataset.test
    classnames = dataset.classnames

    print(f"Train samples: {len(train_items)}")
    print(f"Test samples: {len(test_items)}")
    print(f"Classes: {len(classnames)}")

    return train_items, test_items, classnames

class FocalLoss(nn.Module):
    """Focal Loss for addressing class imbalance"""
    def __init__(self, alpha=0.25, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

def evaluate_model(model, test_dataset, device, batch_size=16):
    """Evaluate model on test set"""
    model.eval()
    
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="Evaluating"):
            images = images.to(device)
            labels = labels.to(device)
            
            # Forward pass
            outputs = model(images)
            predictions = torch.argmax(outputs, dim=1)
            
            all_preds.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    return np.array(all_preds), np.array(all_labels)

def run_context_ablation(context_mode, args, train_items, test_items, classnames, device):
    """Run single context ablation experiment"""
    
    print(f"\n🔬 Starting Context Ablation: {context_mode}")
    print("=" * 60)
    
    # Create experiment directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = f"rs5m_context_{context_mode}_{timestamp}"
    output_dir = Path(args.output_dir) / experiment_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Experiment: {experiment_name}")
    print(f"📁 Output: {output_dir}")
    
    # Initialize model
    model = RS5MContextAblationModel(args.checkpoint, len(classnames), device)
    
    # Create datasets with different context modes
    train_dataset = ContextAblationDataset(train_items, context_mode, model.preprocess)
    test_dataset = ContextAblationDataset(test_items, context_mode, model.preprocess)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    
    # Loss function and optimizer
    criterion = FocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    best_accuracy = 0.0
    training_log = []
    
    print(f"🚀 Training {context_mode} for {args.epochs} epochs...")
    
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        num_batches = 0
        
        # Training
        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs}"):
            images = images.to(device)
            labels = labels.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        current_lr = optimizer.param_groups[0]['lr']
        
        # Log training progress
        log_entry = {
            "epoch": epoch,
            "train_loss": avg_loss,
            "learning_rate": current_lr,
            "context_mode": context_mode
        }
        
        # Evaluation
        if epoch % args.eval_freq == 0 or epoch == args.epochs:
            print(f"\n📊 Evaluating {context_mode} epoch {epoch}...")
            predictions, labels = evaluate_model(model, test_dataset, device)
            
            accuracy = accuracy_score(labels, predictions)
            macro_f1 = f1_score(labels, predictions, average='macro', zero_division=0)
            micro_f1 = f1_score(labels, predictions, average='micro', zero_division=0)
            
            log_entry.update({
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "micro_f1": micro_f1
            })
            
            print(f"🎯 {context_mode} Epoch {epoch}: Accuracy = {accuracy:.4f}, Macro F1 = {macro_f1:.4f}")
            
            # Save best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                torch.save(model.state_dict(), output_dir / "model_best.pth")
                
                # Save detailed results
                results = {
                    "context_mode": context_mode,
                    "accuracy": accuracy,
                    "macro_f1": macro_f1,
                    "micro_f1": micro_f1,
                    "predictions": predictions.tolist(),
                    "labels": labels.tolist(),
                    "classnames": classnames
                }
                
                with open(output_dir / "best_results.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                print(f"💾 New best {context_mode} model saved! Accuracy: {accuracy:.4f}")
        
        training_log.append(log_entry)
        scheduler.step()
        
        print(f"{context_mode} Epoch {epoch}/{args.epochs}: Loss = {avg_loss:.6f}, LR = {current_lr:.6f}")
    
    # Save training log
    with open(output_dir / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
    
    print(f"✅ {context_mode} complete! Best accuracy: {best_accuracy:.4f}")
    
    return best_accuracy, output_dir

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=str, default='data', help='Data root directory')
    parser.add_argument('--checkpoint', type=str, required=True, help='RS5M checkpoint path')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')
    parser.add_argument('--epochs', type=int, default=15, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--focal-alpha', type=float, default=0.25, help='Focal loss alpha')
    parser.add_argument('--focal-gamma', type=float, default=2.0, help='Focal loss gamma')
    parser.add_argument('--eval-freq', type=int, default=5, help='Evaluation frequency')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--context-modes', nargs='+', default=['crop', 'crop_context', 'full_bbox'], 
                       help='Context modes to test')
    
    args = parser.parse_args()
    
    # Set random seed
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Load data
    train_items, test_items, classnames = create_data_loaders(args.data_root, args.batch_size)
    
    # Save classnames
    base_output_dir = Path(args.output_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)
    with open(base_output_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(f"{name}\n")
    
    # Run ablation experiments
    print(f"\n🔬 CONTEXT ABLATION STUDY")
    print(f"🎯 Testing modes: {args.context_modes}")
    print(f"📊 Dataset: {len(train_items)} train, {len(test_items)} test")
    print("=" * 80)
    
    results_summary = {}
    
    for context_mode in args.context_modes:
        try:
            best_acc, exp_dir = run_context_ablation(
                context_mode, args, train_items, test_items, classnames, device
            )
            results_summary[context_mode] = {
                "accuracy": best_acc,
                "experiment_dir": str(exp_dir)
            }
        except Exception as e:
            print(f"❌ Error in {context_mode}: {e}")
            results_summary[context_mode] = {
                "accuracy": 0.0,
                "error": str(e)
            }
    
    # Save comprehensive results
    with open(base_output_dir / "ablation_summary.json", "w") as f:
        json.dump(results_summary, f, indent=2)
    
    # Print final comparison
    print(f"\n🏆 CONTEXT ABLATION RESULTS")
    print("=" * 80)
    for mode, result in results_summary.items():
        if "error" not in result:
            print(f"{mode:15} | Accuracy: {result['accuracy']:.4f}")
        else:
            print(f"{mode:15} | ERROR: {result['error']}")
    
    # Find best performing mode
    best_mode = max(results_summary.keys(), 
                   key=lambda k: results_summary[k].get('accuracy', 0))
    best_acc = results_summary[best_mode].get('accuracy', 0)
    
    print(f"\n🎯 BEST CONTEXT MODE: {best_mode} ({best_acc:.4f} accuracy)")
    print(f"📁 Results saved to: {base_output_dir}")

if __name__ == "__main__":
    main()