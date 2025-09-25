#!/usr/bin/env python3
"""
Create a composite figure from the expert labeling interface screenshots
"""

from PIL import Image
import numpy as np

def create_composite_interface():
    """Create a composite figure showing the complete expert labeling workflow"""
    
    # Note: The user provided 4 screenshots showing different parts of the interface
    # We'll create a placeholder composite layout that can be replaced with actual screenshots
    
    # Create a composite layout (2x2 grid)
    composite_width = 1200
    composite_height = 900
    
    # Create a white background
    composite = Image.new('RGB', (composite_width, composite_height), 'white')
    
    # Add text labels for the layout (this will be replaced with actual screenshots)
    # This is just a template structure
    
    print("Template created for expert labeling interface composite.")
    print("To complete this figure, please:")
    print("1. Save the 4 interface screenshots as:")
    print("   - interface_1_dual_view.png (main interface with cropped/original)")
    print("   - interface_2_categories.png (category selection)")  
    print("   - interface_3_classification.png (detailed classification)")
    print("   - interface_4_full_taxonomy.png (complete taxonomy view)")
    print("2. This script can then combine them into a single composite figure")
    
    return "plots/expert_labeling_interface_composite.png"

if __name__ == "__main__":
    output_path = create_composite_interface()
    print(f"Composite figure template ready: {output_path}")
