#!/usr/bin/env python3
"""
Fixed quick test to verify M4 Max setup and basic functionality
Handles common import issues and provides clear diagnostics
"""
import sys
import os

def test_python_environment():
    """Test basic Python environment"""
    print("🐍 Testing Python Environment...")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")

def test_pytorch_mps():
    """Test PyTorch and MPS availability"""
    print("\n🔍 Testing PyTorch MPS Setup...")
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ PyTorch imported successfully")
        
        # Test MPS availability
        if hasattr(torch.backends, 'mps'):
            mps_available = torch.backends.mps.is_available()
            mps_built = torch.backends.mps.is_built()
            print(f"MPS available: {mps_available}")
            print(f"MPS built: {mps_built}")
            
            if mps_available:
                device = torch.device("mps")
                print(f"✅ Using device: {device}")
                
                # Test basic tensor operations
                try:
                    x = torch.randn(10, 10).to(device)
                    y = torch.mm(x, x.t())
                    print(f"✅ Basic tensor operations work: {y.shape}")
                    return device
                except Exception as e:
                    print(f"⚠️  MPS tensor operations failed: {e}")
                    print("Falling back to CPU")
                    return torch.device("cpu")
            else:
                print("⚠️  MPS not available, using CPU")
                return torch.device("cpu")
        else:
            print("⚠️  MPS backend not found, using CPU")
            return torch.device("cpu")
            
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        print("Please check your PyTorch installation")
        return None

def test_critical_imports():
    """Test imports for all critical dependencies"""
    print("\n📦 Testing Critical Imports...")
    
    imports_to_test = [
        ("torch", "PyTorch"),
        ("torchvision", "TorchVision"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
    ]
    
    for module_name, display_name in imports_to_test:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {display_name} {version}")
        except ImportError as e:
            print(f"❌ {display_name} import failed: {e}")

def test_optional_imports():
    """Test optional but important dependencies"""
    print("\n🔧 Testing Optional Dependencies...")
    
    optional_imports = [
        ("dassl", "DaSsL Framework"),
        ("clip", "CLIP"),
        ("open_clip", "OpenCLIP"),  
        ("timm", "TIMM"),
        ("yacs", "YACS")
    ]
    
    for module_name, display_name in optional_imports:
        try:
            __import__(module_name)
            print(f"✅ {display_name} available")
        except ImportError as e:
            print(f"⚠️  {display_name} not available: {e}")
            if module_name == "dassl":
                print("    Install with: pip install git+https://github.com/KaiyangZhou/Dassl.pytorch.git")
            elif module_name == "clip":
                print("    This will be available from Li et al.'s code")

def test_data_structure():
    """Test expected data structure"""
    print("\n📁 Testing Data Structure...")
    
    # Check for Li et al.'s code
    li_code_paths = [
        "../final_code",
        "../final_code/train.py",
        "../final_code/trainers",
        "../final_code/datasets"
    ]
    
    for path in li_code_paths:
        if os.path.exists(path):
            print(f"✅ Found Li et al.'s code: {path}")
        else:
            print(f"⚠️  Missing: {path}")
    
    # Check for data directories
    data_paths = [
        "../data",
        "../data/annotations",
        "../data/images", 
        "../data/processed"
    ]
    
    for path in data_paths:
        if os.path.exists(path):
            print(f"✅ Found data directory: {path}")
        else:
            print(f"⚠️  Missing data directory: {path} (will be created as needed)")

def test_memory_and_performance():
    """Test system memory and performance indicators"""
    print("\n💾 Testing System Resources...")
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"Total RAM: {memory.total // (1024**3)}GB")
        print(f"Available RAM: {memory.available // (1024**3)}GB")
        print(f"CPU cores: {psutil.cpu_count()}")
        
        if memory.total >= 32 * (1024**3):  # 32GB+
            print("✅ Sufficient memory for large models")
        else:
            print("⚠️  Limited memory - use smaller batch sizes")
            
    except ImportError:
        print("psutil not available - install with: pip install psutil")

def main():
    """Run all tests"""
    print("🚀 FLAG CLASSIFICATION ENVIRONMENT TEST")
    print("=" * 60)
    
    test_python_environment()
    device = test_pytorch_mps()
    test_critical_imports()
    test_optional_imports()
    test_data_structure()
    test_memory_and_performance()
    
    print("\n" + "=" * 60)
    
    if device is not None:
        print("✅ ENVIRONMENT TEST COMPLETE!")
        print(f"🖥️  Primary compute device: {device}")
        
        print("\nNext steps for Week 9:")
        print("1. Copy Li et al.'s code components to your adaptation directory")
        print("2. Create dataset class for your expert flag annotations")
        print("3. Modify trainer for hierarchical flag prompts")
        print("4. Test with small dataset subset")
        
        if device.type == "mps":
            print("\n🚀 M4 Max optimizations:")
            print("   - Use batch sizes: RN50=32, ViT-B/16=24")
            print("   - Prefer fp32 precision for stability")
            print("   - Take advantage of unified memory architecture")
    else:
        print("❌ ENVIRONMENT TEST FAILED!")
        print("Please fix PyTorch installation before proceeding")

if __name__ == "__main__":
    main()
