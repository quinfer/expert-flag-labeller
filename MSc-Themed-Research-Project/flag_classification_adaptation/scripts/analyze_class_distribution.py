#!/usr/bin/env python3
"""
Statistical Analysis of Flag Class Distribution
Provides comprehensive statistical analysis of the 70 flag classes
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns

def load_annotations(file_path):
    """Load and parse annotations JSON file"""
    with open(file_path, 'r') as f:
        annotations = json.load(f)
    return annotations

def analyze_class_distribution(annotations):
    """Comprehensive statistical analysis of class distribution"""
    
    # Extract hierarchical components
    categories = []
    contexts = []
    specific_flags = []
    hierarchical_classes = []
    confidences = []
    
    for image_id, annotation in annotations.items():
        categories.append(annotation['category'])
        contexts.append(annotation['context'])
        specific_flags.append(annotation['specific_flag'])
        hierarchical_classes.append(annotation['hierarchical_classname'])
        confidences.append(annotation['confidence'])
    
    # Create comprehensive statistics
    stats_report = {
        'dataset_overview': {
            'total_images': len(annotations),
            'unique_hierarchical_classes': len(set(hierarchical_classes)),
            'unique_categories': len(set(categories)),
            'unique_contexts': len(set(contexts)),
            'unique_specific_flags': len(set(specific_flags))
        }
    }
    
    # Category-level analysis
    category_counts = Counter(categories)
    stats_report['category_distribution'] = {
        'counts': dict(category_counts),
        'percentages': {k: (v/len(categories)*100) for k, v in category_counts.items()},
        'statistics': {
            'mean': np.mean(list(category_counts.values())),
            'median': np.median(list(category_counts.values())),
            'std': np.std(list(category_counts.values())),
            'min': min(category_counts.values()),
            'max': max(category_counts.values()),
            'gini_coefficient': calculate_gini(list(category_counts.values()))
        }
    }
    
    # Context-level analysis
    context_counts = Counter(contexts)
    stats_report['context_distribution'] = {
        'counts': dict(context_counts),
        'percentages': {k: (v/len(contexts)*100) for k, v in context_counts.items()},
        'statistics': {
            'mean': np.mean(list(context_counts.values())),
            'median': np.median(list(context_counts.values())),
            'std': np.std(list(context_counts.values())),
            'min': min(context_counts.values()),
            'max': max(context_counts.values()),
            'gini_coefficient': calculate_gini(list(context_counts.values()))
        }
    }
    
    # Hierarchical class analysis (all 70 classes)
    hierarchical_counts = Counter(hierarchical_classes)
    stats_report['hierarchical_class_distribution'] = {
        'counts': dict(hierarchical_counts),
        'percentages': {k: (v/len(hierarchical_classes)*100) for k, v in hierarchical_counts.items()},
        'statistics': {
            'mean': np.mean(list(hierarchical_counts.values())),
            'median': np.median(list(hierarchical_counts.values())),
            'std': np.std(list(hierarchical_counts.values())),
            'min': min(hierarchical_counts.values()),
            'max': max(hierarchical_counts.values()),
            'gini_coefficient': calculate_gini(list(hierarchical_counts.values())),
            'class_imbalance_ratio': max(hierarchical_counts.values()) / min(hierarchical_counts.values())
        }
    }
    
    # Confidence analysis
    stats_report['confidence_analysis'] = {
        'mean': np.mean(confidences),
        'median': np.median(confidences),
        'std': np.std(confidences),
        'min': min(confidences),
        'max': max(confidences),
        'distribution': dict(Counter(confidences))
    }
    
    # Cross-category analysis
    category_context_matrix = defaultdict(lambda: defaultdict(int))
    for cat, ctx in zip(categories, contexts):
        category_context_matrix[cat][ctx] += 1
    
    stats_report['cross_category_analysis'] = dict(category_context_matrix)
    
    # Class balance analysis
    class_balance_analysis = analyze_class_balance(hierarchical_counts)
    stats_report['class_balance_analysis'] = class_balance_analysis
    
    return stats_report

def calculate_gini(values):
    """Calculate Gini coefficient for inequality measurement"""
    values = sorted(values)
    n = len(values)
    cumsum = np.cumsum(values)
    return (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(values, 1))) / (n * sum(values))

def analyze_class_balance(class_counts):
    """Analyze class balance and imbalance patterns"""
    values = list(class_counts.values())
    
    # Quartile analysis
    q1, q2, q3 = np.percentile(values, [25, 50, 75])
    
    # Classification of classes by frequency
    rare_classes = [k for k, v in class_counts.items() if v <= q1]
    common_classes = [k for k, v in class_counts.items() if v >= q3]
    medium_classes = [k for k, v in class_counts.items() if q1 < v < q3]
    
    return {
        'quartiles': {'Q1': q1, 'Q2': q2, 'Q3': q3},
        'class_categories': {
            'rare_classes': {'count': len(rare_classes), 'classes': rare_classes},
            'medium_classes': {'count': len(medium_classes), 'classes': medium_classes},
            'common_classes': {'count': len(common_classes), 'classes': common_classes}
        },
        'imbalance_metrics': {
            'coefficient_of_variation': np.std(values) / np.mean(values),
            'imbalance_ratio': max(values) / min(values),
            'effective_number_of_classes': len([v for v in values if v >= np.mean(values) * 0.1])
        }
    }

def generate_summary_report(stats_report):
    """Generate human-readable summary report"""
    
    print("=" * 80)
    print("FLAG CLASS DISTRIBUTION STATISTICAL ANALYSIS")
    print("=" * 80)
    
    # Dataset Overview
    overview = stats_report['dataset_overview']
    print(f"\n📊 DATASET OVERVIEW:")
    print(f"   Total Images: {overview['total_images']:,}")
    print(f"   Hierarchical Classes: {overview['unique_hierarchical_classes']}")
    print(f"   Primary Categories: {overview['unique_categories']}")
    print(f"   Contexts: {overview['unique_contexts']}")
    print(f"   Specific Flags: {overview['unique_specific_flags']}")
    
    # Category Distribution
    cat_dist = stats_report['category_distribution']
    print(f"\n🏷️  PRIMARY CATEGORY DISTRIBUTION:")
    for category, count in sorted(cat_dist['counts'].items(), key=lambda x: x[1], reverse=True):
        percentage = cat_dist['percentages'][category]
        print(f"   {category:<15}: {count:>4} images ({percentage:>5.1f}%)")
    
    cat_stats = cat_dist['statistics']
    print(f"\n   Category Statistics:")
    print(f"   Mean per category: {cat_stats['mean']:.1f}")
    print(f"   Std deviation: {cat_stats['std']:.1f}")
    print(f"   Gini coefficient: {cat_stats['gini_coefficient']:.3f}")
    
    # Hierarchical Class Balance
    hier_dist = stats_report['hierarchical_class_distribution']
    hier_stats = hier_dist['statistics']
    print(f"\n🎯 HIERARCHICAL CLASS BALANCE (70 classes):")
    print(f"   Mean per class: {hier_stats['mean']:.1f}")
    print(f"   Median per class: {hier_stats['median']:.1f}")
    print(f"   Std deviation: {hier_stats['std']:.1f}")
    print(f"   Min class size: {hier_stats['min']}")
    print(f"   Max class size: {hier_stats['max']}")
    print(f"   Imbalance ratio: {hier_stats['class_imbalance_ratio']:.1f}:1")
    print(f"   Gini coefficient: {hier_stats['gini_coefficient']:.3f}")
    
    # Class Balance Analysis
    balance = stats_report['class_balance_analysis']
    print(f"\n⚖️  CLASS BALANCE ANALYSIS:")
    print(f"   Rare classes (≤Q1): {balance['class_categories']['rare_classes']['count']}")
    print(f"   Medium classes: {balance['class_categories']['medium_classes']['count']}")
    print(f"   Common classes (≥Q3): {balance['class_categories']['common_classes']['count']}")
    print(f"   Coefficient of Variation: {balance['imbalance_metrics']['coefficient_of_variation']:.3f}")
    
    # Top and Bottom Classes
    sorted_classes = sorted(hier_dist['counts'].items(), key=lambda x: x[1], reverse=True)
    print(f"\n🔝 TOP 10 MOST FREQUENT CLASSES:")
    for i, (class_name, count) in enumerate(sorted_classes[:10], 1):
        percentage = hier_dist['percentages'][class_name]
        print(f"   {i:2d}. {class_name:<40}: {count:>3} ({percentage:>4.1f}%)")
    
    print(f"\n🔻 BOTTOM 10 LEAST FREQUENT CLASSES:")
    for i, (class_name, count) in enumerate(sorted_classes[-10:], 1):
        percentage = hier_dist['percentages'][class_name]
        print(f"   {i:2d}. {class_name:<40}: {count:>3} ({percentage:>4.1f}%)")
    
    # Confidence Analysis
    conf_analysis = stats_report['confidence_analysis']
    print(f"\n🎯 ANNOTATION CONFIDENCE ANALYSIS:")
    print(f"   Mean confidence: {conf_analysis['mean']:.2f}")
    print(f"   Confidence distribution: {conf_analysis['distribution']}")
    
    return stats_report

def main():
    """Main analysis function"""
    try:
        # Resolve paths robustly relative to this file location
        adaptation_dir = Path(__file__).resolve().parent
        project_dir = adaptation_dir.parent
        annotations_path = project_dir / 'data' / 'ni_flags' / 'annotations.json'

        # Load annotations
        annotations = load_annotations(str(annotations_path))
        
        # Perform statistical analysis
        stats_report = analyze_class_distribution(annotations)
        
        # Generate summary report
        generate_summary_report(stats_report)
        
        # Save detailed statistics next to this script
        out_path = adaptation_dir / 'detailed_class_statistics.json'
        with open(out_path, 'w') as f:
            json.dump(stats_report, f, indent=2)
        
        print(f"\n💾 Detailed statistics saved to '{out_path}'")
        
        return stats_report
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return None

if __name__ == "__main__":
    main()