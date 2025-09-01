#!/usr/bin/env python3
"""
Enhanced training script with hierarchical metrics logging
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

import torch
import json
from pathlib import Path
from collections import defaultdict

# Import the standard training script components
from train_minimal_mps import *

class HierarchicalMetricsCallback:
    """Callback to compute hierarchical metrics during training"""
    
    def __init__(self, classnames):
        self.classnames = classnames
        self.metrics_history = defaultdict(list)
        
    def compute_hierarchical_metrics(self, predictions, labels):
        """Compute metrics at different hierarchy levels"""
        metrics = {}
        
        # Overall accuracy
        overall_acc = (predictions == labels).float().mean().item() * 100
        metrics['overall'] = overall_acc
        
        # Category-level accuracy
        pred_categories = []
        true_categories = []
        for pred, true in zip(predictions, labels):
            if pred < len(self.classnames) and true < len(self.classnames):
                pred_cat = self.classnames[pred].split('-')[0]
                true_cat = self.classnames[true].split('-')[0]
                pred_categories.append(pred_cat)
                true_categories.append(true_cat)
        
        if pred_categories:
            category_acc = sum(1 for p, t in zip(pred_categories, true_categories) if p == t)
            category_acc = category_acc / len(pred_categories) * 100
            metrics['category'] = category_acc
        
        # Context-level accuracy
        pred_contexts = []
        true_contexts = []
        for pred, true in zip(predictions, labels):
            if pred < len(self.classnames) and true < len(self.classnames):
                pred_ctx = '-'.join(self.classnames[pred].split('-')[:2])
                true_ctx = '-'.join(self.classnames[true].split('-')[:2])
                pred_contexts.append(pred_ctx)
                true_contexts.append(true_ctx)
        
        if pred_contexts:
            context_acc = sum(1 for p, t in zip(pred_contexts, true_contexts) if p == t)
            context_acc = context_acc / len(pred_contexts) * 100
            metrics['context'] = context_acc
        
        return metrics
    
    def log_metrics(self, epoch, metrics, phase='train'):
        """Log metrics for tracking"""
        self.metrics_history[f'{phase}_overall'].append(metrics.get('overall', 0))
        self.metrics_history[f'{phase}_category'].append(metrics.get('category', 0))
        self.metrics_history[f'{phase}_context'].append(metrics.get('context', 0))
        
        print(f"\n📊 {phase.upper()} Hierarchical Metrics (Epoch {epoch}):")
        print(f"   Overall (Level 3): {metrics.get('overall', 0):.2f}%")
        print(f"   Category (Level 1): {metrics.get('category', 0):.2f}%")
        print(f"   Context (Level 2): {metrics.get('context', 0):.2f}%")
    
    def save_metrics(self, output_dir):
        """Save metrics history to file"""
        output_path = Path(output_dir) / "hierarchical_metrics.json"
        with open(output_path, 'w') as f:
            json.dump(dict(self.metrics_history), f, indent=2)
        print(f"💾 Metrics saved to: {output_path}")


# Monkey-patch the trainer to add hierarchical metrics
def add_hierarchical_evaluation(trainer_class):
    """Add hierarchical evaluation to trainer"""
    
    original_test = trainer_class.test
    
    def test_with_hierarchical(self):
        """Enhanced test with hierarchical metrics"""
        # Run original test
        original_test(self)
        
        # Compute hierarchical metrics if we have classnames
        if hasattr(self.dm.dataset, 'classnames'):
            print("\n" + "="*60)
            print("📊 COMPUTING HIERARCHICAL METRICS")
            print("="*60)
            
            callback = HierarchicalMetricsCallback(self.dm.dataset.classnames)
            
            # Get predictions on test set
            self.model.eval()
            all_preds = []
            all_labels = []
            
            with torch.no_grad():
                for batch in self.test_loader:
                    input, label = self.parse_batch_test(batch)
                    output = self.model(input)
                    predictions = output.argmax(dim=1)
                    
                    all_preds.extend(predictions.cpu().numpy())
                    all_labels.extend(label.cpu().numpy())
            
            # Compute metrics
            all_preds = torch.tensor(all_preds)
            all_labels = torch.tensor(all_labels)
            metrics = callback.compute_hierarchical_metrics(all_preds, all_labels)
            
            # Log results
            callback.log_metrics(self.epoch, metrics, phase='test')
            
            # Save to output directory
            if hasattr(self.cfg, 'OUTPUT_DIR'):
                callback.save_metrics(self.cfg.OUTPUT_DIR)
    
    trainer_class.test = test_with_hierarchical
    return trainer_class


# Apply the patch when importing
try:
    from trainers.cocoop import CoCoOp
    CoCoOp = add_hierarchical_evaluation(CoCoOp)
    print("✅ Hierarchical metrics added to CoCoOp trainer")
except ImportError:
    print("⚠️ Could not patch CoCoOp trainer")


def main_with_metrics():
    """Run training with enhanced metrics"""
    import sys
    
    # Add custom callback flag
    if '--hierarchical-metrics' in sys.argv:
        sys.argv.remove('--hierarchical-metrics')
        print("✅ Hierarchical metrics enabled")
    
    # Run normal training
    main(sys.argv[1:])


if __name__ == "__main__":
    import sys
    main_with_metrics()
