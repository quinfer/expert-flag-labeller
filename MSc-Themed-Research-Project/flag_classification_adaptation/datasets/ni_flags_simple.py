"""
Simple NIFlags dataset that works with train.txt/val.txt/test.txt format
"""

import os
from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase

@DATASET_REGISTRY.register()
class NIFlags(DatasetBase):  # Changed name to NIFlags
    """Northern Ireland Flags Dataset - Simple version"""
    
    dataset_dir = "ni_flags"
    
    def __init__(self, cfg):
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        
        # Auto-detect which dataset to use
        v2_dir = os.path.join(root, "ni_flags_v2")
        v1_dir = os.path.join(root, "ni_flags")
        
        if os.path.exists(os.path.join(v2_dir, "train.txt")):
            self.dataset_dir = v2_dir
            print(f"\n✅ Using EXPANDED dataset: ni_flags_v2 (5,490 samples)")
        elif os.path.exists(os.path.join(v1_dir, "train.txt")):
            self.dataset_dir = v1_dir
            print(f"\n📁 Using original dataset: ni_flags")
        else:
            self.dataset_dir = os.path.join(root, self.dataset_dir)
            print(f"\n📁 Using dataset at: {self.dataset_dir}")
        
        # Read splits
        train = self.read_data(os.path.join(self.dataset_dir, "train.txt"))
        val = self.read_data(os.path.join(self.dataset_dir, "val.txt"))
        test = self.read_data(os.path.join(self.dataset_dir, "test.txt"))
        
        # Load class names
        classnames_file = os.path.join(self.dataset_dir, "classnames.txt")
        if os.path.exists(classnames_file):
            with open(classnames_file, 'r') as f:
                classnames = [line.strip() for line in f.readlines()]
        else:
            classnames = [f"class_{i}" for i in range(100)]
        
        # Print statistics
        print(f"   Train: {len(train)} samples")
        print(f"   Val: {len(val)} samples")
        print(f"   Test: {len(test)} samples")
        print(f"   Classes: {len(classnames)}")
        
        super().__init__(train_x=train, val=val, test=test)
        
        self._num_classes = len(classnames)
        self._classnames = classnames
        self._lab2cname = {i: classnames[i] for i in range(len(classnames))}
    
    def read_data(self, filepath):
        """Read data from txt files"""
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
                if not impath.startswith('/'):
                    impath = os.path.join(self.dataset_dir, impath)
                
                item = Datum(
                    impath=impath,
                    label=int(label),
                    classname=f"class_{label}"
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
