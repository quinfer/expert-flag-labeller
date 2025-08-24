#!/usr/bin/env python3
"""
Complete Flag Classification Data Export and Training Setup
Week 9 - MSc Themed Research Project

This script:
1. Exports your 8,204 expert classifications from Supabase
2. Sets up the complete training data structure
3. Validates the dataset integration
4. Provides initial training commands for M4 Max

Usage:
    python complete_data_setup.py --export-method [csv|supabase] [--csv-path PATH]
"""

import argparse
import json
import os
import sys
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
import shutil

def setup_data_structure():
    """
    Ensure the data directory structure matches Li et al.'s expectations
    """
    print("📁 Setting up data directory structure...")
    
    base_data_dir = Path("../data")
    flag_data_dir = base_data_dir / "ni_flags"
    
    # Create required directories
    directories = [
        flag_data_dir,
        flag_data_dir / "images",
        flag_data_dir / "split_fewshot",
        base_data_dir / "annotations"
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified: {dir_path}")
    
    return flag_data_dir

def export_from_csv(csv_path):
    """
    Enhanced CSV export with better error handling and column detection
    """
    print(f"📊 Loading classifications from CSV: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Load CSV with flexible column detection
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Detect column names (handle various naming conventions)
    image_col = None
    category_col = None
    context_col = None
    flag_col = None
    confidence_col = None
    
    # Flexible column matching
    for col in df.columns:
        col_lower = col.lower()
        if 'image' in col_lower and ('name' in col_lower or 'id' in col_lower or 'file' in col_lower):
            image_col = col
        elif 'category' in col_lower or col_lower == 'type':
            category_col = col
        elif 'context' in col_lower or 'display' in col_lower:
            context_col = col
        elif 'flag' in col_lower and 'specific' in col_lower:
            flag_col = col
        elif 'confidence' in col_lower or 'score' in col_lower:
            confidence_col = col
    
    print(f"🔍 Detected columns:")
    print(f"   Image: {image_col}")
    print(f"   Category: {category_col}")
    print(f"   Context: {context_col}")
    print(f"   Specific Flag: {flag_col}")
    print(f"   Confidence: {confidence_col}")
    
    if not all([image_col, category_col]):
        raise ValueError("Could not detect required columns (image, category)")
    
    # Convert to training format
    classifications = {}
    skipped = 0
    
    for _, row in df.iterrows():
        image_name = str(row[image_col]).strip()
        category = str(row[category_col]).strip() if pd.notna(row[category_col]) else 'unknown'
        context = str(row[context_col]).strip() if context_col and pd.notna(row[context_col]) else 'unknown'
        specific_flag = str(row[flag_col]).strip() if flag_col and pd.notna(row[flag_col]) else 'unknown'
        confidence = float(row[confidence_col]) if confidence_col and pd.notna(row[confidence_col]) else 4.0
        
        if image_name and image_name != 'nan':
            classifications[image_name] = {
                'category': category,
                'context': context,
                'specific_flag': specific_flag,
                'confidence': confidence
            }
        else:
            skipped += 1
    
    print(f"✅ Processed {len(classifications)} classifications (skipped {skipped})")
    return classifications

def export_with_supabase_client(url, key, table_name='classifications'):
    """
    Enhanced Supabase export with better error handling
    """
    try:
        from supabase import create_client, Client
    except ImportError:
        print("❌ Supabase client not installed. Install with: pip install supabase")
        return None
    
    print(f"🔗 Connecting to Supabase at {url}...")
    supabase: Client = create_client(url, key)
    
    try:
        # Try different possible table names
        table_names = [table_name, 'expert_classifications', 'annotations', 'labels']
        
        for table in table_names:
            try:
                response = supabase.table(table).select("*").limit(1).execute()
                if response.data:
                    print(f"📊 Found data in table: {table}")
                    # Get all data
                    response = supabase.table(table).select("*").execute()
                    print(f"📊 Retrieved {len(response.data)} classifications")
                    
                    classifications = {}
                    for record in response.data:
                        image_name = (record.get('image_name') or 
                                    record.get('image_id') or 
                                    record.get('filename'))
                        if image_name:
                            classifications[image_name] = {
                                'category': record.get('category', 'unknown'),
                                'context': record.get('context', 'unknown'),
                                'specific_flag': record.get('specific_flag', 'unknown'),
                                'confidence': record.get('confidence', 4.0)
                            }
                    
                    return classifications
            except Exception as e:
                print(f"   Table '{table}' not found or accessible")
                continue
        
        raise Exception(f"No accessible tables found among: {table_names}")
        
    except Exception as e:
        print(f"❌ Error querying Supabase: {e}")
        return None

def convert_to_hierarchical_format(classifications):
    """
    Enhanced hierarchical format conversion with validation
    """
    print("🔄 Converting to hierarchical format...")
    
    processed = {}
    class_distribution = Counter()
    validation_issues = []
    
    for image_name, data in classifications.items():
        # Clean and standardize hierarchical components
        category = str(data['category']).replace(' ', '_').replace('-', '_').replace('/', '_')
        context = str(data['context']).replace(' ', '_').replace('-', '_').replace('/', '_')
        specific_flag = str(data['specific_flag']).replace(' ', '_').replace('-', '_').replace('/', '_')
        
        # Validation
        if category == 'unknown' or category == 'nan':
            validation_issues.append(f"Missing category for {image_name}")
        
        # Create hierarchical classname
        hierarchical_classname = f"{category}-{context}-{specific_flag}"
        
        processed[image_name] = {
            'category': category,
            'context': context,
            'specific_flag': specific_flag,
            'hierarchical_classname': hierarchical_classname,
            'confidence': float(data['confidence'])
        }
        
        class_distribution[hierarchical_classname] += 1
    
    print(f"✅ Processed {len(processed)} classifications")
    print(f"📊 Found {len(class_distribution)} unique hierarchical classes")
    
    if validation_issues:
        print(f"⚠️  Found {len(validation_issues)} validation issues:")
        for issue in validation_issues[:5]:  # Show first 5
            print(f"   {issue}")
        if len(validation_issues) > 5:
            print(f"   ... and {len(validation_issues) - 5} more")
    
    # Show class distribution
    print("🔝 Top 15 most common classes:")
    for i, (class_name, count) in enumerate(class_distribution.most_common(15)):
        print(f"   {i+1:2d}. {class_name}: {count} images")
    
    return processed, class_distribution

def save_for_training(processed_classifications, flag_data_dir):
    """
    Save in format exactly matching Li et al.'s expectations
    """
    print("💾 Saving training data...")
    
    # Save main annotations file
    annotations_file = flag_data_dir / "annotations.json"
    with open(annotations_file, 'w') as f:
        json.dump(processed_classifications, f, indent=2)
    print(f"✅ Saved annotations: {annotations_file}")
    
    # Create classnames.txt for reference
    unique_classes = set()
    for data in processed_classifications.values():
        unique_classes.add(data['hierarchical_classname'])
    
    classnames_file = flag_data_dir / "classnames.txt"
    with open(classnames_file, 'w') as f:
        for classname in sorted(unique_classes):
            f.write(f"{classname}\n")
    print(f"✅ Saved class names: {classnames_file}")
    
    # Create statistics file
    stats = {
        'total_images': len(processed_classifications),
        'total_classes': len(unique_classes),
        'min_confidence': min(d['confidence'] for d in processed_classifications.values()),
        'max_confidence': max(d['confidence'] for d in processed_classifications.values()),
        'avg_confidence': sum(d['confidence'] for d in processed_classifications.values()) / len(processed_classifications)
    }
    
    stats_file = flag_data_dir / "dataset_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved statistics: {stats_file}")
    
    return annotations_file, classnames_file

def validate_image_availability(processed_classifications, flag_data_dir):
    """
    Check which images are available and create missing image report
    """
    print("🖼️  Validating image availability...")
    
    image_dir = flag_data_dir / "images"
    available_images = []
    missing_images = []
    
    # Get list of available images
    if image_dir.exists():
        available_files = set(os.listdir(image_dir))
    else:
        available_files = set()
        print(f"⚠️  Image directory doesn't exist: {image_dir}")
    
    for image_name in processed_classifications.keys():
        if image_name in available_files:
            available_images.append(image_name)
        else:
            missing_images.append(image_name)
    
    print(f"📊 Image availability:")
    print(f"   Available: {len(available_images)}")
    print(f"   Missing: {len(missing_images)}")
    
    if missing_images:
        missing_file = flag_data_dir / "missing_images.txt"
        with open(missing_file, 'w') as f:
            for img in sorted(missing_images):
                f.write(f"{img}\n")
        print(f"📝 Missing images list saved to: {missing_file}")
        
        # Update processed classifications to only include available images
        filtered_classifications = {
            img: data for img, data in processed_classifications.items()
            if img in available_images
        }
        
        print(f"🔄 Filtered to {len(filtered_classifications)} images with available files")
        return filtered_classifications
    
    return processed_classifications

def create_training_config(flag_data_dir, total_classes):
    """
    Create training configuration optimized for M4 Max
    """
    config_content = f"""# Flag Classification Training Config - Week 9
# Optimized for M4 Max MacBook Pro

# Dataset configuration
DATASET:
  ROOT: "../data"
  NAME: "NIFlags"
  NUM_SHOTS: -1  # Use all available data

# Model configuration  
MODEL:
  NAME: "CoCoOp"
  BACKBONE:
    NAME: "RN50"  # Start with ResNet-50 for faster iteration
    
# Training configuration optimized for M4 Max
TRAIN:
  BATCH_SIZE: 32  # Optimal for RN50 on M4 Max
  LR: 0.002
  MAX_EPOCH: 50  # Start with 50 epochs for quick validation
  WEIGHT_DECAY: 5e-4
  WARMUP_EPOCH: 1
  WARMUP_TYPE: "constant"
  WARMUP_CONS_LR: 1e-5

# Few-shot configuration
DATASET:
  NUM_SHOTS: 16  # For few-shot experiments

# Output configuration
OUTPUT_DIR: "./experiments/niflags_initial"
SEED: 1

# Hierarchical prompt configuration (adapted from Li et al.)
TRAINER:
  COCOOP:
    N_CTX: 16  # Context length
    CSC: False  # Class-specific contexts
    CTX_INIT: "a photo of a flag"  # Initial context
    
# Classes: {total_classes} hierarchical flag classes
# Expected format: category-context-specific_flag
"""
    
    config_file = flag_data_dir / "training_config.yaml"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"⚙️  Created training config: {config_file}")
    return config_file

def create_training_commands(flag_data_dir):
    """
    Generate ready-to-run training commands for M4 Max
    """
    commands = f"""
# Flag Classification Training Commands - Week 9
# Copy and paste these commands to start training

# 1. Navigate to your working directory
cd {os.path.abspath('.')}

# 2. Activate your conda environment  
conda activate flag_classification

# 3. Initial validation run (5 epochs, quick test)
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_validation \\
    --max-epoch 5 \\
    --batch-size 16

# 4. Full training run (50 epochs)
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_rn50_50epochs \\
    --max-epoch 50 \\
    --batch-size 32

# 5. ViT-B/16 training (after RN50 validation)
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/vit_b16.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_vitb16_50epochs \\
    --max-epoch 50 \\
    --batch-size 24

# 6. Few-shot experiment (16-shot)
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_16shot \\
    --dataset-num-shots 16 \\
    --max-epoch 100 \\
    --batch-size 32

# Monitor training with:
# tensorboard --logdir experiments/
"""
    
    commands_file = flag_data_dir / "training_commands.sh"
    with open(commands_file, 'w') as f:
        f.write(commands)
    
    print(f"🚀 Training commands saved to: {commands_file}")
    return commands_file

def main():
    parser = argparse.ArgumentParser(description='Complete Flag Classification Data Setup')
    parser.add_argument('--export-method', choices=['csv', 'supabase'], required=True,
                       help='Method to export data from Supabase')
    parser.add_argument('--csv-path', type=str,
                       help='Path to CSV file (required if export-method is csv)')
    parser.add_argument('--supabase-url', type=str,
                       help='Supabase URL (required if export-method is supabase)')
    parser.add_argument('--supabase-key', type=str,
                       help='Supabase anon key (required if export-method is supabase)')
    parser.add_argument('--table-name', type=str, default='classifications',
                       help='Supabase table name (default: classifications)')
    
    args = parser.parse_args()
    
    print("🎯 FLAG CLASSIFICATION DATA SETUP - WEEK 9")
    print("=" * 60)
    
    try:
        # Step 1: Setup directory structure
        flag_data_dir = setup_data_structure()
        
        # Step 2: Export data
        print("\n📤 STEP 2: Exporting expert classifications...")
        if args.export_method == 'csv':
            if not args.csv_path:
                raise ValueError("--csv-path required for CSV export method")
            classifications = export_from_csv(args.csv_path)
        else:  # supabase
            if not args.supabase_url or not args.supabase_key:
                raise ValueError("--supabase-url and --supabase-key required for Supabase export")
            classifications = export_with_supabase_client(args.supabase_url, args.supabase_key, args.table_name)
        
        if not classifications:
            raise Exception("Failed to export any classifications")
        
        # Step 3: Convert to hierarchical format
        print("\n🔄 STEP 3: Converting to hierarchical format...")
        processed, distribution = convert_to_hierarchical_format(classifications)
        
        # Step 4: Validate image availability
        print("\n🖼️  STEP 4: Validating image availability...")
        processed = validate_image_availability(processed, flag_data_dir)
        
        # Step 5: Save training data
        print("\n💾 STEP 5: Saving training data...")
        annotations_file, classnames_file = save_for_training(processed, flag_data_dir)
        
        # Step 6: Create configuration files
        print("\n⚙️  STEP 6: Creating training configuration...")
        config_file = create_training_config(flag_data_dir, len(set(d['hierarchical_classname'] for d in processed.values())))
        
        # Step 7: Generate training commands
        print("\n🚀 STEP 7: Generating training commands...")
        commands_file = create_training_commands(flag_data_dir)
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 DATA SETUP COMPLETE!")
        print("=" * 60)
        print(f"✅ Processed {len(processed)} expert classifications")
        print(f"✅ Found {len(set(d['hierarchical_classname'] for d in processed.values()))} unique classes")
        print(f"✅ Data saved to: {flag_data_dir}")
        print(f"✅ Ready for training!")
        
        print("\n📋 NEXT STEPS:")
        print("1. Ensure your flag images are in:", flag_data_dir / "images")
        print("2. Review generated files:", flag_data_dir)
        print("3. Run validation command from:", commands_file)
        print("4. Monitor training progress and results")
        
        print("\n🎯 WEEK 9 MILESTONE: Data integration complete!")
        print("Focus next 2-3 days on initial training and validation.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
