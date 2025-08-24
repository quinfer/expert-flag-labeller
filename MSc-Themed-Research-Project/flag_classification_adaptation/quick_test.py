#!/usr/bin/env python3
"""
Quick test to verify M4 Max setup and basic functionality
"""
import torch
import sys
import os

def test_pytorch_mps():
    print("🔍 Testing PyTorch MPS Setup...")
    print(f"PyTorch version: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print(f"MPS built: {torch.backends.mps.is_built()}")
    
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print(f"✅ Using device: {device}")
        
        # Test basic operations
        x = torch.randn(100, 100).to(device)
        y = torch.mm(x, x.t())
        print(f"✅ Matrix multiplication test passed: {y.shape}")
        
        return device
    else:
        print("⚠️  MPS not available, falling back to CPU")
        return torch.device("cpu")

def test_data_structure():
    print("\n📁 Testing data structure...")
    
    expected_paths = [
        "../data",
        "../data/annotations", 
        "../data/images",
        "../data/processed"
    ]
    
    for path in expected_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
        else:
            print(f"⚠️  Missing: {path}")

def test_imports():
    print("\n📦 Testing critical imports...")
    
    try:
        import clip
        print("✅ CLIP imported successfully")
    except ImportError as e:
        print(f"❌ CLIP import failed: {e}")
    
    try:
        import open_clip
        print("✅ OpenCLIP imported successfully")
    except ImportError as e:
        print(f"❌ OpenCLIP import failed: {e}")
    
    try:
        from dassl.config import get_cfg_default
        print("✅ DaSsL imported successfully")
    except ImportError as e:
        print(f"❌ DaSsL import failed: {e}")

if __name__ == "__main__":
    print("🚀 FLAG CLASSIFICATION QUICK TEST")
    print("=" * 50)
    
    device = test_pytorch_mps()
    test_data_structure() 
    test_imports()
    
    print("\n" + "=" * 50)
    print("✅ Quick test complete!")
    print("Next steps:")
    print("1. Run: conda activate flag_classification")
    print("2. Add your expert classifications to ../data/annotations/")
    print("3. Copy flag images to ../data/images/")
    print("4. Run data preparation script")
