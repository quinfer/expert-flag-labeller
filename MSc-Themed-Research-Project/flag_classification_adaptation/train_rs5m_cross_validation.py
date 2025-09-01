#!/usr/bin/env python3
"""
RS5M ViT-H-14 Fine-tuning - 5-Fold Cross-Validation Study
=========================================================

Rigorous statistical validation of the economic consolidation breakthrough
using 5-fold cross-validation for publication-ready results.

Key Features:
- 5-fold stratified cross-validation
- Economic super-consolidation (16→7 classes)
- Standard training (no oversampling, no focal loss)
- Fixed class mapping and reproducible splits
- Comprehensive statistical analysis
- Publication-ready confidence intervals

Author: MSc Research Project
Date: January 2025
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
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
from sklearn.model_selection import StratifiedKFold
import open_clip
import scipy.stats as stats

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import Dassl components
from dassl.engine import TRAINER_REGISTRY
from dassl.data import DataManager
from dassl.config import get_cfg_default
from dassl.utils import set_random_seed

# Import our dataset
from datasets.ni_flags_super_consolidated import NIFlagsSuperConsolidated

def set_random_seed(seed):
    """Set random seed for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)

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
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Load visual encoder weights
        visual_state_dict = {}
        for key, value in checkpoint.items():
            if key.startswith('visual.'):
                new_key = key.replace('visual.', '')
                visual_state_dict[new_key] = value
        
        self.model.visual.load_state_dict(visual_state_dict, strict=False)
        
        # Replace classification head with improved architecture
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
    
    def forward(self, x):
        features = self.model.visual(x)
        logits = self.classifier(features)
        return logits

class DasslDatasetWrapper(torch.utils.data.Dataset):
    """Wrapper to convert Dassl Datum objects to tensors"""
    
    def __init__(self, dassl_dataset, transform=None):
        self.data = dassl_dataset
        self.transform = transform
    
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
        
        return image, item.label

def create_cv_splits(dataset, n_splits=5, random_state=42):
    """Create stratified cross-validation splits"""
    
    # Extract labels for stratification
    labels = [item.label for item in dataset.train_x + dataset.val + dataset.test]
    indices = list(range(len(labels)))
    
    # Create stratified k-fold splits
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    cv_splits = []
    all_data = dataset.train_x + dataset.val + dataset.test
    
    for fold_idx, (train_indices, test_indices) in enumerate(skf.split(indices, labels)):
        # Create train/test splits for this fold
        train_data = [all_data[i] for i in train_indices]
        test_data = [all_data[i] for i in test_indices]
        
        # Further split train into train/val (80/20)
        train_labels = [item.label for item in train_data]
        train_indices_inner = list(range(len(train_data)))
        
        # Use stratified split for train/val
        inner_skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state + fold_idx)
        inner_train_idx, inner_val_idx = next(inner_skf.split(train_indices_inner, train_labels))
        
        fold_train = [train_data[i] for i in inner_train_idx]
        fold_val = [train_data[i] for i in inner_val_idx]
        fold_test = test_data
        
        cv_splits.append({
            'fold': fold_idx,
            'train': fold_train,
            'val': fold_val,
            'test': fold_test
        })
        
        print(f"Fold {fold_idx}: Train={len(fold_train)}, Val={len(fold_val)}, Test={len(fold_test)}")
    
    return cv_splits

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

def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for images, labels in train_loader:
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
    
    return total_loss / len(train_loader), 100. * correct / total

def evaluate_fold(model, test_loader, device, classnames):
    """Evaluate model on test set"""
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
    unique_predictions = len(set(all_predictions))
    
    return {
        'accuracy': float(accuracy),
        'macro_f1': float(macro_f1),
        'predictions': [int(p) for p in all_predictions],
        'labels': [int(l) for l in all_labels],
        'unique_predictions': int(unique_predictions)
    }

def train_single_fold(fold_data, fold_idx, args, device, classnames):
    """Train and evaluate a single fold"""
    
    print(f"\n🔬 FOLD {fold_idx + 1}/5")
    print(f"   Train: {len(fold_data['train'])} samples")
    print(f"   Val: {len(fold_data['val'])} samples") 
    print(f"   Test: {len(fold_data['test'])} samples")
    
    # Create transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Create datasets
    train_dataset = DasslDatasetWrapper(fold_data['train'], transform)
    val_dataset = DasslDatasetWrapper(fold_data['val'], transform)
    test_dataset = DasslDatasetWrapper(fold_data['test'], transform)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, 
                             num_workers=args.num_workers, pin_memory=False)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False,
                           num_workers=args.num_workers, pin_memory=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=False)
    
    # Create model
    model = RS5MModel(num_classes=len(classnames), checkpoint_path=args.checkpoint).to(device)
    
    # Standard training setup
    criterion = nn.CrossEntropyLoss()
    
    # Differential learning rates
    backbone_params = []
    classifier_params = []
    
    for name, param in model.named_parameters():
        if 'classifier' in name:
            classifier_params.append(param)
        else:
            backbone_params.append(param)
    
    optimizer = optim.AdamW([
        {'params': backbone_params, 'lr': args.lr * 0.1},
        {'params': classifier_params, 'lr': args.lr}
    ], weight_decay=0.01)
    
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    best_val_accuracy = 0
    best_test_results = None
    
    for epoch in range(args.epochs):
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Validate
        val_results = evaluate_fold(model, val_loader, device, classnames)
        
        # Test (for final evaluation)
        test_results = evaluate_fold(model, test_loader, device, classnames)
        
        # Update learning rate
        scheduler.step()
        
        # Save best model based on validation accuracy
        if val_results['accuracy'] > best_val_accuracy:
            best_val_accuracy = val_results['accuracy']
            best_test_results = test_results
        
        if epoch % 5 == 0 or epoch == args.epochs - 1:
            print(f"   Epoch {epoch+1:2d}: Train={train_acc:5.1f}%, Val={val_results['accuracy']*100:5.1f}%, Test={test_results['accuracy']*100:5.1f}%")
    
    print(f"   ✅ Fold {fold_idx + 1} Best: {best_test_results['accuracy']*100:.2f}% (Classes: {best_test_results['unique_predictions']}/7)")
    
    return best_test_results

def analyze_cv_results(cv_results):
    """Analyze cross-validation results with statistical tests"""
    
    accuracies = [result['accuracy'] for result in cv_results]
    macro_f1s = [result['macro_f1'] for result in cv_results]
    unique_preds = [result['unique_predictions'] for result in cv_results]
    
    # Calculate statistics
    acc_mean = np.mean(accuracies)
    acc_std = np.std(accuracies, ddof=1)  # Sample standard deviation
    acc_sem = acc_std / np.sqrt(len(accuracies))  # Standard error of mean
    
    f1_mean = np.mean(macro_f1s)
    f1_std = np.std(macro_f1s, ddof=1)
    
    # 95% confidence interval
    confidence_level = 0.95
    degrees_freedom = len(accuracies) - 1
    t_value = stats.t.ppf((1 + confidence_level) / 2, degrees_freedom)
    acc_ci_margin = t_value * acc_sem
    acc_ci_lower = acc_mean - acc_ci_margin
    acc_ci_upper = acc_mean + acc_ci_margin
    
    print(f"\n📊 CROSS-VALIDATION RESULTS ANALYSIS")
    print(f"=" * 60)
    print(f"🎯 ACCURACY STATISTICS:")
    print(f"   Mean: {acc_mean:.4f} ({acc_mean*100:.2f}%)")
    print(f"   Std:  {acc_std:.4f} ({acc_std*100:.2f}%)")
    print(f"   SEM:  {acc_sem:.4f} ({acc_sem*100:.2f}%)")
    print(f"   95% CI: [{acc_ci_lower:.4f}, {acc_ci_upper:.4f}] ([{acc_ci_lower*100:.2f}%, {acc_ci_upper*100:.2f}%])")
    print(f"   Range: {min(accuracies):.4f} - {max(accuracies):.4f} ({(max(accuracies)-min(accuracies))*100:.2f}% spread)")
    
    print(f"\n📈 MACRO F1 STATISTICS:")
    print(f"   Mean: {f1_mean:.4f} ({f1_mean*100:.2f}%)")
    print(f"   Std:  {f1_std:.4f} ({f1_std*100:.2f}%)")
    
    print(f"\n🎯 CLASS LEARNING CONSISTENCY:")
    print(f"   Unique classes learned: {unique_preds}")
    print(f"   Mean: {np.mean(unique_preds):.1f}/7 classes")
    print(f"   Range: {min(unique_preds)}-{max(unique_preds)}/7 classes")
    
    print(f"\n📋 INDIVIDUAL FOLD RESULTS:")
    for i, result in enumerate(cv_results):
        print(f"   Fold {i+1}: {result['accuracy']*100:5.2f}% accuracy, {result['macro_f1']*100:5.2f}% F1, {result['unique_predictions']}/7 classes")
    
    # Statistical assessment
    print(f"\n✅ STATISTICAL ASSESSMENT:")
    
    if acc_std < 0.02:  # Less than 2% standard deviation
        reproducibility = "EXCELLENT"
        print(f"   🎉 EXCELLENT reproducibility (σ = {acc_std*100:.2f}%)")
    elif acc_std < 0.05:  # Less than 5% standard deviation
        reproducibility = "GOOD"
        print(f"   ✅ GOOD reproducibility (σ = {acc_std*100:.2f}%)")
    else:
        reproducibility = "MODERATE"
        print(f"   ⚠️  MODERATE reproducibility (σ = {acc_std*100:.2f}%)")
    
    if acc_mean > 0.90:  # Above 90% mean accuracy
        print(f"   🏆 BREAKTHROUGH CONFIRMED: Mean accuracy {acc_mean*100:.2f}% > 90%")
        breakthrough = True
    else:
        print(f"   📊 Good performance but below 90% threshold")
        breakthrough = False
    
    # Compare with previous results
    multi_seed_mean = 0.9457  # From our previous multi-seed validation
    print(f"\n🔍 COMPARISON WITH MULTI-SEED VALIDATION:")
    print(f"   Cross-Validation: {acc_mean*100:.2f}% ± {acc_std*100:.2f}%")
    print(f"   Multi-Seed:       {multi_seed_mean*100:.2f}% ± 0.22%")
    print(f"   Difference:       {(acc_mean - multi_seed_mean)*100:+.2f}%")
    
    if abs(acc_mean - multi_seed_mean) < 0.02:  # Within 2%
        print(f"   ✅ CONSISTENT: Results match multi-seed validation")
        consistency = "CONSISTENT"
    else:
        print(f"   ⚠️  DIVERGENT: Results differ from multi-seed validation")
        consistency = "DIVERGENT"
    
    return {
        'accuracy_mean': acc_mean,
        'accuracy_std': acc_std,
        'accuracy_ci_lower': acc_ci_lower,
        'accuracy_ci_upper': acc_ci_upper,
        'macro_f1_mean': f1_mean,
        'macro_f1_std': f1_std,
        'unique_predictions_mean': np.mean(unique_preds),
        'reproducibility': reproducibility,
        'breakthrough_confirmed': breakthrough,
        'consistency_with_multi_seed': consistency,
        'individual_results': cv_results
    }

def main():
    parser = argparse.ArgumentParser(description='RS5M Fine-tuning - 5-Fold Cross-Validation')
    parser.add_argument('--data-root', type=str, default='data',
                       help='Path to data directory')
    parser.add_argument('--checkpoint', type=str, default='final_code/checkpoints/RS5M_ViT-H-14.pt',
                       help='Path to RS5M checkpoint')
    parser.add_argument('--epochs', type=int, default=15,
                       help='Number of training epochs per fold')
    parser.add_argument('--batch-size', type=int, default=8,
                       help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--num-workers', type=int, default=4,
                       help='Number of data loading workers')
    parser.add_argument('--n-folds', type=int, default=5,
                       help='Number of cross-validation folds')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Create experiment directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(f"flag_classification_adaptation/experiments/rs5m_cross_validation_{args.n_folds}fold_{timestamp}")
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🔬 5-FOLD CROSS-VALIDATION STUDY")
    print(f"📁 Experiment directory: {exp_dir}")
    print(f"🎯 Strategy: Economic super-consolidation (16→7 classes) with rigorous CV")
    print(f"📊 Validation: {args.n_folds}-fold stratified cross-validation")
    print(f"⏱️  Expected time: ~{args.n_folds * 30} minutes total")
    
    # Load dataset and create CV splits
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = args.data_root
    cfg.DATASET.NAME = "NIFlagsSuperConsolidated"
    
    dataset = NIFlagsSuperConsolidated(cfg)
    classnames = dataset.classnames
    
    print(f"\n📊 Dataset: {len(dataset.train_x + dataset.val + dataset.test)} total samples, {len(classnames)} classes")
    
    # Create cross-validation splits
    cv_splits = create_cv_splits(dataset, n_splits=args.n_folds, random_state=args.seed)
    
    # Run cross-validation
    cv_results = []
    
    for fold_idx, fold_data in enumerate(cv_splits):
        fold_result = train_single_fold(fold_data, fold_idx, args, device, classnames)
        cv_results.append(fold_result)
    
    # Analyze results
    analysis = analyze_cv_results(cv_results)
    
    # Save results
    final_results = {
        'experiment_type': 'cross_validation',
        'n_folds': args.n_folds,
        'strategy': 'economic_consolidation_7class',
        'statistical_analysis': analysis,
        'args': vars(args),
        'timestamp': timestamp
    }
    
    with open(exp_dir / 'cv_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n🎉 5-FOLD CROSS-VALIDATION COMPLETE!")
    print(f"   Mean Accuracy: {analysis['accuracy_mean']*100:.2f}% ± {analysis['accuracy_std']*100:.2f}%")
    print(f"   95% CI: [{analysis['accuracy_ci_lower']*100:.2f}%, {analysis['accuracy_ci_upper']*100:.2f}%]")
    print(f"   Reproducibility: {analysis['reproducibility']}")
    print(f"   Breakthrough: {'CONFIRMED' if analysis['breakthrough_confirmed'] else 'PARTIAL'}")
    print(f"   Results saved to: {exp_dir}")
    
    return analysis['accuracy_mean']

if __name__ == '__main__':
    main()