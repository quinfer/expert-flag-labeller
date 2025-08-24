#!/usr/bin/env python3
"""
Export expert flag classifications from Supabase for training
"""
import json
import os
import pandas as pd
from pathlib import Path

def export_from_csv(csv_path):
    """
    Export from CSV file (if you export from Supabase dashboard)
    """
    print(f"📊 Loading classifications from CSV: {csv_path}")
    
    # Load CSV - adjust column names as needed based on your Supabase schema
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Convert to the format expected by Li et al.'s code
    classifications = {}
    
    for _, row in df.iterrows():
        # Adjust these column names to match your Supabase schema
        image_name = row.get('image_name') or row.get('image_id') or row.get('filename')
        category = row.get('category') or row.get('primary_category')
        context = row.get('context') or row.get('display_context')
        specific_flag = row.get('specific_flag') or row.get('flag_type')
        confidence = row.get('confidence', 4.0)
        
        if image_name and category:
            classifications[image_name] = {
                'category': str(category).strip(),
                'context': str(context).strip() if context else 'unknown',
                'specific_flag': str(specific_flag).strip() if specific_flag else 'unknown',
                'confidence': float(confidence) if confidence else 4.0
            }
    
    return classifications

def export_with_supabase_client(url, key):
    """
    Export directly from Supabase using Python client
    """
    try:
        from supabase import create_client, Client
    except ImportError:
        print("❌ Supabase client not installed. Install with: pip install supabase")
        return None
    
    print(f"🔗 Connecting to Supabase...")
    supabase: Client = create_client(url, key)
    
    # Query all classifications - adjust table name as needed
    try:
        response = supabase.table('classifications').select("*").execute()
        print(f"📊 Retrieved {len(response.data)} classifications from Supabase")
        
        classifications = {}
        for record in response.data:
            image_name = record.get('image_name') or record.get('image_id')
            if image_name:
                classifications[image_name] = {
                    'category': record.get('category', 'unknown'),
                    'context': record.get('context', 'unknown'),
                    'specific_flag': record.get('specific_flag', 'unknown'),
                    'confidence': record.get('confidence', 4.0)
                }
        
        return classifications
        
    except Exception as e:
        print(f"❌ Error querying Supabase: {e}")
        return None

def convert_to_hierarchical_format(classifications):
    """
    Convert classifications to hierarchical format expected by Li et al.'s code
    """
    print("🔄 Converting to hierarchical format...")
    
    processed = {}
    class_distribution = {}
    
    for image_name, data in classifications.items():
        # Clean and standardize the hierarchical components
        category = data['category'].replace(' ', '_').replace('-', '_')
        context = data['context'].replace(' ', '_').replace('-', '_')
        specific_flag = data['specific_flag'].replace(' ', '_').replace('-', '_')
        
        # Create hierarchical classname: category-context-specific_flag
        hierarchical_classname = f"{category}-{context}-{specific_flag}"
        
        processed[image_name] = {
            'category': category,
            'context': context,
            'specific_flag': specific_flag,
            'hierarchical_classname': hierarchical_classname,
            'confidence': data['confidence']
        }
        
        # Track class distribution
        class_distribution[hierarchical_classname] = class_distribution.get(hierarchical_classname, 0) + 1
    
    print(f"✅ Processed {len(processed)} classifications")
    print(f"📊 Found {len(class_distribution)} unique hierarchical classes")
    
    # Show top classes
    sorted_classes = sorted(class_distribution.items(), key=lambda x: x[1], reverse=True)
    print("🔝 Top 10 most common classes:")
    for i, (class_name, count) in enumerate(sorted_classes[:10]):
        print(f"   {i+1:2d}. {class_name}: {count} images")
    
    return processed, class_distribution

def save_for_training(processed_classifications, output_dir="../data"):
    """
    Save classifications in format ready for training
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    annotations_dir = output_dir / "annotations"
    annotations_dir.mkdir(exist_ok=True)
    
    # Save processed annotations
    annotations_file = annotations_dir / "expert_classifications.json"
    with open(annotations_file, 'w') as f:
        json.dump(processed_classifications, f, indent=2)
    
    print(f"💾 Saved annotations to: {annotations_file}")
    
    # Create classnames.txt for reference
    unique_classes = set()
    for data in processed_classifications.values():
        unique_classes.add(data['hierarchical_classname'])
    
    classnames_file = annotations_dir / "classnames.txt"
    with open(classnames_file, 'w') as f:
        for classname in sorted(unique_classes):
            f.write(f"{classname}\n")
    
    print(f"📝 Saved class names to: {classnames_file}")
    print(f"🎯 Ready for training with {len(unique_classes)} classes!")

def main():
    print("🎯 EXPERT FLAG CLASSIFICATIONS EXPORT")
    print("=" * 50)
    
    # Method 1: From CSV export
    csv_path = input("📁 Path to CSV export from Supabase (or press Enter to skip): ").strip()
    
    if csv_path and os.path.exists(csv_path):
        classifications = export_from_csv(csv_path)
    else:
        print("⚠️  CSV path not provided or doesn't exist")
        
        # Method 2: Direct Supabase connection
        use_direct = input("🔗 Connect directly to Supabase? (y/N): ").strip().lower()
        
        if use_direct == 'y':
            url = input("🌐 Supabase URL: ").strip()
            key = input("🔑 Supabase Anon Key: ").strip()
            
            if url and key:
                classifications = export_with_supabase_client(url, key)
            else:
                print("❌ Missing Supabase credentials")
                return
        else:
            print("❌ No data source provided")
            return
    
    if not classifications:
        print("❌ Failed to load classifications")
        return
    
    # Process and save
    processed, distribution = convert_to_hierarchical_format(classifications)
    save_for_training(processed)
    
    print("\n🎉 DATA EXPORT COMPLETE!")
    print("✅ Expert classifications ready for training")
    print("📁 Next: Ensure your flag images are in ../data/images/")

if __name__ == "__main__":
    main()
