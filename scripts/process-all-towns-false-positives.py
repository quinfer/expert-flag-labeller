#!/usr/bin/env python3
"""
Comprehensive processing of false positive data for all towns
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import sys

def get_available_towns():
    """Get list of all available towns from pickle files"""
    pickle_dir = Path("false_positive_checks")
    
    # Find all towns that have the required files
    towns = []
    
    for file in pickle_dir.glob("*list.pickle"):
        town_name = file.stem.replace("list", "")
        
        # Check if this town has all required files
        results_file = pickle_dir / f"{town_name}results.pickle"
        correct_file = pickle_dir / f"{town_name}resultsCORRECT.pickle"
        
        if results_file.exists() and correct_file.exists():
            towns.append(town_name)
        else:
            print(f"⚠️  Town {town_name} missing required files - skipping")
    
    return sorted(towns)

def load_town_data(town_name):
    """Load all three pickle files for a specific town"""
    print(f"📂 Loading data for {town_name}...")
    
    base_path = Path("false_positive_checks")
    
    try:
        # Load list of image paths
        with open(base_path / f"{town_name}list.pickle", 'rb') as f:
            image_paths = pickle.load(f)
        
        # Load CV results
        with open(base_path / f"{town_name}results.pickle", 'rb') as f:
            cv_results = pickle.load(f)
        
        # Load manual corrections
        manual_corrections = pd.read_pickle(base_path / f"{town_name}resultsCORRECT.pickle")
        
        print(f"✅ {town_name}: {len(image_paths)} paths, CV shape: {cv_results.shape}, Manual shape: {manual_corrections.shape}")
        
        return image_paths, cv_results, manual_corrections
        
    except Exception as e:
        print(f"❌ Error loading {town_name}: {e}")
        return None, None, None

def analyze_town_corrections(town_name, df):
    """Analyze the manually corrected data for a specific town"""
    print(f"\n📊 ANALYSIS FOR {town_name}:")
    print(f"{'='*50}")
    
    # Analyze the flags_correct column
    correct_flags = df['flags_correct'].value_counts().sort_index()
    print(f"📋 Manual classification results:")
    total = len(df)
    
    true_positives = correct_flags.get(1, 0)
    false_positives = correct_flags.get(0, 0)
    
    print(f"   TRUE POSITIVES: {true_positives:,} ({true_positives/total*100:.1f}%)")
    print(f"   FALSE POSITIVES: {false_positives:,} ({false_positives/total*100:.1f}%)")
    
    # Calculate changes from CV to manual
    if 'flags' in df.columns:
        original_tp = len(df[df['flags'] == 1])
        manual_tp = true_positives
        
        print(f"   Original CV flagged: {original_tp:,} true positives")
        print(f"   Manual correction: {manual_tp:,} true positives")
        print(f"   Correction impact: {manual_tp - original_tp:+,} images")
    
    return {
        'total_images': total,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'original_cv_tp': original_tp if 'flags' in df.columns else 0,
        'manual_tp': true_positives,
        'fp_rate': false_positives / total * 100
    }

def create_town_mapping(town_name, df):
    """Create filtering mapping for a specific town"""
    true_positives = []
    false_positives = []
    
    for _, row in df.iterrows():
        # Handle different filename formats
        filename = str(row['f'])
        if not filename.endswith('.jpg'):
            filename += '.jpg'
        
        is_true_positive = row['flags_correct'] == 1
        
        if is_true_positive:
            true_positives.append(filename)
        else:
            false_positives.append(filename)
    
    # Sort for consistency
    true_positives.sort()
    false_positives.sort()
    
    return {
        'town': town_name,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'total_images': len(true_positives) + len(false_positives),
        'metadata': {
            'source': 'manual_corrections',
            'processed_date': datetime.now().isoformat(),
            'true_positive_count': len(true_positives),
            'false_positive_count': len(false_positives),
            'false_positive_rate': len(false_positives) / (len(true_positives) + len(false_positives)) * 100
        }
    }

def save_town_data(town_name, mapping):
    """Save filtering data for a specific town"""
    # Create town-specific directory
    town_dir = Path("src/data/towns")
    town_dir.mkdir(exist_ok=True)
    
    # Save comprehensive mapping
    town_file = town_dir / f"{town_name.lower().replace(' ', '_')}.json"
    with open(town_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✅ Saved {town_name} data to: {town_file}")
    
    return town_file

def process_single_town(town_name):
    """Process a single town's false positive data"""
    print(f"\n🎯 PROCESSING {town_name}")
    print("="*60)
    
    # Load data
    image_paths, cv_results, manual_corrections = load_town_data(town_name)
    
    if manual_corrections is None:
        print(f"❌ Skipping {town_name} - failed to load data")
        return None
    
    # Analyze corrections
    stats = analyze_town_corrections(town_name, manual_corrections)
    
    # Create mapping
    mapping = create_town_mapping(town_name, manual_corrections)
    
    # Save data
    town_file = save_town_data(town_name, mapping)
    
    # Return stats for aggregation
    return {
        'town': town_name,
        'file': str(town_file),
        **stats
    }

def create_comprehensive_filter():
    """Create a comprehensive filter combining all towns"""
    print(f"\n🌍 CREATING COMPREHENSIVE FILTER")
    print("="*60)
    
    towns_dir = Path("src/data/towns")
    all_false_positives = []
    all_true_positives = []
    town_stats = []
    
    # Aggregate all town data
    for town_file in towns_dir.glob("*.json"):
        with open(town_file, 'r') as f:
            town_data = json.load(f)
        
        town_name = town_data['town']
        false_positives = town_data['false_positives']
        true_positives = town_data['true_positives']
        
        all_false_positives.extend(false_positives)
        all_true_positives.extend(true_positives)
        
        town_stats.append({
            'town': town_name,
            'false_positives': len(false_positives),
            'true_positives': len(true_positives),
            'total': len(false_positives) + len(true_positives),
            'fp_rate': town_data['metadata']['false_positive_rate']
        })
    
    # Create comprehensive mapping
    comprehensive_filter = {
        'false_positives': sorted(list(set(all_false_positives))),
        'true_positives': sorted(list(set(all_true_positives))),
        'metadata': {
            'total_towns': len(town_stats),
            'total_false_positives': len(set(all_false_positives)),
            'total_true_positives': len(set(all_true_positives)),
            'total_images': len(set(all_false_positives)) + len(set(all_true_positives)),
            'overall_fp_rate': len(set(all_false_positives)) / (len(set(all_false_positives)) + len(set(all_true_positives))) * 100,
            'processed_date': datetime.now().isoformat(),
            'town_breakdown': town_stats
        }
    }
    
    # Save comprehensive filter
    comprehensive_file = Path("src/data/false-positives-comprehensive.json")
    with open(comprehensive_file, 'w') as f:
        json.dump(comprehensive_filter, f, indent=2)
    
    # Save lookup-only version for performance
    lookup_file = Path("src/data/false-positives-lookup-all.json")
    lookup_data = {
        'false_positives': comprehensive_filter['false_positives'],
        'count': len(comprehensive_filter['false_positives']),
        'metadata': {
            'total_towns': comprehensive_filter['metadata']['total_towns'],
            'overall_fp_rate': comprehensive_filter['metadata']['overall_fp_rate']
        }
    }
    
    with open(lookup_file, 'w') as f:
        json.dump(lookup_data, f, indent=2)
    
    print(f"✅ Comprehensive filter saved to: {comprehensive_file}")
    print(f"✅ Lookup file saved to: {lookup_file}")
    
    # Print summary
    print(f"\n📊 COMPREHENSIVE SUMMARY:")
    print(f"   Total towns processed: {len(town_stats)}")
    print(f"   Total images analyzed: {comprehensive_filter['metadata']['total_images']:,}")
    print(f"   False positives: {comprehensive_filter['metadata']['total_false_positives']:,}")
    print(f"   True positives: {comprehensive_filter['metadata']['total_true_positives']:,}")
    print(f"   Overall false positive rate: {comprehensive_filter['metadata']['overall_fp_rate']:.1f}%")
    
    return comprehensive_filter

def main():
    """Main processing function"""
    print("🎯 COMPREHENSIVE FALSE POSITIVE PROCESSING")
    print("="*60)
    
    # Get available towns
    towns = get_available_towns()
    print(f"📍 Found {len(towns)} towns to process:")
    for i, town in enumerate(towns, 1):
        print(f"   {i:2d}. {town}")
    
    # Process each town
    all_stats = []
    
    for i, town in enumerate(towns, 1):
        print(f"\n🏘️  Processing town {i}/{len(towns)}: {town}")
        
        try:
            stats = process_single_town(town)
            if stats:
                all_stats.append(stats)
            print(f"✅ Completed {town}")
        except Exception as e:
            print(f"❌ Error processing {town}: {e}")
            continue
    
    # Create comprehensive filter
    if all_stats:
        comprehensive_filter = create_comprehensive_filter()
        
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"   Successfully processed: {len(all_stats)}/{len(towns)} towns")
        print(f"   Total false positives identified: {comprehensive_filter['metadata']['total_false_positives']:,}")
        print(f"   Ready for integration into app filtering system!")
    else:
        print(f"\n❌ No towns were successfully processed!")

if __name__ == "__main__":
    main() 