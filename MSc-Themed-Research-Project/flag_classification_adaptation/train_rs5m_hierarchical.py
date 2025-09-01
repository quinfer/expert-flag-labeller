#!/usr/bin/env python3
"""
RS5M ViT-H-14 Fine-tuning with Hierarchical Prompting for Flag Classification
Implements multi-level prompt structure: Category → Flag → Context
Based on Li et al. 2023 methodology with hierarchical extensions
"""

import os
import sys
import json
import argparse
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
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Fix OpenMP conflict on M4 Max
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import datasets
try:
    from datasets.ni_flags_consolidated import NIFlagsConsolidated
    print("✅ Successfully imported NIFlagsConsolidated dataset")
except ImportError as e:
    print(f"❌ Failed to import NIFlagsConsolidated dataset: {e}")
    sys.exit(1)

from dassl.data.datasets import DATASET_REGISTRY
import clip
from torchvision import transforms

def set_random_seed(seed):
    """Set random seed for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)

def setup_device():
    """Setup device with M4 Max MPS support"""
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("🚀 MPS (Metal Performance Shaders) DETECTED!")
        print("🎯 Using M4 Max GPU acceleration")
        print("=" * 80)
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("🚀 CUDA GPU DETECTED!")
        print("🎯 Using NVIDIA GPU acceleration")
        print("=" * 80)
    else:
        device = torch.device("cpu")
        print("⚠️  WARNING: Using CPU - Training will be SLOW!")
    
    return device

class HierarchicalPromptGenerator:
    """Generate hierarchical prompts for flag classification"""
    
    def __init__(self):
        # Define hierarchical structure based on economic consolidation
        self.category_prompts = {
            "Unionist": "a Unionist political flag display",
            "Nationalist": "a Nationalist political flag display", 
            "Paramilitary": "a paramilitary organization flag display",
            "Fraternal": "a fraternal cultural organization flag display",
            "International": "an international flag display",
            "Sport": "a sports organization flag display",
            "Seasonal": "a seasonal decorative flag display",
            "Regional": "a regional identity flag display",
            "Commemorative": "a commemorative historical flag display"
        }
        
        self.flag_prompts = {
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
            "Bunting": "decorative bunting display"
        }
        
        self.context_prompts = {
            "Building_mounted": "mounted on a building",
            "Lamppost_mounted": "mounted on a lamppost", 
            "Pole_mounted": "mounted on a flagpole",
            "Window_display": "displayed in a window",
            "Temporary_installation": "in a temporary installation",
            "Permanent_installation": "in a permanent installation",
            "Memorial": "at a memorial site",
            "Bunting_display": "as decorative bunting",
            "Street_decoration": "as street decoration"
        }
        
        # Map consolidated classes to hierarchical components
        self.class_hierarchy = {
            "Unionist_High_Impact": ("Unionist", "Union_Jack", "Building_mounted"),
            "Unionist_Medium_Impact": ("Unionist", "Ulster_Banner", "Building_mounted"), 
            "Unionist_Low_Impact": ("Unionist", "Union_Jack", "Window_display"),
            "Nationalist_Display": ("Nationalist", "Irish_Tricolor", "Building_mounted"),
            "Regional_Scottish": ("Regional", "Scottish_Saltire", "Building_mounted"),
            "Paramilitary_Loyalist": ("Paramilitary", "UDA", "Lamppost_mounted"),
            "Paramilitary_Other": ("Paramilitary", "UVF", "Building_mounted"),
            "Fraternal_Cultural": ("Fraternal", "Orange_Order", "Lamppost_mounted"),
            "International_Republican": ("International", "Palestinian", "Building_mounted"),
            "International_Loyalist": ("International", "Israeli", "Lamppost_mounted"),
            "International_EU": ("International", "European_Union", "Building_mounted"),
            "International_Other": ("International", "Palestinian", "Building_mounted"),
            "Sport_GAA": ("Sport", "GAA", "Building_mounted"),
            "Sport_Other": ("Sport", "Local_Club", "Lamppost_mounted"),
            "Seasonal_Decorative": ("Seasonal", "Bunting", "Bunting_display"),
            "Commemorative_Historical": ("Commemorative", "WW1_Commemorative", "Memorial")
        }
    
    def generate_hierarchical_prompt(self, class_name, level="full"):
        """Generate hierarchical prompt for a class"""
        if class_name not in self.class_hierarchy:
            return f"a flag display of {class_name}"
            
        category, flag, context = self.class_hierarchy[class_name]
        
        if level == "category":
            return self.category_prompts.get(category, f"a {category} flag display")
        elif level == "flag":
            category_desc = self.category_prompts.get(category, f"a {category}")
            flag_desc = self.flag_prompts.get(flag, flag)
            return f"{category_desc} showing {flag_desc}"
        elif level == "full":
            category_desc = self.category_prompts.get(category, f"a {category}")
            flag_desc = self.flag_prompts.get(flag, flag)
            context_desc = self.context_prompts.get(context, f"in {context}")
            return f"{category_desc} showing {flag_desc} {context_desc}"
        else:
            return f"a flag display of {class_name}"
    
    def get_all_prompts(self, classnames, level="full"):
        """Get prompts for all classes"""
        return [self.generate_hierarchical_prompt(name, level) for name in classnames]

def create_data_loaders(data_root, batch_size=8, num_workers=4):
    """Create train/test data loaders using Dassl dataset"""
    print(f"Creating data loaders from {data_root}")
    
    # Create minimal config for dataset
    from dassl.config import get_cfg_default
    cfg = get_cfg_default()
    cfg.DATASET.ROOT = str(Path(data_root).resolve())
    cfg.DATASET.NAME = "NIFlagsConsolidated"
    
    # Use Dassl dataset registry with proper config
    dataset = DATASET_REGISTRY.get("NIFlagsConsolidated")(cfg=cfg)
    
    # Get train/test splits
    train_items = dataset.train_x
    test_items = dataset.test
    classnames = dataset.classnames
    
    print(f"Train samples: {len(train_items)}")
    print(f"Test samples: {len(test_items)}")
    print(f"Classes: {len(classnames)}")
    
    return train_items, test_items, classnames

class FlagDataset(Dataset):
    """Dataset for flag images with hierarchical prompts"""
    
    def __init__(self, items, transform=None):
        self.items = items
        self.transform = transform
        
    def __len__(self):
        return len(self.items)
        
    def __getitem__(self, idx):
        item = self.items[idx]
        
        # Load image
        image = Image.open(item.impath).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
            
        return image, item.label

class HierarchicalRS5MModel(nn.Module):
    """RS5M model with hierarchical prompting"""
    
    def __init__(self, checkpoint_path, classnames, device):
        super().__init__()
        self.device = device
        self.classnames = classnames
        self.num_classes = len(classnames)
        
        # Load RS5M checkpoint
        print(f"Loading RS5M ViT-H-14 from {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Build custom ViT-H-14 architecture matching RS5M exactly
        print("🔄 Building custom ViT-H-14 architecture to match RS5M...")
        
        # Import the CLIP model components we need
        from clip.model import VisionTransformer, Transformer
        
        # Create ViT-H-14 vision encoder matching RS5M architecture
        # Based on checkpoint analysis: 1280 dim, 257 patches (16x16 + 1 cls), 14x14 conv
        vision_width = 1280
        vision_layers = 32  # ViT-H has 32 layers
        vision_heads = 16   # ViT-H has 16 attention heads
        embed_dim = 1024    # Shared embedding dimension
        
        self.visual = VisionTransformer(
            input_resolution=224,
            patch_size=14,
            width=vision_width,
            layers=vision_layers,
            heads=vision_heads,
            output_dim=embed_dim
        ).to(device)
        
        # Create text encoder matching RS5M architecture
        context_length = 77
        vocab_size = 49408  # Standard CLIP vocab size
        transformer_width = 1024
        transformer_heads = 16
        transformer_layers = 24  # ViT-H text encoder has 24 layers
        
        self.transformer = Transformer(
            width=transformer_width,
            layers=transformer_layers,
            heads=transformer_heads,
            attn_mask=self.build_attention_mask(context_length)
        ).to(device)
        
        # Text embedding components
        self.token_embedding = nn.Embedding(vocab_size, transformer_width).to(device)
        self.positional_embedding = nn.Parameter(torch.empty(context_length, transformer_width)).to(device)
        self.ln_final = nn.LayerNorm(transformer_width).to(device)
        self.text_projection = nn.Parameter(torch.empty(transformer_width, embed_dim)).to(device)
        
        # Logit scale parameter
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07)).to(device)
        
        # Load RS5M weights into our custom architecture
        print("📦 Loading RS5M weights into custom ViT-H-14 architecture...")
        
        # Load vision encoder weights
        vision_state_dict = {}
        for key, value in checkpoint.items():
            if key.startswith('visual.'):
                new_key = key[7:]  # Remove 'visual.' prefix
                vision_state_dict[new_key] = value
        
        missing_keys, unexpected_keys = self.visual.load_state_dict(vision_state_dict, strict=False)
        print(f"✅ Loaded vision encoder: {len(vision_state_dict)} weights")
        
        # Load text encoder weights
        text_weights_loaded = 0
        text_state_dict = {}
        
        for key, value in checkpoint.items():
            if key == 'positional_embedding':
                self.positional_embedding.data = value.to(device)
                text_weights_loaded += 1
            elif key == 'text_projection':
                self.text_projection.data = value.to(device)
                text_weights_loaded += 1
            elif key == 'logit_scale':
                self.logit_scale.data = value.to(device)
                text_weights_loaded += 1
            elif key.startswith('transformer.'):
                # Collect transformer weights for batch loading
                new_key = key[12:]  # Remove 'transformer.' prefix
                text_state_dict[new_key] = value
            elif key == 'token_embedding.weight':
                self.token_embedding.weight.data = value.to(device)
                text_weights_loaded += 1
            elif key == 'ln_final.weight':
                self.ln_final.weight.data = value.to(device)
                text_weights_loaded += 1
            elif key == 'ln_final.bias':
                self.ln_final.bias.data = value.to(device)
                text_weights_loaded += 1
        
        # Load transformer weights
        if text_state_dict:
            missing_keys, unexpected_keys = self.transformer.load_state_dict(text_state_dict, strict=False)
            text_weights_loaded += len(text_state_dict) - len(missing_keys)
        
        print(f"✅ Loaded text encoder: {text_weights_loaded} weights")
        
        # Convert to float32 for MPS compatibility
        if device.type == 'mps':
            self.visual = self.visual.float()
            self.transformer = self.transformer.float()
            self.token_embedding = self.token_embedding.float()
        
        print("✅ Full RS5M ViT-H-14 architecture recreated with all weights loaded")
        print("🔬 Adding hierarchical text prompting on top of complete RS5M model")
        
        # Initialize hierarchical prompt generator
        self.prompt_generator = HierarchicalPromptGenerator()
        
        # Create hierarchical prompts
        self.category_prompts = self.prompt_generator.get_all_prompts(classnames, "category")
        self.flag_prompts = self.prompt_generator.get_all_prompts(classnames, "flag") 
        self.full_prompts = self.prompt_generator.get_all_prompts(classnames, "full")
        
        # Tokenize all prompt levels using CLIP tokenizer
        self.category_tokens = clip.tokenize(self.category_prompts).to(device)
        self.flag_tokens = clip.tokenize(self.flag_prompts).to(device)
        self.full_tokens = clip.tokenize(self.full_prompts).to(device)
        
        # Learnable prompt fusion weights
        self.fusion_weights = nn.Parameter(torch.ones(3) / 3)  # [category, flag, full]
        
        print(f"✅ Model loaded with hierarchical prompting")
        print(f"   Categories: {len(set(self.category_prompts))}")
        print(f"   Flags: {len(set(self.flag_prompts))}")
        print(f"   Full prompts: {len(self.full_prompts)}")
    
    def build_attention_mask(self, context_length):
        """Build causal attention mask for text transformer"""
        mask = torch.empty(context_length, context_length)
        mask.fill_(float("-inf"))
        mask.triu_(1)  # zero out the lower diagonal
        return mask
    
    def encode_image(self, images):
        """Encode images using RS5M vision encoder"""
        return self.visual(images.type(self.visual.conv1.weight.dtype))
    
    def encode_text(self, text_tokens):
        """Encode text using RS5M text encoder"""
        x = self.token_embedding(text_tokens).type(self.positional_embedding.dtype)  # [batch_size, n_ctx, d_model]
        
        x = x + self.positional_embedding.type(self.positional_embedding.dtype)
        x = x.permute(1, 0, 2)  # NLD -> LND
        x = self.transformer(x)
        x = x.permute(1, 0, 2)  # LND -> NLD
        x = self.ln_final(x).type(self.positional_embedding.dtype)
        
        # x.shape = [batch_size, n_ctx, transformer.width]
        # take features from the eot embedding (eot_token is the highest number in each sequence)
        x = x[torch.arange(x.shape[0]), text_tokens.argmax(dim=-1)] @ self.text_projection
        
        return x
        
    def forward(self, images):
        # Ensure input images are float32 for MPS compatibility
        if images.dtype != torch.float32:
            images = images.float()
            
        # Extract image features using our custom RS5M ViT-H-14 vision encoder
        image_features = self.encode_image(images)
        image_features = F.normalize(image_features, dim=-1)
        
        # Encode hierarchical prompts using our custom RS5M text encoder
        with torch.no_grad():
            category_features = self.encode_text(self.category_tokens)
            flag_features = self.encode_text(self.flag_tokens)
            full_features = self.encode_text(self.full_tokens)
            
        # Ensure all features are float32
        category_features = category_features.float()
        flag_features = flag_features.float() 
        full_features = full_features.float()
        
        # Normalize text features
        category_features = F.normalize(category_features, dim=-1)
        flag_features = F.normalize(flag_features, dim=-1)
        full_features = F.normalize(full_features, dim=-1)
        
        # Compute similarities at each hierarchical level
        category_sim = torch.matmul(image_features, category_features.t())
        flag_sim = torch.matmul(image_features, flag_features.t())
        full_sim = torch.matmul(image_features, full_features.t())
        
        # Hierarchical fusion with learnable weights
        fusion_weights = F.softmax(self.fusion_weights, dim=0)
        logits = (fusion_weights[0] * category_sim + 
                 fusion_weights[1] * flag_sim + 
                 fusion_weights[2] * full_sim)
        
        return logits

def compute_class_weights(train_items, num_classes):
    """Compute inverse frequency weights for class balancing"""
    class_counts = torch.zeros(num_classes)
    for item in train_items:
        class_counts[item.label] += 1
    
    # Inverse frequency with smoothing
    weights = 1.0 / (class_counts + 1e-6)
    weights = weights / weights.sum() * num_classes  # Normalize
    
    return weights

class FocalLoss(nn.Module):
    """Focal Loss for addressing class imbalance"""
    
    def __init__(self, alpha=0.25, gamma=2.0, weight=None):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.weight = weight
        
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, weight=self.weight, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss.mean()

def train_epoch(model, train_loader, optimizer, criterion, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    num_batches = 0
    
    with tqdm(train_loader, desc="Training") as pbar:
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / num_batches

def evaluate(model, test_loader, device, classnames):
    """Evaluate model performance"""
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        with tqdm(test_loader, desc="Evaluating") as pbar:
            for images, labels in pbar:
                images = images.to(device)
                outputs = model(images)
                preds = outputs.argmax(dim=1).cpu().numpy()
                
                all_preds.extend(preds)
                all_labels.extend(labels.numpy())
    
    # Compute metrics
    accuracy = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    micro_f1 = f1_score(all_labels, all_preds, average='micro', zero_division=0)
    
    return accuracy, macro_f1, micro_f1, all_preds, all_labels

def main():
    parser = argparse.ArgumentParser(description="RS5M Hierarchical Prompting Fine-tuning")
    parser.add_argument("--data-root", type=str, default="data", help="Root directory of dataset")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to RS5M checkpoint")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size (reduce if OOM)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--focal-alpha", type=float, default=0.25, help="Focal loss alpha")
    parser.add_argument("--focal-gamma", type=float, default=2.0, help="Focal loss gamma")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--eval-freq", type=int, default=5, help="Evaluation frequency (epochs)")
    
    args = parser.parse_args()
    
    # Set random seed
    set_random_seed(args.seed)
    
    # Setup device
    device = setup_device()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save args
    with open(output_dir / "args.json", "w") as f:
        json.dump(vars(args), f, indent=2)
    
    # Create data loaders
    train_items, test_items, classnames = create_data_loaders(args.data_root, args.batch_size)
    num_classes = len(classnames)
    
    # Save classnames
    with open(output_dir / "classnames.txt", "w") as f:
        for name in classnames:
            f.write(f"{name}\n")
    
    # Create transforms (matching CLIP preprocessing)
    transform = transforms.Compose([
        transforms.Resize(224, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create datasets
    train_dataset = FlagDataset(train_items, transform=transform)
    test_dataset = FlagDataset(test_items, transform=transform)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    # Initialize model
    model = HierarchicalRS5MModel(args.checkpoint, classnames, device)
    
    # Compute class weights
    class_weights = compute_class_weights(train_items, num_classes).to(device)
    
    # Setup loss and optimizer
    criterion = FocalLoss(alpha=args.focal_alpha, gamma=args.focal_gamma, weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    print(f"\n🚀 Starting hierarchical training for {args.epochs} epochs...")
    print(f"📊 Dataset: {num_classes} classes, {len(train_items)} train, {len(test_items)} test")
    print(f"🎯 Device: {device}")
    print(f"📝 Output: {output_dir}")
    
    # Training loop
    best_accuracy = 0
    training_log = []
    
    for epoch in range(1, args.epochs + 1):
        print(f"\n📅 Epoch {epoch}/{args.epochs}")
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        scheduler.step()
        
        current_lr = scheduler.get_last_lr()[0]
        print(f"📉 Train Loss: {train_loss:.4f}, LR: {current_lr:.6f}")
        
        # Evaluate
        if epoch % args.eval_freq == 0 or epoch == args.epochs:
            print("🔍 Evaluating...")
            accuracy, macro_f1, micro_f1, preds, labels = evaluate(model, test_loader, device, classnames)
            
            print(f"📊 Accuracy: {accuracy:.4f}")
            print(f"📊 Macro F1: {macro_f1:.4f}")
            print(f"📊 Micro F1: {micro_f1:.4f}")
            
            # Save best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'epoch': epoch,
                    'accuracy': accuracy,
                    'macro_f1': macro_f1,
                    'micro_f1': micro_f1
                }, output_dir / "best_model.pt")
                
                # Save best results
                with open(output_dir / "best_results.json", "w") as f:
                    json.dump({
                        'accuracy': accuracy,
                        'macro_f1': macro_f1,
                        'micro_f1': micro_f1,
                        'predictions': preds,
                        'labels': labels
                    }, f, indent=2)
                
                print(f"💾 New best model saved! Accuracy: {accuracy:.4f}")
        
        # Log training progress
        log_entry = {
            'epoch': epoch,
            'train_loss': train_loss,
            'learning_rate': current_lr
        }
        if epoch % args.eval_freq == 0 or epoch == args.epochs:
            log_entry.update({
                'accuracy': accuracy,
                'macro_f1': macro_f1,
                'micro_f1': micro_f1
            })
        training_log.append(log_entry)
        
        # Save training log
        with open(output_dir / "training_log.json", "w") as f:
            json.dump(training_log, f, indent=2)
    
    print(f"\n🏁 Training complete!")
    print(f"📊 Best accuracy: {best_accuracy:.4f}")
    print(f"📁 Results saved to: {output_dir}")

if __name__ == "__main__":
    main()