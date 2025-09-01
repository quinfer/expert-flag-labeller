"""
NIFlags Dataset Super Consolidated - Reduced from 70 to 7 classes for maximum consolidation
Compatible with DaSSL framework
"""

import os
import json
import pickle
from collections import OrderedDict
from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import mkdir_if_missing

@DATASET_REGISTRY.register()
class NIFlagsSuperConsolidated(DatasetBase):
    """Northern Ireland Flags Dataset Super Consolidated - 7 classes for maximum consolidation
    
    Classes:
    1. Cultural_Community
    2. Historical_Memorial  
    3. International_Other
    4. Nationalist_All
    5. Paramilitary_All
    6. Sport_Community
    7. Unionist_All
    """
    
    dataset_dir = "ni_flags_super_consolidated"  # Points to super consolidated data directory
    
    def __init__(self, cfg):
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.image_dir = os.path.join(self.dataset_dir, "images")
        self.split_path = os.path.join(self.dataset_dir, "split_zhou_NIFlagsSuperConsolidated.json")
        
        # Load class names first
        classnames_file = os.path.join(self.dataset_dir, "classnames.txt")
        if os.path.exists(classnames_file):
            with open(classnames_file, 'r') as f:
                classnames = [line.strip() for line in f.readlines() if line.strip()]
        else:
            # Default 7 super consolidated classes
            classnames = [
                "Cultural_Community",
                "Historical_Memorial", 
                "International_Other",
                "Nationalist_All",
                "Paramilitary_All",
                "Sport_Community",
                "Unionist_All"
            ]
            
        self._classnames = classnames
        self._lab2cname = {i: classnames[i] for i in range(len(classnames))}
        self._cname2lab = {v: k for k, v in self._lab2cname.items()}
        
        # Now load data
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
            
        super().__init__(train_x=train, val=val, test=test)
        
        print(f"📊 NIFlags Super Consolidated Dataset Loaded")
        print(f"   Root: {self.dataset_dir}")
        print(f"   Train: {len(train)} samples")
        print(f"   Val: {len(val)} samples") 
        print(f"   Test: {len(test)} samples")
        print(f"   Classes: {len(classnames)} super consolidated classes")
        print("=" * 80)

    @property
    def classnames(self):
        return self._classnames

    @property
    def lab2cname(self):
        return self._lab2cname

    @property
    def cname2lab(self):
        return self._cname2lab
        
    def create_splits_from_annotations(self):
        """Create train/val/test splits from annotations.json"""
        annotations_file = os.path.join(self.dataset_dir, "annotations.json")
        
        if not os.path.exists(annotations_file):
            raise RuntimeError(f"Annotations file not found: {annotations_file}")
            
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
            
        # Convert to Datum objects
        all_data = []
        for img_name, img_data in annotations.items():
            img_path = os.path.join(self.image_dir, img_name)
            if not os.path.exists(img_path):
                continue
                
            # Use hierarchical_classname for super consolidated
            classname = img_data.get('hierarchical_classname', img_data.get('classname', ''))
            
            # Map classname to label
            if classname in self._cname2lab:
                label = self._cname2lab[classname]
            else:
                # Try to find in default classnames
                if classname in ["Cultural_Community", "Historical_Memorial", "International_Other", 
                               "Nationalist_All", "Paramilitary_All", "Sport_Community", "Unionist_All"]:
                    label = ["Cultural_Community", "Historical_Memorial", "International_Other", 
                           "Nationalist_All", "Paramilitary_All", "Sport_Community", "Unionist_All"].index(classname)
                else:
                    continue  # Skip unknown classes
            
            datum = Datum(
                impath=img_path,
                label=label,
                classname=classname
            )
            all_data.append(datum)
        
        # Create train/val/test splits (80/10/10)
        import random
        random.seed(42)  # For reproducibility
        random.shuffle(all_data)
        
        n_total = len(all_data)
        n_train = int(0.8 * n_total)
        n_val = int(0.1 * n_total)
        
        train = all_data[:n_train]
        val = all_data[n_train:n_train + n_val]
        test = all_data[n_train + n_val:]
        
        return train, val, test
        
    def read_data(self, split_file):
        """Read data from split file"""
        items = []
        
        with open(split_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                img_path = parts[0]
                label = int(parts[1])
                
                # Resolve image path
                if not os.path.isabs(img_path):
                    img_path = os.path.join(self.image_dir, img_path)
                    
                if not os.path.exists(img_path):
                    continue
                    
                # Get classname from label
                if 0 <= label < len(self._classnames):
                    classname = self._classnames[label]
                else:
                    continue
                    
                datum = Datum(
                    impath=img_path,
                    label=label, 
                    classname=classname
                )
                items.append(datum)
                
        return items