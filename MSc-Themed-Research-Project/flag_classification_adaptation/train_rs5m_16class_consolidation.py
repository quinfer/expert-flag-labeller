#!/usr/bin/env python3
"""
RS5M ViT-H-14 Fine-tuning - 16-Class Economic Consolidation Test
================================================================

Tests if economic consolidation principles scale to the original 16-class problem.
This validates the universality of our consolidation breakthrough.

Key Features:
- Uses original 16-class consolidated dataset (NIFlagsConsolidated)
- Same economic principles as 7-class success
- Standard training (no oversampling, no focal loss)
- Fixed class mapping and reproducible splits
- Comprehensive evaluation and logging

Author: MSc Research Project
Date: January 2025
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
import json
import argparse
import os
import sys
from pathlib import Path
from collections import Counter
import random
import numpy as np
from datetime import datetime
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import open_clip

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import Dassl components
from dassl.engine import TRAINER_REGISTRY
from dassl.data import DataManager
from dassl.config import get_cfg_default
from dassl.utils import set_random_seed

# Import our dataset
from datasets.ni_flags_consolidated import NIFlagsConsolidated

def set_random_seed(seed):
    """Set random seed for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)

class ClassMapper:
    """Ensures consistent class mapping between dataset and classnames.txt"""
    
    def __init__(self, classnames_file):
        with open(classnames_file, 'r') as f:
            self.file_order_classes = [line.strip() for line in f.readlines()]
        
        # Dataset uses alphabetical order internally
        self.dataset_order_classes = sorted(self.file_order_classes)
        
        # Create mapping from dataset index to file index
        self.dataset_to_file_idx = {}
        for dataset_idx, class_name in enumerate(self.dataset_order_classes):
            file_idx = self.file_order_classes.index(class_name)
            self.dataset_to_file_idx[dataset_idx] = file_idx
        
        print(f"🔧 Class Mapper: Dataset order → File order mapping created")
        print(f"   Example: Dataset[0]='{self.dataset_order_classes[0]}' → File[{self.dataset_to_file_idx[0]}]")

class RS5MModel(nn.Module):
    """RS5M ViT-H-14 model with improved classification head"""
    
    def __init__(self, num_classes, checkpoint_path):
        super().__init__()
        
        # Load RS5M ViT-H-14 architecture
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None
        )
        
        # Load RS5M checkpoint
        print(f"📥 Loading RS5M checkpoint from {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Load visual encoder weights
        visual_state_dict = {}
        for key, value in checkpoint.items():
            if key.startswith('visual.'):
                new_key = key.replace('visual.', '')
                visual_state_dict[new_key] = value
        
        missing_keys, unexpected_keys = self.model.visual.load_state_dict(visual_state_dict, strict=False)
        print(f"✅ Loaded RS5M visual weights: {len(visual_state_dict)} parameters")
        if missing_keys:
            print(f"⚠️  Missing keys: {len(missing_keys)}")
        if unexpected_keys:
            print(f"⚠️  Unexpected keys: {len(unexpected_keys)}")
        
        # Replace classification head with improved architecture
        # Get the feature dimension
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224)
            features = self.model.visual(dummy_input)
            feature_dim = features.shape[-1]
        
        # Multi-layer classification head with dropout
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
        
        print(f"🧠 Model: RS5M ViT-H-14 with {num_classes}-class head")
    
    def forward(self, x):
        # Extract visual features using RS5M
        features = self.model.visual(x)
        
        # Apply classification head
        logits = self.classifier(features)
        return logits

class DasslDatasetWrapper(torch.utils.data.Dataset):
    """Wrapper to convert Dassl Datum objects to tensors"""
    
    def __init__(self, dassl_dataset, transform=None, class_mapper=None):
        self.data = dassl_dataset
        self.transform = transform
        self.class_mapper = class_mapper
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Load image
        from PIL import Image
        image = Image.open(item.impath).convert('RGB')
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        # Map class index if mapper provided
        label = item.label
        if self.class_mapper:
            label = self.class_mapper.dataset_to_file_idx[label]
        
        return image, label

def create_data_loaders(data_root, batch_size, num_workers=4, seed=42):
    """Create data loaders for 16-class consolidated dataset"""
    
    set_random_seed(seed)  # Ensure reproducible splits
    
    # Create minimal Dassl config
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = data_root
    cfg.DATASET.NAME = "NIFlagsConsolidated"
    
    # Create 16-class consolidated dataset
    dataset = NIFlagsConsolidated(cfg)
    
    print(f"📊 Dataset loaded: {len(dataset.train_x)} train, {len(dataset.val)} val, {len(dataset.test)} test")
    
    # Create class mapper for consistent indexing
    classnames_file = Path(data_root) / "ni_flags_consolidated" / "classnames.txt"
    class_mapper = ClassMapper(classnames_file)
    
    # Standard transforms (no augmentation for clean comparison)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Create wrapped datasets with class mapping
    train_dataset = DasslDatasetWrapper(dataset.train_x, transform, class_mapper)
    val_dataset = DasslDatasetWrapper(dataset.val, transform, class_mapper)
    test_dataset = DasslDatasetWrapper(dataset.test, transform, class_mapper)
    
    # Create standard data loaders (NO weighted sampling - test pure consolidation)
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,  # Standard shuffle, no balancing
        num_workers=num_workers,
        pin_memory=False  # Disable for MPS compatibility
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=num_workers,
        pin_memory=False
    )
    
    test_loader = DataLoader(
        test_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=num_workers,
        pin_memory=False
    )
    
    # Print class distribution (should be imbalanced)
    train_labels = [class_mapper.dataset_to_file_idx[item.label] for item in dataset.train_x]
    label_counts = Counter(train_labels)
    
    print(f"\n📈 Training Class Distribution (16-Class, No Balancing):")
    for class_idx in sorted(label_counts.keys()):
        class_name = class_mapper.file_order_classes[class_idx]
        count = label_counts[class_idx]
        percentage = count / len(train_labels) * 100
        print(f"   {class_name}: {count} samples ({percentage:.1f}%)")
    
    return train_loader, val_loader, test_loader, class_mapper.file_order_classes

def setup_device():
    """Setup computation device"""
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("🚀 Using Metal Performance Shaders (MPS)")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("🚀 Using CUDA")
    else:
        device = torch.device("cpu")
        print("💻 Using CPU")
    
    return device

def train_epoch(model, train_loader, criterion, optimizer, device, epoch):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_idx, (images, labels) in enumerate(train_loader):
        images = images.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        if batch_idx % 10 == 0:
            print(f'Epoch {epoch}, Batch {batch_idx}/{len(train_loader)}, '
                  f'Loss: {loss.item():.4f}, Acc: {100.*correct/total:.2f}%')
    
    return total_loss / len(train_loader), 100. * correct / total

def evaluate(model, test_loader, device, classnames):
    """Evaluate model and return detailed metrics"""
    model.eval()
    all_predictions = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            _, predicted = outputs.max(1)
            
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Calculate metrics
    accuracy = sum(p == l for p, l in zip(all_predictions, all_labels)) / len(all_labels)
    macro_f1 = f1_score(all_labels, all_predictions, average='macro', zero_division=0)
    
    # Count unique predictions
    unique_predictions = len(set(all_predictions))
    
    print(f"\n📊 Evaluation Results:")
    print(f"   Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"   Macro F1: {macro_f1:.4f} ({macro_f1*100:.2f}%)")
    print(f"   Unique predictions: {unique_predictions}/{len(classnames)} classes")
    
    # Print classification report
    try:
        report = classification_report(all_labels, all_predictions, 
                                     target_names=classnames, zero_division=0)
        print(f"\n📋 Classification Report:\n{report}")
    except Exception as e:
        print(f"⚠️  Classification report error: {e}")
    
    return {
        'accuracy': float(accuracy),
        'macro_f1': float(macro_f1),
        'predictions': [int(p) for p in all_predictions],
        'labels': [int(l) for l in all_labels],
        'classnames': classnames,
        'unique_predictions': int(unique_predictions),
        'strategies_used': {
            'economic_consolidation_16class': True,
            'oversampling': False,
            'focal_loss': False,
            'weighted_sampling': False
        }
    }

def main():
    parser = argparse.ArgumentParser(description='RS5M Fine-tuning - 16-Class Economic Consolidation Test')
    parser.add_argument('--data-root', type=str, default='data',
                       help='Path to data directory')
    parser.add_argument('--checkpoint', type=str, default='final_code/checkpoints/RS5M_ViT-H-14.pt',
                       help='Path to RS5M checkpoint')
    parser.add_argument('--epochs', type=int, default=20,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=8,
                       help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--num-workers', type=int, default=4,
                       help='Number of data loading workers')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Create experiment directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(f"flag_classification_adaptation/experiments/rs5m_16class_consolidation_seed{args.seed}_{timestamp}")
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎯 16-CLASS ECONOMIC CONSOLIDATION TEST")
    print(f"📁 Experiment directory: {exp_dir}")
    print(f"🔬 Strategy: Economic consolidation principles applied to 16-class problem")
    print(f"📊 Baseline comparison: 0.56% (16-class with all strategies failed)")
    print(f"🎯 Goal: Validate consolidation universality across problem scales")
    
    # Create data loaders
    train_loader, val_loader, test_loader, classnames = create_data_loaders(
        args.data_root, args.batch_size, args.num_workers, args.seed
    )
    
    # Create model
    model = RS5MModel(
        num_classes=len(classnames),
        checkpoint_path=args.checkpoint
    ).to(device)
    
    # Standard cross-entropy loss (no focal loss)
    criterion = nn.CrossEntropyLoss()
    
    # Differential learning rates for pretrained vs new layers
    backbone_params = []
    classifier_params = []
    
    for name, param in model.named_parameters():
        if 'classifier' in name:
            classifier_params.append(param)
        else:
            backbone_params.append(param)
    
    optimizer = optim.AdamW([
        {'params': backbone_params, 'lr': args.lr * 0.1},  # Lower LR for pretrained
        {'params': classifier_params, 'lr': args.lr}        # Higher LR for new layers
    ], weight_decay=0.01)
    
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    print(f"\n🚀 Training Configuration:")
    print(f"   Classes: {len(classnames)} (16-class consolidated)")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch size: {args.batch_size}")
    print(f"   Learning rate: {args.lr} (backbone: {args.lr * 0.1})")
    print(f"   Loss function: CrossEntropyLoss (standard)")
    print(f"   Optimizer: AdamW with differential LRs")
    print(f"   Strategy: Economic consolidation principles (no oversampling)")
    
    # Training loop
    best_accuracy = 0
    best_results = None
    
    for epoch in range(args.epochs):
        print(f"\n📚 Epoch {epoch+1}/{args.epochs}")
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device, epoch+1)
        
        # Evaluate
        results = evaluate(model, test_loader, device, classnames)
        
        # Update learning rate
        scheduler.step()
        
        # Save best model
        if results['accuracy'] > best_accuracy:
            best_accuracy = results['accuracy']
            best_results = results
            
            # Save model checkpoint
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'epoch': epoch,
                'accuracy': results['accuracy'],
                'macro_f1': results['macro_f1']
            }, exp_dir / 'best_model.pt')
        
        print(f"   Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"   Test Acc: {results['accuracy']*100:.2f}%, Macro F1: {results['macro_f1']*100:.2f}%")
        print(f"   Best Acc: {best_accuracy*100:.2f}%")
    
    # Save final results
    with open(exp_dir / 'best_results.json', 'w') as f:
        json.dump(best_results, f, indent=2)
    
    # Save training configuration
    config = {
        'experiment_type': '16class_economic_consolidation_test',
        'strategies': {
            'economic_consolidation': '16-class consolidated dataset',
            'oversampling': False,
            'focal_loss': False,
            'weighted_sampling': False,
            'class_mapping_fix': True
        },
        'comparison_baseline': {
            'method': '16-class with all strategies',
            'accuracy': 0.0056,
            'status': 'failed'
        },
        'args': vars(args),
        'final_accuracy': float(best_accuracy),
        'final_macro_f1': float(best_results['macro_f1']) if best_results else 0,
        'improvement_vs_baseline': f"{best_accuracy/0.0056:.1f}x" if best_accuracy > 0 else "N/A"
    }
    
    with open(exp_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n🎉 16-CLASS CONSOLIDATION TEST COMPLETE!")
    print(f"   Final Accuracy: {best_accuracy*100:.2f}%")
    print(f"   Final Macro F1: {best_results['macro_f1']*100:.2f}%")
    print(f"   Classes Learned: {best_results['unique_predictions']}/16")
    print(f"   Improvement vs Baseline: {best_accuracy/0.0056:.1f}x")
    print(f"   Results saved to: {exp_dir}")
    
    # Assessment vs 7-class results
    consolidation_7class_acc = 0.9457  # Multi-seed mean
    if best_accuracy > 0.8:  # 80% threshold for "good" 16-class performance
        print(f"\n✅ CONSOLIDATION SCALES SUCCESSFULLY!")
        print(f"   16-class: {best_accuracy*100:.2f}% vs 7-class: {consolidation_7class_acc*100:.2f}%")
        print(f"   Economic consolidation principles work across problem scales!")
    else:
        print(f"\n📊 CONSOLIDATION SCALING ANALYSIS:")
        print(f"   16-class: {best_accuracy*100:.2f}% vs 7-class: {consolidation_7class_acc*100:.2f}%")
        print(f"   Consider: More aggressive consolidation may be needed for 16-class")
    
    return best_accuracy

if __name__ == '__main__':
    main()