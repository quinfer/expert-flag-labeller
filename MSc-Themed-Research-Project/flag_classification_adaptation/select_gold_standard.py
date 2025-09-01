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
            'towns': list(self.df['town'].unique()) if 'town' in self.df.columns else [],
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
        self.df['hierarchical'] = (self.df['primary_category'].astype(str) + '|' + 
                                   self.df['display_context'].astype(str) + '|' + 
                                   self.df['specific_flag'].astype(str))
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
                                   strategy: str = 'comprehensive') -> pd.DataFrame:
        """
        Select images for gold standard test set using comprehensive strategy
        """
        
        analysis = self.analyze_dataset()
        agreement_df = analysis['agreement_df']
        
        # Comprehensive strategy: mix of different selection criteria
        selected = []
        
        # 1/3 high agreement for reliable evaluation (167 images)
        n_high = num_images // 3
        high_agreement = agreement_df[agreement_df['overall_agreement'] >= 0.8]
        high_agreement = high_agreement.sort_values(['overall_agreement', 'mean_confidence'], 
                                                   ascending=False)
        selected.extend(high_agreement['image_id'].head(n_high).tolist())
        
        # 1/3 representative of distribution (167 images)
        n_rep = num_images // 3
        # Get proportional representation
        hier_counts = self.df['hierarchical'].value_counts()
        total_weight = hier_counts.sum()
        
        rep_selected = []
        for hier_class, count in hier_counts.items():
            n_select = max(1, int(n_rep * count / total_weight))
            class_images = self.df[self.df['hierarchical'] == hier_class]['image_id'].unique()
            class_agreement = agreement_df[agreement_df['image_id'].isin(class_images)]
            class_agreement = class_agreement.sort_values('overall_agreement', ascending=False)
            rep_selected.extend(class_agreement['image_id'].head(n_select).tolist())
            if len(rep_selected) >= n_rep:
                break
        selected.extend(rep_selected[:n_rep])
        
        # 1/3 challenging cases (166 images)
        n_challenge = num_images - len(selected)
        # Low agreement cases
        low_agreement = agreement_df[agreement_df['overall_agreement'] < 0.7]
        low_agreement = low_agreement.sort_values('mean_confidence', ascending=False)
        selected.extend(low_agreement['image_id'].head(n_challenge // 2).tolist())
        
        # Rare flags
        rare_flags = self.df['specific_flag'].value_counts().tail(30).index
        rare_images = self.df[self.df['specific_flag'].isin(rare_flags)]['image_id'].unique()
        rare_agreement = agreement_df[agreement_df['image_id'].isin(rare_images)]
        selected.extend(rare_agreement['image_id'].head(n_challenge // 2).tolist())
        
        # Remove duplicates and get exactly num_images
        selected = list(dict.fromkeys(selected))[:num_images]  # Preserve order while removing duplicates
        
        # Create output dataframe
        selected_df = agreement_df[agreement_df['image_id'].isin(selected)].copy()
        
        # Add metadata
        for img_id in selected:
            img_data = self.df[self.df['image_id'] == img_id].iloc[0]
            if 'town' in self.df.columns:
                selected_df.loc[selected_df['image_id'] == img_id, 'town'] = img_data['town']
            selected_df.loc[selected_df['image_id'] == img_id, 'primary_category'] = img_data['primary_category']
            selected_df.loc[selected_df['image_id'] == img_id, 'display_context'] = img_data['display_context']
            
            # Get consensus label
            flags = self.df[self.df['image_id'] == img_id]['specific_flag'].values
            consensus = Counter(flags).most_common(1)[0][0]
            selected_df.loc[selected_df['image_id'] == img_id, 'consensus_flag'] = consensus
        
        return selected_df
    
    def create_labelling_spreadsheet(self, 
                                    selected_df: pd.DataFrame,
                                    output_path: str = 'gold_standard_to_label.csv'):
        """
        Create spreadsheet for expert to fill in
        """
        # Create simplified format for expert
        labelling_data = []
        for _, row in selected_df.iterrows():
            labelling_data.append({
                'image_id': row['image_id'],
                'town': row.get('town', ''),
                'consensus_category': row.get('primary_category', ''),
                'consensus_context': row.get('display_context', ''),
                'consensus_flag': row.get('consensus_flag', ''),
                'agreement_level': f"{row['overall_agreement']:.1%}",
                'num_experts': row['num_annotations'],
                'mean_confidence': f"{row['mean_confidence']:.1f}",
                'expert_category': '',  # To be filled
                'expert_context': '',   # To be filled
                'expert_flag': '',      # To be filled
                'expert_confidence': '', # To be filled
                'notes': ''             # Optional notes
            })
        
        labelling_df = pd.DataFrame(labelling_data)
        
        # Sort by agreement level (high agreement first for expert confidence)
        labelling_df['sort_key'] = labelling_df['agreement_level'].str.rstrip('%').astype(float)
        labelling_df = labelling_df.sort_values('sort_key', ascending=False).drop('sort_key', axis=1)
        
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
        
        if 'town' in selected_df.columns and selected_df['town'].notna().any():
            print(f"\n📍 GEOGRAPHIC DISTRIBUTION")
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


# Main execution
if __name__ == "__main__":
    print("🏆 GOLD STANDARD TEST SET SELECTION")
    print("="*60)
    
    # Initialize selector
    selector = GoldStandardSelector('classifications.csv', seed=42)
    
    # Analyze current dataset
    print("\n📊 Analyzing current dataset...")
    analysis = selector.analyze_dataset()
    print(f"Total images: {analysis['total_images']}")
    print(f"Mean agreement: {analysis['mean_agreement']:.2%}")
    print(f"Categories: {len(analysis['categories'])}")
    
    # Select gold standard images
    print(f"\n🎯 Selecting 500 images using comprehensive strategy...")
    selected_df = selector.select_gold_standard_images(num_images=500)
    
    # Analyze selection
    selector.analyze_selection(selected_df)
    
    # Create labelling spreadsheet
    print(f"\n📝 Creating labelling spreadsheet...")
    labelling_df = selector.create_labelling_spreadsheet(selected_df, 'gold_standard_to_label.csv')
    
    # Save the selection analysis
    selected_df.to_csv('gold_standard_selection_analysis.csv', index=False)
    
    print("\n" + "="*60)
    print("✅ GOLD STANDARD SELECTION COMPLETE!")
    print("="*60)
    print("""
    Files created:
    1. gold_standard_to_label.csv - Send this to your expert
    2. gold_standard_to_label_images.txt - List of image IDs
    3. gold_standard_selection_analysis.csv - Detailed analysis
    
    Next steps:
    1. Send 'gold_standard_to_label.csv' to your best expert
    2. Have them fill in the expert_* columns
    3. This should take approximately 3-4 hours
    4. Use these labels ONLY for testing (never for training)
    """)
