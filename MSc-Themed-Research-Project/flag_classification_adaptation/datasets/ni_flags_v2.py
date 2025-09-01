"""
NIFlags Dataset V2 - Expanded with confidence >= 3.0
Compatible with DaSSL framework
"""

import os
import pickle
from collections import OrderedDict
from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import mkdir_if_missing

@DATASET_REGISTRY.register()
class NIFlagsV2(DatasetBase):
    """Northern Ireland Flags Dataset V2 - Expanded version"""
    
    dataset_dir = "ni_flags_v2"  # Updated directory name
    
    def __init__(self, cfg):
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.image_dir = os.path.join(self.dataset_dir, "images")
        self.split_path = os.path.join(self.dataset_dir, "split_zhou_NIFlagsV2.json")
        
        # Check if custom split exists
        if os.path.exists(self.split_path):
            train, val, test = self.read_split(self.split_path, self.image_dir)
        else:
            # Use our prepared splits
            train = self.read_data(os.path.join(self.dataset_dir, "train.txt"))
            val = self.read_data(os.path.join(self.dataset_dir, "val.txt"))
            test = self.read_data(os.path.join(self.dataset_dir, "test.txt"))
            
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
        print(f"📊 NIFlags V2 Dataset Loaded")
        print(f"{'='*60}")
        print(f"   Root: {self.dataset_dir}")
        print(f"   Train: {len(train)} samples")
        print(f"   Val: {len(val)} samples")
        print(f"   Test: {len(test)} samples")
        print(f"   Classes: {len(classnames)}")
        
        # Show class distribution info
        if train:
            from collections import Counter
            train_labels = [item.label for item in train]
            label_counts = Counter(train_labels)
            most_common = label_counts.most_common(1)[0]
            least_common = label_counts.most_common()[-1]
            print(f"   Most common: {most_common[1]} samples")
            print(f"   Least common: {least_common[1]} samples")
            print(f"   Imbalance ratio: {most_common[1]/least_common[1]:.1f}:1")
        
        print(f"{'='*60}\n")
        
        super().__init__(train_x=train, val=val, test=test)
        
        self._num_classes = len(classnames)
        self._classnames = classnames
        self._lab2cname = {i: classnames[i] for i in range(len(classnames))}
    
    def read_data(self, filepath):
        """Read data from prepared txt files"""
        items = []
        
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            return items
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) == 2:
                impath, label = parts
                # Convert relative path to absolute
                if not impath.startswith('/'):
                    impath = os.path.join(self.dataset_dir, impath)
                
                # Create Datum object
                item = Datum(
                    impath=impath,
                    label=int(label),
                    classname=f"class_{label}"  # Will be replaced with actual name
                )
                items.append(item)
        
        return items
    
    @property
    def num_classes(self):
        return self._num_classes
    
    @property
    def classnames(self):
        return self._classnames
    
    @property
    def lab2cname(self):
        return self._lab2cname

