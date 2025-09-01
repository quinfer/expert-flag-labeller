#!/usr/bin/env python3
"""
Data Preparation Script for Flag Classification
Converts expert annotations to format required by Li et al.'s code

Usage:
    python prepare_flag_data.py --input /path/to/expert/annotations --output /path/to/dataset/root
"""

import os
import json
import shutil
import argparse
from collections import Counter, defaultdict
import pandas as pd


def load_expert_annotations(input_path):
    """
    Load expert annotations from CSV or JSON format
    
    Expected format:
    - CSV: columns ['image_name', 'category', 'context', 'specific_flag', 'confidence']
    - JSON: {image_name: {category, context, specific_flag, confidence}}
    """
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
        annotations = {}
        for _, row in df.iterrows():
            annotations[row['image_name']] = {
                'category': row['category'],
                'context': row['context'], 
                'specific_flag': row['specific_flag'],
                'confidence': row['confidence']
            }
    elif input_path.endswith('.json'):
        with open(input_path, 'r') as f:
            annotations = json.load(f)
    else:
        raise ValueError("Input must be CSV or JSON file")
    
    return annotations


def clean_and_validate_annotations(annotations, min_confidence=3.0):
    """
    Clean and validate expert annotations
    """
    print(f"Original annotations: {len(annotations)}")
    
    # Filter by confidence
    filtered = {k: v for k, v in annotations.items() 
                if v.get('confidence', 0) >= min_confidence}
    print(f"After confidence filtering (>={min_confidence}): {len(filtered)}")
    
    # Clean text fields
    for image_name, anno in filtered.items():
        anno['category'] = anno['category'].strip().replace(' ', '_')
        anno['context'] = anno['context'].strip().replace(' ', '_').replace('-', '_')
        anno['specific_flag'] = anno['specific_flag'].strip().replace(' ', '_')
    
    # Check for missing values
    complete_annotations = {}
    for image_name, anno in filtered.items():
        if all(anno.get(field) for field in ['category', 'context', 'specific_flag']):
            complete_annotations[image_name] = anno
        else:
            print(f"Warning: Incomplete annotation for {image_name}: {anno}")
    
    print(f"Complete annotations: {len(complete_annotations)}")
    return complete_annotations


def analyze_class_distribution(annotations):
    """
    Analyze the distribution of hierarchical classes
    """
    categories = Counter()
    contexts = Counter() 
    specific_flags = Counter()
    hierarchical_classes = Counter()
    
    for anno in annotations.values():
        categories[anno['category']] += 1
        contexts[anno['context']] += 1
        specific_flags[anno['specific_flag']] += 1
        
        hierarchical_class = f"{anno['category']}-{anno['context']}-{anno['specific_flag']}"
        hierarchical_classes[hierarchical_class] += 1
    
    print("\n=== CLASS DISTRIBUTION ANALYSIS ===")
    print(f"Categories: {dict(categories)}")
    print(f"Contexts: {dict(contexts)}")
    print(f"Most common specific flags: {dict(specific_flags.most_common(10))}")
    print(f"Total hierarchical classes: {len(hierarchical_classes)}")
    print(f"Most common hierarchical classes: {dict(hierarchical_classes.most_common(10))}")
    
    # Check for rare classes (might cause issues in few-shot learning)
    rare_classes = [k for k, v in hierarchical_classes.items() if v < 3]
    if rare_classes:
        print(f"Warning: {len(rare_classes)} classes have <3 examples: {rare_classes[:5]}...")
    
    return hierarchical_classes


def setup_dataset_structure(output_dir, annotations, image_source_dir):
    """
    Set up dataset directory structure required by Li et al.'s code
    """
    dataset_dir = os.path.join(output_dir, "ni_flags")
    images_dir = os.path.join(dataset_dir, "images")
    
    # Create directories
    os.makedirs(images_dir, exist_ok=True)
    
    # Copy images to dataset directory
    copied_images = 0
    missing_images = []
    
    for image_name in annotations.keys():
        source_path = os.path.join(image_source_dir, image_name)
        dest_path = os.path.join(images_dir, image_name)
        
        if os.path.exists(source_path):
            if not os.path.exists(dest_path):  # Avoid unnecessary copies
                shutil.copy2(source_path, dest_path)
            copied_images += 1
        else:
            missing_images.append(image_name)
    
    print(f"Copied {copied_images} images to {images_dir}")
    if missing_images:
        print(f"Warning: {len(missing_images)} images not found in source directory")
        print(f"Missing images: {missing_images[:5]}...")
    
    # Save annotations in required format
    annotations_file = os.path.join(dataset_dir, "annotations.json")
    with open(annotations_file, 'w') as f:
        json.dump(annotations, f, indent=2)
    
    print(f"Saved annotations to {annotations_file}")
    return dataset_dir


def create_classnames_file(dataset_dir, annotations):
    """
    Create classnames.txt file (useful for debugging and analysis)
    """
    hierarchical_classes = set()
    for anno in annotations.values():
        hierarchical_class = f"{anno['category']}-{anno['context']}-{anno['specific_flag']}"
        hierarchical_classes.add(hierarchical_class)
    
    classnames_file = os.path.join(dataset_dir, "classnames.txt") 
    with open(classnames_file, 'w') as f:
        for classname in sorted(hierarchical_classes):
            f.write(f"{classname}\n")
    
    print(f"Created {classnames_file} with {len(hierarchical_classes)} classes")


def main():
    parser = argparse.ArgumentParser(description="Prepare flag dataset for hierarchical classification")
    parser.add_argument("--input", required=True, help="Path to expert annotations (CSV or JSON)")
    parser.add_argument("--images", required=True, help="Path to directory containing flag images") 
    parser.add_argument("--output", required=True, help="Output directory for prepared dataset")
    parser.add_argument("--min-confidence", type=float, default=3.0, help="Minimum confidence score")
    
    args = parser.parse_args()
    
    # Load and process annotations
    print("Loading expert annotations...")
    annotations = load_expert_annotations(args.input)
    
    print("Cleaning and validating annotations...")
    clean_annotations = clean_and_validate_annotations(annotations, args.min_confidence)
    
    print("Analyzing class distribution...")
    hierarchical_classes = analyze_class_distribution(clean_annotations)
    
    print("Setting up dataset structure...")
    dataset_dir = setup_dataset_structure(args.output, clean_annotations, args.images)
    
    print("Creating classnames file...")
    create_classnames_file(dataset_dir, clean_annotations)
    
    print("\n=== DATASET PREPARATION COMPLETE ===")
    print(f"Dataset location: {dataset_dir}")
    print(f"Total images: {len(clean_annotations)}")
    print(f"Hierarchical classes: {len(hierarchical_classes)}")
    print(f"Dataset ready for training!")
    
    # Print example training command
    print(f"\nExample training command:")
    print(f"python train.py \\")
    print(f"  --trainer CoCoOpFlags \\")
    print(f"  --dataset-config-file configs/datasets/ni_flags.yaml \\")
    print(f"  --config-file configs/trainers/CoCoOpFlags/rn50_ep50.yaml \\")
    print(f"  --root {args.output} \\")
    print(f"  --output-dir ./output/ni_flags_experiment")


if __name__ == "__main__":
    main()
