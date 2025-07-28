#!/usr/bin/env python3
"""
Analyze false positive data and create a strategy for filtering them out
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import re

def load_pickle_safe(filepath):
    """Safely load pickle file with fallback methods"""
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"⚠️  Standard pickle load failed: {e}")
        
        # Try with different protocol
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f, encoding='latin1')
        except Exception as e2:
            print(f"⚠️  Latin1 encoding failed: {e2}")
            return None

def analyze_list_file():
    """Analyze the list file containing image paths"""
    print(f"\n{'='*60}")
    print("📁 ANALYZING: ENNISKILLENlist.pickle")
    print(f"{'='*60}")
    
    data = load_pickle_safe("false_positive_checks/ENNISKILLENlist.pickle")
    if data is None:
        return None
    
    print(f"📊 Total images: {len(data)}")
    
    # Extract just the filenames from paths
    filenames = []
    for path in data:
        # Extract filename from path
        filename = Path(path).name
        filenames.append(filename)
    
    print(f"📝 Sample filenames:")
    for i, filename in enumerate(filenames[:5]):
        print(f"   {i+1}. {filename}")
    
    return filenames

def analyze_results_file():
    """Analyze the results file containing CV classifications"""
    print(f"\n{'='*60}")
    print("📁 ANALYZING: ENNISKILLENresults.pickle")
    print(f"{'='*60}")
    
    data = load_pickle_safe("false_positive_checks/ENNISKILLENresults.pickle")
    if data is None:
        return None
    
    print(f"📊 Array shape: {data.shape}")
    print(f"📊 Data type: {data.dtype}")
    
    # Analyze the columns
    print(f"\n📋 Column analysis:")
    print(f"   Column 0 (filename): {data[0, 0]} (type: {type(data[0, 0])})")
    print(f"   Column 1 (base_id):  {data[0, 1]} (type: {type(data[0, 1])})")
    print(f"   Column 2 (result):   {data[0, 2]} (type: {type(data[0, 2])})")
    
    # Analyze the results column (should be 0/1 for false/true positive)
    results_col = data[:, 2].astype(int)
    unique_results = np.unique(results_col, return_counts=True)
    print(f"\n📊 Classification results:")
    for value, count in zip(unique_results[0], unique_results[1]):
        percentage = (count / len(data)) * 100
        status = "TRUE POSITIVE" if value == 1 else "FALSE POSITIVE"
        print(f"   {value} ({status}): {count:,} images ({percentage:.1f}%)")
    
    # Create a mapping of filename to classification result
    filename_to_result = {}
    for row in data:
        filename = str(row[0]) + ".jpg"  # Add .jpg extension
        result = int(row[2])
        filename_to_result[filename] = result
    
    return filename_to_result

def analyze_correct_file():
    """Analyze the manually corrected file"""
    print(f"\n{'='*60}")
    print("📁 ANALYZING: ENNISKILLENresultsCORRECT.pickle")
    print(f"{'='*60}")
    
    # Try different methods to load the pandas pickle
    try:
        # Method 1: Direct pandas read
        df = pd.read_pickle("false_positive_checks/ENNISKILLENresultsCORRECT.pickle")
        print(f"✅ Successfully loaded with pandas.read_pickle")
    except Exception as e1:
        print(f"⚠️  pandas.read_pickle failed: {e1}")
        
        # Method 2: Try with pickle directly
        data = load_pickle_safe("false_positive_checks/ENNISKILLENresultsCORRECT.pickle")
        if data is None:
            print("❌ Could not load CORRECT file")
            return None
        
        # If it's not a DataFrame, try to convert
        if not isinstance(data, pd.DataFrame):
            print(f"🔄 Data is {type(data)}, attempting conversion...")
            try:
                df = pd.DataFrame(data)
            except Exception as e2:
                print(f"❌ Conversion failed: {e2}")
                return None
        else:
            df = data
    
    print(f"📊 DataFrame shape: {df.shape}")
    print(f"📊 Columns: {list(df.columns)}")
    print(f"📊 Index: {df.index}")
    
    print(f"\n📝 First few rows:")
    print(df.head())
    
    print(f"\n📝 Data types:")
    print(df.dtypes)
    
    return df

def extract_filename_from_path(path):
    """Extract filename from various path formats"""
    # Handle different path separators and extract just the filename
    filename = Path(path).name
    
    # Ensure it has .jpg extension
    if not filename.endswith('.jpg'):
        filename += '.jpg'
    
    return filename

def create_false_positive_mapping():
    """Create a comprehensive mapping of false positives"""
    print(f"\n{'='*60}")
    print("🔄 CREATING FALSE POSITIVE MAPPING")
    print(f"{'='*60}")
    
    # Load all three files
    filenames = analyze_list_file()
    cv_results = analyze_results_file()
    manual_corrections = analyze_correct_file()
    
    if filenames is None or cv_results is None:
        print("❌ Could not load required files")
        return None
    
    # Create comprehensive mapping
    false_positives = set()
    true_positives = set()
    
    # From CV results: 0 = false positive, 1 = true positive
    for filename, result in cv_results.items():
        if result == 0:
            false_positives.add(filename)
        else:
            true_positives.add(filename)
    
    print(f"\n📊 From computer vision results:")
    print(f"   False positives: {len(false_positives):,}")
    print(f"   True positives: {len(true_positives):,}")
    
    # If we have manual corrections, use those to override CV results
    if manual_corrections is not None:
        print(f"\n🔄 Applying manual corrections...")
        # This would depend on the structure of the CORRECT file
        # We'll implement this once we understand the structure better
    
    # Create final mapping for integration into the app
    result = {
        'false_positives': sorted(list(false_positives)),
        'true_positives': sorted(list(true_positives)),
        'total_images': len(false_positives) + len(true_positives)
    }
    
    return result

def save_false_positive_data(mapping):
    """Save the false positive mapping for use in the app"""
    if mapping is None:
        print("❌ No mapping to save")
        return
    
    # Save as JSON for easy integration
    import json
    
    output_file = "src/data/false-positives-enniskillen.json"
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\n💾 Saved false positive mapping to: {output_file}")
    print(f"   False positives: {len(mapping['false_positives']):,}")
    print(f"   True positives: {len(mapping['true_positives']):,}")
    
    # Show sample false positives
    print(f"\n📝 Sample false positives:")
    for i, fp in enumerate(mapping['false_positives'][:10]):
        print(f"   {i+1}. {fp}")

def main():
    """Main analysis function"""
    print("🔍 ANALYZING FALSE POSITIVE DATA")
    print("="*60)
    
    # Check if directory exists
    if not Path("false_positive_checks").exists():
        print("❌ false_positive_checks directory not found!")
        return
    
    # Create the mapping
    mapping = create_false_positive_mapping()
    
    # Save for integration
    if mapping:
        save_false_positive_data(mapping)
    
    print(f"\n✅ Analysis completed!")

if __name__ == "__main__":
    main() 