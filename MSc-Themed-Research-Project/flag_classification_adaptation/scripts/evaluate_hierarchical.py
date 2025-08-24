#!/usr/bin/env python3
"""
Comprehensive evaluation script for NI Flags classification
Captures category-level, hierarchical, and per-class metrics
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class HierarchicalEvaluator:
    """Evaluate model performance at multiple hierarchical levels"""
    
    def __init__(self, predictions_file=None, model_dir=None):
        self.predictions_file = predictions_file
        self.model_dir = Path(model_dir) if model_dir else Path("experiments/latest")
        
        # Load class information
        self.load_class_info()
        
        # Category groupings
        self.categories = {
            'National': ['National'],
            'Fraternal': ['Fraternal'],
            'Sport': ['Sport'],
            'Military': ['Military'],
            'Historical': ['Historical'],
            'International': ['International'],
            'Proscribed': ['Proscribed'],
            'Bunting': ['Bunting']
        }
        
        # Class frequency groups (based on training data)
        self.frequency_groups = {
            'dominant': [],    # >100 samples
            'common': [],      # 20-100 samples
            'rare': [],        # 5-20 samples
            'very_rare': []    # <5 samples
        }
    
    def load_class_info(self):
        """Load class names and distribution"""
        # Load from dataset
        dataset_dir = Path("../data/ni_flags_v2")
        
        # Load class names
        classnames_file = dataset_dir / "classnames.txt"
        if classnames_file.exists():
            with open(classnames_file, 'r') as f:
                self.classnames = [line.strip() for line in f.readlines()]
        else:
            self.classnames = []
            print("⚠️ classnames.txt not found")
        
        # Load dataset info
        info_file = dataset_dir / "dataset_info.json"
        if info_file.exists():
            with open(info_file, 'r') as f:
                self.dataset_info = json.load(f)
                
            # Categorize classes by frequency
            if 'class_distribution' in self.dataset_info:
                for class_name, count in self.dataset_info['class_distribution'].items():
                    class_idx = self.classnames.index(class_name) if class_name in self.classnames else -1
                    if count >= 100:
                        self.frequency_groups['dominant'].append(class_idx)
                    elif count >= 20:
                        self.frequency_groups['common'].append(class_idx)
                    elif count >= 5:
                        self.frequency_groups['rare'].append(class_idx)
                    else:
                        self.frequency_groups['very_rare'].append(class_idx)
    
    def evaluate_from_log(self, log_file):
        """Extract metrics from training log"""
        print("\n" + "="*60)
        print("📊 EXTRACTING METRICS FROM LOG")
        print("="*60)
        
        if not Path(log_file).exists():
            print(f"❌ Log file not found: {log_file}")
            return None
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find test results
        test_results = {}
        for i, line in enumerate(lines):
            if "Evaluate on the *test* set" in line:
                # Parse next few lines for results
                for j in range(i, min(i+10, len(lines))):
                    if "accuracy:" in lines[j]:
                        # Extract accuracy
                        parts = lines[j].split()
                        for k, part in enumerate(parts):
                            if part == "accuracy:":
                                test_results['overall_accuracy'] = float(parts[k+1].strip('%'))
                    if "macro_f1:" in lines[j]:
                        parts = lines[j].split()
                        for k, part in enumerate(parts):
                            if part == "macro_f1:":
                                test_results['macro_f1'] = float(parts[k+1].strip('%'))
        
        return test_results
    
    def evaluate_predictions(self, predictions, labels, output_file=None):
        """
        Comprehensive evaluation of predictions
        
        Args:
            predictions: numpy array of predicted class indices
            labels: numpy array of true class indices
            output_file: optional path to save results
        """
        
        results = {}
        n_samples = len(predictions)
        
        print("\n" + "="*60)
        print("🎯 HIERARCHICAL EVALUATION")
        print("="*60)
        
        # 1. Overall Accuracy
        overall_correct = (predictions == labels).sum()
        overall_acc = overall_correct / n_samples * 100
        results['overall_accuracy'] = overall_acc
        print(f"\n📊 Overall Accuracy: {overall_acc:.2f}% ({overall_correct}/{n_samples})")
        
        # 2. Category-Level Accuracy (Level 1)
        category_preds = []
        category_labels = []
        for pred_idx, true_idx in zip(predictions, labels):
            if pred_idx < len(self.classnames) and true_idx < len(self.classnames):
                pred_class = self.classnames[pred_idx]
                true_class = self.classnames[true_idx]
                pred_category = pred_class.split('-')[0] if '-' in pred_class else 'Unknown'
                true_category = true_class.split('-')[0] if '-' in true_class else 'Unknown'
                category_preds.append(pred_category)
                category_labels.append(true_category)
        
        category_correct = sum(1 for p, t in zip(category_preds, category_labels) if p == t)
        category_acc = category_correct / len(category_preds) * 100 if category_preds else 0
        results['category_accuracy'] = category_acc
        print(f"\n🏷️ Category-Level Accuracy: {category_acc:.2f}%")
        
        # 3. Context-Level Accuracy (Level 2)
        context_preds = []
        context_labels = []
        for pred_idx, true_idx in zip(predictions, labels):
            if pred_idx < len(self.classnames) and true_idx < len(self.classnames):
                pred_class = self.classnames[pred_idx]
                true_class = self.classnames[true_idx]
                pred_context = '-'.join(pred_class.split('-')[:2]) if '-' in pred_class else 'Unknown'
                true_context = '-'.join(true_class.split('-')[:2]) if '-' in true_class else 'Unknown'
                context_preds.append(pred_context)
                context_labels.append(true_context)
        
        context_correct = sum(1 for p, t in zip(context_preds, context_labels) if p == t)
        context_acc = context_correct / len(context_preds) * 100 if context_preds else 0
        results['context_accuracy'] = context_acc
        print(f"   Context-Level: {context_acc:.2f}%")
        
        # 4. Per-Category Performance
        print(f"\n📈 Per-Category Performance:")
        category_results = {}
        for category in self.categories.keys():
            # Find samples belonging to this category
            category_mask = [true_cat == category for true_cat in category_labels]
            if sum(category_mask) > 0:
                cat_preds = [p for p, m in zip(category_preds, category_mask) if m]
                cat_labels = [l for l, m in zip(category_labels, category_mask) if m]
                cat_correct = sum(1 for p, t in zip(cat_preds, cat_labels) if p == t)
                cat_acc = cat_correct / len(cat_preds) * 100
                category_results[category] = {
                    'accuracy': cat_acc,
                    'support': len(cat_preds)
                }
                print(f"   {category:15}: {cat_acc:5.1f}% ({len(cat_preds)} samples)")
        
        results['category_breakdown'] = category_results
        
        # 5. Performance by Class Frequency
        print(f"\n📊 Performance by Class Frequency:")
        freq_results = {}
        for freq_group, class_indices in self.frequency_groups.items():
            if class_indices:
                mask = [l in class_indices for l in labels]
                if sum(mask) > 0:
                    group_preds = predictions[mask]
                    group_labels = labels[mask]
                    group_correct = (group_preds == group_labels).sum()
                    group_acc = group_correct / len(group_preds) * 100
                    freq_results[freq_group] = {
                        'accuracy': group_acc,
                        'support': len(group_preds),
                        'n_classes': len(class_indices)
                    }
                    print(f"   {freq_group:12}: {group_acc:5.1f}% ({len(group_preds)} samples, {len(class_indices)} classes)")
        
        results['frequency_breakdown'] = freq_results
        
        # 6. National Flags Performance (special focus)
        national_mask = [cat == 'National' for cat in category_labels]
        if sum(national_mask) > 0:
            national_preds = [predictions[i] for i, m in enumerate(national_mask) if m]
            national_labels = [labels[i] for i, m in enumerate(national_mask) if m]
            national_correct = sum(1 for p, t in zip(national_preds, national_labels) if p == t)
            national_acc = national_correct / len(national_preds) * 100
            results['national_flags_accuracy'] = national_acc
            print(f"\n🏴 National Flags Accuracy: {national_acc:.2f}% ({len(national_preds)} samples)")
        
        # 7. Rare Classes Performance (<5 samples in training)
        rare_classes = self.frequency_groups.get('very_rare', [])
        if rare_classes:
            rare_mask = [l in rare_classes for l in labels]
            if sum(rare_mask) > 0:
                rare_preds = predictions[rare_mask]
                rare_labels = labels[rare_mask]
                rare_correct = (rare_preds == rare_labels).sum()
                rare_acc = rare_correct / len(rare_preds) * 100
                results['rare_classes_accuracy'] = rare_acc
                print(f"⚠️ Rare Classes (<5 samples): {rare_acc:.2f}% ({len(rare_preds)} test samples)")
        
        # 8. Confusion Matrix for Top Categories
        self._plot_category_confusion(category_preds, category_labels)
        
        # Save results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
        
        return results
    
    def _plot_category_confusion(self, preds, labels):
        """Plot confusion matrix for categories"""
        from sklearn.metrics import confusion_matrix
        
        # Get unique categories
        categories = sorted(list(set(labels + preds)))
        
        # Create confusion matrix
        cm = confusion_matrix(labels, preds, labels=categories)
        
        # Plot
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=categories, yticklabels=categories)
        plt.title('Category-Level Confusion Matrix')
        plt.xlabel('Predicted Category')
        plt.ylabel('True Category')
        plt.tight_layout()
        plt.savefig('category_confusion_matrix.png', dpi=150)
        plt.close()
        print(f"📊 Confusion matrix saved to: category_confusion_matrix.png")
    
    def generate_report(self, results):
        """Generate comprehensive evaluation report"""
        print("\n" + "="*60)
        print("📄 EVALUATION REPORT")
        print("="*60)
        
        report = f"""
# NI Flags Classification - Evaluation Report

## Overall Performance
- **Overall Accuracy**: {results.get('overall_accuracy', 0):.2f}%
- **Category-Level Accuracy**: {results.get('category_accuracy', 0):.2f}%
- **Context-Level Accuracy**: {results.get('context_accuracy', 0):.2f}%

## Hierarchical Performance
| Level | Description | Accuracy |
|-------|-------------|----------|
| Level 1 | Category (7 classes) | {results.get('category_accuracy', 0):.2f}% |
| Level 2 | Category-Context | {results.get('context_accuracy', 0):.2f}% |
| Level 3 | Full Classification | {results.get('overall_accuracy', 0):.2f}% |

## Category Breakdown
"""
        
        if 'category_breakdown' in results:
            for cat, metrics in results['category_breakdown'].items():
                report += f"- **{cat}**: {metrics['accuracy']:.1f}% ({metrics['support']} samples)\n"
        
        report += f"""

## Special Focus Areas
- **National Flags**: {results.get('national_flags_accuracy', 0):.2f}%
- **Rare Classes (<5 samples)**: {results.get('rare_classes_accuracy', 0):.2f}%

## Performance by Class Frequency
"""
        
        if 'frequency_breakdown' in results:
            for freq, metrics in results['frequency_breakdown'].items():
                report += f"- **{freq.title()}**: {metrics['accuracy']:.1f}% ({metrics['n_classes']} classes)\n"
        
        with open('evaluation_report.md', 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Report saved to: evaluation_report.md")
        
        return report


def evaluate_training_run(experiment_dir):
    """
    Evaluate a completed training run
    """
    print("\n" + "="*60)
    print("🔍 EVALUATING TRAINING RUN")
    print("="*60)
    print(f"Experiment: {experiment_dir}")
    
    evaluator = HierarchicalEvaluator(model_dir=experiment_dir)
    
    # Try to load predictions if available
    log_file = Path(experiment_dir) / "log.txt"
    if log_file.exists():
        results = evaluator.evaluate_from_log(log_file)
        if results:
            print(f"\n✅ Extracted from log:")
            print(f"   Overall Accuracy: {results.get('overall_accuracy', 0):.2f}%")
            print(f"   Macro F1: {results.get('macro_f1', 0):.2f}%")
    
    # Generate detailed report
    # Note: This would need actual predictions, which we'd need to extract from model
    print("\n💡 To get detailed metrics, run the model with --eval-only flag")
    print("   and save predictions for analysis")
    
    return results


def compare_experiments():
    """Compare multiple experiment results"""
    experiments_dir = Path("experiments")
    
    print("\n" + "="*60)
    print("📊 COMPARING EXPERIMENTS")
    print("="*60)
    
    results_table = []
    
    for exp_dir in experiments_dir.iterdir():
        if exp_dir.is_dir():
            log_file = exp_dir / "log.txt"
            if log_file.exists():
                evaluator = HierarchicalEvaluator()
                results = evaluator.evaluate_from_log(log_file)
                if results:
                    results_table.append({
                        'experiment': exp_dir.name,
                        'accuracy': results.get('overall_accuracy', 0),
                        'macro_f1': results.get('macro_f1', 0)
                    })
    
    if results_table:
        df = pd.DataFrame(results_table)
        df = df.sort_values('accuracy', ascending=False)
        print("\n📈 Results Summary:")
        print(df.to_string(index=False))
        
        # Save comparison
        df.to_csv('experiment_comparison.csv', index=False)
        print(f"\n💾 Comparison saved to: experiment_comparison.csv")
    else:
        print("No experiments found with results")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate NI Flags classification')
    parser.add_argument('--experiment', type=str, help='Experiment directory to evaluate')
    parser.add_argument('--compare', action='store_true', help='Compare all experiments')
    parser.add_argument('--predictions', type=str, help='Path to predictions file')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_experiments()
    elif args.experiment:
        evaluate_training_run(args.experiment)
    else:
        print("Usage:")
        print("  python evaluate_hierarchical.py --experiment experiments/your_exp")
        print("  python evaluate_hierarchical.py --compare")
