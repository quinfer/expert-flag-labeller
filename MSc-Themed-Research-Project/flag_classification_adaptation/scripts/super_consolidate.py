#!/usr/bin/env python3
"""
Super-Consolidation Script: Reduce 16 classes to 8 balanced classes
This addresses the severe class imbalance causing low macro-F1 scores
"""

import os
import json
import shutil
from pathlib import Path
from collections import defaultdict, Counter
import random

def create_super_consolidation_mapping():
    """Create 8-class super-consolidation mapping"""
    
    mapping = {
        # Merge ALL Unionist classes - they're the dominant category
        'Unionist_All': [
            'Unionist_High_Impact',
            'Unionist_Medium_Impact', 
            'Unionist_Low_Impact',
            'Regional_Scottish'  # Scottish flags are unionist-aligned
        ],
        
        # Keep Nationalist separate - important political distinction
        'Nationalist_All': [
            'Nationalist_Display',
            'International_Republican'  # Irish republican flags
        ],
        
        # Combine all paramilitary - security concern category
        'Paramilitary_All': [
            'Paramilitary_Loyalist',
            'Paramilitary_Other'
        ],
        
        # Cultural and community displays
        'Cultural_Community': [
            'Fraternal_Cultural',
            'Seasonal_Decorative'
        ],
        
        # Sports and local community
        'Sport_Community': [
            'Sport_GAA',
            'Sport_Other'
        ],
        
        # International (non-political)
        'International_Other': [
            'International_EU',
            'International_Loyalist',
            'International_Other'
        ],
        
        # Historical and commemorative
        'Historical_Memorial': [
            'Commemorative_Historical'
        ],
        
        # Catch-all for very rare classes
        'Other_Rare': [
            # This will catch any remaining classes
        ]
    }
    
    return mapping

def apply_super_consolidation():
    """Apply super-consolidation to create 8-class dataset"""
    
    print("🚀 Starting Super-Consolidation: 16 → 8 Classes")
    print("="*60)
    
    # Paths
    source_dir = Path("../data/ni_flags_consolidated")
    target_dir = Path("../data/ni_flags_super_consolidated")
    
    # Create target directory
    target_dir.mkdir(exist_ok=True)
    (target_dir / "images").mkdir(exist_ok=True)
    
    # Load existing annotations
    annotations_file = source_dir / "annotations.json"
    if not annotations_file.exists():
        print(f"❌ Source annotations not found: {annotations_file}")
        return
    
    with open(annotations_file, 'r') as f:
        source_annotations = json.load(f)
    
    # Get consolidation mapping
    mapping = create_super_consolidation_mapping()
    
    # Create reverse mapping (original class → new class)
    class_mapping = {}
    for new_class, original_classes in mapping.items():
        for orig_class in original_classes:
            # Handle wildcards
            if orig_class.endswith('*'):
                prefix = orig_class[:-1]
                # Find all classes that start with this prefix
                for img_path, annotation in source_annotations.items():
                    if annotation['hierarchical_classname'].startswith(prefix):
                        class_mapping[annotation['hierarchical_classname']] = new_class
            else:
                class_mapping[orig_class] = new_class
    
    # Apply consolidation
    new_annotations = {}
    class_counts = Counter()
    
    print("🔄 Applying super-consolidation...")
    
    for img_path, annotation in source_annotations.items():
        original_class = annotation['hierarchical_classname']
        
        # Map to new class
        if original_class in class_mapping:
            new_class = class_mapping[original_class]
        else:
            # Unmapped classes go to "Other_Rare"
            new_class = 'Other_Rare'
            print(f"⚠️ Unmapped class: {original_class} → Other_Rare")
        
        # Create new annotation
        new_annotation = annotation.copy()
        new_annotation['hierarchical_classname'] = new_class
        new_annotation['original_16class'] = original_class
        new_annotation['super_consolidation_applied'] = True
        
        new_annotations[img_path] = new_annotation
        class_counts[new_class] += 1
        
        # Copy image file
        source_img = source_dir / "images" / img_path
        target_img = target_dir / "images" / img_path
        if source_img.exists() and not target_img.exists():
            shutil.copy2(source_img, target_img)
    
    # Save new annotations
    with open(target_dir / "annotations.json", 'w') as f:
        json.dump(new_annotations, f, indent=2)
    
    # Create classnames.txt
    sorted_classes = sorted(class_counts.keys())
    with open(target_dir / "classnames.txt", 'w') as f:
        for class_name in sorted_classes:
            f.write(f"{class_name}\n")
    
    # Create consolidation stats
    total_samples = sum(class_counts.values())
    consolidation_stats = {
        'total_samples': total_samples,
        'num_classes': len(sorted_classes),
        'consolidation_type': 'super_consolidation_8class',
        'source_classes': 16,
        'target_classes': len(sorted_classes),
        'class_distribution': dict(class_counts),
        'mapping_applied': dict(class_mapping)
    }
    
    with open(target_dir / "consolidation_stats.json", 'w') as f:
        json.dump(consolidation_stats, f, indent=2)
    
    # Print results
    print(f"\n✅ Super-consolidation complete!")
    print(f"📊 Results:")
    print(f"   Source classes: 16")
    print(f"   Target classes: {len(sorted_classes)}")
    print(f"   Total samples: {total_samples}")
    print(f"   Images copied: {len(new_annotations)}")
    
    print(f"\n🏷️ New Class Distribution:")
    for class_name in sorted(class_counts.keys(), key=lambda x: class_counts[x], reverse=True):
        count = class_counts[class_name]
        percentage = (count / total_samples) * 100
        print(f"   {class_name:20}: {count:4d} samples ({percentage:5.1f}%)")
    
    # Calculate balance metrics
    max_count = max(class_counts.values())
    min_count = min(class_counts.values())
    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
    
    print(f"\n📈 Balance Improvement:")
    print(f"   Max class size: {max_count}")
    print(f"   Min class size: {min_count}")
    print(f"   Imbalance ratio: {imbalance_ratio:.1f}:1")
    
    if imbalance_ratio < 50:  # Much better than 800:1 we had before
        print("   ✅ Significantly improved balance!")
    
    print(f"\n📁 Output directory: {target_dir}")
    
    return target_dir

def create_super_consolidated_dataset_config():
    """Create dataset config for super-consolidated data"""
    
    config_content = """# NIFlags Super-Consolidated Dataset Configuration
# Reduced from 16 classes to 8 balanced classes
# Addresses severe class imbalance issues

DATASET:
  NAME: "NIFlagsSuperConsolidated"  # Must match the registered dataset class name
  ROOT: "../data"                   # Will look for ni_flags_super_consolidated subdirectory
  NUM_SHOTS: -1                     # Use all data"""
    
    config_path = Path("configs/datasets/niflags_super_consolidated.yaml")
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"📝 Dataset config created: {config_path}")
    return config_path

def create_super_consolidated_dataset_class():
    """Create dataset class for super-consolidated data"""
    
    dataset_code = '''"""
NIFlags Super-Consolidated Dataset - 8 balanced classes
Compatible with DaSSL framework
"""

import os
import pickle
from collections import OrderedDict
from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import mkdir_if_missing

@DATASET_REGISTRY.register()
class NIFlagsSuperConsolidated(DatasetBase):
    """Northern Ireland Flags Dataset Super-Consolidated - 8 balanced classes"""
    
    dataset_dir = "ni_flags_super_consolidated"  # Points to super-consolidated data directory
    
    def __init__(self, cfg):
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.image_dir = os.path.join(self.dataset_dir, "images")
        self.split_path = os.path.join(self.dataset_dir, "split_zhou_NIFlagsSuperConsolidated.json")
        
        # Check if custom split exists
        if os.path.exists(self.split_path):
            train, val, test = self.read_split(self.split_path, self.image_dir)
        else:
            # Create splits from annotations.json (same logic as consolidated dataset)
            train, val, test = self.create_splits_from_annotations()
            
        # Load class names
        classnames_file = os.path.join(self.dataset_dir, "classnames.txt")
        if os.path.exists(classnames_file):
            with open(classnames_file, 'r') as f:
                classnames = [line.strip() for line in f.readlines()]
        else:
            # Extract from data if classnames file doesn't exist
            all_labels = set()
            for item in train + val + test:
                all_labels.add(item.label)
            classnames = sorted(list(all_labels))
        
        # Print dataset statistics
        print(f"\\n{'='*60}")
        print(f"📊 NIFlags Super-Consolidated Dataset Loaded")
        print(f"{'='*60}")
        print(f"   Root: {self.dataset_dir}")
        print(f"   Train: {len(train)} samples")
        print(f"   Val: {len(val)} samples")
        print(f"   Test: {len(test)} samples")
        print(f"   Classes: {len(classnames)} super-consolidated classes")
        print(f"{'='*60}\\n")
        
        super().__init__(train_x=train, val=val, test=test)

    def create_splits_from_annotations(self):
        """Create train/val/test splits from annotations.json"""
        import json
        import random
        from collections import defaultdict
        
        annotations_file = os.path.join(self.dataset_dir, "annotations.json")
        if not os.path.exists(annotations_file):
            raise FileNotFoundError(f"Annotations file not found: {annotations_file}")
        
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        # Group by class for stratified splitting
        class_to_items = defaultdict(list)
        
        for image_path, annotation in annotations.items():
            if isinstance(annotation, dict) and 'hierarchical_classname' in annotation:
                label = annotation['hierarchical_classname']
                class_to_items[label].append((image_path, annotation))
        
        train_data, val_data, test_data = [], [], []
        
        # Create class name to index mapping
        all_class_names = sorted(list(class_to_items.keys()))
        class_to_idx = {name: idx for idx, name in enumerate(all_class_names)}
        
        # Split each class proportionally (70% train, 15% val, 15% test)
        for class_name, items in class_to_items.items():
            random.shuffle(items)
            n_items = len(items)
            n_train = int(0.7 * n_items)
            n_val = int(0.15 * n_items)
            
            train_items = items[:n_train]
            val_items = items[n_train:n_train + n_val]
            test_items = items[n_train + n_val:]
            
            label_idx = class_to_idx[class_name]
            
            # Convert to Datum objects
            for image_path, annotation in train_items:
                impath = os.path.join(self.image_dir, image_path)
                train_data.append(Datum(impath=impath, label=label_idx, classname=class_name))
            
            for image_path, annotation in val_items:
                impath = os.path.join(self.image_dir, image_path)
                val_data.append(Datum(impath=impath, label=label_idx, classname=class_name))
            
            for image_path, annotation in test_items:
                impath = os.path.join(self.image_dir, image_path)
                test_data.append(Datum(impath=impath, label=label_idx, classname=class_name))
        
        return train_data, val_data, test_data

    def read_data(self, filepath):
        """Read data from train.txt, val.txt, or test.txt files"""
        items = []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        image_path = parts[0]
                        label = int(parts[1])
                        classname = parts[2] if len(parts) > 2 else str(label)
                        impath = os.path.join(self.image_dir, image_path)
                        items.append(Datum(impath=impath, label=label, classname=classname))
        return items
'''
    
    dataset_path = Path("datasets/ni_flags_super_consolidated.py")
    with open(dataset_path, 'w') as f:
        f.write(dataset_code)
    
    print(f"📝 Dataset class created: {dataset_path}")
    return dataset_path

def main():
    """Main super-consolidation function"""
    print("="*60)
    print("🎯 SUPER-CONSOLIDATION: 16 → 8 Classes")
    print("="*60)
    print("Goal: Fix macro-F1 of 8.4% by reducing class imbalance")
    print()
    
    # 1. Apply super-consolidation
    target_dir = apply_super_consolidation()
    
    if target_dir:
        # 2. Create dataset config
        config_path = create_super_consolidated_dataset_config()
        
        # 3. Create dataset class
        dataset_path = create_super_consolidated_dataset_class()
        
        print(f"\\n✅ Super-consolidation complete!")
        print(f"📁 Files created:")
        print(f"   📊 Dataset: {target_dir}")
        print(f"   ⚙️ Config: {config_path}")
        print(f"   🐍 Dataset class: {dataset_path}")
        
        print(f"\\n🚀 Next steps:")
        print(f"   1. Import the new dataset in train_minimal_mps.py")
        print(f"   2. Train with: --dataset-config-file {config_path}")
        print(f"   3. Expected: Macro-F1 0.084 → 0.35-0.45")
        
        # Create training command
        print(f"\\n💻 Training command:")
        print(f"python train_minimal_mps.py --clean --trainer CoCoOp \\\\")
        print(f"    --config-file configs/trainers/CoCoOp/vit_b32.yaml \\\\")
        print(f"    --dataset-config-file {config_path} \\\\")
        print(f"    --output-dir experiments/vit_b32_super_consolidated \\\\")
        print(f"    TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0 \\\\")
        print(f"    OPTIM.MAX_EPOCH 100")

if __name__ == "__main__":
    main()