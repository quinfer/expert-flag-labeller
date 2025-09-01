#!/usr/bin/env python3
"""
Flag Class Consolidation for Economic Impact Analysis
Consolidates 70 imbalanced classes into 15 economically-meaningful categories
"""

import json
import shutil
from pathlib import Path
import pandas as pd
from collections import Counter, defaultdict
import argparse

def load_class_statistics(stats_file='detailed_class_statistics.json'):
    """Load the class distribution statistics"""
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    return stats

def create_economic_consolidation_map(stats):
    """
    Create consolidation mapping based on economic impact potential
    Maps 70 classes -> 15 economically meaningful categories
    """
    class_counts = stats['hierarchical_class_distribution']['counts']
    
    consolidation_map = {}
    
    for class_name, count in class_counts.items():
        parts = class_name.split('-')
        category = parts[0] if len(parts) > 0 else 'unknown'
        context = parts[1] if len(parts) > 1 else 'unknown'
        flag = parts[2] if len(parts) > 2 else 'unknown'
        
        # UNIONIST DISPLAYS (stratified by density for economic impact)
        if 'Union_Jack' in flag or 'Ulster_Banner' in flag:
            if count > 100:
                consolidation_map[class_name] = 'Unionist_High_Impact'
            elif count >= 10:
                consolidation_map[class_name] = 'Unionist_Medium_Impact'
            else:
                consolidation_map[class_name] = 'Unionist_Low_Impact'
        
        # NATIONALIST DISPLAYS
        elif 'Irish_Tricolor' in flag or 'Tricolour' in flag:
            consolidation_map[class_name] = 'Nationalist_Display'
        
        # SCOTTISH (politically complex)
        elif 'Scottish_Saltire' in flag:
            consolidation_map[class_name] = 'Regional_Scottish'
        
        # PARAMILITARY (highest negative economic impact)
        elif category == 'Proscribed':
            # Could subdivide if needed
            if any(x in class_name for x in ['UVF', 'UDA', 'UFF', 'YCV']):
                consolidation_map[class_name] = 'Paramilitary_Loyalist'
            else:
                consolidation_map[class_name] = 'Paramilitary_Other'
        
        # FRATERNAL ORGANISATIONS (Orange Order etc)
        elif category == 'Fraternal':
            consolidation_map[class_name] = 'Fraternal_Cultural'
        
        # BUNTING (seasonal/temporary)
        elif category == 'Bunting':
            consolidation_map[class_name] = 'Seasonal_Decorative'
        
        # SPORT
        elif category == 'Sport':
            if 'GAA' in flag:
                consolidation_map[class_name] = 'Sport_GAA'
            else:
                consolidation_map[class_name] = 'Sport_Other'
        
        # INTERNATIONAL (with political alignment)
        elif category == 'International':
            if 'Palestinian' in flag:
                consolidation_map[class_name] = 'International_Republican'
            elif 'Israeli' in flag:
                consolidation_map[class_name] = 'International_Loyalist'
            elif 'European_Union' in flag:
                consolidation_map[class_name] = 'International_EU'
            else:
                consolidation_map[class_name] = 'International_Other'
        
        # MILITARY/HISTORICAL
        elif category in ['Military', 'Historical']:
            consolidation_map[class_name] = 'Commemorative_Historical'
        
        # CATCH-ALL FOR RARE CLASSES
        elif count < 5:
            consolidation_map[class_name] = 'Other_Rare'
        
        # DEFAULT
        else:
            consolidation_map[class_name] = f'{category}_Other'
    
    return consolidation_map

def apply_consolidation(annotations_file, consolidation_map, output_dir):
    """Apply consolidation to annotations and create new dataset"""
    
    # Load original annotations
    with open(annotations_file, 'r') as f:
        annotations = json.load(f)
    
    # Track statistics
    original_to_new = defaultdict(list)
    new_class_counts = Counter()
    
    # Create consolidated annotations
    consolidated_annotations = {}
    
    for img_id, anno in annotations.items():
        old_class = anno['hierarchical_classname']
        new_class = consolidation_map.get(old_class, 'Other_Unknown')
        
        # Update annotation
        anno['original_classname'] = old_class
        anno['hierarchical_classname'] = new_class
        anno['consolidation_applied'] = True
        
        consolidated_annotations[img_id] = anno
        
        # Track statistics
        original_to_new[new_class].append(old_class)
        new_class_counts[new_class] += 1
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save consolidated annotations
    with open(output_path / 'annotations.json', 'w') as f:
        json.dump(consolidated_annotations, f, indent=2)
    
    # Save consolidation mapping
    with open(output_path / 'consolidation_map.json', 'w') as f:
        json.dump(consolidation_map, f, indent=2)
    
    # Save statistics
    stats = {
        'original_classes': len(consolidation_map),
        'new_classes': len(new_class_counts),
        'class_distribution': dict(new_class_counts),
        'mapping': {k: list(set(v)) for k, v in original_to_new.items()}
    }
    
    with open(output_path / 'consolidation_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    return consolidated_annotations, stats

def generate_class_names_file(output_dir, stats):
    """Generate classnames.txt for training"""
    output_path = Path(output_dir)
    
    # Sort classes by frequency
    sorted_classes = sorted(stats['class_distribution'].items(), 
                           key=lambda x: x[1], reverse=True)
    
    # Write classnames.txt
    with open(output_path / 'classnames.txt', 'w') as f:
        for class_name, _ in sorted_classes:
            f.write(f"{class_name}\n")
    
    return sorted_classes

def copy_images(source_image_dir, output_dir):
    """Copy image files to new consolidated dataset directory"""
    source_path = Path(source_image_dir)
    output_path = Path(output_dir) / 'images'
    
    if source_path.exists():
        print(f"Copying images from {source_path} to {output_path}")
        shutil.copytree(source_path, output_path, dirs_exist_ok=True)
        print(f"Images copied successfully")
    else:
        print(f"Warning: Source image directory {source_path} not found")

def generate_report(original_stats, consolidation_stats):
    """Generate consolidation report for dissertation"""
    
    report = []
    report.append("=" * 80)
    report.append("FLAG CLASS CONSOLIDATION REPORT")
    report.append("=" * 80)
    
    # Original distribution problems
    report.append("\n📊 ORIGINAL DISTRIBUTION PROBLEMS:")
    orig_dist = original_stats['hierarchical_class_distribution']
    dataset_overview = original_stats['dataset_overview']
    orig_stats = orig_dist['statistics']
    report.append(f"  Total classes: {dataset_overview['unique_hierarchical_classes']}")
    report.append(f"  Imbalance ratio: {orig_stats['class_imbalance_ratio']:.1f}:1")
    report.append(f"  Mean samples per class: {orig_stats['mean']:.1f}")
    report.append(f"  Median samples per class: {orig_stats['median']:.1f}")
    
    # Count problematic classes
    class_counts = orig_dist['counts']
    singleton_classes = sum(1 for c in class_counts.values() if c == 1)
    rare_classes = sum(1 for c in class_counts.values() if c <= 5)
    report.append(f"  Classes with 1 sample: {singleton_classes}")
    report.append(f"  Classes with ≤5 samples: {rare_classes}")
    
    # New distribution
    report.append("\n✅ CONSOLIDATED DISTRIBUTION:")
    report.append(f"  Total classes: {consolidation_stats['new_classes']}")
    report.append(f"  Reduction: {consolidation_stats['original_classes'] - consolidation_stats['new_classes']} classes merged")
    
    # New class distribution
    report.append("\n📈 NEW CLASS DISTRIBUTION:")
    sorted_new = sorted(consolidation_stats['class_distribution'].items(), 
                       key=lambda x: x[1], reverse=True)
    
    total_samples = sum(consolidation_stats['class_distribution'].values())
    for class_name, count in sorted_new:
        percentage = (count / total_samples) * 100
        report.append(f"  {class_name:30} {count:4} samples ({percentage:5.1f}%)")
    
    # Calculate new statistics
    new_counts = list(consolidation_stats['class_distribution'].values())
    new_imbalance = max(new_counts) / min(new_counts) if min(new_counts) > 0 else float('inf')
    report.append(f"\n📊 IMPROVEMENT METRICS:")
    report.append(f"  New imbalance ratio: {new_imbalance:.1f}:1")
    report.append(f"  New mean samples: {sum(new_counts)/len(new_counts):.1f}")
    report.append(f"  New median samples: {sorted(new_counts)[len(new_counts)//2]:.1f}")
    report.append(f"  Min samples per class: {min(new_counts)}")
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Consolidate flag classes for economic analysis')
    parser.add_argument('--stats-file', default='detailed_class_statistics.json',
                       help='Path to class statistics JSON')
    parser.add_argument('--annotations', default='../data/ni_flags/annotations.json',
                       help='Path to original annotations')
    parser.add_argument('--images', default='../data/ni_flags/images',
                       help='Path to original images directory')
    parser.add_argument('--output-dir', default='../data/ni_flags_consolidated',
                       help='Output directory for consolidated dataset')
    parser.add_argument('--copy-images', action='store_true',
                       help='Copy images to new directory')
    
    args = parser.parse_args()
    
    print("🚀 Starting flag class consolidation for economic analysis...")
    
    # Load statistics
    print(f"📊 Loading class statistics from {args.stats_file}")
    original_stats = load_class_statistics(args.stats_file)
    
    # Create consolidation mapping
    print("🔄 Creating economic impact consolidation mapping...")
    consolidation_map = create_economic_consolidation_map(original_stats)
    print(f"  Created mapping for {len(consolidation_map)} classes")
    
    # Apply consolidation
    print(f"📝 Applying consolidation to annotations...")
    consolidated_annotations, consolidation_stats = apply_consolidation(
        args.annotations, consolidation_map, args.output_dir
    )
    print(f"  Consolidated {consolidation_stats['original_classes']} → {consolidation_stats['new_classes']} classes")
    
    # Generate classnames file
    print("📋 Generating classnames.txt...")
    sorted_classes = generate_class_names_file(args.output_dir, consolidation_stats)
    
    # Copy images if requested
    if args.copy_images:
        copy_images(args.images, args.output_dir)
    
    # Generate report
    print("\n" + "=" * 80)
    report = generate_report(original_stats, consolidation_stats)
    print(report)
    
    # Save report
    report_path = Path(args.output_dir) / 'consolidation_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Consolidation complete!")
    print(f"📁 Output saved to: {args.output_dir}")
    print(f"📊 Report saved to: {report_path}")
    
    # Print next steps
    print("\n🎯 NEXT STEPS:")
    print("1. Review consolidation_report.txt")
    print("2. Update dataset config to point to consolidated data")
    print("3. Retrain models with new 15-class structure")
    print("4. Compare performance metrics")

if __name__ == "__main__":
    main()
