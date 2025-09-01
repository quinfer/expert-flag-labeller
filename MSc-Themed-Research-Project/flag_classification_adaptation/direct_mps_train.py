#!/usr/bin/env python3
"""
Direct training script that bypasses DaSSL's device management
This FORCES MPS usage by taking complete control
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import time
from tqdm import tqdm
import os
import sys

# Add paths
sys.path.append('.')
sys.path.append('..')

def train_direct_mps():
    """
    Direct training that bypasses DaSSL completely
    """
    print("="*60)
    print("🚀 DIRECT MPS TRAINING - BYPASSING DaSSL")
    print("="*60)
    
    # 1. Force MPS
    if not torch.backends.mps.is_available():
        print("❌ MPS not available!")
        return
    
    device = torch.device("mps")
    print(f"✅ Using device: {device}")
    
    # 2. Load CLIP model directly
    print("\n📦 Loading CLIP model...")
    import clip
    model, preprocess = clip.load("ViT-B/32", device="cpu")  # Load smaller model
    
    # 3. FORCE to MPS
    print("🔥 Forcing model to MPS...")
    model = model.to(device)
    model = model.float()  # Ensure FP32
    
    # Verify
    print(f"✅ Model on MPS: {next(model.parameters()).is_mps}")
    print(f"✅ Model device: {next(model.parameters()).device}")
    
    # 4. Create simple dataset
    print("\n📊 Creating dataset...")
    from datasets.ni_flags import NIFlags
    from dassl.data.transforms import build_transform
    from dassl.config import get_cfg_default
    
    cfg = get_cfg_default()
    cfg.defrost()
    cfg.DATASET.NAME = "NIFlags"
    cfg.DATASET.ROOT = "../data"
    cfg.freeze()
    
    dataset = NIFlags(cfg)
    
    # Simple data loader - NO WORKERS
    train_loader = DataLoader(
        dataset.train_x,
        batch_size=8,  # Small batch for testing
        shuffle=True,
        num_workers=0,  # CRITICAL: No workers for MPS
        pin_memory=False
    )
    
    print(f"✅ Dataset loaded: {len(dataset.train_x)} training samples")
    
    # 5. Setup training
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    # 6. Training loop with timing
    print("\n🏃 Starting training loop...")
    print("="*60)
    
    model.train()
    
    for epoch in range(2):  # Just 2 epochs for testing
        batch_times = []
        
        for batch_idx, batch in enumerate(train_loader):
            if batch_idx >= 10:  # Just 10 batches for testing
                break
            
            start_time = time.time()
            
            # Get data
            if isinstance(batch, dict):
                images = batch["img"]
                labels = batch["label"]
            else:
                images, labels = batch
            
            # FORCE to MPS
            images = images.to(device)
            labels = labels.to(device)
            
            # Verify first batch
            if batch_idx == 0:
                print(f"📍 First batch - Image device: {images.device}")
                print(f"📍 First batch - Image shape: {images.shape}")
            
            # Forward pass
            with torch.cuda.amp.autocast(enabled=False):  # No AMP for MPS
                # Get image features
                image_features = model.encode_image(images)
                
                # Simple classification head
                logits = image_features @ model.logit_scale.exp() * torch.randn(512, 70).to(device).T
                
                # Loss
                loss = F.cross_entropy(logits, labels)
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Timing
            torch.mps.synchronize()  # Ensure computation is done
            batch_time = time.time() - start_time
            batch_times.append(batch_time)
            
            # Print progress
            print(f"Epoch [{epoch+1}/2] Batch [{batch_idx+1}/10] "
                  f"Time: {batch_time:.3f}s Loss: {loss.item():.4f}")
        
        # Summary
        avg_time = sum(batch_times) / len(batch_times)
        print(f"\n📊 Epoch {epoch+1} Summary:")
        print(f"   Average batch time: {avg_time:.3f}s")
        print(f"   Total epoch time: {sum(batch_times):.1f}s")
        
        if avg_time > 10:
            print("   ❌ Still slow - MPS not working properly!")
        else:
            print("   ✅ Fast - MPS is working!")
    
    print("\n" + "="*60)
    print("🏁 Training complete!")
    print("="*60)


def diagnose_cocoop_issue():
    """
    Diagnose why CoCoOp isn't using MPS
    """
    print("\n" + "="*60)
    print("🔍 DIAGNOSING COCOOP MPS ISSUE")
    print("="*60)
    
    # Check if model stays on MPS through the pipeline
    from trainers.cocoop import CoCoOp
    from dassl.config import get_cfg_default
    
    cfg = get_cfg_default()
    cfg.defrost()
    cfg.TRAINER.NAME = "CoCoOp"
    cfg.DATASET.NAME = "NIFlags"
    cfg.DATASET.ROOT = "../data"
    cfg.MODEL.BACKBONE.NAME = "RN50"
    cfg.freeze()
    
    print("\n1️⃣ Creating CoCoOp trainer...")
    
    # Monkey-patch to track device changes
    import trainers.cocoop as cocoop_module
    original_init = cocoop_module.CustomCLIP.__init__
    
    def tracked_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        print(f"   CustomCLIP init - device: {next(self.parameters()).device}")
    
    cocoop_module.CustomCLIP.__init__ = tracked_init
    
    # Try to create trainer
    from dassl.engine import build_trainer
    trainer = build_trainer(cfg)
    
    print(f"\n2️⃣ After build_trainer:")
    print(f"   Model device: {next(trainer.model.parameters()).device}")
    print(f"   Model on MPS: {next(trainer.model.parameters()).is_mps}")
    
    # Check after train() is called
    print("\n3️⃣ The issue is likely in trainer.train() method")
    print("   DaSSL's TrainerX.train() might be moving model back to CPU")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "diagnose":
        diagnose_cocoop_issue()
    else:
        # Run direct training
        train_direct_mps()
