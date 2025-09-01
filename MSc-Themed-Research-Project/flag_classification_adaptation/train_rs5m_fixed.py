#!/usr/bin/env python3
"""
FIXED RS5M Flag Classification Training
Addresses critical class mapping inconsistency and implements proper class balancing
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from pathlib import Path
import numpy as np
from PIL import Image
import time
from datetime import datetime
from tqdm import tqdm
import random
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import json
import os
import argparse
import open_clip
from collections import Counter

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

class FixedNIFlagsDataset(Dataset):
    """Fixed dataset with consistent class mapping and proper balancing"""
    
    def __init__(self, data_items, classnames, preprocess=None, is_training=False):
        self.data_items = data_items
        self.classnames = classnames
        self.preprocess = preprocess
        self.is_training = is_training
        
        # Verify class mapping consistency
        print(f"📊 Fixed Dataset: {len(data_items)} samples, {len(classnames)} classes")
        
        # Check label distribution
        labels = [item.label for item in data_items]
        label_counts = Counter(labels)
        
        print(f"📊 Label Distribution:")
        for label_idx in sorted(label_counts.keys()):
            count = label_counts[label_idx]
            percentage = count / len(labels) * 100
            class_name = classnames[label_idx] if label_idx < len(classnames) else f"Unknown_{label_idx}"
            print(f"  Class {label_idx:2d} ({class_name}): {count:4d} samples ({percentage:.1f}%)")
    
    def __len__(self):
        return len(self.data_items)
    
    def __getitem__(self, idx):
        item = self.data_items[idx]
        
        # Load image
        image = Image.open(item.impath).convert("RGB")
        
        # Apply preprocessing
        if self.preprocess:
            image = self.preprocess(image)
        
        return image, item.label

class RS5MFixedClassifier(nn.Module):
    """RS5M model with fixed class mapping and proper balancing"""
    
    def __init__(self, checkpoint_path, num_classes, device):
        super().__init__()
        self.device = device
        self.num_classes = num_classes
        
        # Load RS5M model using proven working approach
        print(f"🔄 Loading RS5M ViT-H-14 with fixed class mapping...")
        
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None,  # Don't load default weights
            device=device
        )
        
        # Load RS5M checkpoint
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        missing_keys, unexpected_keys = self.model.load_state_dict(ckpt, strict=False)
        
        print(f"✅ Loaded RS5M weights: {len(ckpt)} total keys")
        if len(missing_keys) > 0:
            print(f"⚠️  Missing keys: {len(missing_keys)} (expected)")
        if len(unexpected_keys) > 0:
            print(f"⚠️  Unexpected keys: {len(unexpected_keys)}")
        
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
        
        print(f"✅ Fixed RS5M model ready: {feature_dim}D → {num_classes} classes")
    
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

def create_fixed_data_loaders(data_root, batch_size=8, use_balanced_sampling=True):
    """Create fixed data loaders with consistent class mapping"""
    print(f"🔧 Creating FIXED data loaders from {data_root}")
    print("🎯 Ensuring consistent class mapping throughout pipeline")

    # Create dataset with FIXED random seed for reproducible splits
    set_random_seed(42)  # Fixed seed for consistent splits
    
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = str(Path(data_root).resolve())
    cfg.DATASET.NAME = "NIFlagsConsolidated"

    # Use Dassl dataset registry
    dataset = DATASET_REGISTRY.get("NIFlagsConsolidated")(cfg=cfg)

    # Get splits
    train_items = dataset.train_x
    test_items = dataset.test
    
    # CRITICAL FIX: Use consistent class mapping from classnames.txt
    classnames_file = Path(data_root) / "ni_flags_consolidated" / "classnames.txt"
    if classnames_file.exists():
        with open(classnames_file, 'r') as f:
            file_classnames = [line.strip() for line in f if line.strip()]
        print(f"✅ Using classnames from file: {len(file_classnames)} classes")
        classnames = file_classnames
    else:
        print(f"⚠️  Using dataset classnames: {len(dataset.classnames)} classes")
        classnames = dataset.classnames

    # Create mapping from dataset classnames to file classnames
    dataset_to_file_mapping = {}
    for i, dataset_class in enumerate(dataset.classnames):
        if dataset_class in classnames:
            file_idx = classnames.index(dataset_class)
            dataset_to_file_mapping[i] = file_idx
        else:
            print(f"⚠️  Warning: {dataset_class} not found in file classnames")

    print(f"🔧 Class mapping correction:")
    for dataset_idx, file_idx in dataset_to_file_mapping.items():
        dataset_class = dataset.classnames[dataset_idx]
        file_class = classnames[file_idx]
        if dataset_idx != file_idx:
            print(f"  Dataset Class {dataset_idx} ({dataset_class}) → File Class {file_idx} ({file_class})")

    # Fix labels in train and test items
    def fix_labels(items, mapping):
        fixed_items = []
        for item in items:
            if item.label in mapping:
                new_label = mapping[item.label]
                # Create new item with corrected label
                from dassl.data.datasets import Datum
                fixed_item = Datum(
                    impath=item.impath,
                    label=new_label,
                    domain=item.domain,
                    classname=classnames[new_label]
                )
                fixed_items.append(fixed_item)
            else:
                print(f"⚠️  Warning: Label {item.label} not in mapping")
                fixed_items.append(item)
        return fixed_items

    train_items = fix_labels(train_items, dataset_to_file_mapping)
    test_items = fix_labels(test_items, dataset_to_file_mapping)

    print(f"✅ Fixed labels - Train: {len(train_items)}, Test: {len(test_items)}")

    return train_items, test_items, classnames

def compute_class_weights(train_items, num_classes):
    """Compute class weights for balanced training"""
    class_counts = torch.zeros(num_classes)
    for item in train_items:
        class_counts[int(item.label)] += 1
    
    # Inverse frequency weighting with smoothing
    total_samples = len(train_items)
    class_weights = total_samples / (num_classes * (class_counts + 1e-8))
    
    print("📊 Class weights for balanced training:")
    for i, (count, weight) in enumerate(zip(class_counts, class_weights)):
        print(f"  Class {i:2d}: {int(count):4d} samples, weight: {weight:.3f}")
    
    return class_weights

def create_balanced_sampler(train_items, num_classes):
    """Create weighted sampler for balanced training"""
    # Count samples per class
    class_counts = torch.zeros(num_classes)
    for item in train_items:
        class_counts[int(item.label)] += 1
    
    # Compute sample weights (inverse frequency)
    sample_weights = []
    for item in train_items:
        class_idx = int(item.label)
        weight = 1.0 / (class_counts[class_idx] + 1e-8)
        sample_weights.append(weight)
    
    sample_weights = torch.tensor(sample_weights)
    
    # Create weighted sampler
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(train_items),
        replacement=True
    )
    
    print(f"✅ Created balanced sampler with {len(sample_weights)} sample weights")
    return sampler

class FocalLoss(nn.Module):
    """Focal Loss for addressing class imbalance"""
    def __init__(self, alpha=0.25, gamma=2.0, weight=None, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.weight = weight
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, weight=self.weight, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

def evaluate_model_comprehensive(model, test_dataset, device, classnames, batch_size=16):
    """Comprehensive model evaluation with per-class metrics"""
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
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    
    # Comprehensive metrics
    accuracy = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    micro_f1 = f1_score(all_labels, all_preds, average='micro', zero_division=0)
    
    # Per-class report
    try:
        class_report = classification_report(
            all_labels, all_preds, 
            target_names=classnames,
            output_dict=True,
            zero_division=0
        )
    except Exception as e:
        print(f"⚠️  Classification report error: {e}")
        class_report = {}
    
    # Confusion matrix
    conf_matrix = confusion_matrix(all_labels, all_preds)
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'micro_f1': micro_f1,
        'predictions': all_preds,
        'labels': all_labels,
        'classification_report': class_report,
        'confusion_matrix': conf_matrix
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=str, default='data', help='Data root directory')
    parser.add_argument('--checkpoint', type=str, required=True, help='RS5M checkpoint path')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')
    parser.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--focal-alpha', type=float, default=0.25, help='Focal loss alpha')
    parser.add_argument('--focal-gamma', type=float, default=2.0, help='Focal loss gamma')
    parser.add_argument('--use-balanced-sampling', action='store_true', default=True, help='Use balanced sampling')
    parser.add_argument('--use-class-weights', action='store_true', default=True, help='Use class weights in loss')
    parser.add_argument('--eval-freq', type=int, default=5, help='Evaluation frequency')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = f"rs5m_FIXED_{timestamp}"
    output_dir = Path(args.output_dir) / experiment_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔧 FIXED RS5M Experiment: {experiment_name}")
    print(f"📁 Output: {output_dir}")
    print("🎯 Addresses: Class mapping inconsistency + Class imbalance")
    
    # Load data with fixed class mapping
    train_items, test_items, classnames = create_fixed_data_loaders(
        args.data_root, args.batch_size, args.use_balanced_sampling
    )
    
    # Save fixed classnames
    with open(output_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(f"{name}\n")
    
    # Initialize model
    model = RS5MFixedClassifier(args.checkpoint, len(classnames), device)
    
    # Create datasets
    train_dataset = FixedNIFlagsDataset(train_items, classnames, model.preprocess, is_training=True)
    test_dataset = FixedNIFlagsDataset(test_items, classnames, model.preprocess, is_training=False)
    
    # Create data loaders with optional balanced sampling
    if args.use_balanced_sampling:
        print("🎯 Using balanced sampling for training")
        sampler = create_balanced_sampler(train_items, len(classnames))
        train_loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, num_workers=4)
    else:
        print("📊 Using standard sampling for training")
        train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    
    # Loss function with optional class weights
    if args.use_class_weights:
        print("⚖️  Using class-weighted focal loss")
        class_weights = compute_class_weights(train_items, len(classnames))
        class_weights = class_weights.to(device)
        criterion = FocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma, weight=class_weights)
    else:
        print("📊 Using standard focal loss")
        criterion = FocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma)
    
    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    best_accuracy = 0.0
    training_log = []
    
    print(f"\n🚀 Starting FIXED RS5M training for {args.epochs} epochs...")
    print("🎯 This should give us REAL, meaningful results!")
    
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
            "learning_rate": current_lr
        }
        
        # Evaluation
        if epoch % args.eval_freq == 0 or epoch == args.epochs:
            print(f"\n📊 Evaluating FIXED model epoch {epoch}...")
            eval_results = evaluate_model_comprehensive(model, test_dataset, device, classnames)
            
            accuracy = eval_results['accuracy']
            macro_f1 = eval_results['macro_f1']
            micro_f1 = eval_results['micro_f1']
            
            log_entry.update({
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "micro_f1": micro_f1
            })
            
            print(f"🎯 FIXED Epoch {epoch}: Accuracy = {accuracy:.4f}, Macro F1 = {macro_f1:.4f}")
            
            # Check for diverse predictions
            unique_preds = len(np.unique(eval_results['predictions']))
            print(f"📊 Model predicts {unique_preds}/{len(classnames)} different classes")
            
            # Save best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                torch.save(model.state_dict(), output_dir / "model_best.pth")
                
                # Save comprehensive results
                results = {
                    "accuracy": accuracy,
                    "macro_f1": macro_f1,
                    "micro_f1": micro_f1,
                    "predictions": eval_results['predictions'].tolist(),
                    "labels": eval_results['labels'].tolist(),
                    "classnames": classnames,
                    "classification_report": eval_results['classification_report'],
                    "confusion_matrix": eval_results['confusion_matrix'].tolist(),
                    "unique_predictions": unique_preds,
                    "fixes_applied": [
                        "Fixed class mapping inconsistency",
                        "Added balanced sampling" if args.use_balanced_sampling else "Standard sampling",
                        "Added class weights" if args.use_class_weights else "No class weights",
                        "Fixed random seed for reproducible splits"
                    ]
                }
                
                with open(output_dir / "best_results.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                print(f"💾 New best FIXED model saved! Accuracy: {accuracy:.4f}")
        
        training_log.append(log_entry)
        scheduler.step()
        
        print(f"FIXED Epoch {epoch}/{args.epochs}: Loss = {avg_loss:.6f}, LR = {current_lr:.6f}")
    
    # Save training log
    with open(output_dir / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
    
    print(f"\n✅ FIXED RS5M training complete! Best accuracy: {best_accuracy:.4f}")
    print(f"📁 Results saved to: {output_dir}")
    print("\n🎉 This should be REAL performance - not the previous 72.63% artifact!")

if __name__ == "__main__":
    main()