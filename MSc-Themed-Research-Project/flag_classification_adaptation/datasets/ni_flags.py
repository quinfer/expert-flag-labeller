import os
import pickle
import json
import math
import random
from collections import defaultdict

from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import read_json, write_json, mkdir_if_missing


@DATASET_REGISTRY.register()
class NIFlags(DatasetBase):
    """
    Northern Ireland Flags Dataset for Hierarchical Classification
    
    Expected data structure:
    - Root directory contains 'images/' folder with flag images
    - 'annotations.json' contains expert classifications in format:
      {
        "image_001.jpg": {
          "category": "National",
          "context": "building_mounted", 
          "specific_flag": "Union_Jack",
          "confidence": 4.5,
          "hierarchical_classname": "National-building_mounted-Union_Jack"
        }
      }
    """

    dataset_dir = "ni_flags"

    def __init__(self, cfg):
        root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.image_dir = os.path.join(self.dataset_dir, "images")
        self.anno_file = os.path.join(self.dataset_dir, "annotations.json")
        self.split_path = os.path.join(self.dataset_dir, "split_zhou_NIFlags.json")
        self.split_fewshot_dir = os.path.join(self.dataset_dir, "split_fewshot")
        mkdir_if_missing(self.split_fewshot_dir)

        if os.path.exists(self.split_path):
            train, val, test = self.read_split(self.split_path, self.image_dir)
        else:
            # Create train/val/test splits from your expert annotations
            all_data = self.read_expert_annotations()
            train, val, test = self.create_splits(all_data)
            self.save_split(train, val, test, self.split_path, self.image_dir)

        num_shots = cfg.DATASET.NUM_SHOTS
        if num_shots >= 1:
            seed = cfg.SEED
            preprocessed = os.path.join(self.split_fewshot_dir,
                                        f"shot_{num_shots}-seed_{seed}.pkl")

            if os.path.exists(preprocessed):
                print(f"Loading preprocessed few-shot data from {preprocessed}")
                with open(preprocessed, "rb") as file:
                    data = pickle.load(file)
                    train, val = data["train"], data["val"]
            else:
                train = self.generate_fewshot_dataset(train, num_shots=num_shots)
                val = self.generate_fewshot_dataset(val, num_shots=min(num_shots, 4))
                data = {"train": train, "val": val}
                print(f"Saving preprocessed few-shot data to {preprocessed}")
                with open(preprocessed, "wb") as file:
                    pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

        subsample = cfg.DATASET.SUBSAMPLE_CLASSES
        train, val, test = self.subsample_classes(train, val, test, subsample=subsample)

        super().__init__(train_x=train, val=val, test=test)

    def read_expert_annotations(self):
        """
        Read your expert classifications and convert to hierarchical format
        """
        print(f"Loading expert annotations from {self.anno_file}")
        
        if not os.path.exists(self.anno_file):
            raise FileNotFoundError(f"Annotations file not found: {self.anno_file}")
        
        with open(self.anno_file, 'r') as f:
            annotations = json.load(f)
        
        items = []
        class_to_label = {}
        label_counter = 0
        
        for image_name, annotation in annotations.items():
            # Skip low-confidence annotations if desired
            if annotation.get('confidence', 0) < 3.0:
                continue
                
            impath = os.path.join(self.image_dir, image_name)
            if not os.path.exists(impath):
                print(f"Warning: Image not found: {impath}")
                continue
            
            # Use the pre-computed hierarchical classname
            hierarchical_classname = annotation['hierarchical_classname']
            
            # Map to integer label
            if hierarchical_classname not in class_to_label:
                class_to_label[hierarchical_classname] = label_counter
                label_counter += 1
            
            label = class_to_label[hierarchical_classname]
            
            item = Datum(impath=impath, label=label, classname=hierarchical_classname)
            items.append(item)
        
        print(f"Loaded {len(items)} flag images with {len(class_to_label)} unique classes")
        print(f"Example classes: {list(class_to_label.keys())[:5]}")
        
        return items

    def create_splits(self, all_data, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        Create stratified train/val/test splits ensuring each hierarchical class 
        is represented proportionally
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
        
        # Group by class label for stratified splitting
        class_groups = defaultdict(list)
        for item in all_data:
            class_groups[item.label].append(item)
        
        train, val, test = [], [], []
        
        for label, items in class_groups.items():
            n_items = len(items)
            random.shuffle(items)  # Shuffle within each class
            
            # Calculate split indices
            n_train = max(1, int(n_items * train_ratio))
            n_val = max(1, int(n_items * val_ratio))
            n_test = n_items - n_train - n_val
            
            # Ensure at least one sample in test if possible
            if n_test == 0 and n_items > 2:
                n_train -= 1
                n_test = 1
            
            train.extend(items[:n_train])
            val.extend(items[n_train:n_train + n_val])
            test.extend(items[n_train + n_val:])
        
        print(f"Created splits: Train={len(train)}, Val={len(val)}, Test={len(test)}")
        return train, val, test

    @staticmethod
    def save_split(train, val, test, filepath, path_prefix):
        """Save train/val/test split to JSON file"""
        def _extract(items):
            out = []
            for item in items:
                impath = item.impath
                label = item.label
                classname = item.classname
                impath = impath.replace(path_prefix, "")
                if impath.startswith("/"):
                    impath = impath[1:]
                out.append((impath, label, classname))
            return out

        train = _extract(train)
        val = _extract(val)
        test = _extract(test)

        split = {"train": train, "val": val, "test": test}
        write_json(split, filepath)
        print(f"Saved split to {filepath}")

    @staticmethod
    def read_split(filepath, path_prefix):
        """Load train/val/test split from JSON file"""
        def _convert(items):
            out = []
            for impath, label, classname in items:
                impath = os.path.join(path_prefix, impath)
                item = Datum(impath=impath, label=int(label), classname=classname)
                out.append(item)
            return out

        print(f"Reading split from {filepath}")
        split = read_json(filepath)
        train = _convert(split["train"])
        val = _convert(split["val"])
        test = _convert(split["test"])

        return train, val, test

    @staticmethod
    def subsample_classes(*args, subsample="all"):
        """
        Divide classes into base/new groups for few-shot evaluation
        """
        assert subsample in ["all", "base", "new"]

        if subsample == "all":
            return args

        dataset = args[0]
        labels = set()
        for item in dataset:
            labels.add(item.label)
        labels = list(labels)
        labels.sort()
        n = len(labels)
        m = math.ceil(n / 2)
        
        print(f"SUBSAMPLE {subsample.upper()} CLASSES!")
        if subsample == "base":
            selected = labels[:m]
        else:
            selected = labels[m:]
            
        relabeler = {y: y_new for y_new, y in enumerate(selected)}
        
        output = []
        for dataset in args:
            dataset_new = []
            for item in dataset:
                if item.label not in selected:
                    continue
                item_new = Datum(impath=item.impath,
                                 label=relabeler[item.label],
                                 classname=item.classname)
                dataset_new.append(item_new)
            output.append(dataset_new)

        return output
