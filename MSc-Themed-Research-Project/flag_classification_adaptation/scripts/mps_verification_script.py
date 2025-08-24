#!/usr/bin/env python3
"""
MPS Verification Script - Check if model is REALLY on MPS
"""

import torch
import torch.nn as nn
import time
import psutil
import subprocess

def check_gpu_usage():
    """Check actual GPU usage on macOS"""
    try:
        # Use powermetrics to check GPU usage
        result = subprocess.run(
            ['sudo', 'powermetrics', '--samplers', 'gpu_power', '-i', '1000', '-n', '1'],
            capture_output=True, text=True, timeout=2
        )
        if "GPU" in result.stdout:
            print("✅ GPU activity detected")
        else:
            print("❌ No GPU activity")
    except:
        print("ℹ️  Cannot check GPU (need sudo). Check Activity Monitor > Window > GPU History")

def verify_mps_training():
    """Verify if training is actually using MPS"""
    
    print("="*60)
    print("🔍 MPS VERIFICATION TEST")
    print("="*60)
    
    # 1. Check MPS availability
    print("\n1️⃣ MPS Availability:")
    print(f"   MPS available: {torch.backends.mps.is_available()}")
    print(f"   MPS built: {torch.backends.mps.is_built()}")
    
    # 2. Create test model
    print("\n2️⃣ Creating test model...")
    model = nn.Sequential(
        nn.Conv2d(3, 64, 3),
        nn.ReLU(),
        nn.Conv2d(64, 128, 3),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
        nn.Linear(128, 70)  # 70 classes for your flags
    )
    
    # 3. Test on CPU
    print("\n3️⃣ Testing on CPU:")
    model_cpu = model
    x_cpu = torch.randn(16, 3, 224, 224)  # Your batch size
    
    start = time.time()
    with torch.no_grad():
        for _ in range(5):
            _ = model_cpu(x_cpu)
    cpu_time = (time.time() - start) / 5
    print(f"   CPU time per batch: {cpu_time:.3f}s")
    
    # 4. Test on MPS
    print("\n4️⃣ Testing on MPS:")
    device = torch.device("mps")
    model_mps = model.to(device)
    x_mps = torch.randn(16, 3, 224, 224).to(device)
    
    # Verify tensors are on MPS
    print(f"   Model on MPS: {next(model_mps.parameters()).is_mps}")
    print(f"   Data on MPS: {x_mps.is_mps}")
    
    # Warm up
    for _ in range(10):
        _ = model_mps(x_mps)
    torch.mps.synchronize()
    
    start = time.time()
    with torch.no_grad():
        for _ in range(5):
            _ = model_mps(x_mps)
            torch.mps.synchronize()
    mps_time = (time.time() - start) / 5
    print(f"   MPS time per batch: {mps_time:.3f}s")
    print(f"   Speedup: {cpu_time/mps_time:.1f}x")
    
    # 5. Check if speedup is reasonable
    print("\n5️⃣ Diagnosis:")
    if mps_time < cpu_time * 0.5:  # At least 2x speedup
        print("   ✅ MPS is working correctly!")
    else:
        print("   ❌ MPS is NOT working! Model may be falling back to CPU")
        print("   Possible reasons:")
        print("   - Model not actually moved to MPS")
        print("   - Operations falling back to CPU")
        print("   - MPS device not properly initialized")
    
    return mps_time < cpu_time * 0.5


def test_cocoop_on_mps():
    """Test if CoCoOp model is actually on MPS"""
    print("\n" + "="*60)
    print("🧪 TESTING COCOOP MODEL")
    print("="*60)
    
    try:
        # Import your CoCoOp setup
        from dassl.config import get_cfg_default
        from trainers.cocoop import CoCoOp
        import clip
        
        # Create minimal config
        cfg = get_cfg_default()
        cfg.defrost()
        cfg.TRAINER.NAME = "CoCoOp"
        cfg.TRAINER.COCOOP.N_CTX = 16
        cfg.TRAINER.COCOOP.PREC = "fp32"
        cfg.MODEL.BACKBONE.NAME = "RN50"
        cfg.freeze()
        
        print("\n1️⃣ Loading CLIP model...")
        clip_model, preprocess = clip.load("RN50", device="cpu")
        
        print("\n2️⃣ Checking model device before MPS move:")
        print(f"   On CPU: {next(clip_model.parameters()).is_cpu}")
        
        print("\n3️⃣ Moving to MPS...")
        device = torch.device("mps")
        clip_model = clip_model.to(device)
        
        print("\n4️⃣ Checking model device after MPS move:")
        print(f"   On MPS: {next(clip_model.parameters()).is_mps}")
        print(f"   Device: {next(clip_model.parameters()).device}")
        
        # Test forward pass
        print("\n5️⃣ Testing forward pass...")
        x = torch.randn(8, 3, 224, 224).to(device)
        
        start = time.time()
        with torch.no_grad():
            features = clip_model.encode_image(x)
        torch.mps.synchronize()
        forward_time = time.time() - start
        
        print(f"   Forward pass time: {forward_time:.3f}s")
        print(f"   Output shape: {features.shape}")
        print(f"   Output device: {features.device}")
        
        if forward_time < 5.0:  # Should be fast on MPS
            print("   ✅ Model is using MPS!")
        else:
            print("   ❌ Model is NOT using MPS (too slow)")
            
    except Exception as e:
        print(f"   ❌ Error testing CoCoOp: {e}")


def check_activity_monitor():
    """Instructions for checking GPU usage"""
    print("\n" + "="*60)
    print("📊 HOW TO VERIFY GPU USAGE")
    print("="*60)
    print("""
1. Open Activity Monitor
2. Go to Window → GPU History
3. Run your training script
4. You should see GPU usage spike when training

If GPU usage is 0%:
- Model is NOT on MPS
- Operations are falling back to CPU

If GPU usage is high (>50%):
- Model IS using MPS correctly
    """)


def fix_recommendations():
    """Provide specific fixes"""
    print("\n" + "="*60)
    print("🔧 FIXES TO TRY")
    print("="*60)
    
    print("""
1. REDUCE WORKERS (Critical for MPS):
   DATALOADER.TRAIN_X.NUM_WORKERS 0
   
2. VERIFY MODEL DEVICE in trainers/cocoop.py:
   Add after model creation:
   ```python
   print(f"Model device: {next(self.model.parameters()).device}")
   print(f"Model on MPS: {next(self.model.parameters()).is_mps}")
   ```

3. FORCE MPS in CoCoOp build_model():
   ```python
   # After creating model
   device = torch.device("mps")
   self.model = self.model.to(device)
   
   # Verify
   assert next(self.model.parameters()).is_mps, "Model not on MPS!"
   ```

4. TRY SMALLER MODEL:
   MODEL.BACKBONE.NAME ViT-B/32
   
5. DISABLE MULTIPROCESSING:
   export PYTORCH_ENABLE_MPS_FALLBACK=1
   export OMP_NUM_THREADS=1
   
6. CHECK FOR CPU FALLBACK:
   Some operations may not be supported on MPS and fall back to CPU.
   Run with: PYTORCH_MPS_FALLBACK_VERBOSE=1 python train.py
    """)


if __name__ == "__main__":
    # Run verification
    is_working = verify_mps_training()
    
    # Test CoCoOp specifically
    test_cocoop_on_mps()
    
    # Check system
    check_activity_monitor()
    
    # Provide fixes
    if not is_working:
        fix_recommendations()
    
    print("\n" + "="*60)
    print("🎯 SUMMARY")
    print("="*60)
    if is_working:
        print("✅ MPS is working for basic models")
        print("⚠️  But your CoCoOp training is still slow")
        print("→ The model may not be properly moved to MPS")
    else:
        print("❌ MPS is NOT working properly")
        print("→ Check the fixes above")
