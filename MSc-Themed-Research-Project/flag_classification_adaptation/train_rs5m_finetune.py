#!/usr/bin/env python3
"""
RS5M ViT-H-14 Fine-tuning for Flag Classification
Adapts Li et al. methodology for Northern Ireland flag classification

Based on:
- train_minimal_mps.py (MPS acceleration, dataset loading)
- Li et al. ship classification methodology
- CoCoOp framework with hierarchical prompts
"""
import argparse
import os
import sys
from pathlib import Path

# Fix OpenMP conflict on M4 Max
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import time
from datetime import datetime
import json
from tqdm import tqdm
import open_clip
from PIL import Image
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import datasets
try:
    from datasets.ni_flags_consolidated import NIFlagsConsolidated
    from datasets.ni_flags_super_consolidated import NIFlagsSuperConsolidated
    print("✅ Successfully imported NIFlagsConsolidated and NIFlagsSuperConsolidated datasets")
except ImportError as e:
    print(f"❌ Failed to import NIFlagsConsolidated dataset: {e}")
    sys.exit(1)

from dassl.data.datasets import DATASET_REGISTRY
from dassl.utils import set_random_seed

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

class RS5MFlagClassifier(nn.Module):
    """RS5M ViT-H-14 adapted for flag classification"""
    def __init__(self, checkpoint_path, num_classes, device):
        super().__init__()
        self.device = device
        self.num_classes = num_classes
        
        # Load RS5M model
        print(f"Loading RS5M ViT-H-14 from {checkpoint_path}")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None,  # Don't load default weights
            device=device
        )
        
        # Load RS5M checkpoint
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        self.model.load_state_dict(ckpt, strict=False)
        
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
        
        print(f"✅ Model loaded with {feature_dim}D features → {num_classes} classes")
    
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
        print("🎮 Using CUDA GPU")
    else:
        device = torch.device("cpu")
        print("⚠️  WARNING: Using CPU - Training will be SLOW!")
    
    return device

def create_data_loaders(data_root, batch_size=8, num_workers=4, use_original_classes=False, dataset_name="NIFlagsConsolidated"):
    """Create train/test data loaders using Dassl dataset"""
    print(f"Creating data loaders from {data_root}")
    
    # Create minimal config for dataset
    from dassl.config import get_cfg_default
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = str(Path(data_root).resolve())
    cfg.DATASET.NAME = dataset_name
    
    # Use Dassl dataset registry with proper config
    dataset = DATASET_REGISTRY.get(dataset_name)(cfg=cfg)
    
    # Get train/test splits
    train_items = dataset.train_x
    test_items = dataset.test
    classnames = dataset.classnames
    
    if use_original_classes:
        print("🔄 Converting to original 70-class labels...")
        # Load the annotations to get original class mapping
        annotations_path = Path(data_root) / "ni_flags_consolidated" / "annotations.json"
        if annotations_path.exists():
            import json
            with open(annotations_path, 'r') as f:
                annotations = json.load(f)
            
            # Create mapping from original classnames to indices
            original_classes = set()
            for img_data in annotations.values():
                if 'original_classname' in img_data:
                    original_classes.add(img_data['original_classname'])
            
            original_classes = sorted(list(original_classes))
            original_class_to_idx = {cls: idx for idx, cls in enumerate(original_classes)}
            
            print(f"Found {len(original_classes)} original classes")
            
            # Update train items with original labels
            updated_train_items = []
            for item in train_items:
                img_name = Path(item.impath).name
                if img_name in annotations:
                    original_class = annotations[img_name]['original_classname']
                    original_label = original_class_to_idx[original_class]
                    # Create new datum with original label
                    from dassl.data.datasets import Datum
                    new_item = Datum(
                        impath=item.impath,
                        label=original_label,
                        domain=item.domain,
                        classname=original_class
                    )
                    updated_train_items.append(new_item)
                else:
                    updated_train_items.append(item)
            
            # Update test items with original labels
            updated_test_items = []
            for item in test_items:
                img_name = Path(item.impath).name
                if img_name in annotations:
                    original_class = annotations[img_name]['original_classname']
                    original_label = original_class_to_idx[original_class]
                    # Create new datum with original label
                    from dassl.data.datasets import Datum
                    new_item = Datum(
                        impath=item.impath,
                        label=original_label,
                        domain=item.domain,
                        classname=original_class
                    )
                    updated_test_items.append(new_item)
                else:
                    updated_test_items.append(item)
            
            train_items = updated_train_items
            test_items = updated_test_items
            classnames = original_classes
            
            print(f"✅ Converted to original classes: {len(classnames)} classes")
    
    print(f"Train samples: {len(train_items)}")
    print(f"Test samples: {len(test_items)}")
    print(f"Classes: {len(classnames)}")
    
    return train_items, test_items, classnames

def compute_class_weights(train_items, num_classes):
    """Compute inverse frequency weights for class balancing"""
    class_counts = torch.zeros(num_classes)
    for item in train_items:
        class_counts[int(item.label)] += 1
    
    # Inverse frequency weighting
    class_weights = 1.0 / (class_counts + 1e-8)
    class_weights = class_weights / class_weights.sum() * num_classes
    
    print("Class distribution:")
    for i, (count, weight) in enumerate(zip(class_counts, class_weights)):
        print(f"  Class {i}: {int(count)} samples, weight: {weight:.3f}")
    
    return class_weights

def evaluate_model(model, test_items, device, batch_size=16):
    """Evaluate model on test set"""
    model.eval()
    all_preds = []
    all_labels = []
    
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    
    with torch.no_grad():
        for batch in tqdm(chunks(test_items, batch_size), desc="Evaluating"):
            images = []
            labels = []
            
            for item in batch:
                img = Image.open(item.impath).convert("RGB")
                img_tensor = model.preprocess(img).unsqueeze(0)
                images.append(img_tensor)
                labels.append(int(item.label))
            
            if images:
                batch_images = torch.cat(images, dim=0).to(device)
                logits = model(batch_images)
                preds = logits.argmax(dim=-1).cpu().tolist()
                
                all_preds.extend(preds)
                all_labels.extend(labels)
    
    # Compute metrics
    accuracy = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average='macro')
    micro_f1 = f1_score(all_labels, all_preds, average='micro')
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'micro_f1': micro_f1,
        'predictions': all_preds,
        'labels': all_labels
    }

def train_epoch(model, train_items, optimizer, criterion, device, batch_size=8):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    num_batches = 0
    
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    
    # Shuffle training data
    import random
    train_items = train_items.copy()
    random.shuffle(train_items)
    
    for batch in tqdm(chunks(train_items, batch_size), desc="Training"):
        images = []
        labels = []
        
        for item in batch:
            try:
                img = Image.open(item.impath).convert("RGB")
                img_tensor = model.preprocess(img).unsqueeze(0)
                images.append(img_tensor)
                labels.append(int(item.label))
            except Exception as e:
                print(f"Error loading {item.impath}: {e}")
                continue
        
        if not images:
            continue
            
        batch_images = torch.cat(images, dim=0).to(device)
        batch_labels = torch.tensor(labels, dtype=torch.long).to(device)
        
        optimizer.zero_grad()
        logits = model(batch_images)
        loss = criterion(logits, batch_labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / max(num_batches, 1)

def main():
    parser = argparse.ArgumentParser(description="RS5M ViT-H-14 Fine-tuning for Flag Classification")
    parser.add_argument("--data-root", type=str, default="../data", help="Path to data root")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to RS5M ViT-H-14 checkpoint")
    parser.add_argument("--output-dir", type=str, default="experiments/rs5m_finetune", help="Output directory")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size (reduce if OOM)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--focal-alpha", type=float, default=0.25, help="Focal loss alpha")
    parser.add_argument("--focal-gamma", type=float, default=2.0, help="Focal loss gamma")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--eval-freq", type=int, default=10, help="Evaluation frequency (epochs)")
    parser.add_argument("--use-original-classes", action="store_true", help="Use original 70-class labels instead of consolidated 16-class")
    parser.add_argument("--dataset-name", type=str, default="NIFlagsConsolidated", 
                       choices=["NIFlagsConsolidated", "NIFlagsSuperConsolidated"], 
                       help="Dataset to use (16-class consolidated or 7-class super consolidated)")
    
    args = parser.parse_args()
    
    # Set random seed
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save args
    with open(output_dir / "args.json", "w") as f:
        json.dump(vars(args), f, indent=2)
    
    # Create data loaders
    train_items, test_items, classnames = create_data_loaders(args.data_root, args.batch_size, use_original_classes=args.use_original_classes, dataset_name=args.dataset_name)
    num_classes = len(classnames)
    
    # Save classnames
    with open(output_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(f"{name}\n")
    
    # Create model
    model = RS5MFlagClassifier(args.checkpoint, num_classes, device)
    
    # Setup loss function with class weights
    class_weights = compute_class_weights(train_items, num_classes)
    if args.focal_alpha > 0:
        criterion = FocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma)
        print(f"Using Focal Loss (α={args.focal_alpha}, γ={args.focal_gamma})")
    else:
        criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
        print("Using weighted Cross Entropy Loss")
    
    # Setup optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    print(f"\n🚀 Starting training for {args.epochs} epochs...")
    print(f"📊 Dataset: {num_classes} classes, {len(train_items)} train, {len(test_items)} test")
    print(f"🎯 Device: {device}")
    print(f"📝 Output: {output_dir}")
    
    best_accuracy = 0
    training_log = []
    
    for epoch in range(args.epochs):
        print(f"\n📅 Epoch {epoch+1}/{args.epochs}")
        
        # Train
        train_loss = train_epoch(model, train_items, optimizer, criterion, device, args.batch_size)
        scheduler.step()
        
        # Log
        log_entry = {
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'lr': scheduler.get_last_lr()[0]
        }
        
        # Evaluate
        if (epoch + 1) % args.eval_freq == 0 or epoch == args.epochs - 1:
            print("🔍 Evaluating...")
            results = evaluate_model(model, test_items, device)
            
            log_entry.update({
                'accuracy': results['accuracy'],
                'macro_f1': results['macro_f1'],
                'micro_f1': results['micro_f1']
            })
            
            print(f"📊 Accuracy: {results['accuracy']:.4f}")
            print(f"📊 Macro F1: {results['macro_f1']:.4f}")
            print(f"📊 Micro F1: {results['micro_f1']:.4f}")
            
            # Save best model
            if results['accuracy'] > best_accuracy:
                best_accuracy = results['accuracy']
                torch.save(model.state_dict(), output_dir / "best_model.pth")
                print(f"💾 New best model saved! Accuracy: {best_accuracy:.4f}")
                
                # Save detailed results
                with open(output_dir / "best_results.json", "w") as f:
                    json.dump(results, f, indent=2, default=lambda x: x.tolist() if hasattr(x, 'tolist') else x)
        
        training_log.append(log_entry)
        print(f"📉 Train Loss: {train_loss:.4f}, LR: {scheduler.get_last_lr()[0]:.6f}")
    
    # Save training log
    with open(output_dir / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
    
    # Final evaluation
    print("\n🏁 Final evaluation...")
    final_results = evaluate_model(model, test_items, device)
    
    # Generate classification report
    report = classification_report(
        final_results['labels'], 
        final_results['predictions'],
        target_names=classnames,
        output_dict=True
    )
    
    with open(output_dir / "classification_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print(f"📊 Best Accuracy: {best_accuracy:.4f}")
    print(f"📊 Final Accuracy: {final_results['accuracy']:.4f}")
    print(f"📊 Final Macro F1: {final_results['macro_f1']:.4f}")
    print(f"📝 Results saved to: {output_dir}")
    print("="*60)

if __name__ == "__main__":
    main()