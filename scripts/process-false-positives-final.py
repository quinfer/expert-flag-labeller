#!/usr/bin/env python3
"""
Final processing of false positive data using manual corrections
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import json

def load_all_data():
    """Load all three pickle files"""
    print("📂 Loading all false positive data files...")
    
    # Load list of image paths
    with open("false_positive_checks/ENNISKILLENlist.pickle", 'rb') as f:
        image_paths = pickle.load(f)
    
    # Load CV results
    with open("false_positive_checks/ENNISKILLENresults.pickle", 'rb') as f:
        cv_results = pickle.load(f)
    
    # Load manual corrections
    manual_corrections = pd.read_pickle("false_positive_checks/ENNISKILLENresultsCORRECT.pickle")
    
    print(f"✅ Loaded {len(image_paths)} image paths")
    print(f"✅ Loaded CV results: {cv_results.shape}")
    print(f"✅ Loaded manual corrections: {manual_corrections.shape}")
    
    return image_paths, cv_results, manual_corrections

def analyze_manual_corrections(df):
    """Analyze the manually corrected data"""
    print(f"\n📊 MANUAL CORRECTIONS ANALYSIS:")
    print(f"{'='*50}")
    
    # Analyze the flags_correct column (this should be the authoritative classification)
    correct_flags = df['flags_correct'].value_counts().sort_index()
    print(f"📋 Manual classification results (flags_correct):")
    total = len(df)
    for value, count in correct_flags.items():
        percentage = (count / total) * 100
        status = "TRUE POSITIVE" if value == 1 else "FALSE POSITIVE"
        print(f"   {value} ({status}): {count:,} images ({percentage:.1f}%)")
    
    # Compare original flags vs corrected flags
    print(f"\n🔄 Comparison: Original CV vs Manual Corrections:")
    comparison = pd.crosstab(df['flags'], df['flags_correct'], margins=True)
    print(comparison)
    
    # Calculate how many classifications were changed
    changed = df[df['flags'] != df['flags_correct']]
    print(f"\n📝 Classification changes:")
    print(f"   Total images: {len(df):,}")
    print(f"   Classifications changed: {len(changed):,} ({len(changed)/len(df)*100:.1f}%)")
    print(f"   Classifications unchanged: {len(df) - len(changed):,} ({(len(df) - len(changed))/len(df)*100:.1f}%)")
    
    return df

def create_final_mapping(df):
    """Create the final authoritative mapping using manual corrections"""
    print(f"\n🎯 CREATING FINAL AUTHORITATIVE MAPPING:")
    print(f"{'='*50}")
    
    # Use flags_correct as the authoritative source
    true_positives = []
    false_positives = []
    
    for _, row in df.iterrows():
        filename = str(row['f']) + '.jpg'  # Ensure .jpg extension
        is_true_positive = row['flags_correct'] == 1
        
        if is_true_positive:
            true_positives.append(filename)
        else:
            false_positives.append(filename)
    
    # Sort for consistency
    true_positives.sort()
    false_positives.sort()
    
    print(f"📊 Final results:")
    print(f"   True positives: {len(true_positives):,}")
    print(f"   False positives: {len(false_positives):,}")
    print(f"   Total images: {len(true_positives) + len(false_positives):,}")
    
    # Calculate the improvement from using manual corrections
    original_tp = len(df[df['flags'] == 1])
    corrected_tp = len(true_positives)
    print(f"   Original CV true positives: {original_tp:,}")
    print(f"   After manual correction: {corrected_tp:,}")
    print(f"   Improvement: {corrected_tp - original_tp:+,} images")
    
    return {
        'true_positives': true_positives,
        'false_positives': false_positives,
        'total_images': len(true_positives) + len(false_positives),
        'metadata': {
            'source': 'manual_corrections',
            'town': 'ENNISKILLEN',
            'original_cv_true_positives': original_tp,
            'manual_corrected_true_positives': corrected_tp,
            'improvement': corrected_tp - original_tp
        }
    }

def save_filtering_data(mapping):
    """Save the data for integration into the app"""
    print(f"\n💾 SAVING FILTERING DATA:")
    print(f"{'='*50}")
    
    # Save comprehensive mapping
    output_file = "src/data/false-positives-enniskillen.json"
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✅ Saved to: {output_file}")
    
    # Also save just the false positives list for quick lookup
    false_positives_only = {
        'false_positives': mapping['false_positives'],
        'count': len(mapping['false_positives'])
    }
    
    fp_file = "src/data/false-positives-lookup.json"
    with open(fp_file, 'w') as f:
        json.dump(false_positives_only, f, indent=2)
    
    print(f"✅ Saved lookup file to: {fp_file}")
    
    # Show sample data
    print(f"\n📝 Sample false positives to be filtered out:")
    for i, fp in enumerate(mapping['false_positives'][:10]):
        print(f"   {i+1}. {fp}")
    
    print(f"\n📝 Sample true positives to keep:")
    for i, tp in enumerate(mapping['true_positives'][:10]):
        print(f"   {i+1}. {tp}")

def verify_with_current_images():
    """Verify the mapping against images currently being served"""
    print(f"\n🔍 VERIFYING AGAINST CURRENT SERVED IMAGES:")
    print(f"{'='*50}")
    
    try:
        # Load current static images
        with open("src/data/static-images.json", 'r') as f:
            current_images = json.load(f)
        
        # Extract filenames from current images
        current_filenames = set()
        for img in current_images:
            filename = Path(img['path']).name
            current_filenames.add(filename)
        
        # Load our false positives
        with open("src/data/false-positives-enniskillen.json", 'r') as f:
            fp_data = json.load(f)
        
        false_positive_set = set(fp_data['false_positives'])
        
        # Check overlap
        overlap = current_filenames.intersection(false_positive_set)
        
        print(f"📊 Verification results:")
        print(f"   Images currently served: {len(current_filenames):,}")
        print(f"   False positives identified: {len(false_positive_set):,}")
        print(f"   Overlap (images to filter): {len(overlap):,}")
        
        if overlap:
            print(f"\n📝 Sample images that should be filtered:")
            for i, img in enumerate(list(overlap)[:10]):
                print(f"   {i+1}. {img}")
        
        return len(overlap)
        
    except Exception as e:
        print(f"⚠️  Could not verify against current images: {e}")
        return 0

def main():
    """Main processing function"""
    print("🎯 FINAL FALSE POSITIVE PROCESSING")
    print("="*60)
    
    try:
        # Load all data
        image_paths, cv_results, manual_corrections = load_all_data()
        
        # Analyze manual corrections
        df = analyze_manual_corrections(manual_corrections)
        
        # Create final mapping
        mapping = create_final_mapping(df)
        
        # Save for integration
        save_filtering_data(mapping)
        
        # Verify against current images
        overlap_count = verify_with_current_images()
        
        print(f"\n🎉 SUCCESS!")
        print(f"{'='*60}")
        print(f"✅ Processed {mapping['total_images']:,} images")
        print(f"✅ Identified {len(mapping['false_positives']):,} false positives")
        print(f"✅ Identified {len(mapping['true_positives']):,} true positives")
        if overlap_count > 0:
            print(f"⚠️  {overlap_count:,} currently served images should be filtered")
        print(f"✅ Ready for integration into the app!")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 