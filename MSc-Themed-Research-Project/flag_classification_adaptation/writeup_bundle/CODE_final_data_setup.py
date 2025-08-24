#!/usr/bin/env python3
"""
Final Flag Classification Data Setup - Week 9
Optimized for your specific CSV structure and image organization

Based on analysis results:
- 9,305 expert classifications with 100% image availability
- Hierarchical structure: primary_category -> display_context -> specific_flag
- Images: *_box0.jpg (cropped flag regions) - perfect for training
"""

import argparse
import json
import os
import sys
import pandas as pd
import shutil
import glob
from pathlib import Path
from collections import defaultdict, Counter
from PIL import Image

def setup_data_structure():
    """Setup the exact directory structure needed for Li et al.'s code"""
    print("📁 Setting up data structure for training...")
    
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
        print(f"✅ Created: {dir_path}")
    
    return flag_data_dir

def load_and_process_csv():
    """Load your CSV with the correct column mappings"""
    print("📊 Loading and processing classifications.csv...")
    
    csv_path = "classifications.csv"
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} classifications")
    print(f"Columns: {list(df.columns)}")
    
    # Your exact column mappings from analysis
    column_mapping = {
        'image_id': 'image_id',
        'category': 'primary_category', 
        'context': 'display_context',
        'specific_flag': 'specific_flag',
        'confidence': 'confidence'
    }
    
    print(f"Using column mapping: {column_mapping}")
    
    # Filter out low-confidence and review categories
    print(f"Original rows: {len(df)}")
    
    # Remove "Review" category and low confidence
    df_filtered = df[
        (df[column_mapping['category']] != 'Review') & 
        (df[column_mapping['confidence']] >= 3.0)
    ].copy()
    
    print(f"After filtering: {len(df_filtered)} rows")
    print(f"Removed: {len(df) - len(df_filtered)} low-quality classifications")
    
    return df_filtered, column_mapping

def convert_to_hierarchical_format(df, column_mapping):
    """Convert to hierarchical format for Li et al.'s code"""
    print("🔄 Converting to hierarchical training format...")
    
    processed = {}
    class_distribution = Counter()
    
    for _, row in df.iterrows():
        image_name = str(row[column_mapping['image_id']]).strip()
        
        # Clean hierarchical components
        category = str(row[column_mapping['category']]).replace(' ', '_').replace('-', '_')
        context = str(row[column_mapping['context']]).replace(' ', '_').replace('-', '_')
        specific_flag = str(row[column_mapping['specific_flag']]).replace(' ', '_').replace('-', '_')
        
        # Create hierarchical classname: category-context-specific_flag
        hierarchical_classname = f"{category}-{context}-{specific_flag}"
        
        processed[image_name] = {
            'category': category,
            'context': context,
            'specific_flag': specific_flag,
            'hierarchical_classname': hierarchical_classname,
            'confidence': float(row[column_mapping['confidence']])
        }
        
        class_distribution[hierarchical_classname] += 1
    
    print(f"✅ Processed {len(processed)} classifications")
    print(f"📊 Found {len(class_distribution)} unique hierarchical classes")
    
    # Show top classes
    print("🔝 Top 10 most common hierarchical classes:")
    for i, (class_name, count) in enumerate(class_distribution.most_common(10)):
        print(f"   {i+1:2d}. {class_name}: {count} images")
    
    return processed, class_distribution

def is_decorated_filename(filename: str) -> bool:
    name = filename.lower()
    return (
        name.startswith("composite_")
        or name.startswith("masked_")
        or "_boxed" in name
    )


def copy_images_to_training_directory(
    processed_classifications,
    flag_data_dir,
    prefer_uncropped_originals: bool = True,
    exclude_decorated: bool = True,
    min_side: int = 224,
    source_dirs_override=None,
):
    """Copy the best available images to training directory"""
    print("🖼️  Copying images to training directory...")
    
    target_image_dir = flag_data_dir / "images"
    
    # Your image source directories (in priority order)
    source_dirs = source_dirs_override or [
        "../../public/images",      # Main processed images
        "../../data",               # Alternative location
        "../../flag_imagesCORRECT"  # Backup location
    ]
    
    # Build image index
    print("Building image file index...")
    image_index = {}  # filename -> full_path
    
    for source_dir in source_dirs:
        if os.path.exists(source_dir):
            print(f"  Scanning: {source_dir}")
            jpg_files = glob.glob(os.path.join(source_dir, "**", "*.jpg"), recursive=True)
            print(f"    Found {len(jpg_files)} images")
            
            for img_path in jpg_files:
                filename = os.path.basename(img_path)
                # Skip decorated files if requested
                if exclude_decorated and is_decorated_filename(filename):
                    continue
                if filename not in image_index:  # Keep first (highest priority)
                    image_index[filename] = img_path
    
    print(f"Total unique images available: {len(image_index)}")
    
    # Quality threshold
    MIN_SIDE = max(0, int(min_side or 0))  # 0 disables upscaling safeguard

    # Copy images for training
    copied_count = 0
    missing_count = 0
    missing_images = []
    upscaled_count = 0
    
    for image_name in list(processed_classifications.keys()):
        chosen_name = image_name
        chosen_path = None

        # Prefer the uncropped original if requested and if the key indicates a crop
        if prefer_uncropped_originals and image_name.endswith("_box0.jpg"):
            original_name = image_name.replace("_box0.jpg", ".jpg")
            if original_name in image_index:
                chosen_name = original_name
                chosen_path = image_index[original_name]

        # Fall back to the original key if not chosen yet
        if chosen_path is None and image_name in image_index:
            chosen_path = image_index[image_name]

        if chosen_path is not None:
            source_path = chosen_path
            target_path = target_image_dir / chosen_name

            # Ensure directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Apply min-side safeguard if enabled
            if MIN_SIDE > 0:
                try:
                    with Image.open(source_path) as im:
                        width, height = im.size
                        if min(width, height) < MIN_SIDE:
                            scale = MIN_SIDE / float(min(width, height))
                            new_w = int(round(width * scale))
                            new_h = int(round(height * scale))
                            upscaled = im.resize((new_w, new_h), Image.LANCZOS)
                            upscaled.save(target_path, format="JPEG", quality=95)
                            upscaled_count += 1
                        else:
                            if not target_path.exists():
                                shutil.copy2(source_path, target_path)
                except Exception:
                    if not target_path.exists():
                        shutil.copy2(source_path, target_path)
            else:
                if not target_path.exists():
                    shutil.copy2(source_path, target_path)

            copied_count += 1
        else:
            missing_count += 1
            missing_images.append(image_name)
    
    print(f"📊 Image copying results:")
    print(f"   ✅ Copied/Available: {copied_count}")
    print(f"   ❌ Missing: {missing_count}")
    print(f"   🔼 Upscaled (min side < {MIN_SIDE}px): {upscaled_count}")
    
    if missing_images:
        missing_file = flag_data_dir / "missing_images.txt"
        with open(missing_file, 'w') as f:
            for img in sorted(missing_images):
                f.write(f"{img}\n")
        print(f"📝 Missing images logged to: {missing_file}")
        
        # Remove missing images from processed classifications
        for img in missing_images:
            processed_classifications.pop(img, None)
        
        print(f"🔄 Updated dataset size: {len(processed_classifications)} images")
    
    return len(processed_classifications)

def save_training_annotations(processed_classifications, flag_data_dir):
    """Save annotations in Li et al.'s expected format"""
    print("💾 Saving training annotations...")
    
    # Save main annotations file (for our custom dataset loader)
    annotations_file = flag_data_dir / "annotations.json"
    with open(annotations_file, 'w') as f:
        json.dump(processed_classifications, f, indent=2)
    print(f"✅ Saved: {annotations_file}")
    
    # Create classnames.txt
    unique_classes = set()
    for data in processed_classifications.values():
        unique_classes.add(data['hierarchical_classname'])
    
    classnames_file = flag_data_dir / "classnames.txt"
    with open(classnames_file, 'w') as f:
        for classname in sorted(unique_classes):
            f.write(f"{classname}\n")
    print(f"✅ Saved: {classnames_file}")
    
    # Create dataset statistics
    stats = {
        'total_images': len(processed_classifications),
        'total_classes': len(unique_classes),
        'avg_confidence': sum(d['confidence'] for d in processed_classifications.values()) / len(processed_classifications),
        'hierarchical_structure': {
            'categories': len(set(d['category'] for d in processed_classifications.values())),
            'contexts': len(set(d['context'] for d in processed_classifications.values())),
            'specific_flags': len(set(d['specific_flag'] for d in processed_classifications.values()))
        }
    }
    
    stats_file = flag_data_dir / "dataset_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved: {stats_file}")
    
    return len(unique_classes)

def create_training_configs(flag_data_dir, total_images, total_classes):
    """Create optimized training configurations"""
    print("⚙️  Creating training configurations...")
    
    # Dataset config
    dataset_config = f"""# NIFlags Dataset Configuration
# {total_images} images, {total_classes} hierarchical classes

DATASET:
  NAME: "NIFlags"
  ROOT: "../data"
  NUM_SHOTS: -1  # Use all data initially
"""
    
    configs_dir = Path("configs/datasets")
    configs_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_config_file = configs_dir / "niflags.yaml"
    with open(dataset_config_file, 'w') as f:
        f.write(dataset_config)
    print(f"✅ Created: {dataset_config_file}")
    
    # Training commands
    commands = f"""#!/bin/bash
# Flag Classification Training Commands - Week 9
# {total_images} images, {total_classes} classes

# Activate environment
conda activate flag_classification

# 1. VALIDATION RUN (5 epochs, quick test)
echo "🧪 Running validation test..."
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_validation \\
    --max-epoch 5 \\
    --batch-size 16 \\
    --seed 1

# 2. FULL TRAINING - ResNet50 (50 epochs)
echo "🚀 Starting full RN50 training..."
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_rn50_full \\
    --max-epoch 50 \\
    --batch-size 32 \\
    --seed 1

# 3. ViT-B/16 TRAINING (after RN50 success)
echo "🎯 Starting ViT-B/16 training..."
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/vit_b16.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_vitb16 \\
    --max-epoch 50 \\
    --batch-size 24 \\
    --seed 1

# 4. FEW-SHOT EXPERIMENT (16-shot)
echo "🎲 Running few-shot experiment..."
python train.py \\
    --root ../data \\
    --dataset-config-file configs/datasets/niflags.yaml \\
    --config-file configs/trainers/CoCoOp/rn50.yaml \\
    --trainer CoCoOp \\
    --output-dir experiments/niflags_16shot \\
    --dataset-num-shots 16 \\
    --max-epoch 100 \\
    --batch-size 32 \\
    --seed 1

echo "✅ Training complete! Check results in experiments/ directory"
"""
    
    commands_file = flag_data_dir / "run_training.sh"
    with open(commands_file, 'w') as f:
        f.write(commands)
    os.chmod(commands_file, 0o755)  # Make executable
    print(f"✅ Created: {commands_file}")
    
    return dataset_config_file, commands_file

def build_arg_parser():
    parser = argparse.ArgumentParser(description="Prepare NI Flags dataset")
    parser.add_argument("--prefer-uncropped-originals", action="store_true", default=True,
                        help="Prefer uncropped originals (strip _box0) when available")
    parser.add_argument("--no-prefer-uncropped-originals", action="store_false", dest="prefer_uncropped_originals",
                        help="Disable preferring uncropped originals")
    parser.add_argument("--exclude-decorated", action="store_true", default=True,
                        help="Exclude composite_/masked_/_boxed files from sources")
    parser.add_argument("--include-decorated", action="store_false", dest="exclude_decorated",
                        help="Allow decorated files in sources (not recommended)")
    parser.add_argument("--min-side", type=int, default=224,
                        help="Minimum shorter-side pixels (0 disables upscaling)")
    return parser


def main():
    print("🎯 FINAL FLAG CLASSIFICATION DATA SETUP")
    print("=" * 60)
    print("Based on analysis: 9,305 classifications, 100% image availability")
    print("=" * 60)
    
    try:
        # Parse args
        parser = build_arg_parser()
        args = parser.parse_args([] if hasattr(sys, 'ps1') else None)

        print(f"Options: prefer_uncropped_originals={args.prefer_uncropped_originals}, "
              f"exclude_decorated={args.exclude_decorated}, min_side={args.min_side}")

        # Step 1: Setup directory structure
        flag_data_dir = setup_data_structure()
        
        # Step 2: Load and process CSV
        df, column_mapping = load_and_process_csv()
        
        # Step 3: Convert to hierarchical format
        processed, distribution = convert_to_hierarchical_format(df, column_mapping)
        
        # Step 4: Copy images to training directory
        final_image_count = copy_images_to_training_directory(
            processed,
            flag_data_dir,
            prefer_uncropped_originals=args.prefer_uncropped_originals,
            exclude_decorated=args.exclude_decorated,
            min_side=args.min_side,
        )
        
        # Step 5: Save training annotations
        total_classes = save_training_annotations(processed, flag_data_dir)
        
        # Step 6: Create training configurations
        dataset_config, commands_file = create_training_configs(flag_data_dir, final_image_count, total_classes)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 DATA SETUP COMPLETE!")
        print("=" * 60)
        print(f"✅ Final dataset: {final_image_count} images")
        print(f"✅ Hierarchical classes: {total_classes}")
        print(f"✅ Data directory: {flag_data_dir}")
        print(f"✅ Training config: {dataset_config}")
        print(f"✅ Training commands: {commands_file}")
        
        print("\n🚀 READY TO START TRAINING!")
        print("Run validation test:")
        print(f"  cd {os.path.abspath('.')}")
        print(f"  bash {commands_file}")
        
        print("\n📊 Expected Results:")
        print("- Validation (5 epochs): ~2-3 minutes on M4 Max")
        print("- Full training (50 epochs): ~45-60 minutes")
        print("- Hierarchical accuracy: Target >80% for this dataset size")
        
        print("\n🎯 WEEK 9 MILESTONE: ACHIEVED!")
        print("Data integration complete. Ready for Week 10 experiments.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
