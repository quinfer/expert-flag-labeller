#!/usr/bin/env python3
"""
Data preparation script specifically for your expert flag annotations
"""
import json
import os
import shutil
from pathlib import Path

def prepare_flag_dataset():
    """Prepare flag dataset from your expert annotations"""
    
    # Paths relative to the flag_classification_adaptation directory
    base_dir = Path(__file__).parent.parent.parent  # Back to MSc project root
    data_dir = base_dir / "data"
    annotations_file = data_dir / "annotations" / "expert_classifications.json"
    
    print(f"Looking for annotations at: {annotations_file}")
    
    if not annotations_file.exists():
        print("❌ Expert classifications file not found!")
        print(f"Please add your expert_classifications.json to: {annotations_file}")
        return False
    
    # Load expert annotations
    with open(annotations_file, 'r') as f:
        annotations = json.load(f)
    
    print(f"✅ Loaded {len(annotations)} expert classifications")
    
    # Create processed annotations in the format expected by Li et al.'s code
    processed_annotations = {}
    
    for image_name, classification in annotations.items():
        # Create hierarchical classname: category-context-specific_flag
        hierarchical_name = f"{classification['category']}-{classification['context']}-{classification['specific_flag']}"
        hierarchical_name = hierarchical_name.replace(' ', '_').replace('-', '_')
        
        processed_annotations[image_name] = {
            'category': classification['category'],
            'context': classification['context'], 
            'specific_flag': classification['specific_flag'],
            'hierarchical_classname': hierarchical_name,
            'confidence': classification.get('confidence', 4.0)
        }
    
    # Save processed annotations
    processed_file = data_dir / "processed" / "processed_annotations.json"
    with open(processed_file, 'w') as f:
        json.dump(processed_annotations, f, indent=2)
    
    print(f"✅ Saved processed annotations to: {processed_file}")
    print(f"Example hierarchical classnames:")
    for i, (_, anno) in enumerate(processed_annotations.items()):
        if i < 5:  # Show first 5 examples
            print(f"  - {anno['hierarchical_classname']}")
    
    return True

if __name__ == "__main__":
    print("🎯 PREPARING FLAG DATASET")
    print("=" * 40)
    success = prepare_flag_dataset()
    if success:
        print("✅ Data preparation complete!")
    else:
        print("❌ Data preparation failed")
