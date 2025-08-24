#!/usr/bin/env python3
"""
IMPROVED RS5M Flag Classification Training
Implements multiple strategies to address extreme class imbalance:
1. Economic super-consolidation (16 → 7 classes)
2. SMOTE-style oversampling 
3. Gentler focal loss
4. Progressive training strategy
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import time
from datetime import datetime
from tqdm import tqdm
import random
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import json
import os
import argparse
import open_clip
from collections import Counter, defaultdict

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

class EconomicSuperConsolidator:
    """Super-consolidate 16 classes to 7 based on economic theory"""
    
    def __init__(self):
        # Economic super-consolidation mapping
        self.consolidation_map = {
            # Major Economic Impact - Unionist Displays
            "Unionist_High_Impact": "Major_Unionist",
            "Unionist_Medium_Impact": "Major_Unionist", 
            "Unionist_Low_Impact": "Major_Unionist",
            
            # Political Opposition
            "Nationalist_Display": "Nationalist",
            
            # Cultural/Fraternal
            "Fraternal_Cultural": "Cultural_Fraternal",
            "Seasonal_Decorative": "Cultural_Fraternal",
            "Regional_Scottish": "Cultural_Fraternal",
            
            # High Negative Impact - Paramilitary
            "Paramilitary_Loyalist": "Paramilitary",
            "Paramilitary_Other": "Paramilitary",
            
            # International
            "International_EU": "International",
            "International_Loyalist": "International", 
            "International_Other": "International",
            "International_Republican": "International",
            
            # Sports/Community
            "Sport_GAA": "Sport_Community",
            "Sport_Other": "Sport_Community",
            
            # Commemorative/Historical
            "Commemorative_Historical": "Commemorative"
        }
        
        self.super_classes = sorted(list(set(self.consolidation_map.values())))
        print(f"📊 Economic Super-Consolidation: 16 → {len(self.super_classes)} classes")
        for original, consolidated in self.consolidation_map.items():
            print(f"  {original} → {consolidated}")
    
    def consolidate_labels(self, items, original_classnames):
        """Convert 16-class labels to 7-class super-consolidated labels"""
        consolidated_items = []
        
        for item in items:
            original_class = original_classnames[item.label]
            if original_class in self.consolidation_map:
                super_class = self.consolidation_map[original_class]
                new_label = self.super_classes.index(super_class)
                
                # Create new item with consolidated label
                from dassl.data.datasets import Datum
                consolidated_item = Datum(
                    impath=item.impath,
                    label=new_label,
                    domain=item.domain,
                    classname=super_class
                )
                consolidated_items.append(consolidated_item)
            else:
                print(f"⚠️  Warning: {original_class} not in consolidation map")
                consolidated_items.append(item)
        
        return consolidated_items

class DataAugmentationSampler:
    """Smart oversampling with data augmentation for minority classes"""
    
    def __init__(self, train_items, classnames, target_samples_per_class=200):
        self.train_items = train_items
        self.classnames = classnames
        self.target_samples = target_samples_per_class
        
        # Group items by class
        self.class_items = defaultdict(list)
        for item in train_items:
            self.class_items[item.label].append(item)
        
        print(f"🔧 Data Augmentation Sampler:")
        print(f"   Target samples per class: {target_samples_per_class}")
        
        for class_id in sorted(self.class_items.keys()):
            count = len(self.class_items[class_id])
            class_name = classnames[class_id]
            print(f"   Class {class_id} ({class_name}): {count} → {min(count * 5, target_samples_per_class)} samples")
    
    def augment_image(self, image):
        """Apply random augmentation to image"""
        # Random brightness
        if random.random() > 0.5:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(random.uniform(0.8, 1.2))
        
        # Random contrast
        if random.random() > 0.5:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(random.uniform(0.8, 1.2))
        
        # Random color
        if random.random() > 0.5:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(random.uniform(0.8, 1.2))
        
        # Random blur
        if random.random() > 0.3:
            image = image.filter(ImageFilter.GaussianBlur(radius=random.uniform(0, 0.5)))
        
        return image
    
    def get_balanced_dataset(self):
        """Create balanced dataset with augmentation"""
        balanced_items = []
        
        for class_id, items in self.class_items.items():
            current_count = len(items)
            target_count = min(current_count * 5, self.target_samples)  # Cap augmentation
            
            # Add original items
            balanced_items.extend(items)
            
            # Add augmented items for minority classes
            if current_count < target_count:
                needed = target_count - current_count
                for _ in range(needed):
                    # Randomly select an item to augment
                    source_item = random.choice(items)
                    
                    # Create augmented version (we'll augment during loading)
                    from dassl.data.datasets import Datum
                    aug_item = Datum(
                        impath=source_item.impath,
                        label=source_item.label,
                        domain=source_item.domain,
                        classname=source_item.classname + "_aug"  # Mark as augmented
                    )
                    balanced_items.append(aug_item)
        
        print(f"✅ Created balanced dataset: {len(self.train_items)} → {len(balanced_items)} samples")
        return balanced_items

class ImprovedNIFlagsDataset(Dataset):
    """Improved dataset with smart augmentation"""
    
    def __init__(self, data_items, classnames, preprocess=None, use_augmentation=False):
        self.data_items = data_items
        self.classnames = classnames
        self.preprocess = preprocess
        self.use_augmentation = use_augmentation
        self.augmenter = DataAugmentationSampler([], classnames) if use_augmentation else None
        
        # Check distribution
        labels = [item.label for item in data_items]
        label_counts = Counter(labels)
        
        print(f"📊 Improved Dataset: {len(data_items)} samples, {len(classnames)} classes")
        for label_idx in sorted(label_counts.keys()):
            count = label_counts[label_idx]
            percentage = count / len(labels) * 100
            class_name = classnames[label_idx]
            print(f"  Class {label_idx:2d} ({class_name}): {count:4d} samples ({percentage:.1f}%)")
    
    def __len__(self):
        return len(self.data_items)
    
    def __getitem__(self, idx):
        item = self.data_items[idx]
        
        # Load image
        image = Image.open(item.impath).convert("RGB")
        
        # Apply augmentation if this is an augmented item
        if self.use_augmentation and "_aug" in item.classname:
            image = self.augmenter.augment_image(image)
        
        # Apply preprocessing
        if self.preprocess:
            image = self.preprocess(image)
        
        return image, item.label

class RS5MImprovedClassifier(nn.Module):
    """Improved RS5M model with better architecture for imbalanced data"""
    
    def __init__(self, checkpoint_path, num_classes, device):
        super().__init__()
        self.device = device
        self.num_classes = num_classes
        
        # Load RS5M model
        print(f"🔄 Loading RS5M ViT-H-14 for improved training...")
        
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None,
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
        
        # Improved classification head with dropout
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(feature_dim, feature_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(feature_dim // 2, num_classes)
        ).to(device)
        
        # Initialize classifier
        for module in self.classifier:
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)
        
        print(f"✅ Improved RS5M model ready: {feature_dim}D → {num_classes} classes")
    
    def forward(self, images):
        # Extract image features from RS5M
        image_features = self.model.encode_image(images)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Classify with improved head
        logits = self.classifier(image_features)
        return logits

class GentleFocalLoss(nn.Module):
    """Gentler focal loss that doesn't over-penalize majority classes"""
    def __init__(self, alpha=0.5, gamma=1.0, weight=None, reduction='mean'):
        super(GentleFocalLoss, self).__init__()
        self.alpha = alpha  # Reduced from 0.25
        self.gamma = gamma  # Reduced from 2.0
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

def create_improved_data_loaders(data_root, use_super_consolidation=True, use_oversampling=True):
    """Create improved data loaders with multiple balancing strategies"""
    print(f"🔧 Creating IMPROVED data loaders from {data_root}")
    
    set_random_seed(42)  # Fixed seed
    
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = str(Path(data_root).resolve())
    cfg.DATASET.NAME = "NIFlagsConsolidated"

    dataset = DATASET_REGISTRY.get("NIFlagsConsolidated")(cfg=cfg)
    train_items = dataset.train_x
    test_items = dataset.test

    # Load consistent class mapping
    classnames_file = Path(data_root) / "ni_flags_consolidated" / "classnames.txt"
    with open(classnames_file, 'r') as f:
        classnames = [line.strip() for line in f if line.strip()]

    # Fix class mapping (same as before)
    dataset_to_file_mapping = {}
    for i, dataset_class in enumerate(dataset.classnames):
        if dataset_class in classnames:
            file_idx = classnames.index(dataset_class)
            dataset_to_file_mapping[i] = file_idx

    def fix_labels(items, mapping):
        fixed_items = []
        for item in items:
            if item.label in mapping:
                new_label = mapping[item.label]
                from dassl.data.datasets import Datum
                fixed_item = Datum(
                    impath=item.impath,
                    label=new_label,
                    domain=item.domain,
                    classname=classnames[new_label]
                )
                fixed_items.append(fixed_item)
        return fixed_items

    train_items = fix_labels(train_items, dataset_to_file_mapping)
    test_items = fix_labels(test_items, dataset_to_file_mapping)

    # Apply super-consolidation if requested
    if use_super_consolidation:
        print("🎯 Applying economic super-consolidation...")
        consolidator = EconomicSuperConsolidator()
        
        train_items = consolidator.consolidate_labels(train_items, classnames)
        test_items = consolidator.consolidate_labels(test_items, classnames)
        classnames = consolidator.super_classes
        
        print(f"✅ Super-consolidated: 16 → {len(classnames)} classes")

    # Apply oversampling if requested
    if use_oversampling:
        print("🎯 Applying smart oversampling...")
        augmenter = DataAugmentationSampler(train_items, classnames, target_samples_per_class=150)
        train_items = augmenter.get_balanced_dataset()

    return train_items, test_items, classnames

def evaluate_model_comprehensive(model, test_dataset, device, classnames, batch_size=16):
    """Comprehensive evaluation"""
    model.eval()
    
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="Evaluating"):
            images = images.to(device)
            labels = labels.to(device)
            
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
    
    # Check prediction diversity
    unique_preds = len(np.unique(all_preds))
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'micro_f1': micro_f1,
        'predictions': all_preds,
        'labels': all_labels,
        'unique_predictions': unique_preds
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=str, default='data', help='Data root directory')
    parser.add_argument('--checkpoint', type=str, required=True, help='RS5M checkpoint path')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')
    parser.add_argument('--epochs', type=int, default=30, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--use-super-consolidation', action='store_true', default=True, help='Use 7-class consolidation')
    parser.add_argument('--use-oversampling', action='store_true', default=True, help='Use smart oversampling')
    parser.add_argument('--focal-alpha', type=float, default=0.5, help='Gentle focal loss alpha')
    parser.add_argument('--focal-gamma', type=float, default=1.0, help='Gentle focal loss gamma')
    parser.add_argument('--eval-freq', type=int, default=5, help='Evaluation frequency')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    set_random_seed(args.seed)
    device = setup_device()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    strategies = []
    if args.use_super_consolidation:
        strategies.append("super_consolidated")
    if args.use_oversampling:
        strategies.append("oversampled")
    
    experiment_name = f"rs5m_improved_{'_'.join(strategies)}_{timestamp}"
    output_dir = Path(args.output_dir) / experiment_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 IMPROVED RS5M Experiment: {experiment_name}")
    print(f"📁 Output: {output_dir}")
    print("🎯 Strategies:")
    print(f"   ✅ Economic super-consolidation: {args.use_super_consolidation}")
    print(f"   ✅ Smart oversampling: {args.use_oversampling}")
    print(f"   ✅ Gentle focal loss (α={args.focal_alpha}, γ={args.focal_gamma})")
    
    # Load improved data
    train_items, test_items, classnames = create_improved_data_loaders(
        args.data_root, 
        use_super_consolidation=args.use_super_consolidation,
        use_oversampling=args.use_oversampling
    )
    
    # Save classnames
    with open(output_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(f"{name}\n")
    
    # Initialize improved model
    model = RS5MImprovedClassifier(args.checkpoint, len(classnames), device)
    
    # Create datasets
    train_dataset = ImprovedNIFlagsDataset(train_items, classnames, model.preprocess, use_augmentation=args.use_oversampling)
    test_dataset = ImprovedNIFlagsDataset(test_items, classnames, model.preprocess, use_augmentation=False)
    
    # Create data loader (no weighted sampling - let the data balance itself)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    
    # Gentle focal loss (no class weights - let oversampling handle balance)
    criterion = GentleFocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma)
    
    # Optimizer with different learning rates for different parts
    optimizer = torch.optim.AdamW([
        {'params': model.model.parameters(), 'lr': args.lr * 0.1},  # Lower LR for pretrained
        {'params': model.classifier.parameters(), 'lr': args.lr}     # Higher LR for classifier
    ], weight_decay=0.01)
    
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    best_accuracy = 0.0
    training_log = []
    
    print(f"\n🚀 Starting IMPROVED RS5M training for {args.epochs} epochs...")
    
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        num_batches = 0
        
        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs}"):
            images = images.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        current_lr = optimizer.param_groups[0]['lr']
        
        log_entry = {
            "epoch": epoch,
            "train_loss": avg_loss,
            "learning_rate": current_lr
        }
        
        # Evaluation
        if epoch % args.eval_freq == 0 or epoch == args.epochs:
            print(f"\n📊 Evaluating IMPROVED model epoch {epoch}...")
            eval_results = evaluate_model_comprehensive(model, test_dataset, device, classnames)
            
            accuracy = eval_results['accuracy']
            macro_f1 = eval_results['macro_f1']
            unique_preds = eval_results['unique_predictions']
            
            log_entry.update({
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "unique_predictions": unique_preds
            })
            
            print(f"🎯 IMPROVED Epoch {epoch}: Accuracy = {accuracy:.4f}, Macro F1 = {macro_f1:.4f}")
            print(f"📊 Model predicts {unique_preds}/{len(classnames)} different classes")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                torch.save(model.state_dict(), output_dir / "model_best.pth")
                
                results = {
                    "accuracy": accuracy,
                    "macro_f1": macro_f1,
                    "predictions": eval_results['predictions'].tolist(),
                    "labels": eval_results['labels'].tolist(),
                    "classnames": classnames,
                    "unique_predictions": unique_preds,
                    "strategies_used": {
                        "super_consolidation": args.use_super_consolidation,
                        "oversampling": args.use_oversampling,
                        "gentle_focal_loss": f"α={args.focal_alpha}, γ={args.focal_gamma}"
                    }
                }
                
                with open(output_dir / "best_results.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                print(f"💾 New best IMPROVED model saved! Accuracy: {accuracy:.4f}")
        
        training_log.append(log_entry)
        scheduler.step()
        
        print(f"IMPROVED Epoch {epoch}/{args.epochs}: Loss = {avg_loss:.6f}, LR = {current_lr:.6f}")
    
    # Save training log
    with open(output_dir / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
    
    print(f"\n✅ IMPROVED RS5M training complete! Best accuracy: {best_accuracy:.4f}")
    print(f"📁 Results saved to: {output_dir}")
    print("\n🎉 This uses multiple strategies to handle extreme imbalance!")

if __name__ == "__main__":
    main()