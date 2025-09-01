#!/usr/bin/env python3
"""
Real-time Training Monitor for Focal Loss Experiments
Tracks per-class accuracy and loss dynamics during training
"""

import json
import time
import torch
import numpy as np
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional

class TrainingMonitor:
    """Enhanced training monitor with per-class tracking"""
    
    def __init__(self, num_classes=70, output_dir="experiments/monitoring"):
        self.num_classes = num_classes
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics storage
        self.metrics = defaultdict(list)
        self.per_class_metrics = defaultdict(lambda: defaultdict(list))
        
        # Class distribution info
        self.class_names = self._load_class_names()
        self.class_counts = self._get_class_distribution()
        
        # Real-time tracking
        self.current_epoch = 0
        self.best_accuracy = 0.0
        self.best_rare_accuracy = 0.0
        
    def _load_class_names(self):
        """Load hierarchical class names"""
        # These should match your actual class names
        class_names = {
            0: "National-Lamppost_mounted-Union_Jack",
            1: "National-Building_mounted-Union_Jack",
            2: "National-Lamppost_mounted-Ulster_Banner",
            3: "National-Pole_mounted_(in_ground)-Union_Jack",
            4: "National-Building_mounted-Ulster_Banner",
            5: "Fraternal-Lamppost_mounted-Orange_Order",
            6: "Bunting-Triangular_bunting-Red/White/Blue",
            7: "National-Lamppost_mounted-Irish_Tricolor",
            8: "National-Pole_mounted_(in_ground)-Ulster_Banner",
            9: "Bunting-Bunting_display-Union_Jack_Bunting",
            # Add remaining classes...
        }
        
        # Fill in remaining with generic names if not specified
        for i in range(self.num_classes):
            if i not in class_names:
                class_names[i] = f"Class_{i}"
        
        return class_names
    
    def _get_class_distribution(self):
        """Get actual class distribution"""
        # Your actual distribution
        distribution = {
            0: 777, 1: 417, 2: 386, 3: 142, 4: 99,
            5: 48, 6: 42, 7: 39, 8: 38, 9: 26,
            10: 23, 11: 20, 12: 17, 13: 14, 14: 13,
            15: 13, 16: 11, 17: 10, 18: 8, 19: 8,
            20: 8, 21: 7, 22: 7, 23: 6, 24: 6,
            25: 5, 26: 5, 27: 4, 28: 4, 29: 3,
            # Continue with actual counts...
        }
        
        # Fill remaining with 1 if not specified
        for i in range(self.num_classes):
            if i not in distribution:
                distribution[i] = 1
        
        return distribution
    
    def categorise_classes(self):
        """Categorise classes by frequency"""
        categories = {
            'majority': [],    # >100 samples
            'common': [],      # 20-100 samples
            'rare': [],        # 5-20 samples
            'very_rare': []    # <5 samples
        }
        
        for class_id, count in self.class_counts.items():
            if count > 100:
                categories['majority'].append(class_id)
            elif count >= 20:
                categories['common'].append(class_id)
            elif count >= 5:
                categories['rare'].append(class_id)
            else:
                categories['very_rare'].append(class_id)
        
        return categories
    
    def update(self, epoch: int, batch_idx: int, loss: float, 
               predictions: torch.Tensor, labels: torch.Tensor,
               logits: Optional[torch.Tensor] = None):
        """Update metrics with batch results"""
        
        self.current_epoch = epoch
        
        # Overall metrics
        accuracy = (predictions == labels).float().mean().item()
        self.metrics['loss'].append(loss)
        self.metrics['accuracy'].append(accuracy)
        self.metrics['epoch'].append(epoch)
        self.metrics['batch'].append(batch_idx)
        
        # Per-class accuracy
        for class_id in range(self.num_classes):
            mask = labels == class_id
            if mask.sum() > 0:
                class_acc = (predictions[mask] == class_id).float().mean().item()
                self.per_class_metrics[class_id]['accuracy'].append(class_acc)
                self.per_class_metrics[class_id]['epoch'].append(epoch)
                
                # Track confidence if logits provided
                if logits is not None:
                    class_conf = torch.softmax(logits[mask], dim=1)[:, class_id].mean().item()
                    self.per_class_metrics[class_id]['confidence'].append(class_conf)
        
        # Category-wise accuracy
        categories = self.categorise_classes()
        for category, class_ids in categories.items():
            mask = torch.isin(labels, torch.tensor(class_ids))
            if mask.sum() > 0:
                cat_acc = (predictions[mask] == labels[mask]).float().mean().item()
                self.metrics[f'{category}_accuracy'].append(cat_acc)
        
        # Update best scores
        if accuracy > self.best_accuracy:
            self.best_accuracy = accuracy
        
        rare_mask = torch.isin(labels, torch.tensor(categories['rare'] + categories['very_rare']))
        if rare_mask.sum() > 0:
            rare_acc = (predictions[rare_mask] == labels[rare_mask]).float().mean().item()
            if rare_acc > self.best_rare_accuracy:
                self.best_rare_accuracy = rare_acc
    
    def log_epoch_summary(self, epoch: int):
        """Log summary at end of epoch"""
        print(f"\n" + "="*60)
        print(f"📊 EPOCH {epoch} SUMMARY")
        print("="*60)
        
        # Calculate epoch averages
        epoch_mask = np.array(self.metrics['epoch']) == epoch
        epoch_loss = np.mean(np.array(self.metrics['loss'])[epoch_mask])
        epoch_acc = np.mean(np.array(self.metrics['accuracy'])[epoch_mask])
        
        print(f"📈 Overall:")
        print(f"   Loss: {epoch_loss:.4f}")
        print(f"   Accuracy: {epoch_acc:.2%}")
        print(f"   Best Accuracy: {self.best_accuracy:.2%}")
        
        # Category performance
        categories = self.categorise_classes()
        print(f"\n📊 By Frequency:")
        for category in ['majority', 'common', 'rare', 'very_rare']:
            key = f'{category}_accuracy'
            if key in self.metrics and len(self.metrics[key]) > 0:
                cat_acc = np.mean(self.metrics[key][-100:])  # Last 100 batches
                print(f"   {category.title()}: {cat_acc:.2%}")
        
        # Top/Bottom performing classes
        class_performances = []
        for class_id in range(self.num_classes):
            if class_id in self.per_class_metrics and 'accuracy' in self.per_class_metrics[class_id]:
                recent_acc = np.mean(self.per_class_metrics[class_id]['accuracy'][-10:])
                class_performances.append((class_id, recent_acc))
        
        class_performances.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 Top 5 Classes:")
        for class_id, acc in class_performances[:5]:
            count = self.class_counts.get(class_id, 0)
            name = self.class_names.get(class_id, f"Class_{class_id}")
            print(f"   {name[:30]}: {acc:.2%} (n={count})")
        
        print(f"\n⚠️ Bottom 5 Classes:")
        for class_id, acc in class_performances[-5:]:
            count = self.class_counts.get(class_id, 0)
            name = self.class_names.get(class_id, f"Class_{class_id}")
            print(f"   {name[:30]}: {acc:.2%} (n={count})")
        
        # Save checkpoint
        self.save_metrics(epoch)
    
    def save_metrics(self, epoch: int):
        """Save metrics to file"""
        metrics_file = self.output_dir / f"metrics_epoch_{epoch}.json"
        
        # Prepare serialisable metrics
        save_data = {
            'epoch': epoch,
            'timestamp': datetime.now().isoformat(),
            'overall_metrics': {
                'loss': float(np.mean(self.metrics['loss'][-100:])),
                'accuracy': float(np.mean(self.metrics['accuracy'][-100:])),
                'best_accuracy': float(self.best_accuracy),
                'best_rare_accuracy': float(self.best_rare_accuracy)
            },
            'category_metrics': {},
            'per_class_summary': {}
        }
        
        # Category metrics
        categories = self.categorise_classes()
        for category in ['majority', 'common', 'rare', 'very_rare']:
            key = f'{category}_accuracy'
            if key in self.metrics:
                save_data['category_metrics'][category] = {
                    'accuracy': float(np.mean(self.metrics[key][-100:])),
                    'num_classes': len(categories[category]),
                    'total_samples': sum(self.class_counts[c] for c in categories[category])
                }
        
        # Per-class summary
        for class_id in range(self.num_classes):
            if class_id in self.per_class_metrics:
                save_data['per_class_summary'][str(class_id)] = {
                    'name': self.class_names.get(class_id, f"Class_{class_id}"),
                    'count': self.class_counts.get(class_id, 0),
                    'accuracy': float(np.mean(self.per_class_metrics[class_id].get('accuracy', [0])[-10:])),
                    'confidence': float(np.mean(self.per_class_metrics[class_id].get('confidence', [0])[-10:]))
                }
        
        with open(metrics_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"\n💾 Metrics saved to: {metrics_file}")
    
    def plot_training_curves(self, save_path: Optional[str] = None):
        """Generate training curve plots"""
        if len(self.metrics['loss']) < 10:
            print("Not enough data for plotting")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Loss curve
        axes[0, 0].plot(self.metrics['loss'], alpha=0.3)
        axes[0, 0].plot(np.convolve(self.metrics['loss'], np.ones(50)/50, mode='valid'), 
                       label='Moving Avg (50)')
        axes[0, 0].set_xlabel('Batch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].set_title('Training Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Overall accuracy
        axes[0, 1].plot(self.metrics['accuracy'], alpha=0.3)
        axes[0, 1].plot(np.convolve(self.metrics['accuracy'], np.ones(50)/50, mode='valid'),
                       label='Moving Avg (50)')
        axes[0, 1].axhline(y=self.best_accuracy, color='r', linestyle='--', 
                          label=f'Best: {self.best_accuracy:.2%}')
        axes[0, 1].set_xlabel('Batch')
        axes[0, 1].set_ylabel('Accuracy')
        axes[0, 1].set_title('Overall Accuracy')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Category-wise accuracy
        categories = ['majority', 'common', 'rare', 'very_rare']
        colors = ['green', 'blue', 'orange', 'red']
        for category, color in zip(categories, colors):
            key = f'{category}_accuracy'
            if key in self.metrics and len(self.metrics[key]) > 0:
                axes[1, 0].plot(self.metrics[key], label=category.title(), 
                               color=color, alpha=0.5)
        axes[1, 0].set_xlabel('Batch')
        axes[1, 0].set_ylabel('Accuracy')
        axes[1, 0].set_title('Accuracy by Class Frequency')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Class distribution vs performance
        class_counts_list = []
        class_accs_list = []
        for class_id in range(self.num_classes):
            if class_id in self.per_class_metrics and 'accuracy' in self.per_class_metrics[class_id]:
                class_counts_list.append(self.class_counts.get(class_id, 1))
                class_accs_list.append(np.mean(self.per_class_metrics[class_id]['accuracy'][-10:]))
        
        axes[1, 1].scatter(class_counts_list, class_accs_list, alpha=0.6)
        axes[1, 1].set_xlabel('Number of Training Samples (log scale)')
        axes[1, 1].set_ylabel('Class Accuracy')
        axes[1, 1].set_title('Class Frequency vs Performance')
        axes[1, 1].set_xscale('log')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📊 Plot saved to: {save_path}")
        else:
            save_path = self.output_dir / f"training_curves_epoch_{self.current_epoch}.png"
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.close()


def integrate_with_trainer():
    """
    Code to integrate monitoring into your trainer
    Add this to your cocoop.py trainer
    """
    integration_code = '''
# Add to cocoop.py at the top:
from training_monitor import TrainingMonitor

# In CoCoOp.__init__ or build_model:
self.monitor = TrainingMonitor(num_classes=len(classnames))

# In forward_backward method, after computing loss:
with torch.no_grad():
    predictions = logits.argmax(dim=1)
    self.monitor.update(
        epoch=self.epoch,
        batch_idx=self.batch_idx,
        loss=loss.item(),
        predictions=predictions,
        labels=label,
        logits=logits
    )

# At end of each epoch (in train method):
self.monitor.log_epoch_summary(self.epoch)
self.monitor.plot_training_curves()

# For testing phase:
def test(self):
    # Your existing test code...
    # Add monitoring:
    test_acc_per_class = defaultdict(list)
    for batch in test_loader:
        # ... existing code ...
        for class_id in range(self.num_classes):
            mask = labels == class_id
            if mask.sum() > 0:
                class_acc = (predictions[mask] == class_id).float().mean()
                test_acc_per_class[class_id].append(class_acc.item())
    
    # Log final test results
    print("\\n" + "="*60)
    print("🎯 FINAL TEST RESULTS")
    print("="*60)
    for category, class_ids in self.monitor.categorise_classes().items():
        cat_accs = [np.mean(test_acc_per_class[c]) for c in class_ids if c in test_acc_per_class]
        if cat_accs:
            print(f"{category.title()} Classes: {np.mean(cat_accs):.2%}")
'''
    
    print("\n" + "="*60)
    print("📝 INTEGRATION INSTRUCTIONS")
    print("="*60)
    print(integration_code)
    
    return integration_code


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 TRAINING MONITOR SETUP")
    print("="*60)
    
    # Example usage
    monitor = TrainingMonitor(num_classes=70)
    
    # Show class categorisation
    categories = monitor.categorise_classes()
    print("\n📊 Class Distribution Analysis:")
    for category, class_ids in categories.items():
        total_samples = sum(monitor.class_counts.get(c, 0) for c in class_ids)
        print(f"   {category.title()}: {len(class_ids)} classes, {total_samples} samples")
    
    # Show integration instructions
    integrate_with_trainer()
    
    print("\n✅ Monitor ready for integration!")
