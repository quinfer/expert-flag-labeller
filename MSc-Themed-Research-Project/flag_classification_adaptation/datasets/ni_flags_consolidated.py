"""
NIFlags Dataset Consolidated - Reduced from 70 to 16 classes for economic analysis
Compatible with DaSSL framework
"""

import os
import pickle
from collections import OrderedDict
from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import mkdir_if_missing

@DATASET_REGISTRY.register()
class NIFlagsConsolidated(DatasetBase):
    """Northern Ireland Flags Dataset Consolidated - 16 classes for economic analysis"""
    
    dataset_dir = "ni_flags_consolidated"  # Points to consolidated data directory
    
    def __init__(self, cfg):
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.image_dir = os.path.join(self.dataset_dir, "images")
        self.split_path = os.path.join(self.dataset_dir, "split_zhou_NIFlagsConsolidated.json")
        
        # Check if custom split exists
        if os.path.exists(self.split_path):
            train, val, test = self.read_split(self.split_path, self.image_dir)
        else:
            # Use our prepared splits if they exist
            train_file = os.path.join(self.dataset_dir, "train.txt")
            val_file = os.path.join(self.dataset_dir, "val.txt")
            test_file = os.path.join(self.dataset_dir, "test.txt")
            
            if all(os.path.exists(f) for f in [train_file, val_file, test_file]):
                train = self.read_data(train_file)
                val = self.read_data(val_file)
                test = self.read_data(test_file)
            else:
                # Create splits from annotations.json
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
        print(f"\n{'='*60}")
        print(f"📊 NIFlags Consolidated Dataset Loaded")
        print(f"{'='*60}")
        print(f"   Root: {self.dataset_dir}")
        print(f"   Train: {len(train)} samples")
        print(f"   Val: {len(val)} samples")
        print(f"   Test: {len(test)} samples")
        print(f"   Classes: {len(classnames)} consolidated classes")
        print(f"{'='*60}\n")
        
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