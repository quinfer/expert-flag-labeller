#!/usr/bin/env python3
"""
Figure 1b: Flag Type Exemplars Using Real Composite Images

Shows representative examples from each flag type category using actual composite 
images from the expert labeller app, providing authentic visual context.
"""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from typing import Dict, List

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

def load_test_data(index_path: Path) -> pd.DataFrame:
    """Load test set data with flag types."""
    return pd.read_csv(index_path)

def get_composite_image_path(original_path: str, static_images_data: List[Dict]) -> str:
    """Find composite image path for a given original image path."""
    # Extract filename from original path
    filename = Path(original_path).name
    
    # Search in static images data
    for entry in static_images_data:
        if entry['filename'] == filename and entry.get('has_composite', False):
            # Convert to absolute path
            composite_path = Path('/Users/quinference/Documents/expert-flag-labeler/public') / entry['composite_image'].lstrip('/')
            if composite_path.exists():
                return str(composite_path)
    
    # Fallback 1: Direct construction from test image path
    # Test images are in MSc-Themed-Research-Project/data/ni_flags_super_consolidated/images/
    # Need to find corresponding composite in public/images/
    test_path = Path(original_path)
    filename_base = test_path.stem  # Remove .jpg extension
    
    # Search all composite images for matching filename
    public_images_dir = Path('/Users/quinference/Documents/expert-flag-labeler/public/images')
    for town_dir in public_images_dir.iterdir():
        if town_dir.is_dir():
            composite_pattern = town_dir / f"composite_{filename_base}.jpg"
            if composite_pattern.exists():
                return str(composite_pattern)
    
    # Fallback 2: Search by partial filename match
    for town_dir in public_images_dir.iterdir():
        if town_dir.is_dir():
            for composite_file in town_dir.glob(f"composite_*{filename_base[:20]}*.jpg"):
                return str(composite_file)
    
    return None

def load_composite_image(image_path: str) -> np.ndarray:
    """Load composite image at original resolution - no resizing to preserve quality."""
    try:
        img = Image.open(image_path).convert('RGB')
        return np.array(img)
    except Exception as e:
        print(f"⚠️  Error loading {image_path}: {e}")
        # Create small placeholder
        placeholder = np.ones((100, 150, 3), dtype=np.uint8) * 200
        return placeholder

def select_representative_images(df: pd.DataFrame, static_images_data: List[Dict], 
                                n_per_type: int = 2) -> Dict[str, List[str]]:
    """Select representative composite images for each flag type, filtering for quality."""
    representatives = {}
    
    # Prefer certain image sizes for better quality (larger images tend to be clearer)
    preferred_sizes = ['300', '240', '180', '120', '060']
    
    for flag_type in df['flag_type'].unique():
        type_df = df[df['flag_type'] == flag_type]
        
        # Get composite image paths with quality scoring
        candidate_paths = []
        for _, row in type_df.iterrows():
            composite_path = get_composite_image_path(row['image_path'], static_images_data)
            if composite_path:
                # Score based on image size (larger = better quality)
                score = 0
                for i, size in enumerate(preferred_sizes):
                    if f"_{size}_" in composite_path:
                        score = len(preferred_sizes) - i
                        break
                
                # Avoid bunting (often has specific patterns in filenames or paths)
                if flag_type == "Cultural – Orange Order":
                    # For Orange Order, prefer images that are likely to be actual flags
                    # Avoid images that might be bunting (often smaller or in specific locations)
                    if "bunting" in composite_path.lower() or "_060_" in composite_path:
                        score -= 5  # Penalize likely bunting
                
                candidate_paths.append((composite_path, score))
        
        # Sort by score (higher = better) and select best ones
        candidate_paths.sort(key=lambda x: x[1], reverse=True)
        
        if candidate_paths:
            # Take top candidates up to n_per_type
            selected = [path for path, score in candidate_paths[:n_per_type]]
            representatives[flag_type] = selected
        else:
            representatives[flag_type] = []
    
    return representatives

def create_flag_exemplars_figure(df: pd.DataFrame, static_images_data: List[Dict],
                                output_png: Path, output_pdf: Path):
    """Create flag exemplars figure using real composite images."""
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Select representative images
    representatives = select_representative_images(df, static_images_data, n_per_type=2)
    
    # Select one representative from each major category for cleaner 2x2 layout
    selected_types = [
        ("Unionist – Union Jack", representatives.get("Unionist – Union Jack", []), '#1f77b4'),
        ("Nationalist – Tricolour", representatives.get("Nationalist – Tricolour", []), '#ff7f0e'),
        ("Cultural – Orange Order", representatives.get("Cultural – Orange Order", []), '#2ca02c'),
        ("Paramilitary – UVF", representatives.get("Paramilitary (UDA/UVF/UFF/YCV)", []), '#d62728')
    ]
    
    # Create 2x2 figure for cleaner layout
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Flag Type Exemplars: Economic Categories and Visual Diversity', 
                fontsize=18, fontweight='bold', y=0.95)
    
    for col_idx, (category, flag_types) in enumerate(categories.items()):
        color = CATEGORY_COLORS[category]
        
        # Category header
        axes[0, col_idx].text(0.5, 1.1, category, ha='center', va='bottom',
                             fontsize=14, fontweight='bold', color=color,
                             transform=axes[0, col_idx].transAxes,
                             bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.2))
        
        # Show up to 2 flag types per category
        for row_idx in range(2):
            ax = axes[row_idx, col_idx]
            
            if row_idx < len(flag_types):
                flag_type = flag_types[row_idx]
                images = representatives[flag_type]
                
                if images:
                    # Load and show first representative image at original resolution
                    img = load_composite_image(images[0])
                    ax.imshow(img, interpolation='none')  # Disable matplotlib interpolation
                    
                    # Add colored border
                    for spine in ax.spines.values():
                        spine.set_edgecolor(color)
                        spine.set_linewidth(3)
                    
                    # Add flag type label
                    flag_label = flag_type.split(' – ')[1] if ' – ' in flag_type else flag_type
                    ax.set_title(flag_label, fontsize=11, fontweight='bold', color=color, pad=10)
                    
                else:
                    # No images available
                    ax.text(0.5, 0.5, 'No composite\nimages available', 
                           ha='center', va='center', fontsize=10,
                           transform=ax.transAxes)
                    ax.set_title(flag_types[row_idx].split(' – ')[1], fontsize=11, color=color)
            else:
                # Empty cell
                ax.axis('off')
            
            ax.set_xticks([])
            ax.set_yticks([])
    
    # Add description
    fig.text(0.5, 0.02, 
            'Real composite images from Northern Ireland communities showing flag diversity across economic categories.\n'
            'Images include contextual information (buildings, poles, surroundings) as seen by the classification model.',
            ha='center', va='bottom', fontsize=11, style='italic')
    
    plt.tight_layout(rect=[0, 0.08, 1, 0.92])
    
    # Save figure
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300, bbox_inches='tight')
    fig.savefig(output_pdf, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✅ Flag exemplars figure saved to {output_png}")
    
    # Print summary with actual paths for verification
    print("\n📊 Representative Images Selected:")
    for category, flag_types in categories.items():
        print(f"  {category}:")
        for flag_type in flag_types:
            images = representatives.get(flag_type, [])
            print(f"    {flag_type}: {len(images)} images")
            for i, img_path in enumerate(images):
                filename = Path(img_path).name
                print(f"      {i+1}. {filename}")

def main():
    parser = argparse.ArgumentParser(description='Generate Flag Exemplars Figure')
    parser.add_argument('--index-csv', type=Path,
                       default=Path('MSc-Themed-Research-Project/data/index_test.csv'),
                       help='Test set index CSV file')
    parser.add_argument('--static-images', type=Path,
                       default=Path('src/data/static-images.json'),
                       help='Static images JSON file')
    parser.add_argument('--output-dir', type=Path,
                       default=Path('MSc-Themed-Research-Project/write-up/plots'),
                       help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Load data
    df = load_test_data(args.index_csv)
    with open(args.static_images, 'r', encoding='utf-8') as f:
        static_images_data = json.load(f)
    
    # Output paths
    output_png = args.output_dir / 'figure1b_flag_exemplars.png'
    output_pdf = args.output_dir / 'figure1b_flag_exemplars.pdf'
    
    # Create the figure
    create_flag_exemplars_figure(df, static_images_data, output_png, output_pdf)
    
    print(f"✅ Figure 1b (Flag Exemplars) created successfully!")

if __name__ == "__main__":
    main()
