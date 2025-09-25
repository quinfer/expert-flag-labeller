#!/usr/bin/env python3
"""
Generate Figure 1b: Flag Type Exemplars (2x2 Layout)
Shows representative composite images from the expert labeller app for each major flag type.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from typing import Dict, List, Optional
import random

# Configuration
EXPERT_LABELLER_IMAGES_DIR = Path("public/images")
STATIC_IMAGES_PATH = Path("src/data/static-images.json")
TEST_INDEX_PATH = Path("MSc-Themed-Research-Project/data/index_test.csv")
OUTPUT_PATH = Path("MSc-Themed-Research-Project/write-up/plots/figure1b_flag_exemplars.png")

def load_static_images_data() -> List[Dict]:
    """Load the static images data from the expert labeller app."""
    with open(STATIC_IMAGES_PATH, 'r') as f:
        return json.load(f)

def get_composite_image_path(original_path: str, static_images_data: List[Dict]) -> Optional[str]:
    """Find the corresponding composite image path for an original test image."""
    # Extract just the filename from the original path
    original_filename = Path(original_path).name
    
    # Search for matching entry in static images data
    for entry in static_images_data:
        if entry['path'].endswith(original_filename):
            composite_filename = entry.get('composite_image')
            if composite_filename:
                # Extract town from original path and construct full composite path
                town = Path(original_path).parent.name
                town_dir = EXPERT_LABELLER_IMAGES_DIR / town
                
                # Find the composite file (handling different naming patterns)
                filename_base = composite_filename.replace('.jpg', '').replace('composite_', '')
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
                                n_per_type: int = 1) -> Dict[str, List[str]]:
    """Select representative composite images for each flag type, filtering for quality."""
    representatives = {}
    
    for flag_type in df['flag_type'].unique():
        type_images = df[df['flag_type'] == flag_type]['image_path'].tolist()
        composite_paths = []
        
        for img_path in type_images:
            composite_path = get_composite_image_path(img_path, static_images_data)
            if composite_path and Path(composite_path).exists():
                composite_paths.append(composite_path)
        
        if composite_paths:
            # Prioritize higher resolution images and avoid bunting-like images
            def image_quality_score(path):
                score = 0
                filename = Path(path).name
                
                # Prefer higher resolution (300px > 240px > 60px)
                if '_300_' in filename:
                    score += 100
                elif '_240_' in filename:
                    score += 50
                elif '_60_' in filename:
                    score -= 50  # Penalize small images (often bunting)
                
                # For Orange Order, heavily penalize likely bunting images
                if "Orange Order" in flag_type and '_60_' in filename:
                    score -= 200
                
                return score
            
            # Sort by quality score and take the best ones
            composite_paths.sort(key=image_quality_score, reverse=True)
            representatives[flag_type] = composite_paths[:n_per_type]
    
    return representatives

def main():
    """Generate Figure 1b with flag type exemplars in 2x2 layout."""
    print("🏁 Generating Figure 1b: Flag Type Exemplars (2x2 Layout)")
    
    # Load data
    df = pd.read_csv(TEST_INDEX_PATH)
    static_images_data = load_static_images_data()
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Select representative images
    representatives = select_representative_images(df, static_images_data, n_per_type=1)
    
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
                fontsize=20, fontweight='bold', y=0.95)
    
    # Define positions for 2x2 layout
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    
    for idx, ((flag_type, images, color), (row, col)) in enumerate(zip(selected_types, positions)):
        ax = axes[row, col]
        ax.set_xticks([])
        ax.set_yticks([])
        
        if images:
            # Load and show first representative image at original resolution
            img = load_composite_image(images[0])
            ax.imshow(img, interpolation='none')  # Disable matplotlib interpolation
            
            # Add colored border
            for spine in ax.spines.values():
                spine.set_edgecolor(color)
                spine.set_linewidth(4)
            
            # Add flag type label with specific paramilitary type
            if "Paramilitary" in flag_type:
                label = "Paramilitary – UVF"
            else:
                label = flag_type
            
            ax.set_title(label, fontsize=16, fontweight='bold', color=color, pad=20)
            
        else:
            # No image available
            ax.text(0.5, 0.5, f'No {flag_type}\nimage available', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, style='italic')
            ax.set_facecolor('#f0f0f0')
            for spine in ax.spines.values():
                spine.set_edgecolor(color)
                spine.set_linewidth(2)
                spine.set_linestyle('--')
    
    # Add description
    fig.text(0.5, 0.02, 
            'Real composite images from Northern Ireland communities showing flag diversity across economic categories.\n'
            'Images include contextual information (buildings, poles, surroundings) as seen by the classification model.',
            ha='center', va='bottom', fontsize=12, style='italic')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.12)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save figure
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✅ Flag exemplars figure (2x2) saved to {OUTPUT_PATH}")
    
    # Print summary
    print(f"\n📊 Representative Images Selected (2x2 Layout):")
    for flag_type, images, color in selected_types:
        if images:
            print(f"  {flag_type}: {Path(images[0]).name}")
        else:
            print(f"  {flag_type}: No images available")
    
    print("✅ Figure 1b (Flag Exemplars 2x2) created successfully!")

if __name__ == "__main__":
    main()
