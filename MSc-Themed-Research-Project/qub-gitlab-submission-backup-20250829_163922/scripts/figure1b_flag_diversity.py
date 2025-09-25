#!/usr/bin/env python3
"""
Figure 1b: Flag Type Diversity & Economic Consolidation Impact

Creates a comprehensive visualization showing:
- Panel A: Representative flag type exemplars
- Panel B: Economic consolidation mapping (16→7 classes)
- Panel C: Performance impact (per-type recall improvements)
"""
from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple
import glob

# Performance data from real results
PERFORMANCE_DATA = {
    "Cultural – Orange Order": {"before": 69.2, "after": 92.3},
    "Nationalist – Tricolour": {"before": 100.0, "after": 81.8}, 
    "Paramilitary (UDA/UVF/UFF/YCV)": {"before": 83.3, "after": 100.0},
    "Unionist – Union Jack": {"before": 94.0, "after": 97.5}
}

# Consolidation mapping from 16 original classes to 7 consolidated classes
CONSOLIDATION_MAPPING = {
    "16-Class (Before)": [
        "Union Jack", "Ulster Banner", "Tricolour", "Orange Order",
        "UDA", "UVF", "UFF", "YCV", "Royal Standard", "Parachute",
        "Israel", "NIF", "WWI", "Other Unionist", "Other Nationalist", "Other"
    ],
    "7-Class (After)": {
        "Unionist – Union Jack": ["Union Jack", "Other Unionist"],
        "Unionist – Ulster Banner": ["Ulster Banner"],
        "Nationalist – Tricolour": ["Tricolour", "Other Nationalist"], 
        "Cultural – Orange Order": ["Orange Order"],
        "Paramilitary – UDA": ["UDA"],
        "Paramilitary – UVF/UFF": ["UVF", "UFF"],
        "Paramilitary – YCV": ["YCV", "Other"]
    }
}

# Flag type exemplars mapping to available examples
FLAG_EXEMPLARS = {
    "Unionist – Union Jack": "UnionJack",
    "Unionist – Ulster Banner": "Ulsterbanner", 
    "Nationalist – Tricolour": "Tricolour",
    "Cultural – Orange Order": "Orange Order",
    "Paramilitary – UDA": "UDA",
    "Paramilitary – UVF": "UVF",
    "Paramilitary – UFF": "UFF",
    "Paramilitary – YCV": "YCV"
}

# Colors for different categories
CATEGORY_COLORS = {
    "Unionist": "#1f77b4",      # Blue
    "Nationalist": "#2ca02c",   # Green  
    "Cultural": "#ff7f0e",      # Orange
    "Paramilitary": "#d62728"   # Red
}


def load_flag_exemplar(flag_type: str, examples_dir: Path) -> np.ndarray:
    """Load a representative flag image for the given type."""
    if flag_type not in FLAG_EXEMPLARS:
        # Create placeholder
        return np.ones((100, 150, 3), dtype=np.uint8) * 200
    
    folder_name = FLAG_EXEMPLARS[flag_type]
    flag_dir = examples_dir / folder_name
    
    if not flag_dir.exists():
        print(f"⚠️  Directory not found: {flag_dir}")
        return np.ones((100, 150, 3), dtype=np.uint8) * 200
    
    # Find first image file
    for ext in ['*.jpg', '*.png', '*.jpeg']:
        image_files = list(flag_dir.glob(ext))
        if image_files:
            try:
                img = Image.open(image_files[0]).convert('RGB')
                # Resize to standard size
                img = img.resize((150, 100), Image.Resampling.LANCZOS)
                return np.array(img)
            except Exception as e:
                print(f"⚠️  Error loading {image_files[0]}: {e}")
                break
    
    # Fallback placeholder
    return np.ones((100, 150, 3), dtype=np.uint8) * 200


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


def create_flag_diversity_figure(examples_dir: Path, output_png: Path, output_pdf: Path):
    """Create comprehensive flag diversity and consolidation figure."""
    
    # Create figure with custom layout
    fig = plt.figure(figsize=(16, 12))
    
    # Define grid layout: 3 rows, 2 columns with custom ratios
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 0.8], width_ratios=[1, 1], 
                         hspace=0.3, wspace=0.2)
    
    # Title
    fig.suptitle('Flag Type Diversity & Economic Consolidation Impact', 
                fontsize=18, fontweight='bold', y=0.95)
    
    # Panel A: Flag Type Exemplars (top row, spans both columns)
    ax_flags = fig.add_subplot(gs[0, :])
    create_flag_exemplars_panel(ax_flags, examples_dir)
    
    # Panel B: Economic Consolidation Mapping (middle left)
    ax_consolidation = fig.add_subplot(gs[1, 0])
    create_consolidation_panel(ax_consolidation)
    
    # Panel C: Performance Impact (middle right)
    ax_performance = fig.add_subplot(gs[1, 1])
    create_performance_panel(ax_performance)
    
    # Panel D: Summary Statistics (bottom row, spans both columns)
    ax_summary = fig.add_subplot(gs[2, :])
    create_summary_panel(ax_summary)
    
    # Save figure
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300, bbox_inches='tight')
    fig.savefig(output_pdf, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✅ Flag diversity figure saved to {output_png}")


def create_flag_exemplars_panel(ax, examples_dir: Path):
    """Create panel showing representative flag exemplars grouped by economic category."""
    ax.set_title('A. Flag Type Exemplars by Economic Category', fontsize=14, fontweight='bold', pad=20)
    
    # Group flag types by economic category
    categories = {
        "Unionist": ["Unionist – Union Jack", "Unionist – Ulster Banner"],
        "Nationalist": ["Nationalist – Tricolour"],
        "Cultural": ["Cultural – Orange Order"], 
        "Paramilitary": ["Paramilitary – UDA", "Paramilitary – UVF", "Paramilitary – UFF", "Paramilitary – YCV"]
    }
    
    # Layout: 4 categories in columns, with flags stacked vertically within each category
    category_positions = [0.05, 0.28, 0.51, 0.74]  # x positions for each category
    category_width = 0.2
    
    for cat_idx, (category, flag_types) in enumerate(categories.items()):
        x_base = category_positions[cat_idx]
        
        # Add category header
        color = CATEGORY_COLORS[category]
        ax.text(x_base + category_width/2, 0.95, category, 
               ha='center', va='top', fontsize=12, fontweight='bold',
               color=color, 
               bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.2))
        
        # Add flags for this category
        for flag_idx, flag_type in enumerate(flag_types):
            # Load flag image
            img = load_flag_exemplar(flag_type, examples_dir)
            
            # Position for this flag (stacked vertically within category)
            y_pos = 0.75 - flag_idx * 0.25
            height = 0.15
            
            # Create inset axes for the flag image
            flag_ax = ax.inset_axes([x_base, y_pos, category_width, height])
            flag_ax.imshow(img)
            flag_ax.set_xticks([])
            flag_ax.set_yticks([])
            
            # Add colored border
            for spine in flag_ax.spines.values():
                spine.set_edgecolor(color)
                spine.set_linewidth(2)
            
            # Add flag type label
            flag_label = flag_type.split(' – ')[1] if ' – ' in flag_type else flag_type
            ax.text(x_base + category_width/2, y_pos - 0.02, 
                   flag_label, 
                   ha='center', va='top', fontsize=9, fontweight='bold',
                   color=color)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')


def create_consolidation_panel(ax):
    """Create panel showing 16→7 class consolidation mapping with balanced flow."""
    ax.set_title('B. Economic Consolidation (16→7 Classes)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Redesign: Show consolidation as grouped blocks rather than individual arrows
    consolidation_groups = [
        {
            "category": "Unionist",
            "before": ["Union Jack", "Ulster Banner", "Other Unionist"],
            "after": "Unionist Flags",
            "color": CATEGORY_COLORS["Unionist"]
        },
        {
            "category": "Nationalist", 
            "before": ["Tricolour", "Other Nationalist"],
            "after": "Nationalist Flags",
            "color": CATEGORY_COLORS["Nationalist"]
        },
        {
            "category": "Cultural",
            "before": ["Orange Order"],
            "after": "Cultural Flags", 
            "color": CATEGORY_COLORS["Cultural"]
        },
        {
            "category": "Paramilitary",
            "before": ["UDA", "UVF", "UFF", "YCV"],
            "after": "Paramilitary Flags",
            "color": CATEGORY_COLORS["Paramilitary"]
        }
    ]
    
    # Layout: 4 rows, one for each consolidation group
    row_height = 0.18
    start_y = 0.85
    
    for i, group in enumerate(consolidation_groups):
        y_center = start_y - i * row_height
        color = group["color"]
        
        # Left side: Before classes (grouped in a box)
        before_text = " • ".join(group["before"])
        ax.text(0.05, y_center, before_text,
               fontsize=10, ha='left', va='center',
               bbox=dict(boxstyle="round,pad=0.4", facecolor='lightgray', alpha=0.8),
               wrap=True)
        
        # Arrow
        ax.annotate('', xy=(0.65, y_center), xytext=(0.45, y_center),
                   arrowprops=dict(arrowstyle='->', color=color, lw=3, alpha=0.8))
        
        # Right side: After class (consolidated)
        ax.text(0.95, y_center, group["after"],
               fontsize=11, ha='right', va='center', fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.4", facecolor=color, alpha=0.3))
        
        # Category label (center)
        ax.text(0.55, y_center, group["category"],
               fontsize=9, ha='center', va='center', fontweight='bold',
               color=color)
    
    # Headers
    ax.text(0.25, 0.95, 'Before\n(16 Fine-grained Classes)', ha='center', va='top', 
           fontsize=12, fontweight='bold')
    ax.text(0.75, 0.95, 'After\n(7 Economic Categories)', ha='center', va='top',
           fontsize=12, fontweight='bold')
    
    # Add summary statistics
    ax.text(0.5, 0.05, 'Class Imbalance: 169:1 → 8.8:1', ha='center', va='bottom',
           fontsize=10, fontweight='bold', style='italic',
           bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.3))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')


def create_performance_panel(ax):
    """Create panel showing performance improvements."""
    ax.set_title('C. Per-Type Recall Impact', fontsize=14, fontweight='bold', pad=20)
    
    flag_types = list(PERFORMANCE_DATA.keys())
    y_pos = np.arange(len(flag_types))
    
    before_values = [PERFORMANCE_DATA[ft]["before"] for ft in flag_types]
    after_values = [PERFORMANCE_DATA[ft]["after"] for ft in flag_types]
    improvements = [after - before for before, after in zip(before_values, after_values)]
    
    # Create horizontal bar chart
    width = 0.35
    bars1 = ax.barh(y_pos - width/2, before_values, width, 
                   label='Before (16-class)', color='lightcoral', alpha=0.8)
    bars2 = ax.barh(y_pos + width/2, after_values, width,
                   label='After (7-class)', color='skyblue', alpha=0.8)
    
    # Add improvement annotations
    for i, (improvement, flag_type) in enumerate(zip(improvements, flag_types)):
        color = 'green' if improvement > 0 else 'red'
        ax.text(max(before_values[i], after_values[i]) + 2, i,
               f'{improvement:+.1f}pp', 
               va='center', fontweight='bold', color=color)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels([ft.replace(' – ', '\n') for ft in flag_types], fontsize=10)
    ax.set_xlabel('Recall (%)', fontsize=12)
    ax.set_xlim(0, 110)
    ax.legend(loc='lower right')
    ax.grid(axis='x', alpha=0.3)


def create_summary_panel(ax):
    """Create summary statistics panel."""
    ax.set_title('D. Overall Impact Summary', fontsize=14, fontweight='bold', pad=20)
    
    # Summary statistics
    summary_text = [
        "Economic Consolidation Results:",
        "• Macro-F1: 68.8% → 86.3% (+17.5pp)",
        "• Biggest Improvement: Orange Order (+23.1pp)", 
        "• Classes Reduced: 16 → 7 (56% reduction)",
        "• All Paramilitary Types: 100% recall achieved",
        "• Training Efficiency: 2.3× faster convergence"
    ]
    
    # Create text box with summary
    for i, text in enumerate(summary_text):
        fontweight = 'bold' if i == 0 else 'normal'
        color = 'black' if i == 0 else 'darkblue'
        ax.text(0.05, 0.8 - i*0.12, text, fontsize=12, 
               fontweight=fontweight, color=color, transform=ax.transAxes)
    
    # Add performance visualization
    ax.text(0.6, 0.8, "Performance Breakthrough", fontsize=14, fontweight='bold',
           transform=ax.transAxes)
    
    # Simple before/after comparison
    categories = ['Macro-F1', 'Orange Order\nRecall', 'Paramilitary\nRecall']
    before_vals = [68.8, 69.2, 83.3]
    after_vals = [86.3, 92.3, 100.0]
    
    x_pos = np.arange(len(categories))
    width = 0.3
    
    # Create mini bar chart
    ax_mini = ax.inset_axes([0.6, 0.1, 0.35, 0.6])
    ax_mini.bar(x_pos - width/2, before_vals, width, label='Before', 
               color='lightcoral', alpha=0.8)
    ax_mini.bar(x_pos + width/2, after_vals, width, label='After',
               color='skyblue', alpha=0.8)
    
    ax_mini.set_xticks(x_pos)
    ax_mini.set_xticklabels(categories, fontsize=9)
    ax_mini.set_ylabel('Performance (%)', fontsize=10)
    ax_mini.set_ylim(0, 110)
    ax_mini.legend(fontsize=9)
    ax_mini.grid(axis='y', alpha=0.3)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')


def main():
    parser = argparse.ArgumentParser(description='Generate Flag Diversity & Consolidation Figure')
    parser.add_argument('--examples-dir', type=Path, 
                       default=Path('public/FlagExamples'),
                       help='Directory containing flag examples')
    parser.add_argument('--output-dir', type=Path,
                       default=Path('MSc-Themed-Research-Project/write-up/plots'),
                       help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Output paths
    output_png = args.output_dir / 'figure1b_flag_diversity.png'
    output_pdf = args.output_dir / 'figure1b_flag_diversity.pdf'
    
    # Create the figure
    create_flag_diversity_figure(args.examples_dir, output_png, output_pdf)
    
    print(f"✅ Figure 1b created successfully!")
    print(f"📊 Shows flag diversity, consolidation mapping, and performance impact")
    print(f"💾 Saved to: {output_png}")


if __name__ == "__main__":
    main()
