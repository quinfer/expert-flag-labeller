#!/usr/bin/env python3
"""
Gold Standard Test Set Selection for NI Flags Dataset
======================================================

Selects optimal 500 images for single-expert gold standard labelling
Ensures stratified representation across all categories and contexts
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple
import json
from datetime import datetime
import random

class GoldStandardSelector:
    """
    Intelligent selection of images for gold standard test set
    """
    
    def __init__(self, classifications_path: str, seed: int = 42):
        """
        Args:
            classifications_path: Path to classifications.csv
            seed: Random seed for reproducibility
        """
        self.df = pd.read_csv(classifications_path)
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        print(f"Loaded {len(self.df)} classifications")
        print(f"Unique images: {self.df['image_id'].nunique()}")
        print(f"Unique experts: {self.df['expert_id'].nunique()}")
        
    def analyze_dataset(self) -> Dict:
        """
        Comprehensive analysis of current dataset
        """
        analysis = {
            'total_images': self.df['image_id'].nunique(),
            'total_annotations': len(self.df),
            'experts': list(self.df['expert_id'].unique()),
            'towns': list(self.df['town'].unique()),
            'categories': {},
            'contexts': {},
            'specific_flags': {},
            'combinations': {}
        }
        
        # Count distributions
        analysis['categories'] = self.df['primary_category'].value_counts().to_dict()
        analysis['contexts'] = self.df['display_context'].value_counts().to_dict()
        analysis['specific_flags'] = self.df['specific_flag'].value_counts().to_dict()
        
        # Analyze hierarchical combinations
        self.df['hierarchical'] = (self.df['primary_category'] + '|' + 
                                   self.df['display_context'] + '|' + 
                                   self.df['specific_flag'])
        analysis['combinations'] = self.df['hierarchical'].value_counts().head(20).to_dict()
        
        # Agreement analysis per image
        agreement_scores = []
        for img_id in self.df['image_id'].unique():
            img_annotations = self.df[self.df['image_id'] == img_id]
            
            # Check agreement at different levels
            cat_agreement = self._calculate_agreement(img_annotations['primary_category'])
            ctx_agreement = self._calculate_agreement(img_annotations['display_context'])
            flag_agreement = self._calculate_agreement(img_annotations['specific_flag'])
            
            agreement_scores.append({
                'image_id': img_id,
                'num_annotations': len(img_annotations),
                'category_agreement': cat_agreement,
                'context_agreement': ctx_agreement,
                'flag_agreement': flag_agreement,
                'overall_agreement': flag_agreement,  # Use most specific level
                'mean_confidence': img_annotations['confidence'].mean()
            })
        
        analysis['agreement_df'] = pd.DataFrame(agreement_scores)
        analysis['mean_agreement'] = analysis['agreement_df']['overall_agreement'].mean()
        
        return analysis
    
    def _calculate_agreement(self, annotations) -> float:
        """Calculate agreement rate for a set of annotations"""
        if len(annotations) <= 1:
            return 1.0
        counts = Counter(annotations)
        return counts.most_common(1)[0][1] / len(annotations)
    
    def select_gold_standard_images(self, 
                                   num_images: int = 500,
                                   strategy: str = 'stratified_agreement') -> pd.DataFrame:
        """
        Select images for gold standard test set
        
        Strategies:
        - 'stratified_agreement': Balance categories with high-agreement images
        - 'representative': Match training distribution
        - 'challenging': Include disputed cases for error analysis
        - 'comprehensive': Mix of all strategies
        """
        
        analysis = self.analyze_dataset()
        agreement_df = analysis['agreement_df']
        
        if strategy == 'stratified_agreement':
            selected = self._stratified_agreement_selection(agreement_df, num_images)
            
        elif strategy == 'representative':
            selected = self._representative_selection(agreement_df, num_images)
            
        elif strategy == 'challenging':
            selected = self._challenging_selection(agreement_df, num_images)
            
        elif strategy == 'comprehensive':
            # Mix of strategies
            n_per_strategy = num_images // 3
            selected = []
            
            # 1/3 high agreement for reliable evaluation
            high_agreement = self._stratified_agreement_selection(
                agreement_df, n_per_strategy, min_agreement=0.8
            )
            selected.extend(high_agreement)
            
            # 1/3 representative of training distribution
            representative = self._representative_selection(
                agreement_df, n_per_strategy
            )
            selected.extend(representative)
            
            # 1/3 challenging cases for error analysis
            challenging = self._challenging_selection(
                agreement_df, num_images - len(selected)
            )
            selected.extend(challenging)
            
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Remove duplicates and get final selection
        selected = list(set(selected))[:num_images]
        
        # Create output dataframe
        selected_df = agreement_df[agreement_df['image_id'].isin(selected)].copy()
        
        # Add metadata
        for img_id in selected:
            img_data = self.df[self.df['image_id'] == img_id].iloc[0]
            selected_df.loc[selected_df['image_id'] == img_id, 'town'] = img_data['town']
            selected_df.loc[selected_df['image_id'] == img_id, 'primary_category'] = img_data['primary_category']
            selected_df.loc[selected_df['image_id'] == img_id, 'display_context'] = img_data['display_context']
            
            # Get consensus label
            flags = self.df[self.df['image_id'] == img_id]['specific_flag'].values
            consensus = Counter(flags).most_common(1)[0][0]
            selected_df.loc[selected_df['image_id'] == img_id, 'consensus_flag'] = consensus
        
        return selected_df
    
    def _stratified_agreement_selection(self, 
                                       agreement_df: pd.DataFrame,
                                       num_images: int,
                                       min_agreement: float = 0.7) -> List[str]:
        """
        Select images with high agreement, stratified by category
        """
        # Filter by minimum agreement
        high_agreement = agreement_df[agreement_df['overall_agreement'] >= min_agreement]
        
        selected = []
        
        # Get category distribution
        categories = self.df['primary_category'].unique()
        per_category = num_images // len(categories)
        
        for category in categories:
            # Get images in this category with high agreement
            cat_images = self.df[self.df['primary_category'] == category]['image_id'].unique()
            cat_high = high_agreement[high_agreement['image_id'].isin(cat_images)]
            
            # Sort by agreement and confidence
            cat_high = cat_high.sort_values(['overall_agreement', 'mean_confidence'], 
                                           ascending=False)
            
            # Select top images
            selected.extend(cat_high['image_id'].head(per_category).tolist())
        
        # Fill remainder with highest agreement images
        remaining = num_images - len(selected)
        if remaining > 0:
            unused = high_agreement[~high_agreement['image_id'].isin(selected)]
            unused = unused.sort_values('overall_agreement', ascending=False)
            selected.extend(unused['image_id'].head(remaining).tolist())
        
        return selected
    
    def _representative_selection(self, 
                                 agreement_df: pd.DataFrame,
                                 num_images: int) -> List[str]:
        """
        Select images matching training distribution
        """
        selected = []
        
        # Get distribution of hierarchical classes
        hier_counts = self.df['hierarchical'].value_counts()
        
        # Calculate how many images per class
        total_weight = hier_counts.sum()
        
        for hier_class, count in hier_counts.items():
            # Proportional allocation
            n_select = max(1, int(num_images * count / total_weight))
            
            # Get images of this class
            class_images = self.df[self.df['hierarchical'] == hier_class]['image_id'].unique()
            
            # Prefer high-agreement images
            class_agreement = agreement_df[agreement_df['image_id'].isin(class_images)]
            class_agreement = class_agreement.sort_values('overall_agreement', ascending=False)
            
            selected.extend(class_agreement['image_id'].head(n_select).tolist())
            
            if len(selected) >= num_images:
                break
        
        return selected[:num_images]
    
    def _challenging_selection(self, 
                              agreement_df: pd.DataFrame,
                              num_images: int) -> List[str]:
        """
        Select challenging/disputed images for error analysis
        """
        # Mix of different challenge types
        selected = []
        
        # 1. Low agreement cases (disputed)
        low_agreement = agreement_df[agreement_df['overall_agreement'] < 0.6]
        low_agreement = low_agreement.sort_values('overall_agreement')
        selected.extend(low_agreement['image_id'].head(num_images // 3).tolist())
        
        # 2. Medium confidence cases
        medium_conf = agreement_df[
            (agreement_df['mean_confidence'] >= 3) & 
            (agreement_df['mean_confidence'] <= 4)
        ]
        selected.extend(medium_conf['image_id'].head(num_images // 3).tolist())
        
        # 3. Rare classes
        rare_flags = self.df['specific_flag'].value_counts().tail(20).index
        rare_images = self.df[self.df['specific_flag'].isin(rare_flags)]['image_id'].unique()
        rare_agreement = agreement_df[agreement_df['image_id'].isin(rare_images)]
        selected.extend(rare_agreement['image_id'].head(num_images // 3).tolist())
        
        return list(set(selected))[:num_images]
    
    def create_labelling_spreadsheet(self, 
                                    selected_df: pd.DataFrame,
                                    output_path: str = 'gold_standard_to_label.csv'):
        """
        Create spreadsheet for expert to fill in
        """
        # Create simplified format for expert
        labelling_df = pd.DataFrame({
            'image_id': selected_df['image_id'],
            'town': selected_df['town'],
            'consensus_category': selected_df['primary_category'],
            'consensus_context': selected_df['display_context'],
            'consensus_flag': selected_df['consensus_flag'],
            'agreement_level': selected_df['overall_agreement'],
            'expert_category': '',  # To be filled
            'expert_context': '',   # To be filled
            'expert_flag': '',      # To be filled
            'expert_confidence': '', # To be filled
            'notes': ''             # Optional notes
        })
        
        # Sort by agreement level (high agreement first for expert confidence)
        labelling_df = labelling_df.sort_values('agreement_level', ascending=False)
        
        # Save
        labelling_df.to_csv(output_path, index=False)
        print(f"✅ Created labelling spreadsheet: {output_path}")
        
        # Also create a simple image list
        image_list_path = output_path.replace('.csv', '_images.txt')
        with open(image_list_path, 'w') as f:
            for img_id in labelling_df['image_id']:
                f.write(f"{img_id}\n")
        print(f"✅ Created image list: {image_list_path}")
        
        return labelling_df
    
    def analyze_selection(self, selected_df: pd.DataFrame) -> None:
        """
        Print analysis of selected gold standard set
        """
        print("\n" + "="*60)
        print("GOLD STANDARD TEST SET ANALYSIS")
        print("="*60)
        
        print(f"\n📊 SELECTION STATISTICS")
        print(f"Total images selected: {len(selected_df)}")
        print(f"Mean agreement: {selected_df['overall_agreement'].mean():.2%}")
        print(f"Mean confidence: {selected_df['mean_confidence'].mean():.2f}")
        
        print(f"\n📍 GEOGRAPHIC DISTRIBUTION")
        if 'town' in selected_df.columns:
            towns = selected_df['town'].value_counts().head(5)
            for town, count in towns.items():
                print(f"  {town}: {count} images")
        
        print(f"\n🏷️ CATEGORY DISTRIBUTION")
        if 'primary_category' in selected_df.columns:
            categories = selected_df['primary_category'].value_counts()
            for cat, count in categories.items():
                print(f"  {cat}: {count} images ({100*count/len(selected_df):.1f}%)")
        
        print(f"\n🎯 AGREEMENT DISTRIBUTION")
        print(f"  Perfect agreement (100%): {(selected_df['overall_agreement'] == 1.0).sum()}")
        print(f"  High agreement (≥80%): {(selected_df['overall_agreement'] >= 0.8).sum()}")
        print(f"  Medium agreement (60-80%): {((selected_df['overall_agreement'] >= 0.6) & (selected_df['overall_agreement'] < 0.8)).sum()}")
        print(f"  Low agreement (<60%): {(selected_df['overall_agreement'] < 0.6).sum()}")
        
        print(f"\n✨ BENEFITS OF THIS SELECTION")
        print("1. Enables direct comparison with literature baselines")
        print("2. Eliminates inter-annotator noise in evaluation")
        print("3. Provides consistent ground truth for all experiments")
        print("4. Includes stratified representation of all categories")
        print("5. Balances reliable evaluation with error analysis capability")


# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Select Gold Standard Test Set")
    parser.add_argument('--input', type=str, default='classifications.csv',
                       help='Path to classifications CSV')
    parser.add_argument('--output', type=str, default='gold_standard_to_label.csv',
                       help='Output path for labelling spreadsheet')
    parser.add_argument('--num-images', type=int, default=500,
                       help='Number of images to select')
    parser.add_argument('--strategy', type=str, default='comprehensive',
                       choices=['stratified_agreement', 'representative', 
                               'challenging', 'comprehensive'],
                       help='Selection strategy')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    print("🏆 GOLD STANDARD TEST SET SELECTION")
    print("="*60)
    
    # Initialize selector
    selector = GoldStandardSelector(args.input, seed=args.seed)
    
    # Analyze current dataset
    print("\n📊 Analyzing current dataset...")
    analysis = selector.analyze_dataset()
    print(f"Total images: {analysis['total_images']}")
    print(f"Mean agreement: {analysis['mean_agreement']:.2%}")
    print(f"Categories: {len(analysis['categories'])}")
    print(f"Towns: {len(analysis['towns'])}")
    
    # Select gold standard images
    print(f"\n🎯 Selecting {args.num_images} images using '{args.strategy}' strategy...")
    selected_df = selector.select_gold_standard_images(
        num_images=args.num_images,
        strategy=args.strategy
    )
    
    # Analyze selection
    selector.analyze_selection(selected_df)
    
    # Create labelling spreadsheet
    print(f"\n📝 Creating labelling spreadsheet...")
    labelling_df = selector.create_labelling_spreadsheet(selected_df, args.output)
    
    print("\n" + "="*60)
    print("✅ GOLD STANDARD SELECTION COMPLETE!")
    print("="*60)
    print(f"""
    Next steps:
    1. Send '{args.output}' to your expert
    2. Have them fill in the expert_* columns
    3. This should take approximately {args.num_images * 0.5 / 60:.1f} hours
    4. Use these labels ONLY for testing (never for training)
    5. Report both gold standard AND multi-expert results
    
    Expected impact:
    - Reported accuracy increase: +10-15% (due to label consistency)
    - Enables fair comparison with literature
    - Provides definitive evaluation metric
    - Strengthens dissertation methodology
    """)
