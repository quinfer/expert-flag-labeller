#!/usr/bin/env python3
"""
Script to investigate the structure of pickle files containing false positive data
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import sys

def investigate_pickle_file(filepath):
    """Investigate the structure and contents of a pickle file"""
    print(f"\n{'='*60}")
    print(f"📁 INVESTIGATING: {filepath.name}")
    print(f"📊 File size: {filepath.stat().st_size / (1024*1024):.1f} MB")
    print(f"{'='*60}")
    
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        print(f"🔍 Data type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"📋 Dictionary with {len(data)} keys:")
            for i, (key, value) in enumerate(data.items()):
                if i < 10:  # Show first 10 keys
                    print(f"   {key}: {type(value)} - {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                elif i == 10:
                    print(f"   ... and {len(data) - 10} more keys")
                    break
                    
        elif isinstance(data, list):
            print(f"📋 List with {len(data)} items:")
            if len(data) > 0:
                print(f"   First item type: {type(data[0])}")
                print(f"   First item: {str(data[0])[:200]}{'...' if len(str(data[0])) > 200 else ''}")
                
                if len(data) > 1:
                    print(f"   Second item: {str(data[1])[:200]}{'...' if len(str(data[1])) > 200 else ''}")
                    
                if len(data) > 5:
                    print(f"   Last item: {str(data[-1])[:200]}{'...' if len(str(data[-1])) > 200 else ''}")
                    
        elif isinstance(data, pd.DataFrame):
            print(f"📊 DataFrame with shape: {data.shape}")
            print(f"   Columns: {list(data.columns)}")
            print(f"   Index: {data.index}")
            print("\n📝 First few rows:")
            print(data.head())
            
        elif isinstance(data, np.ndarray):
            print(f"📊 NumPy array with shape: {data.shape}")
            print(f"   Data type: {data.dtype}")
            print(f"   First few elements: {data.flat[:10]}")
            
        else:
            print(f"📄 Content preview: {str(data)[:500]}{'...' if len(str(data)) > 500 else ''}")
            
        # If it's a list or dict, try to analyze patterns in the data
        if isinstance(data, list) and len(data) > 0:
            analyze_list_patterns(data)
        elif isinstance(data, dict):
            analyze_dict_patterns(data)
            
    except Exception as e:
        print(f"❌ Error loading pickle file: {e}")

def analyze_list_patterns(data):
    """Analyze patterns in list data"""
    print(f"\n🔍 PATTERN ANALYSIS:")
    
    # Check if items are consistent types
    types = [type(item) for item in data[:100]]  # Sample first 100
    unique_types = set(types)
    print(f"   Item types in first 100: {unique_types}")
    
    # If items are dictionaries, analyze their keys
    if len(unique_types) == 1 and dict in unique_types:
        sample_keys = set()
        for item in data[:10]:
            if isinstance(item, dict):
                sample_keys.update(item.keys())
        print(f"   Sample dictionary keys: {list(sample_keys)}")
        
        # Show structure of first dict
        if len(data) > 0 and isinstance(data[0], dict):
            print(f"   First dict structure:")
            for key, value in data[0].items():
                print(f"      {key}: {type(value)} = {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")

def analyze_dict_patterns(data):
    """Analyze patterns in dictionary data"""
    print(f"\n🔍 PATTERN ANALYSIS:")
    
    # Look for filename-like keys
    filename_keys = []
    for key in list(data.keys())[:20]:  # Sample first 20 keys
        if isinstance(key, str) and ('.jpg' in key.lower() or '.png' in key.lower() or '.jpeg' in key.lower()):
            filename_keys.append(key)
    
    if filename_keys:
        print(f"   🖼️  Found filename-like keys: {len(filename_keys)} examples:")
        for key in filename_keys[:5]:
            print(f"      {key}")
    
    # Analyze value types
    sample_values = list(data.values())[:20]
    value_types = set(type(v) for v in sample_values)
    print(f"   Value types: {value_types}")

def main():
    """Main function to investigate all pickle files"""
    pickle_dir = Path("false_positive_checks")
    
    if not pickle_dir.exists():
        print(f"❌ Directory {pickle_dir} not found!")
        return
    
    pickle_files = list(pickle_dir.glob("*.pickle"))
    
    if not pickle_files:
        print("❌ No pickle files found!")
        return
    
    print(f"🔍 Found {len(pickle_files)} pickle files to investigate:")
    for file in pickle_files:
        print(f"   📁 {file.name}")
    
    for pickle_file in sorted(pickle_files):
        investigate_pickle_file(pickle_file)
    
    print(f"\n{'='*60}")
    print("✅ Investigation completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 