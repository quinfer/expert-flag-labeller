#!/usr/bin/env python3
"""
Data preparation script for NI Flags dataset
Uses confidence threshold ≥3.0 to expand dataset
Processes classifications_0708.csv
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import pandas as pd
import numpy as np
import json
import shutil
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_new_dataset(csv_path="classifications_0708.csv"):
    """Analyze the new CSV file"""
    print("\n" + "="*60)
    print("📊 ANALYZING NEW DATASET")
    print("="*60)
    
    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} rows from {csv_path}")
    
    # Show columns
    print(f"\n📋 Columns: {list(df.columns)}")
    
    # Check for required columns and adapt to new format
    print("\n🔧 Adapting column format...")
    
    # Create hierarchical classification from separate columns
    if 'hierarchical_classification' not in df.columns:
        if all(col in df.columns for col in ['primary_category', 'display_context', 'specific_flag']):
            # Replace NaN values with 'Unknown' for each component
            df['primary_category'] = df['primary_category'].fillna('Unknown')
            df['display_context'] = df['display_context'].fillna('Unknown')
            df['specific_flag'] = df['specific_flag'].fillna('Unknown')
            
            # Create hierarchical classification
            df['hierarchical_classification'] = df['primary_category'].astype(str) + '-' + \
                                               df['display_context'].astype(str) + '-' + \
                                               df['specific_flag'].astype(str)
            
            print("✅ Created hierarchical_classification from component columns")
            print(f"   Example: {df['hierarchical_classification'].iloc[0]}")
        else:
            print("❌ Cannot create hierarchical classification - missing component columns")
            print(f"   Available columns: {df.columns.tolist()}")
            return df
    
    # Handle confidence column
    if 'average_confidence' not in df.columns:
        if 'confidence' in df.columns:
            df['average_confidence'] = df['confidence']
            print("✅ Using 'confidence' column as average_confidence")
        elif 'confidence_score' in df.columns:
            df['average_confidence'] = df['confidence_score']
            print("✅ Using 'confidence_score' column as average_confidence")
    
    # Handle image URL/ID
    if 'image_url' not in df.columns:
        if 'image_id' in df.columns:
            df['image_url'] = df['image_id'].astype(str)
            print("✅ Using 'image_id' column as image identifier")
    
    # Confidence statistics
    if 'average_confidence' in df.columns:
        print(f"\n📈 Confidence Statistics:")
        print(f"   Min: {df['average_confidence'].min():.2f}")
        print(f"   Max: {df['average_confidence'].max():.2f}")
        print(f"   Mean: {df['average_confidence'].mean():.2f}")
        print(f"   Median: {df['average_confidence'].median():.2f}")
        
        # Samples by threshold
        print("\n📊 Samples by confidence threshold:")
        thresholds = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
        threshold_counts = {}
        for threshold in thresholds:
            count = len(df[df['average_confidence'] >= threshold])
            threshold_counts[threshold] = count
            print(f"   ≥{threshold}: {count:4d} samples")
        
        # Recommended threshold
        if threshold_counts[3.0] > 2000:
            print(f"\n✅ Recommended: Use confidence ≥3.0 ({threshold_counts[3.0]} samples)")
        elif threshold_counts[2.5] > 2000:
            print(f"\n✅ Recommended: Use confidence ≥2.5 ({threshold_counts[2.5]} samples)")
        else:
            print(f"\n⚠️ Warning: Even with ≥2.0, only {threshold_counts[2.0]} samples")
    
    return df

def prepare_dataset_with_confidence(df, confidence_threshold=3.0, output_dir="../data/ni_flags_v2"):
    """
    Prepare dataset with specified confidence threshold
    """
    print("\n" + "="*60)
    print(f"🔧 PREPARING DATASET (confidence ≥{confidence_threshold})")
    print("="*60)
    
    # Check if hierarchical_classification exists
    if 'hierarchical_classification' not in df.columns:
        print("❌ hierarchical_classification column missing!")
        print("Available columns:", df.columns.tolist())
        return None, None, None, None
    
    # Check if average_confidence exists
    if 'average_confidence' not in df.columns:
        print("❌ average_confidence column missing!")
        print("Available columns:", df.columns.tolist())
        return None, None, None, None
    
    # Filter by confidence
    filtered_df = df[df['average_confidence'] >= confidence_threshold].copy()
    print(f"✅ Filtered: {len(filtered_df)} samples with confidence ≥{confidence_threshold}")
    
    # Create hierarchical labels
    filtered_df['label'] = filtered_df['hierarchical_classification'].fillna('Unknown-Unknown-Unknown')
    
    # Get unique classes
    unique_classes = filtered_df['label'].unique()
    print(f"📊 Unique classes: {len(unique_classes)}")
    
    # Create class mapping
    class_to_idx = {cls: idx for idx, cls in enumerate(sorted(unique_classes))}
    idx_to_class = {idx: cls for cls, idx in class_to_idx.items()}
    
    # Add numeric labels
    filtered_df['label_idx'] = filtered_df['label'].map(class_to_idx)
    
    # Class distribution
    class_counts = filtered_df['label'].value_counts()
    print(f"\n📊 Class Distribution:")
    print(f"   Most common: {class_counts.iloc[0]} samples ({class_counts.index[0][:40]})")
    print(f"   Least common: {class_counts.iloc[-1]} samples ({class_counts.index[-1][:40]})")
    print(f"   Imbalance ratio: {class_counts.iloc[0] / class_counts.iloc[-1]:.1f}:1")
    
    # Singleton classes
    singleton_classes = class_counts[class_counts == 1]
    print(f"   Singleton classes: {len(singleton_classes)}")
    
    # Classes with <5 samples
    rare_classes = class_counts[class_counts < 5]
    print(f"   Classes with <5 samples: {len(rare_classes)}")
    
    return filtered_df, class_to_idx, idx_to_class, class_counts

def split_dataset(filtered_df, class_counts, min_samples_per_class=2):
    """
    Split dataset into train/val/test with stratification
    Handle rare classes carefully
    """
    print("\n" + "="*60)
    print("📂 SPLITTING DATASET")
    print("="*60)
    
    # Separate by class frequency
    train_data = []
    val_data = []
    test_data = []
    
    for class_name, count in class_counts.items():
        class_samples = filtered_df[filtered_df['label'] == class_name]
        
        if count == 1:
            # Singleton: put in training
            train_data.append(class_samples)
            print(f"   Singleton → train: {class_name[:30]}")
        elif count == 2:
            # Two samples: one train, one val
            train_data.append(class_samples.iloc[:1])
            val_data.append(class_samples.iloc[1:2])
        elif count == 3:
            # Three samples: two train, one val
            train_data.append(class_samples.iloc[:2])
            val_data.append(class_samples.iloc[2:3])
        elif count < 10:
            # Rare: 70% train, 30% val
            n_train = max(2, int(0.7 * count))
            train_data.append(class_samples.iloc[:n_train])
            val_data.append(class_samples.iloc[n_train:])
        else:
            # Normal: 70% train, 15% val, 15% test
            n_train = int(0.7 * count)
            n_val = int(0.15 * count)
            train_data.append(class_samples.iloc[:n_train])
            val_data.append(class_samples.iloc[n_train:n_train+n_val])
            test_data.append(class_samples.iloc[n_train+n_val:])
    
    # Combine
    train_df = pd.concat(train_data, ignore_index=True) if train_data else pd.DataFrame()
    val_df = pd.concat(val_data, ignore_index=True) if val_data else pd.DataFrame()
    test_df = pd.concat(test_data, ignore_index=True) if test_data else pd.DataFrame()
    
    print(f"\n📊 Split Results:")
    print(f"   Train: {len(train_df)} samples ({len(train_df['label'].unique())} classes)")
    print(f"   Val: {len(val_df)} samples ({len(val_df['label'].unique())} classes)")
    print(f"   Test: {len(test_df)} samples ({len(test_df['label'].unique())} classes)")
    print(f"   Total: {len(train_df) + len(val_df) + len(test_df)} samples")
    
    return train_df, val_df, test_df

def download_and_organize_images(train_df, val_df, test_df, output_dir="../data/ni_flags_v2"):
    """
    Download images and create dataset structure
    """
    print("\n" + "="*60)
    print("💾 ORGANIZING DATASET")
    print("="*60)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create directories
    images_dir = output_path / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Save splits as text files
    splits = {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }
    
    for split_name, split_df in splits.items():
        if len(split_df) == 0:
            continue
            
        split_file = output_path / f"{split_name}.txt"
        with open(split_file, 'w') as f:
            for _, row in split_df.iterrows():
                # Format: image_path label_idx
                image_name = f"{split_name}_{row.name:05d}.jpg"
                image_path = f"images/{image_name}"
                f.write(f"{image_path} {row['label_idx']}\n")
        
        print(f"✅ Created {split_file.name} with {len(split_df)} entries")
    
    # Save class names
    all_classes = sorted(set(
        list(train_df['label'].unique()) + 
        list(val_df['label'].unique()) + 
        list(test_df['label'].unique() if len(test_df) > 0 else [])
    ))
    
    classnames_file = output_path / "classnames.txt"
    with open(classnames_file, 'w') as f:
        for class_name in all_classes:
            f.write(f"{class_name}\n")
    
    print(f"✅ Created classnames.txt with {len(all_classes)} classes")
    
    # Save metadata
    metadata = {
        'confidence_threshold': 3.0,
        'total_samples': len(train_df) + len(val_df) + len(test_df),
        'num_classes': len(all_classes),
        'train_samples': len(train_df),
        'val_samples': len(val_df),
        'test_samples': len(test_df),
        'class_distribution': train_df['label'].value_counts().to_dict()
    }
    
    metadata_file = output_path / "dataset_info.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved metadata to dataset_info.json")
    
    return output_path

def visualize_class_distribution(class_counts, output_path="class_distribution_confidence3.png"):
    """Create visualization of class distribution"""
    print("\n" + "="*60)
    print("📊 CREATING VISUALIZATIONS")
    print("="*60)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Top 20 classes
    top_20 = class_counts.head(20)
    axes[0, 0].barh(range(len(top_20)), top_20.values)
    axes[0, 0].set_yticks(range(len(top_20)))
    axes[0, 0].set_yticklabels([name[:30] for name in top_20.index], fontsize=8)
    axes[0, 0].set_xlabel('Number of Samples')
    axes[0, 0].set_title('Top 20 Classes')
    axes[0, 0].invert_yaxis()
    
    # 2. Distribution histogram
    axes[0, 1].hist(class_counts.values, bins=50, edgecolor='black')
    axes[0, 1].set_xlabel('Number of Samples per Class')
    axes[0, 1].set_ylabel('Number of Classes')
    axes[0, 1].set_title('Class Frequency Distribution')
    axes[0, 1].set_yscale('log')
    
    # 3. Cumulative distribution
    sorted_counts = sorted(class_counts.values, reverse=True)
    cumsum = np.cumsum(sorted_counts)
    axes[1, 0].plot(range(len(cumsum)), cumsum / cumsum[-1] * 100)
    axes[1, 0].set_xlabel('Number of Classes')
    axes[1, 0].set_ylabel('Cumulative % of Data')
    axes[1, 0].set_title('Cumulative Class Distribution')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].axhline(y=50, color='r', linestyle='--', alpha=0.5)
    axes[1, 0].axhline(y=80, color='r', linestyle='--', alpha=0.5)
    
    # 4. Category distribution
    categories = defaultdict(int)
    for class_name, count in class_counts.items():
        category = class_name.split('-')[0] if '-' in class_name else 'Unknown'
        categories[category] += count
    
    category_df = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
    category_df = category_df.sort_values('Count', ascending=False)
    
    axes[1, 1].pie(category_df['Count'], labels=category_df['Category'], autopct='%1.1f%%')
    axes[1, 1].set_title('Distribution by Category')
    
    plt.suptitle(f'Class Distribution Analysis (Confidence ≥3.0)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved visualization to {output_path}")
    plt.close()
    
    return categories

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🚀 NI FLAGS DATASET PREPARATION V2")
    print("="*60)
    print("Using new classifications_0708.csv with confidence ≥3.0")
    
    # Step 1: Analyze new dataset
    df = analyze_new_dataset("classifications_0708.csv")
    
    # Step 2: Prepare with confidence threshold
    confidence_threshold = 3.0
    result = prepare_dataset_with_confidence(
        df, confidence_threshold=confidence_threshold
    )
    
    if result[0] is None:
        print("❌ Dataset preparation failed. Please check the CSV format.")
        return None
    
    filtered_df, class_to_idx, idx_to_class, class_counts = result
    
    # Step 3: Split dataset
    train_df, val_df, test_df = split_dataset(filtered_df, class_counts)
    
    # Step 4: Organize files
    output_dir = "../data/ni_flags_v2"
    dataset_path = download_and_organize_images(train_df, val_df, test_df, output_dir)
    
    # Step 5: Visualize
    categories = visualize_class_distribution(class_counts)
    
    # Step 6: Summary
    print("\n" + "="*60)
    print("✅ DATASET PREPARATION COMPLETE")
    print("="*60)
    print(f"📂 Dataset saved to: {dataset_path}")
    print(f"📊 Total samples: {len(filtered_df)}")
    print(f"🏷️ Total classes: {len(class_counts)}")
    print(f"⚖️ Max imbalance: {class_counts.iloc[0] / class_counts.iloc[-1]:.1f}:1")
    
    print("\n📈 Category breakdown:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(filtered_df) * 100
        print(f"   {category:20}: {count:4d} samples ({percentage:5.1f}%)")
    
    print("\n🎯 Next steps:")
    print("1. Update configs/datasets/niflags.yaml to point to ni_flags_v2")
    print("2. Modify datasets/ni_flags.py to use the new data")
    print("3. Run training with expanded dataset")
    print("4. Consider data augmentation for rare classes")
    
    # Save summary report
    summary = {
        'dataset_version': 'v2',
        'source_file': 'classifications_0708.csv',
        'confidence_threshold': confidence_threshold,
        'total_samples': len(filtered_df),
        'num_classes': len(class_counts),
        'train_samples': len(train_df),
        'val_samples': len(val_df),
        'test_samples': len(test_df),
        'max_imbalance_ratio': float(class_counts.iloc[0] / class_counts.iloc[-1]),
        'singleton_classes': int(sum(class_counts == 1)),
        'rare_classes_under_5': int(sum(class_counts < 5)),
        'categories': dict(categories)
    }
    
    with open('dataset_preparation_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Summary saved to dataset_preparation_summary.json")
    
    return dataset_path

if __name__ == "__main__":
    main()
