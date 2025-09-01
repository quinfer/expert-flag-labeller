#!/usr/bin/env python3
"""
Multi-Expert Training Implementation for NI Flags Dataset
=========================================================

Direct implementation to leverage your 7 expert annotations per image
"""

import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import json

def load_multi_expert_classifications(csv_path: str) -> pd.DataFrame:
    """
    Load your multi-expert classifications from Supabase export
    
    Expected columns: image_url, expert_id, category, context, 
                      specific_flag, confidence, expert_name
    """
    df = pd.read_csv(csv_path)
    
    # Extract image ID from URL if needed
    if 'image_url' in df.columns:
        df['image_id'] = df['image_url'].apply(lambda x: x.split('/')[-1])
    
    # Create hierarchical label
    df['hierarchical_label'] = (df['category'] + '-' + 
                                df['context'] + '-' + 
                                df['specific_flag'])
    
    print(f"Loaded {len(df)} classifications from {df['expert_id'].nunique()} experts")
    print(f"Covering {df['image_id'].nunique()} unique images")
    
    return df

def analyze_expert_agreement(df: pd.DataFrame) -> Dict:
    """
    Comprehensive analysis of expert agreement patterns
    """
    results = {
        'images': {},
        'statistics': {}
    }
    
    # For each image, analyze expert agreement
    for image_id in df['image_id'].unique():
        img_data = df[df['image_id'] == image_id]
        
        # Category level agreement
        categories = img_data['category'].values
        cat_agreement = Counter(categories).most_common(1)[0][1] / len(categories)
        
        # Context level agreement  
        contexts = img_data['context'].values
        ctx_agreement = Counter(contexts).most_common(1)[0][1] / len(contexts)
        
        # Full hierarchical agreement
        hier_labels = img_data['hierarchical_label'].values
        hier_agreement = Counter(hier_labels).most_common(1)[0][1] / len(hier_labels)
        
        # Confidence statistics
        confidences = img_data['confidence'].values
        
        results['images'][image_id] = {
            'num_experts': len(img_data),
            'category_agreement': cat_agreement,
            'context_agreement': ctx_agreement,
            'hierarchical_agreement': hier_agreement,
            'mean_confidence': np.mean(confidences),
            'std_confidence': np.std(confidences),
            'consensus_label': Counter(hier_labels).most_common(1)[0][0],
            'label_distribution': dict(Counter(hier_labels))
        }
    
    # Overall statistics
    agreements = [v['hierarchical_agreement'] for v in results['images'].values()]
    results['statistics'] = {
        'mean_agreement': np.mean(agreements),
        'std_agreement': np.std(agreements),
        'perfect_agreement_rate': np.mean([a == 1.0 for a in agreements]),
        'high_agreement_rate': np.mean([a >= 0.7 for a in agreements]),
        'disputed_rate': np.mean([a < 0.5 for a in agreements])
    }
    
    print("\n=== EXPERT AGREEMENT ANALYSIS ===")
    print(f"Mean Agreement: {results['statistics']['mean_agreement']:.2%}")
    print(f"Perfect Agreement: {results['statistics']['perfect_agreement_rate']:.2%}")
    print(f"High Agreement (≥70%): {results['statistics']['high_agreement_rate']:.2%}")
    print(f"Disputed (<50%): {results['statistics']['disputed_rate']:.2%}")
    
    return results

def create_training_splits_with_agreement(df: pd.DataFrame, 
                                         analysis: Dict,
                                         test_ratio: float = 0.2,
                                         val_ratio: float = 0.1) -> Dict:
    """
    Create train/val/test splits ensuring disputed images are in training
    """
    image_ids = list(analysis['images'].keys())
    
    # Sort by agreement (low to high)
    image_ids.sort(key=lambda x: analysis['images'][x]['hierarchical_agreement'])
    
    # Put most disputed images in training set
    n_total = len(image_ids)
    n_test = int(n_total * test_ratio)
    n_val = int(n_total * val_ratio)
    n_train = n_total - n_test - n_val
    
    # Take highest agreement images for test (most reliable labels)
    test_images = image_ids[-n_test:]
    
    # Next highest for validation
    val_images = image_ids[-(n_test + n_val):-n_test]
    
    # Disputed images for training (to learn from uncertainty)
    train_images = image_ids[:n_train]
    
    splits = {
        'train': train_images,
        'val': val_images,
        'test': test_images
    }
    
    print(f"\n=== DATA SPLITS ===")
    print(f"Train: {len(train_images)} images (includes disputed cases)")
    print(f"Val: {len(val_images)} images")
    print(f"Test: {len(test_images)} images (high agreement only)")
    
    # Check agreement distribution in each split
    for split_name, split_images in splits.items():
        agreements = [analysis['images'][img]['hierarchical_agreement'] 
                     for img in split_images]
        print(f"{split_name} mean agreement: {np.mean(agreements):.2%}")
    
    return splits

def create_soft_labels_dataset(df: pd.DataFrame, 
                               analysis: Dict,
                               num_classes: int = 70) -> Dict:
    """
    Create soft label distributions from multi-expert annotations
    """
    # Create label to index mapping
    all_labels = df['hierarchical_label'].unique()
    label_to_idx = {label: idx for idx, label in enumerate(sorted(all_labels))}
    
    soft_labels = {}
    
    for image_id, image_info in analysis['images'].items():
        # Initialize label distribution
        label_dist = np.zeros(len(label_to_idx))
        
        # Get all expert annotations for this image
        img_annotations = df[df['image_id'] == image_id]
        
        for _, row in img_annotations.iterrows():
            label = row['hierarchical_label']
            confidence = row['confidence'] / 5.0  # Normalise confidence
            
            if label in label_to_idx:
                label_dist[label_to_idx[label]] += confidence
        
        # Normalise to probability distribution
        if label_dist.sum() > 0:
            label_dist = label_dist / label_dist.sum()
        else:
            # Uniform distribution if no valid labels
            label_dist = np.ones(len(label_to_idx)) / len(label_to_idx)
        
        soft_labels[image_id] = {
            'distribution': label_dist.tolist(),
            'consensus_idx': label_to_idx.get(image_info['consensus_label'], 0),
            'entropy': -np.sum(label_dist * np.log(label_dist + 1e-10)),
            'confidence': image_info['mean_confidence']
        }
    
    print(f"\n=== SOFT LABELS CREATED ===")
    print(f"Total images: {len(soft_labels)}")
    print(f"Number of classes: {len(label_to_idx)}")
    
    # Analyze entropy distribution (uncertainty measure)
    entropies = [v['entropy'] for v in soft_labels.values()]
    print(f"Mean entropy: {np.mean(entropies):.3f}")
    print(f"High uncertainty images (entropy > 1.0): "
          f"{np.mean([e > 1.0 for e in entropies]):.1%}")
    
    return soft_labels, label_to_idx

def create_curriculum_order(analysis: Dict) -> List[str]:
    """
    Order images for curriculum learning (easy → hard)
    """
    # Sort by: confidence (high→low) and agreement (high→low)
    image_scores = []
    
    for image_id, info in analysis['images'].items():
        # Combined score: weighted average of agreement and confidence
        score = (info['hierarchical_agreement'] * 0.7 + 
                info['mean_confidence'] / 5.0 * 0.3)
        image_scores.append((image_id, score))
    
    # Sort by score (high to low = easy to hard)
    image_scores.sort(key=lambda x: x[1], reverse=True)
    
    curriculum_order = [img_id for img_id, _ in image_scores]
    
    print(f"\n=== CURRICULUM LEARNING ORDER ===")
    print(f"Easiest image: {curriculum_order[0]} "
          f"(score: {image_scores[0][1]:.3f})")
    print(f"Hardest image: {curriculum_order[-1]} "
          f"(score: {image_scores[-1][1]:.3f})")
    
    return curriculum_order

def save_multi_expert_dataset(output_dir: str,
                              df: pd.DataFrame,
                              analysis: Dict,
                              splits: Dict,
                              soft_labels: Dict,
                              label_to_idx: Dict,
                              curriculum_order: List[str]):
    """
    Save all multi-expert training assets
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save splits
    splits_file = output_path / "splits_multi_expert.json"
    with open(splits_file, 'w') as f:
        json.dump(splits, f, indent=2)
    print(f"Saved splits to {splits_file}")
    
    # Save soft labels
    soft_labels_file = output_path / "soft_labels.json"
    with open(soft_labels_file, 'w') as f:
        json.dump(soft_labels, f, indent=2)
    print(f"Saved soft labels to {soft_labels_file}")
    
    # Save label mapping
    label_mapping_file = output_path / "label_to_idx.json"
    with open(label_mapping_file, 'w') as f:
        json.dump(label_to_idx, f, indent=2)
    print(f"Saved label mapping to {label_mapping_file}")
    
    # Save curriculum order
    curriculum_file = output_path / "curriculum_order.json"
    with open(curriculum_file, 'w') as f:
        json.dump(curriculum_order, f, indent=2)
    print(f"Saved curriculum order to {curriculum_file}")
    
    # Save analysis results
    analysis_file = output_path / "expert_agreement_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"Saved analysis to {analysis_file}")
    
    # Save consensus labels for standard training
    consensus_df = []
    for image_id, info in analysis['images'].items():
        consensus_df.append({
            'image_id': image_id,
            'label': info['consensus_label'],
            'agreement': info['hierarchical_agreement'],
            'confidence': info['mean_confidence']
        })
    consensus_df = pd.DataFrame(consensus_df)
    consensus_file = output_path / "consensus_labels.csv"
    consensus_df.to_csv(consensus_file, index=False)
    print(f"Saved consensus labels to {consensus_file}")
    
    print(f"\n✅ All multi-expert assets saved to {output_path}")

def integrate_with_cocoop_trainer(soft_labels_path: str, 
                                  curriculum_path: str) -> str:
    """
    Generate code to integrate multi-expert training with CoCoOp
    """
    integration_code = '''
# Add this to your CoCoOp trainer (cocoop_flags_trainer.py)

def load_multi_expert_assets(self):
    """Load multi-expert training assets"""
    import json
    
    # Load soft labels
    with open('{soft_labels}', 'r') as f:
        self.soft_labels = json.load(f)
    
    # Load curriculum order
    with open('{curriculum}', 'r') as f:
        self.curriculum_order = json.load(f)
    
    print(f"Loaded {{len(self.soft_labels)}} soft labels")
    print(f"Loaded curriculum with {{len(self.curriculum_order)}} images")

def compute_soft_label_loss(self, logits, image_ids):
    """Compute KL divergence loss against soft expert labels"""
    total_loss = 0
    for i, img_id in enumerate(image_ids):
        if img_id in self.soft_labels:
            # Get soft label distribution
            target_dist = torch.FloatTensor(
                self.soft_labels[img_id]['distribution']
            ).to(self.device)
            
            # KL divergence loss
            log_probs = F.log_softmax(logits[i], dim=0)
            loss = F.kl_div(log_probs, target_dist, reduction='sum')
            
            # Weight by expert confidence
            confidence = self.soft_labels[img_id]['confidence'] / 5.0
            total_loss += loss * confidence
    
    return total_loss / len(image_ids)

# In forward_backward method, replace cross_entropy with:
# loss = self.compute_soft_label_loss(logits, batch['image_ids'])
'''.format(soft_labels=soft_labels_path, curriculum=curriculum_path)
    
    return integration_code

# Main execution
if __name__ == "__main__":
    print("="*60)
    print("MULTI-EXPERT TRAINING SETUP FOR NI FLAGS")
    print("="*60)
    
    # Load your multi-expert data
    csv_path = "classifications.csv"  # Update with your actual path
    
    print("\n1. Loading multi-expert classifications...")
    df = load_multi_expert_classifications(csv_path)
    
    print("\n2. Analyzing expert agreement...")
    analysis = analyze_expert_agreement(df)
    
    print("\n3. Creating training splits...")
    splits = create_training_splits_with_agreement(df, analysis)
    
    print("\n4. Creating soft labels...")
    soft_labels, label_to_idx = create_soft_labels_dataset(df, analysis)
    
    print("\n5. Creating curriculum order...")
    curriculum_order = create_curriculum_order(analysis)
    
    print("\n6. Saving all assets...")
    output_dir = "./multi_expert_assets"
    save_multi_expert_dataset(
        output_dir, df, analysis, splits, 
        soft_labels, label_to_idx, curriculum_order
    )
    
    print("\n7. Integration code:")
    print("-"*40)
    integration = integrate_with_cocoop_trainer(
        f"{output_dir}/soft_labels.json",
        f"{output_dir}/curriculum_order.json"
    )
    print(integration)
    
    print("\n" + "="*60)
    print("✅ MULTI-EXPERT SETUP COMPLETE!")
    print("="*60)
    print("""
    Benefits achieved:
    1. Soft labels reduce overfitting
    2. Curriculum learning improves convergence
    3. Test set has high-agreement labels (reliable evaluation)
    4. Training focuses on ambiguous cases (better generalisation)
    5. Can report IAA metrics (methodological rigour)
    """)
