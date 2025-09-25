#!/usr/bin/env python3
"""
Figure 1c: Economic Consolidation Impact

Shows the consolidation flow from 16→7 classes and the resulting performance impact,
with clean layout and no overlapping elements.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List

# Performance data from real results
PERFORMANCE_DATA = {
    "Cultural – Orange Order": {"before": 69.2, "after": 92.3},
    "Nationalist – Tricolour": {"before": 100.0, "after": 81.8}, 
    "Paramilitary (UDA/UVF/UFF/YCV)": {"before": 83.3, "after": 100.0},
    "Unionist – Union Jack": {"before": 94.0, "after": 97.5}
}

# Colors for different categories
CATEGORY_COLORS = {
    "Unionist": "#1f77b4",      # Blue
    "Nationalist": "#2ca02c",   # Green  
    "Cultural": "#ff7f0e",      # Orange
    "Paramilitary": "#d62728"   # Red
}

def get_category_color(flag_type: str) -> str:
    """Get color for flag type based on category."""
    if "Unionist" in flag_type:
        return CATEGORY_COLORS["Unionist"]
    elif "Nationalist" in flag_type:
        return CATEGORY_COLORS["Nationalist"]
    elif "Cultural" in flag_type:
        return CATEGORY_COLORS["Cultural"]
    elif "Paramilitary" in flag_type:
        return CATEGORY_COLORS["Paramilitary"]
    else:
        return "#7f7f7f"  # Gray default

def create_consolidation_flow_panel(ax):
    """Create clean consolidation flow panel."""
    ax.set_title('Economic Consolidation Flow (16→7 Classes)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Consolidation groups with better spacing
    consolidation_groups = [
        {
            "category": "Unionist",
            "before": ["Union Jack", "Ulster Banner", "Other Unionist"],
            "after": "Unionist Flags",
            "color": CATEGORY_COLORS["Unionist"],
            "count_before": 3,
            "count_after": 2
        },
        {
            "category": "Nationalist", 
            "before": ["Tricolour", "Other Nationalist"],
            "after": "Nationalist Flags",
            "color": CATEGORY_COLORS["Nationalist"],
            "count_before": 2,
            "count_after": 1
        },
        {
            "category": "Cultural",
            "before": ["Orange Order"],
            "after": "Cultural Flags", 
            "color": CATEGORY_COLORS["Cultural"],
            "count_before": 1,
            "count_after": 1
        },
        {
            "category": "Paramilitary",
            "before": ["UDA", "UVF", "UFF", "YCV", "Other"],
            "after": "Paramilitary Flags",
            "color": CATEGORY_COLORS["Paramilitary"],
            "count_before": 5,
            "count_after": 3
        }
    ]
    
    # Layout with more space
    row_height = 0.2
    start_y = 0.85
    
    for i, group in enumerate(consolidation_groups):
        y_center = start_y - i * row_height
        color = group["color"]
        
        # Left side: Before classes (in a clean box)
        before_text = f"{group['count_before']} classes:\n" + " • ".join(group["before"][:3])
        if len(group["before"]) > 3:
            before_text += f"\n+ {len(group['before'])-3} more"
        
        ax.text(0.02, y_center, before_text,
               fontsize=9, ha='left', va='center',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
        
        # Clean arrow with category label
        ax.annotate('', xy=(0.65, y_center), xytext=(0.35, y_center),
                   arrowprops=dict(arrowstyle='->', color=color, lw=4, alpha=0.9))
        
        # Category label on arrow
        ax.text(0.5, y_center + 0.03, group["category"],
               fontsize=10, ha='center', va='bottom', fontweight='bold',
               color=color,
               bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.9))
        
        # Right side: After class (consolidated)
        after_text = f"{group['count_after']} consolidated:\n{group['after']}"
        ax.text(0.98, y_center, after_text,
               fontsize=10, ha='right', va='center', fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.5", facecolor=color, alpha=0.3))
    
    # Clear headers
    ax.text(0.18, 0.95, 'Before: 16 Fine-grained Classes', ha='center', va='top', 
           fontsize=12, fontweight='bold')
    ax.text(0.82, 0.95, 'After: 7 Economic Categories', ha='center', va='top',
           fontsize=12, fontweight='bold')
    
    # Summary at bottom
    ax.text(0.5, 0.05, 'Result: Class Imbalance Reduced from 169:1 to 8.8:1', 
           ha='center', va='bottom',
           fontsize=12, fontweight='bold', style='italic',
           bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.4))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

def create_performance_panel(ax):
    """Create performance comparison panel."""
    ax.set_title('Performance Impact by Flag Type', fontsize=14, fontweight='bold', pad=20)
    
    flag_types = list(PERFORMANCE_DATA.keys())
    # Shorten labels for better fit
    short_labels = [ft.replace(' – ', '\n').replace('(UDA/UVF/UFF/YCV)', '(All Types)') for ft in flag_types]
    
    y_pos = np.arange(len(flag_types))
    
    before_values = [PERFORMANCE_DATA[ft]["before"] for ft in flag_types]
    after_values = [PERFORMANCE_DATA[ft]["after"] for ft in flag_types]
    improvements = [after - before for before, after in zip(before_values, after_values)]
    
    # Create horizontal bar chart with better spacing
    width = 0.35
    bars1 = ax.barh(y_pos - width/2, before_values, width, 
                   label='Before (16-class)', color='lightcoral', alpha=0.8)
    bars2 = ax.barh(y_pos + width/2, after_values, width,
                   label='After (7-class)', color='skyblue', alpha=0.8)
    
    # Add improvement annotations
    for i, improvement in enumerate(improvements):
        color = 'green' if improvement > 0 else 'red'
        symbol = '+' if improvement > 0 else ''
        ax.text(max(before_values[i], after_values[i]) + 2, i,
               f'{symbol}{improvement:.1f}pp', 
               va='center', fontweight='bold', color=color, fontsize=11)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(short_labels, fontsize=10)
    ax.set_xlabel('Recall (%)', fontsize=12)
    ax.set_xlim(0, 115)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(axis='x', alpha=0.3)

def create_summary_panel(ax):
    """Create overall summary panel."""
    ax.set_title('Overall Impact Summary', fontsize=14, fontweight='bold', pad=20)
    
    # Key statistics in a clean layout
    stats = [
        ("Macro-F1 Improvement", "68.8% → 86.3%", "+17.5pp", "green"),
        ("Class Imbalance Reduction", "169:1 → 8.8:1", "19× improvement", "blue"),
        ("Paramilitary Recall", "83.3% → 100%", "Perfect classification", "red"),
        ("Orange Order Improvement", "69.2% → 92.3%", "+23.1pp (largest gain)", "orange")
    ]
    
    # Create a clean table-like layout
    for i, (metric, values, improvement, color) in enumerate(stats):
        y_pos = 0.8 - i * 0.18
        
        # Metric name
        ax.text(0.05, y_pos, metric, fontsize=12, fontweight='bold', va='center')
        
        # Values
        ax.text(0.45, y_pos, values, fontsize=11, va='center', ha='center',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.5))
        
        # Improvement
        ax.text(0.75, y_pos, improvement, fontsize=11, fontweight='bold', 
               va='center', ha='center', color=color,
               bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.2))
    
    # Add overall conclusion
    ax.text(0.5, 0.1, 'Economic consolidation transforms extreme imbalance into manageable classification task',
           ha='center', va='center', fontsize=12, fontweight='bold', style='italic',
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.3))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

def create_consolidation_impact_figure(output_png: Path, output_pdf: Path):
    """Create economic consolidation impact figure."""
    
    # Create figure with three panels
    fig, axes = plt.subplots(3, 1, figsize=(14, 16))
    fig.suptitle('Economic Consolidation Impact Analysis', 
                fontsize=18, fontweight='bold', y=0.95)
    
    # Panel A: Consolidation Flow
    create_consolidation_flow_panel(axes[0])
    
    # Panel B: Performance Impact
    create_performance_panel(axes[1])
    
    # Panel C: Summary
    create_summary_panel(axes[2])
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    
    # Save figure
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300, bbox_inches='tight')
    fig.savefig(output_pdf, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✅ Consolidation impact figure saved to {output_png}")

def main():
    parser = argparse.ArgumentParser(description='Generate Consolidation Impact Figure')
    parser.add_argument('--output-dir', type=Path,
                       default=Path('MSc-Themed-Research-Project/write-up/plots'),
                       help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Output paths
    output_png = args.output_dir / 'figure1c_consolidation_impact.png'
    output_pdf = args.output_dir / 'figure1c_consolidation_impact.pdf'
    
    # Create the figure
    create_consolidation_impact_figure(output_png, output_pdf)
    
    print(f"✅ Figure 1c (Consolidation Impact) created successfully!")

if __name__ == "__main__":
    main()
