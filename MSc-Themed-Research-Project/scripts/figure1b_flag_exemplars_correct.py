#!/usr/bin/env python3
"""
Generate Figure 1b: Flag Type Exemplars (2x2 Layout) - Using Correct Test Images
Shows representative composite images from the expert labeller app that correspond to actual test set images.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from typing import Dict, List, Optional
import random

# Configuration
PUBLIC_IMAGES_DIR = Path("public/images")
TEST_INDEX_PATH = Path("MSc-Themed-Research-Project/data/index_test.csv")
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

def find_composite_image_for_test_image(test_image_path: str) -> Optional[str]:
    """Find the corresponding composite image for a test image."""
    filename = Path(test_image_path).name
    base_id = filename.split('_')[0]  # Extract hash before first underscore
    
    # Search all town directories for composite images with this base ID
    for town_dir in PUBLIC_IMAGES_DIR.iterdir():
        if town_dir.is_dir():
            # Try exact match first
            exact_match = town_dir / f"composite_{filename}"
            if exact_match.exists():
                return str(exact_match)
            
            # Try pattern match (handles box0 vs box1 differences)
            for composite_file in town_dir.glob(f"composite_{base_id}*.jpg"):
                return str(composite_file)
    
    return None

def select_best_examples_per_flag_type(df: pd.DataFrame) -> Dict[str, str]:
    """Select the best composite image example for each flag type from the test set."""
    examples = {}
    
    for flag_type in df['flag_type'].unique():
        type_images = df[df['flag_type'] == flag_type]
        
        # Prioritize higher resolution images (300 > 240 > 180 > 120 > 060)
        # and avoid very small images which might be bunting
        def image_quality_score(row):
            filename = Path(row['image_path']).name
            score = 0
            
            # Extract size from filename (e.g., "t1gXeuoPbFq0MyFVQAnnJg_240_box0.jpg" -> "240")
            parts = filename.split('_')
            if len(parts) >= 2:
                try:
                    size = int(parts[1])
                    if size == 300:
                        score += 100
                    elif size == 240:
                        score += 80
                    elif size == 180:
                        score += 60
                    elif size == 120:
                        score += 40
                    elif size == 60:
                        score += 10  # Low score for small images
                except ValueError:
                    score += 20  # Default score if size can't be parsed
            
            # For Orange Order, heavily penalize very small images (likely bunting)
            if "Orange Order" in flag_type and "060" in filename:
                score -= 50
            
            return score
        
        # Sort by quality score and select the best one
        best_image = type_images.iloc[type_images.apply(image_quality_score, axis=1).argmax()]
        
        # Find corresponding composite image
        composite_path = find_composite_image_for_test_image(best_image['image_path'])
        if composite_path:
            examples[flag_type] = composite_path
            print(f"✅ {flag_type}: {Path(best_image['image_path']).name} -> {Path(composite_path).name}")
        else:
            print(f"❌ {flag_type}: No composite found for {Path(best_image['image_path']).name}")
    
    return examples

def main():
    """Generate Figure 1b with flag type exemplars in 2x2 layout using actual test images."""
    print("🏁 Generating Figure 1b: Flag Type Exemplars (2x2 Layout) - Using Test Set Images")
    
    # Load test data
    df = pd.read_csv(TEST_INDEX_PATH)
    print(f"📊 Loaded {len(df)} test images")
    print(f"Flag types in test set: {list(df['flag_type'].unique())}")
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Select best examples for each flag type
    examples = select_best_examples_per_flag_type(df)
    
    # Define the layout with colors - using the exact flag types from test data
    selected_types = [
        ("Unionist – Union Jack", examples.get("Unionist – Union Jack"), '#1f77b4'),
        ("Nationalist – Tricolour", examples.get("Nationalist – Tricolour"), '#ff7f0e'),
        ("Cultural – Orange Order", examples.get("Cultural – Orange Order"), '#2ca02c'),
        ("Paramilitary (UDA/UVF/UFF/YCV)", examples.get("Paramilitary (UDA/UVF/UFF/YCV)"), '#d62728')
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
            
            # Clean up flag type label for display
            display_label = flag_type
            if flag_type == "Paramilitary (UDA/UVF/UFF/YCV)":
                display_label = "Paramilitary – UVF"
            
            ax.set_title(display_label, fontsize=16, fontweight='bold', color=color, pad=20)
            
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
            'Images correspond to actual test set examples used in the classification experiments.',
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
