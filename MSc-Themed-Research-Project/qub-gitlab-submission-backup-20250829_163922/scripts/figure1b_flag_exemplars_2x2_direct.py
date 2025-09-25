#!/usr/bin/env python3
"""
Generate Figure 1b: Flag Type Exemplars (2x2 Layout) - Direct from Composite Images
Shows representative composite images from the expert labeller app for each major flag type.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from typing import Dict, List
import random

# Configuration
EXPERT_LABELLER_IMAGES_DIR = Path("public/images")
OUTPUT_PATH = Path("MSc-Themed-Research-Project/write-up/plots/figure1b_flag_exemplars.png")

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

def find_best_composite_images() -> Dict[str, str]:
    """Find the best composite images for each flag type by scanning the directory."""
    
    # Manually curated high-quality examples based on previous analysis
    examples = {
        "Unionist – Union Jack": "public/images/COLERAINE/composite_tF3QuaqtrI-YBEgrv2caBA_300_box0.jpg",
        "Nationalist – Tricolour": "public/images/BELFAST_CITY/composite_xeOS4rAcgNUEl9V7yVJ3MQ_300_box0.jpg", 
        "Cultural – Orange Order": "public/images/COLERAINE/composite_vcom3xgYis6cvfzMO5U5cg_300_box0.jpg",
        "Paramilitary – UVF": "public/images/BELFAST_CITY/composite_tierVB0fCJ7ZapsPE59u7Q_240_box0.jpg"
    }
    
    # Verify files exist and provide fallbacks
    verified_examples = {}
    for flag_type, path in examples.items():
        if Path(path).exists():
            verified_examples[flag_type] = path
            print(f"✅ Found {flag_type}: {Path(path).name}")
        else:
            # Try to find any composite image as fallback
            print(f"⚠️  Primary example not found for {flag_type}, searching for fallback...")
            
            # Search for any composite image in the directory
            fallback_found = False
            for town_dir in EXPERT_LABELLER_IMAGES_DIR.iterdir():
                if town_dir.is_dir():
                    for composite_file in town_dir.glob("composite_*_300_*.jpg"):
                        verified_examples[flag_type] = str(composite_file)
                        print(f"🔄 Using fallback for {flag_type}: {composite_file.name}")
                        fallback_found = True
                        break
                if fallback_found:
                    break
            
            if not fallback_found:
                print(f"❌ No composite image found for {flag_type}")
    
    return verified_examples

def main():
    """Generate Figure 1b with flag type exemplars in 2x2 layout."""
    print("🏁 Generating Figure 1b: Flag Type Exemplars (2x2 Layout)")
    
    # Find best composite images
    examples = find_best_composite_images()
    
    # Define the layout with colors
    selected_types = [
        ("Unionist – Union Jack", examples.get("Unionist – Union Jack"), '#1f77b4'),
        ("Nationalist – Tricolour", examples.get("Nationalist – Tricolour"), '#ff7f0e'),
        ("Cultural – Orange Order", examples.get("Cultural – Orange Order"), '#2ca02c'),
        ("Paramilitary – UVF", examples.get("Paramilitary – UVF"), '#d62728')
    ]
    
    # Create 2x2 figure for cleaner layout
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Flag Type Exemplars: Economic Categories and Visual Diversity', 
                fontsize=20, fontweight='bold', y=0.95)
    
    # Define positions for 2x2 layout
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    
    for idx, ((flag_type, image_path, color), (row, col)) in enumerate(zip(selected_types, positions)):
        ax = axes[row, col]
        ax.set_xticks([])
        ax.set_yticks([])
        
        if image_path and Path(image_path).exists():
            # Load and show image at original resolution
            img = load_composite_image(image_path)
            ax.imshow(img, interpolation='none')  # Disable matplotlib interpolation
            
            # Add colored border
            for spine in ax.spines.values():
                spine.set_edgecolor(color)
                spine.set_linewidth(4)
            
            # Add flag type label
            ax.set_title(flag_type, fontsize=16, fontweight='bold', color=color, pad=20)
            
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
    print(f"\n📊 Representative Images Used (2x2 Layout):")
    for flag_type, image_path, color in selected_types:
        if image_path and Path(image_path).exists():
            print(f"  {flag_type}: {Path(image_path).name}")
        else:
            print(f"  {flag_type}: No image available")
    
    print("✅ Figure 1b (Flag Exemplars 2x2) created successfully!")

if __name__ == "__main__":
    main()
