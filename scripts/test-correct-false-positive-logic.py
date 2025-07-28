#!/usr/bin/env python3
"""
Test script to apply the correct false positive logic:
flags!=0 AND Indicator==1 AND flags_correct==0
"""

import pickle
import pandas as pd
import numpy as np
import json

def test_correct_logic():
    """Test the correct false positive logic on ENNISKILLEN data"""
    print("🧪 TESTING CORRECT FALSE POSITIVE LOGIC")
    print("="*60)
    print("Logic: flags!=0 AND Indicator==1 AND flags_correct==0")
    print("="*60)
    
    try:
        # Load the corrected ENNISKILLEN data
        df = pd.read_pickle("false_positive_checks/ENNISKILLENresultsCORRECT.pickle")
        
        print(f"📂 Loaded ENNISKILLEN data: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        print()
        
        # Examine the data structure first
        print("🔍 DATA STRUCTURE ANALYSIS:")
        print(f"   Total images: {len(df):,}")
        print(f"   Unique values in 'flags': {sorted(df['flags'].unique())}")
        print(f"   Unique values in 'indicator': {list(df['indicator'].unique())}")
        print(f"   Data types - indicator: {df['indicator'].dtype}")
        print(f"   Unique values in 'flags_correct': {sorted(df['flags_correct'].unique())}")
        print()
        
        # Create the comprehensive classification matrix
        print("📊 COMPREHENSIVE CLASSIFICATION MATRIX:")
        print("flags vs flags_correct:")
        flags_vs_correct = pd.crosstab(df['flags'], df['flags_correct'], margins=True)
        print(flags_vs_correct)
        print()
        
        print("indicator vs flags_correct:")
        indicator_vs_correct = pd.crosstab(df['indicator'], df['flags_correct'], margins=True)
        print(indicator_vs_correct)
        print()
        
        # Apply the correct false positive logic
        print("🎯 APPLYING CORRECT FALSE POSITIVE LOGIC:")
        print("   Condition: flags!=0 AND indicator==1 AND flags_correct==0")
        
        # Step by step filtering
        step1 = df[df['flags'] != 0]
        print(f"   Step 1 (flags!=0): {len(step1):,} images")
        
        step2 = step1[step1['indicator'] == '1.0']
        print(f"   Step 2 (+ indicator==1): {len(step2):,} images")
        
        false_positives = step2[step2['flags_correct'] == 0]
        print(f"   Step 3 (+ flags_correct==0): {len(false_positives):,} images")
        print(f"   🎯 FINAL FALSE POSITIVES: {len(false_positives):,}")
        print()
        
        # Also get true positives for comparison
        true_positives = df[(df['flags'] != 0) & (df['indicator'] == '1.0') & (df['flags_correct'] == 1)]
        print(f"   ✅ TRUE POSITIVES (flags!=0 AND indicator==1 AND flags_correct==1): {len(true_positives):,}")
        print()
        
        # Calculate meaningful statistics
        total_flagged = len(df[(df['flags'] != 0) & (df['indicator'] == '1.0')])
        if total_flagged > 0:
            fp_rate = len(false_positives) / total_flagged * 100
            print(f"📈 STATISTICS:")
            print(f"   Total flagged (flags!=0 AND indicator==1): {total_flagged:,}")
            print(f"   False positives: {len(false_positives):,}")
            print(f"   True positives: {len(true_positives):,}")
            print(f"   False positive rate: {fp_rate:.1f}%")
            print(f"   True positive rate: {100-fp_rate:.1f}%")
        print()
        
        # Extract filenames for false positives
        fp_filenames = []
        for _, row in false_positives.iterrows():
            filename = str(row['f'])
            if not filename.endswith('.jpg'):
                filename += '.jpg'
            fp_filenames.append(filename)
        
        # Extract filenames for true positives  
        tp_filenames = []
        for _, row in true_positives.iterrows():
            filename = str(row['f'])
            if not filename.endswith('.jpg'):
                filename += '.jpg'
            tp_filenames.append(filename)
        
        print("📝 SAMPLE RESULTS:")
        print(f"   Sample false positives to filter:")
        for i, fp in enumerate(fp_filenames[:10]):
            print(f"      {i+1}. {fp}")
        print(f"   Sample true positives to keep:")
        for i, tp in enumerate(tp_filenames[:10]):
            print(f"      {i+1}. {tp}")
        print()
        
        # Compare with the old wrong logic
        old_wrong_fps = len(df[df['flags_correct'] == 0])
        print("🔄 COMPARISON WITH PREVIOUS WRONG LOGIC:")
        print(f"   Previous wrong logic (flags_correct==0): {old_wrong_fps:,} images")
        print(f"   Correct logic (flags!=0 AND indicator=='1.0' AND flags_correct==0): {len(false_positives):,} images")
        if len(false_positives) > 0:
            print(f"   Reduction factor: {old_wrong_fps / len(false_positives):.1f}x fewer false positives")
        else:
            print(f"   Reduction: No false positives found with correct logic!")
        print()
        
        return {
            'total_images': len(df),
            'false_positives': len(false_positives),
            'true_positives': len(true_positives),
            'total_flagged': total_flagged,
            'fp_rate': fp_rate if total_flagged > 0 else 0,
            'fp_filenames': fp_filenames,
            'tp_filenames': tp_filenames,
            'old_wrong_count': old_wrong_fps
        }
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_corrected_results(results):
    """Save the corrected results for comparison"""
    if not results:
        return
    
    print("💾 SAVING CORRECTED RESULTS:")
    
    # Save the corrected false positive lookup
    corrected_data = {
        'false_positives': results['fp_filenames'],
        'count': results['false_positives'],
        'metadata': {
            'logic': 'flags!=0 AND indicator=="1.0" AND flags_correct==0',
            'town': 'ENNISKILLEN',
            'total_images': results['total_images'],
            'total_flagged': results['total_flagged'],
            'true_positives': results['true_positives'],
            'false_positive_rate': results['fp_rate'],
            'improvement_vs_wrong_logic': "No false positives found" if results['false_positives'] == 0 else f"{results['old_wrong_count'] / results['false_positives']:.1f}x reduction"
        }
    }
    
    output_file = "src/data/false-positives-lookup-corrected.json"
    with open(output_file, 'w') as f:
        json.dump(corrected_data, f, indent=2)
    
    print(f"✅ Saved corrected data to: {output_file}")
    print(f"   📊 {results['false_positives']:,} false positives (vs {results['old_wrong_count']:,} with wrong logic)")
    print(f"   📈 {results['fp_rate']:.1f}% false positive rate")

def main():
    """Main test function"""
    results = test_correct_logic()
    
    if results:
        save_corrected_results(results)
        
        print("\n🎉 CORRECTED LOGIC TEST COMPLETE!")
        print("="*60)
        print(f"✅ Identified {results['false_positives']:,} actual false positives")
        print(f"✅ Preserved {results['true_positives']:,} true positives") 
        print(f"✅ {results['fp_rate']:.1f}% false positive rate (reasonable for CV algorithm)")
        if results['false_positives'] > 0:
            print(f"✅ {results['old_wrong_count'] / results['false_positives']:.1f}x reduction from wrong logic")
        else:
            print(f"✅ Perfect accuracy - no false positives found!")
        print("\n🚀 Ready to apply this logic to all 50 towns!")
    else:
        print("\n❌ Test failed - please check the data structure")

if __name__ == "__main__":
    main() 