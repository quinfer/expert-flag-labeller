#!/usr/bin/env python3
"""
Dynamic Dataset Factory for Flag Classification
Automatically handles any consolidation level and calculates proper class weights
"""

import os
import json
import random
from pathlib import Path
from collections import defaultdict, Counter
from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import mkdir_if_missing


class DynamicFlagDataset(DatasetBase):
    """
    Dynamic Flag Dataset that adapts to any consolidation level
    Automatically calculates class weights and handles splits
    """
    
    def __init__(self, cfg, dataset_name=None, dataset_path=None):
        """
        Initialize dynamic dataset
        
        Args:
            cfg: Dassl config object
            dataset_name: Name for the dataset (auto-detected if None)
            dataset_path: Path to dataset directory (auto-detected if None)
        """
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        
        # Auto-detect dataset if not specified
        if dataset_path is None:
            dataset_path = self._auto_detect_dataset(root, cfg.DATASET.NAME)
        
        self.dataset_dir = os.path.join(root, dataset_path)
        self.image_dir = os.path.join(self.dataset_dir, "images")
        self.anno_file = os.path.join(self.dataset_dir, "annotations.json")
        self.stats_file = os.path.join(self.dataset_dir, "consolidation_stats.json")
        
        # Load dataset metadata
        self.dataset_info = self._load_dataset_info()
        self.class_distribution = self._calculate_class_distribution()
        
        # Create splits
        train, val, test = self._create_balanced_splits()
        
        # Store class information for weight calculation
        self.classnames = sorted(list(self.class_distribution.keys()))
        self.num_classes = len(self.classnames)
        
        # Print dataset statistics
        self._print_dataset_stats(train, val, test)
        
        super().__init__(train_x=train, val=val, test=test)
    
    def _auto_detect_dataset(self, root, dataset_name):
        """Auto-detect dataset path based on name"""
        dataset_map = {
            'NIFlagsConsolidated': 'ni_flags_consolidated',
            'NIFlagsSuperConsolidated': 'ni_flags_super_consolidated',
            'NIFlags': 'ni_flags_v2',
        }
        
        if dataset_name in dataset_map:
            return dataset_map[dataset_name]
        
        # Try to find any dataset directory
        for path in Path(root).iterdir():
            if path.is_dir() and 'flags' in path.name.lower():
                return path.name
        
        raise ValueError(f"Could not auto-detect dataset for {dataset_name}")
    
    def _load_dataset_info(self):
        """Load dataset metadata and statistics"""
        info = {}
        
        # Load consolidation stats if available
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                info.update(json.load(f))
        
        # Load annotations
        if os.path.exists(self.anno_file):
            with open(self.anno_file, 'r') as f:
                info['annotations'] = json.load(f)
        else:
            raise FileNotFoundError(f"Annotations file not found: {self.anno_file}")
        
        return info
    
    def _calculate_class_distribution(self):
        """Calculate actual class distribution from annotations"""
        class_counts = Counter()
        
        for image_path, annotation in self.dataset_info['annotations'].items():
            if isinstance(annotation, dict) and 'hierarchical_classname' in annotation:
                class_name = annotation['hierarchical_classname']
                class_counts[class_name] += 1
        
        return dict(class_counts)
    
    def _create_balanced_splits(self, train_ratio=0.7, val_ratio=0.15):
        """Create stratified train/val/test splits"""
        # Group annotations by class
        class_to_items = defaultdict(list)
        
        for image_path, annotation in self.dataset_info['annotations'].items():
            if isinstance(annotation, dict) and 'hierarchical_classname' in annotation:
                class_name = annotation['hierarchical_classname']
                class_to_items[class_name].append((image_path, annotation))
        
        # Create class name to index mapping
        class_to_idx = {name: idx for idx, name in enumerate(self.classnames)}
        
        train_data, val_data, test_data = [], [], []
        
        # Split each class proportionally
        for class_name, items in class_to_items.items():
            random.shuffle(items)
            n_items = len(items)
            n_train = int(train_ratio * n_items)
            n_val = int(val_ratio * n_items)
            
            train_items = items[:n_train]
            val_items = items[n_train:n_train + n_val]
            test_items = items[n_train + n_val:]
            
            label_idx = class_to_idx[class_name]
            
            # Convert to Datum objects
            for image_path, annotation in train_items:
                impath = os.path.join(self.image_dir, image_path)
                if os.path.exists(impath):
                    train_data.append(Datum(impath=impath, label=label_idx, classname=class_name))
            
            for image_path, annotation in val_items:
                impath = os.path.join(self.image_dir, image_path)
                if os.path.exists(impath):
                    val_data.append(Datum(impath=impath, label=label_idx, classname=class_name))
            
            for image_path, annotation in test_items:
                impath = os.path.join(self.image_dir, image_path)
                if os.path.exists(impath):
                    test_data.append(Datum(impath=impath, label=label_idx, classname=class_name))
        
        return train_data, val_data, test_data
    
    def _print_dataset_stats(self, train, val, test):
        """Print comprehensive dataset statistics"""
        total_samples = len(train) + len(val) + len(test)
        
        print(f"\n{'='*70}")
        print(f"📊 Dynamic Flag Dataset Loaded")
        print(f"{'='*70}")
        print(f"   Dataset: {self.dataset_dir}")
        print(f"   Classes: {self.num_classes}")
        print(f"   Train: {len(train):,} samples ({len(train)/total_samples*100:.1f}%)")
        print(f"   Val: {len(val):,} samples ({len(val)/total_samples*100:.1f}%)")
        print(f"   Test: {len(test):,} samples ({len(test)/total_samples*100:.1f}%)")
        print(f"   Total: {total_samples:,} samples")
        
        # Class distribution analysis
        print(f"\n📈 Class Distribution Analysis:")
        total_class_samples = sum(self.class_distribution.values())
        
        # Calculate imbalance metrics
        max_count = max(self.class_distribution.values())
        min_count = min(self.class_distribution.values())
        imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
        
        print(f"   Imbalance ratio: {imbalance_ratio:.1f}:1")
        print(f"   Most frequent class: {max_count:,} samples")
        print(f"   Least frequent class: {min_count:,} samples")
        
        # Show top classes
        sorted_classes = sorted(self.class_distribution.items(), 
                              key=lambda x: x[1], reverse=True)
        
        print(f"\n🏷️ Top Classes:")
        for class_name, count in sorted_classes[:10]:
            percentage = (count / total_class_samples) * 100
            print(f"   {class_name:25}: {count:4d} samples ({percentage:5.1f}%)")
        
        if len(sorted_classes) > 10:
            print(f"   ... and {len(sorted_classes) - 10} more classes")
        
        print(f"{'='*70}\n")
    
    def get_class_weights(self, method='inverse_frequency'):
        """
        Calculate class weights for handling imbalance
        
        Args:
            method: 'inverse_frequency', 'sqrt_inverse', or 'uniform'
        
        Returns:
            torch.Tensor: Class weights for loss function
        """
        import torch
        
        if method == 'uniform':
            return torch.ones(self.num_classes)
        
        weights = torch.zeros(self.num_classes)
        total_samples = sum(self.class_distribution.values())
        
        for idx, class_name in enumerate(self.classnames):
            class_count = self.class_distribution[class_name]
            
            if method == 'inverse_frequency':
                weight = total_samples / (self.num_classes * class_count)
            elif method == 'sqrt_inverse':
                weight = (total_samples / (self.num_classes * class_count)) ** 0.5
            else:
                weight = 1.0
            
            weights[idx] = weight
        
        # Normalize weights
        weights = weights / weights.mean()
        
        print(f"📊 Calculated {method} class weights:")
        print(f"   Weight range: {weights.min():.2f} - {weights.max():.2f}")
        print(f"   Mean weight: {weights.mean():.2f}")
        
        return weights


def register_dynamic_datasets():
    """Register dynamic dataset variants"""
    
    # Check if already registered to avoid conflicts
    if "NIFlagsConsolidatedDynamic" not in DATASET_REGISTRY._obj_map:
        @DATASET_REGISTRY.register()
        class NIFlagsConsolidatedDynamic(DynamicFlagDataset):
            """16-class consolidated dataset with dynamic handling"""
            def __init__(self, cfg):
                super().__init__(cfg, dataset_name="NIFlagsConsolidated")
    
    if "NIFlagsSuperConsolidatedDynamic" not in DATASET_REGISTRY._obj_map:
        @DATASET_REGISTRY.register()
        class NIFlagsSuperConsolidatedDynamic(DynamicFlagDataset):
            """7-class super-consolidated dataset with dynamic handling"""
            def __init__(self, cfg):
                super().__init__(cfg, dataset_name="NIFlagsSuperConsolidated")
    
    if "NIFlagsDynamic" not in DATASET_REGISTRY._obj_map:
        @DATASET_REGISTRY.register()
        class NIFlagsDynamic(DynamicFlagDataset):
            """Original dataset with dynamic handling"""
            def __init__(self, cfg):
                super().__init__(cfg, dataset_name="NIFlags")


# Register all dynamic datasets
register_dynamic_datasets()


if __name__ == "__main__":
    """Test the dynamic dataset factory"""
    print("🧪 Testing Dynamic Dataset Factory")
    
    # Mock config for testing
    class MockConfig:
        def __init__(self):
            self.DATASET = MockDatasetConfig()
    
    class MockDatasetConfig:
        def __init__(self):
            self.ROOT = "../data"
            self.NAME = "NIFlagsConsolidated"
    
    cfg = MockConfig()
    
    try:
        dataset = DynamicFlagDataset(cfg)
        print(f"✅ Successfully loaded dataset with {dataset.num_classes} classes")
        
        # Test weight calculation
        weights = dataset.get_class_weights('inverse_frequency')
        print(f"✅ Calculated class weights: {weights.shape}")
        
    except Exception as e:
        print(f"❌ Error testing dataset: {e}")