#!/usr/bin/env python3
"""
Create expert-confirmed dataset from all towns
Logic: indicator='1.0' (expert-reviewed) with flags_correct as actual flag count
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def get_available_towns():
    """Get list of all available towns from pickle files"""
    pickle_dir = Path("false_positive_checks")
    
    towns = []
    for file in pickle_dir.glob("*list.pickle"):
        town_name = file.stem.replace("list", "")
        
        # Check if this town has the corrected file
        correct_file = pickle_dir / f"{town_name}resultsCORRECT.pickle"
        
        if correct_file.exists():
            towns.append(town_name)
        else:
            print(f"⚠️  Town {town_name} missing corrected file - skipping")
    
    return sorted(towns)

def process_town_expert_confirmed(town_name):
    """Extract expert-confirmed images for a specific town"""
    print(f"\n🏘️  Processing {town_name}...")
    
    try:
        # Load the corrected data
        df = pd.read_pickle(f"false_positive_checks/{town_name}resultsCORRECT.pickle")
        
        # Extract expert-confirmed images (indicator='1.0')
        expert_confirmed = df[df['indicator'] == '1.0']
        
        print(f"   📊 Total images in {town_name}: {len(df):,}")
        print(f"   ✅ Expert-confirmed images: {len(expert_confirmed):,}")
        
        if len(expert_confirmed) == 0:
            print(f"   ⚠️  No expert-confirmed images found in {town_name}")
            return None
        
        # Analyze flag counts
        flag_counts = expert_confirmed['flags_correct'].value_counts().sort_index()
        print(f"   📋 Flag distribution:")
        for flag_count, image_count in flag_counts.items():
            print(f"      {flag_count} flags: {image_count:,} images")
        
        # Create the dataset entries
        expert_images = []
        for _, row in expert_confirmed.iterrows():
            filename = str(row['f'])
            if not filename.endswith('.jpg'):
                filename += '.jpg'
            
            expert_images.append({
                'filename': filename,
                'town': town_name,
                'pano_id': str(row['pano_id']),
                'flags_count': int(row['flags_correct']),
                'original_flags': int(row['flags']) if pd.notna(row['flags']) else 0
            })
        
        # Sort by filename for consistency
        expert_images.sort(key=lambda x: x['filename'])
        
        return {
            'town': town_name,
            'expert_confirmed_count': len(expert_confirmed),
            'total_images': len(df),
            'flag_distribution': {int(k): int(v) for k, v in dict(flag_counts).items()},
            'images': expert_images
        }
        
    except Exception as e:
        print(f"   ❌ Error processing {town_name}: {e}")
        return None

def create_comprehensive_expert_dataset():
    """Create comprehensive expert-confirmed dataset from all towns"""
    print("🎯 CREATING COMPREHENSIVE EXPERT-CONFIRMED DATASET")
    print("="*60)
    
    # Get all available towns
    towns = get_available_towns()
    print(f"📍 Found {len(towns)} towns to process")
    
    all_expert_images = []
    town_summaries = []
    total_expert_images = 0
    overall_flag_distribution = {}
    
    # Process each town
    for i, town in enumerate(towns, 1):
        print(f"\n[{i}/{len(towns)}] Processing {town}...")
        
        result = process_town_expert_confirmed(town)
        if result:
            town_summaries.append({
                'town': result['town'],
                'expert_confirmed': int(result['expert_confirmed_count']),
                'total_images': int(result['total_images']),
                'percentage': float((result['expert_confirmed_count'] / result['total_images']) * 100),
                'flag_distribution': result['flag_distribution']
            })
            
            # Add to overall dataset
            all_expert_images.extend(result['images'])
            total_expert_images += result['expert_confirmed_count']
            
            # Aggregate flag distribution (convert numpy types to native Python)
            for flag_count, count in result['flag_distribution'].items():
                flag_count_int = int(flag_count)
                count_int = int(count)
                overall_flag_distribution[flag_count_int] = overall_flag_distribution.get(flag_count_int, 0) + count_int
            
            print(f"   ✅ Added {result['expert_confirmed_count']:,} expert-confirmed images")
        else:
            print(f"   ❌ Failed to process {town}")
    
    # Create comprehensive dataset
    comprehensive_dataset = {
        'metadata': {
            'created_date': datetime.now().isoformat(),
            'logic': 'indicator="1.0" (expert-confirmed images)',
            'total_towns': int(len(town_summaries)),
            'total_expert_confirmed_images': int(total_expert_images),
            'overall_flag_distribution': {int(k): int(v) for k, v in sorted(overall_flag_distribution.items())},
            'town_breakdown': town_summaries
        },
        'images': all_expert_images
    }
    
    return comprehensive_dataset

def save_expert_dataset(dataset):
    """Save the expert-confirmed dataset"""
    print(f"\n💾 SAVING EXPERT-CONFIRMED DATASET")
    print("="*60)
    
    # Save comprehensive dataset
    comprehensive_file = "src/data/expert-confirmed-comprehensive.json"
    with open(comprehensive_file, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    # Create lookup version for app integration
    lookup_data = {
        'expert_confirmed_images': [img['filename'] for img in dataset['images']],
        'count': len(dataset['images']),
        'metadata': {
            'total_towns': dataset['metadata']['total_towns'],
            'flag_distribution': dataset['metadata']['overall_flag_distribution'],
            'logic': dataset['metadata']['logic']
        }
    }
    
    lookup_file = "src/data/expert-confirmed-lookup.json"
    with open(lookup_file, 'w') as f:
        json.dump(lookup_data, f, indent=2)
    
    # Create detailed mapping for the app
    detailed_mapping = {}
    for img in dataset['images']:
        detailed_mapping[img['filename']] = {
            'town': img['town'],
            'flags_count': img['flags_count'],
            'pano_id': img['pano_id']
        }
    
    detailed_file = "src/data/expert-confirmed-detailed.json"
    with open(detailed_file, 'w') as f:
        json.dump(detailed_mapping, f, indent=2)
    
    print(f"✅ Saved comprehensive dataset: {comprehensive_file}")
    print(f"✅ Saved lookup data: {lookup_file}")
    print(f"✅ Saved detailed mapping: {detailed_file}")
    
    # Print summary statistics
    print(f"\n📊 EXPERT-CONFIRMED DATASET SUMMARY:")
    print(f"   🏘️  Towns processed: {dataset['metadata']['total_towns']}")
    print(f"   ✅ Expert-confirmed images: {dataset['metadata']['total_expert_confirmed_images']:,}")
    print(f"   📋 Flag distribution:")
    for flag_count, count in sorted(dataset['metadata']['overall_flag_distribution'].items()):
        print(f"      {flag_count} flags: {count:,} images")
    
    # Show top towns by expert-confirmed images
    print(f"\n🏆 TOP TOWNS BY EXPERT-CONFIRMED IMAGES:")
    sorted_towns = sorted(dataset['metadata']['town_breakdown'], 
                         key=lambda x: x['expert_confirmed'], reverse=True)
    for i, town in enumerate(sorted_towns[:10], 1):
        print(f"   {i:2d}. {town['town']}: {town['expert_confirmed']:,} images ({town['percentage']:.1f}%)")
    
    return {
        'comprehensive_file': comprehensive_file,
        'lookup_file': lookup_file,
        'detailed_file': detailed_file,
        'total_images': dataset['metadata']['total_expert_confirmed_images']
    }

def main():
    """Main processing function"""
    try:
        # Create comprehensive expert dataset
        dataset = create_comprehensive_expert_dataset()
        
        # Save the dataset
        result = save_expert_dataset(dataset)
        
        print(f"\n🎉 SUCCESS!")
        print("="*60)
        print(f"✅ Created expert-confirmed dataset with {result['total_images']:,} images")
        print(f"✅ Dataset covers {dataset['metadata']['total_towns']} towns")
        print(f"✅ Ready for app integration!")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Update app to use expert-confirmed dataset")
        print(f"   2. Serve only curated, high-quality flag images")
        print(f"   3. Provide flag count information to experts")
        print(f"   4. Test improved expert experience")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 