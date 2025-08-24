#!/usr/bin/env python3
"""
Fixed Hierarchical Prompting for RS5M Flag Classification
Uses the WORKING RS5M approach as foundation + proper hierarchical prompting
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
import numpy as np
from PIL import Image
import time
from datetime import datetime
from tqdm import tqdm
import random
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import json
import os
import argparse
import clip
import open_clip

# Add the flag_classification_adaptation directory to path for dataset imports
import sys
sys.path.append(str(Path(__file__).parent))

from dassl.data import DataManager
from dassl.utils import setup_logger, set_random_seed, collect_env_info
from dassl.config import get_cfg_default
from dassl.engine import TRAINER_REGISTRY, TrainerX
from dassl.data.datasets import DATASET_REGISTRY

# Import our custom datasets to register them
from datasets.ni_flags_consolidated import NIFlagsConsolidated

class HierarchicalPromptGenerator:
    """Generate hierarchical prompts for flag classification"""
    
    def __init__(self):
        # Economic-based hierarchical mapping
        self.class_hierarchy = {
            # High Economic Impact Unionist
            "Unionist_High_Impact": {
                "category": "Unionist", 
                "flag": "Union_Jack",
                "context": "Building_mounted"
            },
            "Unionist_Medium_Impact": {
                "category": "Unionist", 
                "flag": "Ulster_Banner",
                "context": "Lamppost_mounted"
            },
            
            # Nationalist Displays
            "Nationalist_Display": {
                "category": "Nationalist", 
                "flag": "Irish_Tricolor",
                "context": "Window_display"
            },
            
            # Fraternal Cultural
            "Fraternal_Cultural": {
                "category": "Fraternal", 
                "flag": "Orange_Order",
                "context": "Permanent_installation"
            },
            
            # International Solidarity
            "International_Solidarity_Palestinian": {
                "category": "International", 
                "flag": "Palestinian",
                "context": "Building_mounted"
            },
            "International_Solidarity_Israeli": {
                "category": "International", 
                "flag": "Israeli",
                "context": "Building_mounted"
            },
            "International_EU": {
                "category": "International", 
                "flag": "European_Union",
                "context": "Pole_mounted"
            },
            
            # Sports Organizations
            "Sport_GAA": {
                "category": "Sport", 
                "flag": "GAA",
                "context": "Temporary_installation"
            },
            "Sport_Local": {
                "category": "Sport", 
                "flag": "Local_Club",
                "context": "Temporary_installation"
            },
            
            # Paramilitary (Highest Negative Impact)
            "Paramilitary_UDA": {
                "category": "Paramilitary", 
                "flag": "UDA",
                "context": "Building_mounted"
            },
            "Paramilitary_UVF": {
                "category": "Paramilitary", 
                "flag": "UVF",
                "context": "Building_mounted"
            },
            
            # Seasonal Decorative
            "Seasonal_Decorative": {
                "category": "Seasonal", 
                "flag": "Bunting",
                "context": "Street_decoration"
            },
            
            # Regional Identity
            "Regional_Scottish": {
                "category": "Regional", 
                "flag": "Scottish_Saltire",
                "context": "Building_mounted"
            },
            
            # Commemorative Historical
            "Commemorative_WW1": {
                "category": "Commemorative", 
                "flag": "WW1_Commemorative",
                "context": "Memorial"
            },
            
            # Mixed Displays
            "Mixed_Unionist_Nationalist": {
                "category": "Mixed", 
                "flag": "Multiple_flags",
                "context": "Street_decoration"
            },
            "Mixed_Multiple": {
                "category": "Mixed", 
                "flag": "Multiple_flags",
                "context": "Street_decoration"
            }
        }
        
        # Prompt templates
        self.category_templates = {
            "Unionist": "a Unionist political flag display",
            "Nationalist": "a Nationalist political flag display", 
            "Paramilitary": "a paramilitary organization flag display",
            "Fraternal": "a fraternal cultural organization flag display",
            "International": "an international flag display",
            "Sport": "a sports organization flag display",
            "Seasonal": "a seasonal decorative flag display",
            "Regional": "a regional identity flag display",
            "Commemorative": "a commemorative historical flag display",
            "Mixed": "a mixed flag display"
        }
        
        self.flag_templates = {
            "Union_Jack": "Union Jack British flag",
            "Ulster_Banner": "Ulster Banner Northern Ireland flag", 
            "Irish_Tricolor": "Irish Tricolor flag",
            "Scottish_Saltire": "Scottish Saltire flag",
            "Orange_Order": "Orange Order fraternal flag",
            "Palestinian": "Palestinian solidarity flag",
            "Israeli": "Israeli flag",
            "European_Union": "European Union flag",
            "GAA": "GAA Gaelic sports flag",
            "UDA": "UDA paramilitary flag",
            "UVF": "UVF paramilitary flag",
            "Local_Club": "local sports club flag",
            "WW1_Commemorative": "World War 1 commemorative flag",
            "Bunting": "decorative bunting display",
            "Multiple_flags": "multiple flags"
        }
        
        self.context_templates = {
            "Building_mounted": "mounted on a building",
            "Lamppost_mounted": "mounted on a lamppost", 
            "Pole_mounted": "mounted on a flagpole",
            "Window_display": "displayed in a window",
            "Temporary_installation": "in a temporary installation",
            "Permanent_installation": "in a permanent installation",
            "Memorial": "at a memorial site",
            "Street_decoration": "as street decoration"
        }
    
    def get_all_prompts(self, classnames, level):
        """Generate prompts for all classes at specified hierarchical level"""
        prompts = []
        
        for classname in classnames:
            if classname in self.class_hierarchy:
                hierarchy = self.class_hierarchy[classname]
                
                if level == "category":
                    prompt = f"a photo of {self.category_templates[hierarchy['category']]}"
                elif level == "flag":
                    prompt = f"a photo of {self.flag_templates[hierarchy['flag']]}"
                elif level == "context":
                    prompt = f"a photo of a flag {self.context_templates[hierarchy['context']]}"
                elif level == "full":
                    prompt = f"a photo of {self.flag_templates[hierarchy['flag']]} {self.context_templates[hierarchy['context']]}, {self.category_templates[hierarchy['category']]}"
                else:
                    prompt = f"a photo of {classname.replace('_', ' ').lower()}"
            else:
                # Fallback for unmapped classes
                prompt = f"a photo of {classname.replace('_', ' ').lower()}"
            
            prompts.append(prompt)
        
        return prompts

class HierarchicalRS5MModel(nn.Module):
    """RS5M model with hierarchical prompting - using WORKING approach"""
    
    def __init__(self, checkpoint_path, classnames, device):
        super().__init__()
        self.device = device
        self.classnames = classnames
        self.num_classes = len(classnames)

        # Use the WORKING RS5M approach (from train_rs5m_finetune.py)
        print(f"🔄 Loading RS5M ViT-H-14 using OpenCLIP (proven working approach)...")
        
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-H-14', 
            pretrained=None,  # Don't load default weights
            device=device
        )
        
        # Load RS5M checkpoint (this is the working approach)
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        missing_keys, unexpected_keys = self.model.load_state_dict(ckpt, strict=False)
        
        print(f"✅ Loaded RS5M weights: {len(ckpt)} total keys")
        if len(missing_keys) > 0:
            print(f"⚠️  Missing keys: {len(missing_keys)} (expected)")
        if len(unexpected_keys) > 0:
            print(f"⚠️  Unexpected keys: {len(unexpected_keys)}")

        # Initialize hierarchical prompt generator
        self.prompt_generator = HierarchicalPromptGenerator()

        # Generate hierarchical prompts
        print("🔄 Generating hierarchical prompts...")
        self.category_prompts = self.prompt_generator.get_all_prompts(classnames, "category")
        self.flag_prompts = self.prompt_generator.get_all_prompts(classnames, "flag")
        self.context_prompts = self.prompt_generator.get_all_prompts(classnames, "context")
        self.full_prompts = self.prompt_generator.get_all_prompts(classnames, "full")

        print(f"✅ Generated prompts:")
        print(f"   Category prompts: {len(set(self.category_prompts))} unique")
        print(f"   Flag prompts: {len(set(self.flag_prompts))} unique")
        print(f"   Context prompts: {len(set(self.context_prompts))} unique")
        print(f"   Full prompts: {self.num_classes} total")
        
        # Pre-encode all text prompts (more efficient than encoding during training)
        print("🔄 Pre-encoding text prompts...")
        with torch.no_grad():
            # Tokenize and encode
            category_tokens = clip.tokenize(self.category_prompts).to(device)
            flag_tokens = clip.tokenize(self.flag_prompts).to(device)
            context_tokens = clip.tokenize(self.context_prompts).to(device)
            full_tokens = clip.tokenize(self.full_prompts).to(device)
            
            # Encode using RS5M text encoder
            self.category_features = self.model.encode_text(category_tokens)
            self.flag_features = self.model.encode_text(flag_tokens)
            self.context_features = self.model.encode_text(context_tokens)
            self.full_features = self.model.encode_text(full_tokens)
            
            # Normalize all features
            self.category_features = F.normalize(self.category_features, dim=-1)
            self.flag_features = F.normalize(self.flag_features, dim=-1)
            self.context_features = F.normalize(self.context_features, dim=-1)
            self.full_features = F.normalize(self.full_features, dim=-1)

        # Learnable hierarchical fusion weights (start with emphasis on full prompts)
        self.fusion_weights = nn.Parameter(torch.tensor([0.1, 0.2, 0.1, 0.6]))  # [category, flag, context, full]
        
        print(f"✅ Hierarchical RS5M model ready!")

    def forward(self, images):
        # Extract image features using RS5M (proven working approach)
        image_features = self.model.encode_image(images)
        image_features = F.normalize(image_features, dim=-1)
        
        # Compute similarities at all hierarchical levels
        category_sim = torch.matmul(image_features, self.category_features.t())
        flag_sim = torch.matmul(image_features, self.flag_features.t())
        context_sim = torch.matmul(image_features, self.context_features.t())
        full_sim = torch.matmul(image_features, self.full_features.t())
        
        # Apply learnable fusion weights (softmax normalized)
        weights = F.softmax(self.fusion_weights, dim=0)
        
        # Weighted combination of hierarchical similarities
        final_logits = (weights[0] * category_sim + 
                       weights[1] * flag_sim + 
                       weights[2] * context_sim + 
                       weights[3] * full_sim)
        
        # Scale logits (learned temperature)
        logit_scale = self.model.logit_scale.exp()
        final_logits = final_logits * logit_scale
        
        return final_logits

def setup_device():
    """Setup device with MPS support"""
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("=" * 60)
        print("🚀 MPS (Metal Performance Shaders) DETECTED!")
        print("🎯 Using M4 Max GPU acceleration")
        print("=" * 60)
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("🚀 CUDA GPU DETECTED!")
        print("🎯 Using NVIDIA GPU acceleration")
        print("=" * 60)
    else:
        device = torch.device("cpu")
        print("💻 Using CPU")
        print("=" * 60)

    return device

def create_data_loaders(data_root, batch_size=8, num_workers=4):
    """Create train/test data loaders using Dassl dataset"""
    print(f"Creating data loaders from {data_root}")

    # Create minimal config for dataset
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = str(Path(data_root).resolve())
    cfg.DATASET.NAME = "NIFlagsConsolidated"

    # Use Dassl dataset registry
    dataset = DATASET_REGISTRY.get("NIFlagsConsolidated")(cfg=cfg)

    # Get train/test splits
    train_items = dataset.train_x
    test_items = dataset.test
    classnames = dataset.classnames

    print(f"Train samples: {len(train_items)}")
    print(f"Test samples: {len(test_items)}")
    print(f"Classes: {len(classnames)}")

    return train_items, test_items, classnames

class FocalLoss(nn.Module):
    """Focal Loss for addressing class imbalance"""
    def __init__(self, alpha=0.25, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

def evaluate_model(model, test_items, device, batch_size=16):
    """Evaluate model on test set"""
    model.eval()
    all_preds = []
    all_labels = []
    
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    
    with torch.no_grad():
        for batch in tqdm(chunks(test_items, batch_size), desc="Evaluating"):
            images = []
            labels = []
            
            for item in batch:
                img = Image.open(item.impath).convert("RGB")
                # Use the model's preprocessing
                img_tensor = model.preprocess(img)
                images.append(img_tensor)
                labels.append(item.label)
            
            # Stack batch
            images = torch.stack(images).to(device)
            labels = torch.tensor(labels).to(device)
            
            # Forward pass
            outputs = model(images)
            predictions = torch.argmax(outputs, dim=1)
            
            all_preds.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    return np.array(all_preds), np.array(all_labels)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=str, default='data', help='Data root directory')
    parser.add_argument('--checkpoint', type=str, required=True, help='RS5M checkpoint path')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')
    parser.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--focal-alpha', type=float, default=0.25, help='Focal loss alpha')
    parser.add_argument('--focal-gamma', type=float, default=2.0, help='Focal loss gamma')
    parser.add_argument('--eval-freq', type=int, default=5, help='Evaluation frequency')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Set random seed
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = f"rs5m_hierarchical_fixed_{timestamp}"
    output_dir = Path(args.output_dir) / experiment_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Experiment: {experiment_name}")
    print(f"📁 Output: {output_dir}")
    
    # Load data
    train_items, test_items, classnames = create_data_loaders(args.data_root, args.batch_size)
    
    # Save classnames
    with open(output_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(f"{name}\n")
    
    # Initialize model
    model = HierarchicalRS5MModel(args.checkpoint, classnames, device)
    
    # Loss function and optimizer
    criterion = FocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    best_accuracy = 0.0
    training_log = []
    
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]
    
    print(f"\n🚀 Starting hierarchical training for {args.epochs} epochs...")
    
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        num_batches = 0
        
        # Training
        for batch in tqdm(chunks(train_items, args.batch_size), desc=f"Epoch {epoch}/{args.epochs}"):
            images = []
            labels = []
            
            for item in batch:
                img = Image.open(item.impath).convert("RGB")
                img_tensor = model.preprocess(img)
                images.append(img_tensor)
                labels.append(item.label)
            
            # Stack batch
            images = torch.stack(images).to(device)
            labels = torch.tensor(labels).to(device)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        current_lr = optimizer.param_groups[0]['lr']
        
        # Log training progress
        log_entry = {
            "epoch": epoch,
            "train_loss": avg_loss,
            "learning_rate": current_lr
        }
        
        # Evaluation
        if epoch % args.eval_freq == 0 or epoch == args.epochs:
            print(f"\n📊 Evaluating epoch {epoch}...")
            predictions, labels = evaluate_model(model, test_items, device)
            
            accuracy = accuracy_score(labels, predictions)
            macro_f1 = f1_score(labels, predictions, average='macro', zero_division=0)
            micro_f1 = f1_score(labels, predictions, average='micro', zero_division=0)
            
            log_entry.update({
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "micro_f1": micro_f1
            })
            
            print(f"🎯 Epoch {epoch}: Accuracy = {accuracy:.4f}, Macro F1 = {macro_f1:.4f}")
            
            # Save best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                torch.save(model.state_dict(), output_dir / "model_best.pth")
                
                # Save detailed results
                results = {
                    "accuracy": accuracy,
                    "macro_f1": macro_f1,
                    "micro_f1": micro_f1,
                    "predictions": predictions.tolist(),
                    "labels": labels.tolist(),
                    "classnames": classnames,
                    "fusion_weights": model.fusion_weights.detach().cpu().tolist()
                }
                
                with open(output_dir / "best_results.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                print(f"💾 New best model saved! Accuracy: {accuracy:.4f}")
        
        training_log.append(log_entry)
        scheduler.step()
        
        print(f"Epoch {epoch}/{args.epochs}: Loss = {avg_loss:.6f}, LR = {current_lr:.6f}")
    
    # Save training log
    with open(output_dir / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
    
    print(f"\n✅ Training complete! Best accuracy: {best_accuracy:.4f}")
    print(f"📁 Results saved to: {output_dir}")
    
    # Print learned fusion weights
    final_weights = F.softmax(model.fusion_weights, dim=0)
    print(f"\n🔧 Learned fusion weights:")
    print(f"   Category: {final_weights[0]:.3f}")
    print(f"   Flag: {final_weights[1]:.3f}")
    print(f"   Context: {final_weights[2]:.3f}")
    print(f"   Full: {final_weights[3]:.3f}")

if __name__ == "__main__":
    main()