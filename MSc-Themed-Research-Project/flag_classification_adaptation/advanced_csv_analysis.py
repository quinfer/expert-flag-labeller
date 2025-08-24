#!/usr/bin/env python3
"""
Updated CSV and Image Analysis for Flag Classification
Handles the complex directory structure with location-based organization
"""
import pandas as pd
import os
import glob
from collections import Counter, defaultdict
from pathlib import Path

def analyze_csv_structure():
    """Analyze the CSV structure and extract key information"""
    print("📊 ANALYZING CSV STRUCTURE")
    print("=" * 50)
    
    csv_path = "classifications.csv"
    
    # Read sample to understand structure
    sample_df = pd.read_csv(csv_path, nrows=5)
    print(f"Columns: {list(sample_df.columns)}")
    
    # Read full CSV
    df = pd.read_csv(csv_path)
    print(f"Total classifications: {len(df)}")
    
    # Identify key columns
    image_id_col = None
    category_col = None
    context_col = None
    flag_col = None
    confidence_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'image' in col_lower and ('id' in col_lower or 'name' in col_lower):
            image_id_col = col
        elif 'category' in col_lower:
            category_col = col
        elif 'context' in col_lower:
            context_col = col
        elif 'flag' in col_lower and 'specific' in col_lower:
            flag_col = col
        elif 'confidence' in col_lower or 'score' in col_lower:
            confidence_col = col
    
    print(f"\n🔍 Detected columns:")
    print(f"  Image ID: {image_id_col}")
    print(f"  Category: {category_col}")
    print(f"  Context: {context_col}")
    print(f"  Specific Flag: {flag_col}")
    print(f"  Confidence: {confidence_col}")
    
    # Show sample data
    print(f"\n📋 Sample data:")
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        print(f"\nRow {i+1}:")
        for col in [image_id_col, category_col, context_col, flag_col, confidence_col]:
            if col:
                print(f"  {col}: {row[col]}")
    
    # Analyze hierarchical structure
    if category_col:
        print(f"\n🏗️ HIERARCHICAL STRUCTURE")
        print(f"Categories ({df[category_col].nunique()} unique):")
        for cat, count in df[category_col].value_counts().head(10).items():
            print(f"  {cat}: {count}")
    
    if context_col:
        print(f"\nContexts ({df[context_col].nunique()} unique):")
        for ctx, count in df[context_col].value_counts().head(10).items():
            print(f"  {ctx}: {count}")
    
    if flag_col:
        print(f"\nSpecific Flags ({df[flag_col].nunique()} unique):")
        for flag, count in df[flag_col].value_counts().head(10).items():
            print(f"  {flag}: {count}")
    
    return df, image_id_col, category_col, context_col, flag_col, confidence_col

def find_images_in_directory_structure():
    """Find all images in the complex directory structure"""
    print(f"\n🔍 SCANNING IMAGE DIRECTORY STRUCTURE")
    print("=" * 50)
    
    # Check both possible image locations
    image_base_paths = [
        "../../public/images",  # Main processed images
        "../../flag_imagesCORRECT",  # Alternative location
        "../../data"  # Data directory
    ]
    
    all_images = {}  # filename -> full_path
    location_stats = defaultdict(int)
    
    for base_path in image_base_paths:
        if os.path.exists(base_path):
            print(f"📁 Scanning: {base_path}")
            
            # Find all jpg files recursively
            jpg_files = glob.glob(os.path.join(base_path, "**", "*.jpg"), recursive=True)
            print(f"  Found {len(jpg_files)} .jpg files")
            
            for img_path in jpg_files:
                filename = os.path.basename(img_path)
                relative_path = os.path.relpath(img_path, base_path)
                location = os.path.dirname(relative_path) if os.path.dirname(relative_path) else "root"
                
                all_images[filename] = img_path
                location_stats[location] += 1
        else:
            print(f"❌ Not found: {base_path}")
    
    print(f"\n📊 Image inventory:")
    print(f"  Total image files: {len(all_images)}")
    print(f"  Locations: {len(location_stats)}")
    
    # Show top locations
    print(f"\nTop 10 locations by image count:")
    for location, count in sorted(location_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {location}: {count} images")
    
    # Analyze filename patterns
    print(f"\n🔤 Filename patterns:")
    
    # Count different file suffixes
    suffix_patterns = Counter()
    base_id_patterns = Counter()
    
    for filename in all_images.keys():
        # Extract patterns like _000_box0.jpg, _060.jpg, etc.
        if '_box' in filename:
            suffix_patterns['_boxN.jpg (cropped flags)'] += 1
        elif filename.startswith('composite_'):
            suffix_patterns['composite_*.jpg'] += 1
        elif any(angle in filename for angle in ['_000', '_060', '_120', '_180', '_240', '_300']):
            suffix_patterns['_angle.jpg (street view angles)'] += 1
        else:
            suffix_patterns['other'] += 1
            
        # Extract base ID (everything before last underscore and angle)
        parts = filename.replace('.jpg', '').split('_')
        if len(parts) >= 2:
            # This should be the hash ID like "F6AsbXhdt2Gk6sG5aI4W4w"
            base_id = parts[0]
            base_id_patterns[base_id] += 1
    
    print(f"File type patterns:")
    for pattern, count in suffix_patterns.most_common():
        print(f"  {pattern}: {count}")
    
    print(f"\nUnique base IDs (hash patterns): {len(base_id_patterns)}")
    print(f"Sample base IDs: {list(base_id_patterns.keys())[:5]}")
    
    return all_images, base_id_patterns

def match_csv_to_images(df, image_id_col, all_images, base_id_patterns):
    """Match CSV records to available image files"""
    print(f"\n🔗 MATCHING CSV TO IMAGES")
    print("=" * 50)
    
    if not image_id_col:
        print("❌ No image ID column found in CSV")
        return {}
    
    matches = {}
    match_strategies = {
        'direct': 0,
        'without_extension': 0,
        'base_id_match': 0,
        'no_match': 0
    }
    
    # Get sample of image IDs from CSV
    sample_csv_ids = df[image_id_col].dropna().head(20).tolist()
    
    print(f"Testing with {len(sample_csv_ids)} sample CSV image IDs...")
    
    for csv_id in sample_csv_ids:
        csv_id_str = str(csv_id).strip()
        found_match = False
        
        # Strategy 1: Direct filename match
        if csv_id_str in all_images:
            matches[csv_id_str] = all_images[csv_id_str]
            match_strategies['direct'] += 1
            found_match = True
            print(f"  ✅ Direct: {csv_id_str}")
        
        # Strategy 2: Without extension
        elif csv_id_str.replace('.jpg', '').replace('.jpeg', '') + '.jpg' in all_images:
            clean_id = csv_id_str.replace('.jpg', '').replace('.jpeg', '') + '.jpg'
            matches[csv_id_str] = all_images[clean_id]
            match_strategies['without_extension'] += 1
            found_match = True
            print(f"  ✅ No ext: {csv_id_str} -> {clean_id}")
        
        # Strategy 3: Base ID matching (extract hash part)
        else:
            # Try to extract base hash ID from CSV ID
            csv_base_id = csv_id_str.split('_')[0] if '_' in csv_id_str else csv_id_str.replace('.jpg', '')
            
            # Look for any image with this base ID
            matching_images = [fname for fname in all_images.keys() if fname.startswith(csv_base_id)]
            
            if matching_images:
                # Prefer _box0 versions (cropped flags) if available
                box_images = [fname for fname in matching_images if '_box0' in fname]
                if box_images:
                    matches[csv_id_str] = all_images[box_images[0]]
                    print(f"  ✅ Base+box: {csv_id_str} -> {box_images[0]}")
                else:
                    matches[csv_id_str] = all_images[matching_images[0]]
                    print(f"  ✅ Base: {csv_id_str} -> {matching_images[0]}")
                match_strategies['base_id_match'] += 1
                found_match = True
        
        if not found_match:
            match_strategies['no_match'] += 1
            print(f"  ❌ No match: {csv_id_str}")
    
    # Calculate success rates
    total_tested = len(sample_csv_ids)
    success_rate = (total_tested - match_strategies['no_match']) / total_tested * 100
    
    print(f"\n📊 MATCHING RESULTS:")
    print(f"  Sample size: {total_tested}")
    print(f"  Direct matches: {match_strategies['direct']}")
    print(f"  Extension fixes: {match_strategies['without_extension']}")
    print(f"  Base ID matches: {match_strategies['base_id_match']}")
    print(f"  No matches: {match_strategies['no_match']}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    # Estimate for full dataset
    estimated_matches = int(len(df) * (success_rate / 100))
    print(f"  Estimated total matches: ~{estimated_matches} out of {len(df)}")
    
    return matches, success_rate, match_strategies

def generate_setup_recommendations(df, success_rate, image_id_col, category_col, context_col, flag_col):
    """Generate specific setup recommendations based on analysis"""
    print(f"\n🎯 SETUP RECOMMENDATIONS")
    print("=" * 50)
    
    if success_rate > 80:
        print("✅ EXCELLENT image availability! Ready for training setup.")
        
        print(f"\n📋 Next steps:")
        print(f"1. Run the complete data setup:")
        print(f"   python complete_data_setup.py --export-method csv --csv-path classifications.csv")
        
        print(f"\n2. Update image search paths in the setup to include:")
        print(f"   - ../../public/images (main processed images)")
        print(f"   - ../../flag_imagesCORRECT (alternative images)")
        
        print(f"\n3. Configuration for your hierarchical structure:")
        print(f"   Category column: {category_col}")
        print(f"   Context column: {context_col}")
        print(f"   Specific flag column: {flag_col}")
        
        print(f"\n4. Recommended image preference order:")
        print(f"   1st choice: *_box0.jpg (cropped flag regions)")
        print(f"   2nd choice: composite_*.jpg (composite views)")
        print(f"   3rd choice: *_000.jpg (front-facing street view)")
        
    elif success_rate > 50:
        print("⚠️ GOOD image availability. Minor path adjustments needed.")
        
        print(f"\n🔧 Required fixes:")
        print(f"1. Update image search paths in training scripts")
        print(f"2. Implement base ID matching logic")
        print(f"3. Set preference for _box0.jpg files (cropped flags)")
        
    else:
        print("❌ LOW image availability. Investigation required.")
        
        print(f"\n🔍 Debug steps:")
        print(f"1. Verify CSV image ID format matches actual filenames")
        print(f"2. Check if additional image processing is needed")
        print(f"3. Consider using alternative matching strategies")
    
    print(f"\n📊 Training dataset estimate:")
    estimated_images = int(len(df) * (success_rate / 100))
    if estimated_images > 2000:
        print(f"   🎉 Excellent: ~{estimated_images} images - robust training possible")
    elif estimated_images > 1000:
        print(f"   ✅ Good: ~{estimated_images} images - solid training dataset")
    elif estimated_images > 500:
        print(f"   ⚠️ Moderate: ~{estimated_images} images - consider data augmentation")
    else:
        print(f"   ❌ Limited: ~{estimated_images} images - may need more data")

def main():
    print("🎯 FLAG CLASSIFICATION: CSV & IMAGE ANALYSIS")
    print("=" * 60)
    
    # Step 1: Analyze CSV structure
    df, image_id_col, category_col, context_col, flag_col, confidence_col = analyze_csv_structure()
    
    # Step 2: Find all available images
    all_images, base_id_patterns = find_images_in_directory_structure()
    
    # Step 3: Match CSV to images
    matches, success_rate, strategies = match_csv_to_images(df, image_id_col, all_images, base_id_patterns)
    
    # Step 4: Generate recommendations
    generate_setup_recommendations(df, success_rate, image_id_col, category_col, context_col, flag_col)
    
    print(f"\n" + "=" * 60)
    print("🎉 ANALYSIS COMPLETE!")
    print("Use the recommendations above to proceed with data setup.")
    
    return {
        'df': df,
        'image_columns': {
            'image_id': image_id_col,
            'category': category_col,
            'context': context_col,
            'flag': flag_col,
            'confidence': confidence_col
        },
        'image_stats': {
            'total_images': len(all_images),
            'unique_base_ids': len(base_id_patterns),
            'success_rate': success_rate
        },
        'matches': matches
    }

if __name__ == "__main__":
    main()
