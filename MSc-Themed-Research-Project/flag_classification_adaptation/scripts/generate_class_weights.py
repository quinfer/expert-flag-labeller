#!/usr/bin/env python3
"""
Generate class weights for the new expanded dataset (5,490 samples, 90 classes)
"""

import json
import torch
import numpy as np
from pathlib import Path

def generate_class_weights():
    """Generate class weights from the new dataset statistics"""
    
    # Load the dataset info
    dataset_info_path = Path("../data/ni_flags_v2/dataset_info.json")
    
    if not dataset_info_path.exists():
        print(f"❌ {dataset_info_path} not found!")
        print("Please run prepare_dataset_v2.py first")
        return None
    
    with open(dataset_info_path, 'r') as f:
        info = json.load(f)
    
    print("\n" + "="*60)
    print("📊 GENERATING CLASS WEIGHTS FOR NEW DATASET")
    print("="*60)
    print(f"Total samples: {info['total_samples']}")
    print(f"Number of classes: {info['num_classes']}")
    
    # Get class distribution
    class_distribution = info['class_distribution']
    
    # Load class names to maintain order
    classnames_path = Path("../data/ni_flags_v2/classnames.txt")
    with open(classnames_path, 'r') as f:
        classnames = [line.strip() for line in f.readlines()]
    
    # Create ordered class counts
    class_counts = {}
    for idx, classname in enumerate(classnames):
        if classname in class_distribution:
            class_counts[idx] = class_distribution[classname]
        else:
            class_counts[idx] = 1  # Default for missing classes
    
    print(f"\n📈 Class distribution:")
    print(f"   Max count: {max(class_counts.values())} samples")
    print(f"   Min count: {min(class_counts.values())} samples")
    print(f"   Imbalance ratio: {max(class_counts.values()) / min(class_counts.values()):.1f}:1")
    
    # Calculate weights using inverse frequency with square root smoothing
    num_classes = len(classnames)
    total_samples = sum(class_counts.values())
    
    weights_dict = {}
    for idx in range(num_classes):
        count = class_counts.get(idx, 1)
        # Inverse frequency with square root smoothing (same as original)
        weight = np.sqrt(total_samples / (num_classes * count))
        weights_dict[idx] = weight
    
    # Convert to tensor and normalize
    weights = torch.zeros(num_classes)
    for idx, weight in weights_dict.items():
        weights[idx] = weight
    
    # Normalize to mean of 1.0
    weights = weights / weights.mean()
    
    print(f"\n📊 Weight statistics:")
    print(f"   Min weight: {weights.min():.3f}")
    print(f"   Max weight: {weights.max():.3f}")
    print(f"   Mean weight: {weights.mean():.3f}")
    print(f"   Std weight: {weights.std():.3f}")
    
    # Show weights for different frequency groups
    print(f"\n📈 Sample weights by frequency:")
    
    # Most common classes
    sorted_counts = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    print("\n   Top 5 classes (most samples):")
    for idx, count in sorted_counts[:5]:
        print(f"      {classnames[idx][:40]:40} : {count:4d} samples, weight={weights[idx]:.3f}")
    
    print("\n   Bottom 5 classes (least samples):")
    for idx, count in sorted_counts[-5:]:
        print(f"      {classnames[idx][:40]:40} : {count:4d} samples, weight={weights[idx]:.3f}")
    
    # Generate Python code for the weights
    print("\n" + "="*60)
    print("📝 PYTHON CODE FOR COCOOP.PY")
    print("="*60)
    print("\nReplace the _create_class_weights method with this:\n")
    
    code = f'''    def _create_class_weights(self, num_classes):
        """Create inverse frequency weights for class imbalance - UPDATED FOR 5.5K DATASET"""
        # Updated class distribution from NIFlags V2 dataset (90 classes, 5490 samples)
        # Generated from classifications_0708.csv with confidence >= 3.0
        
        class_counts = {{'''
    
    # Add the actual counts
    for idx in range(min(20, num_classes)):  # Show first 20 for brevity
        count = class_counts.get(idx, 1)
        code += f"\n            {idx}: {count},"
    
    code += f"\n            # ... {num_classes - 20} more classes"
    code += f"\n            # Full distribution in dataset_info.json"
    code += "\n        }\n"
    
    code += f'''        
        # Calculate inverse frequency weights with square root smoothing
        weights = torch.ones(num_classes)
        total_samples = {total_samples}
        
        # Use actual counts for classes we have
        for idx in range(num_classes):
            if idx in class_counts:
                count = class_counts[idx]
            else:
                count = 1  # Default for unknown classes
            
            # Inverse frequency with square root smoothing
            weights[idx] = (total_samples / (num_classes * count)) ** 0.5
        
        # Normalize
        weights = weights / weights.mean()
        
        print(f"✅ Created class weights for {{num_classes}} classes")
        print(f"   Weight range: {{weights.min():.2f}} - {{weights.max():.2f}}")
        
        return weights'''
    
    print(code)
    
    # Save the weights to a file
    weights_dict = {
        'num_classes': num_classes,
        'total_samples': total_samples,
        'class_counts': class_counts,
        'weights': weights.tolist(),
        'imbalance_ratio': max(class_counts.values()) / min(class_counts.values())
    }
    
    output_path = Path("class_weights_v2.json")
    with open(output_path, 'w') as f:
        json.dump(weights_dict, f, indent=2)
    
    print(f"\n💾 Weights saved to: {output_path}")
    
    # Also save as PyTorch tensor
    torch.save(weights, "class_weights_v2.pt")
    print(f"💾 PyTorch tensor saved to: class_weights_v2.pt")
    
    return weights, class_counts

if __name__ == "__main__":
    weights, counts = generate_class_weights()
    
    if weights is not None:
        print("\n" + "="*60)
        print("✅ CLASS WEIGHTS GENERATED SUCCESSFULLY")
        print("="*60)
        print("\n🎯 Next steps:")
        print("1. Copy the generated code above into trainers/cocoop.py")
        print("2. Replace the _create_class_weights method")
        print("3. Run training with updated weights")
        
        print("\n📊 Summary:")
        print(f"   90 classes with proper weights")
        print(f"   Weights range from {weights.min():.3f} to {weights.max():.3f}")
        print(f"   Heavily upweighting rare classes")
