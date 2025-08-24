#!/usr/bin/env python3
"""
Create visualizations for flag class distribution analysis
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import Counter

def create_distribution_plots():
    """Create comprehensive visualizations of class distribution"""
    
    # Load the detailed statistics
    script_dir = Path(__file__).resolve().parent
    stats_path = script_dir / 'detailed_class_statistics.json'
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create a comprehensive figure with multiple subplots
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Primary Category Distribution (Pie Chart)
    plt.subplot(4, 2, 1)
    cat_data = stats['category_distribution']['counts']
    plt.pie(cat_data.values(), labels=cat_data.keys(), autopct='%1.1f%%', startangle=90)
    plt.title('Primary Category Distribution\n(8 Categories)', fontsize=14, fontweight='bold')
    
    # 2. Primary Category Distribution (Bar Chart)
    plt.subplot(4, 2, 2)
    categories = list(cat_data.keys())
    counts = list(cat_data.values())
    bars = plt.bar(categories, counts, color=sns.color_palette("husl", len(categories)))
    plt.title('Primary Category Distribution\n(Absolute Counts)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Number of Images')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # 3. Top 20 Hierarchical Classes
    plt.subplot(4, 2, 3)
    hier_data = stats['hierarchical_class_distribution']['counts']
    top_20 = dict(sorted(hier_data.items(), key=lambda x: x[1], reverse=True)[:20])
    
    plt.barh(range(len(top_20)), list(top_20.values()), 
             color=sns.color_palette("viridis", len(top_20)))
    plt.yticks(range(len(top_20)), [label.replace('-', '-\n') if len(label) > 30 else label 
                                   for label in top_20.keys()], fontsize=8)
    plt.xlabel('Number of Images')
    plt.title('Top 20 Most Frequent Hierarchical Classes', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # 4. Class Frequency Distribution (Histogram)
    plt.subplot(4, 2, 4)
    frequencies = list(hier_data.values())
    plt.hist(frequencies, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.xlabel('Images per Class')
    plt.ylabel('Number of Classes')
    plt.title('Class Frequency Distribution\n(Histogram of Class Sizes)', fontsize=14, fontweight='bold')
    plt.axvline(np.mean(frequencies), color='red', linestyle='--', 
                label=f'Mean: {np.mean(frequencies):.1f}')
    plt.axvline(np.median(frequencies), color='orange', linestyle='--', 
                label=f'Median: {np.median(frequencies):.1f}')
    plt.legend()
    
    # 5. Context Distribution
    plt.subplot(4, 2, 5)
    context_data = stats['context_distribution']['counts']
    contexts = list(context_data.keys())
    context_counts = list(context_data.values())
    
    plt.bar(range(len(contexts)), context_counts, 
            color=sns.color_palette("Set2", len(contexts)))
    plt.xticks(range(len(contexts)), contexts, rotation=45, ha='right')
    plt.ylabel('Number of Images')
    plt.title('Context Distribution\n(11 Different Contexts)', fontsize=14, fontweight='bold')
    
    # 6. Confidence Distribution
    plt.subplot(4, 2, 6)
    conf_data = stats['confidence_analysis']['distribution']
    confidences = list(conf_data.keys())
    conf_counts = list(conf_data.values())
    
    plt.bar(confidences, conf_counts, color=['lightcoral', 'gold', 'lightgreen'])
    plt.xlabel('Confidence Level')
    plt.ylabel('Number of Images')
    plt.title('Annotation Confidence Distribution', fontsize=14, fontweight='bold')
    
    # Add percentage labels
    total_images = sum(conf_counts)
    for conf, count in zip(confidences, conf_counts):
        percentage = (count / total_images) * 100
        plt.text(conf, count + 20, f'{count}\\n({percentage:.1f}%)', 
                ha='center', va='bottom', fontweight='bold')
    
    # 7. Class Imbalance Analysis (Log Scale)
    plt.subplot(4, 2, 7)
    sorted_classes = sorted(hier_data.items(), key=lambda x: x[1], reverse=True)
    class_indices = range(1, len(sorted_classes) + 1)
    class_counts = [count for _, count in sorted_classes]
    
    plt.semilogy(class_indices, class_counts, 'b-', linewidth=2, marker='o', markersize=3)
    plt.xlabel('Class Rank')
    plt.ylabel('Number of Images (Log Scale)')
    plt.title('Class Imbalance Pattern\n(Ranked by Frequency)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add annotations for extreme values
    plt.annotate(f'Most frequent: {class_counts[0]}', 
                xy=(1, class_counts[0]), xytext=(10, class_counts[0]*2),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red')
    plt.annotate(f'Least frequent: {class_counts[-1]}', 
                xy=(len(class_counts), class_counts[-1]), 
                xytext=(len(class_counts)-10, class_counts[-1]*10),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red')
    
    # 8. Cumulative Distribution
    plt.subplot(4, 2, 8)
    cumulative_counts = np.cumsum(class_counts)
    cumulative_percentage = (cumulative_counts / cumulative_counts[-1]) * 100
    
    plt.plot(class_indices, cumulative_percentage, 'g-', linewidth=3)
    plt.xlabel('Number of Classes (Ranked)')
    plt.ylabel('Cumulative Percentage of Images')
    plt.title('Cumulative Distribution of Images\n(Pareto Analysis)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add 80-20 rule line
    plt.axhline(80, color='red', linestyle='--', alpha=0.7, label='80% of images')
    plt.axvline(len(class_counts) * 0.2, color='red', linestyle='--', alpha=0.7, 
                label='20% of classes')
    plt.legend()
    
    plt.tight_layout()
    out_png = script_dir / 'flag_class_distribution_analysis.png'
    out_pdf = script_dir / 'flag_class_distribution_analysis.pdf'
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    
    print("📊 Distribution plots saved as:")
    print(f"   - {out_png}")
    print(f"   - {out_pdf}")
    
    return fig

if __name__ == "__main__":
    create_distribution_plots()
    plt.show()