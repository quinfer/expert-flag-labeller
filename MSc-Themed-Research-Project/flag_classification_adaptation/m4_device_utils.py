#!/usr/bin/env python3
"""
Device Compatibility Utilities for M4 Max MacBook Pro
Handles MPS (Metal Performance Shaders) integration for Li et al.'s code
"""

import torch
import os
import psutil
from typing import Tuple, Dict, Any


class M4DeviceManager:
    """
    Device management for M4 Max with MPS support
    """
    
    def __init__(self):
        self.device = self._get_optimal_device()
        self.device_info = self._get_device_info()
        self._optimize_for_device()
    
    def _get_optimal_device(self) -> torch.device:
        """Get the best available device"""
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    
    def _get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information"""
        info = {
            "device_type": str(self.device),
            "pytorch_version": torch.__version__,
        }
        
        if self.device.type == "mps":
            info.update({
                "mps_available": torch.backends.mps.is_available(),
                "mps_built": torch.backends.mps.is_built(),
                "unified_memory_gb": psutil.virtual_memory().total // (1024**3),
                "available_memory_gb": psutil.virtual_memory().available // (1024**3),
            })
        elif self.device.type == "cuda":
            info.update({
                "cuda_version": torch.version.cuda,
                "gpu_count": torch.cuda.device_count(),
                "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
            })
        
        return info
    
    def _optimize_for_device(self):
        """Apply device-specific optimizations"""
        if self.device.type == "mps":
            # MPS optimizations for M4 Max
            os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
            torch.backends.mps.empty_cache()
            
            # Enable optimized operations
            torch.backends.cuda.matmul.allow_tf32 = False  # Not applicable for MPS but good practice
            
        elif self.device.type == "cuda":
            # CUDA optimizations
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
    
    def get_optimal_batch_size(self, model_type: str = "RN50") -> int:
        """Get optimal batch size for different model types"""
        if self.device.type == "mps":
            # Conservative batch sizes for M4 Max MPS
            batch_sizes = {
                "RN50": 32,
                "ViT-B/16": 24,
                "ViT-L/14": 16,
                "ViT-H/14": 8,
            }
        elif self.device.type == "cuda":
            # More aggressive batch sizes for CUDA
            batch_sizes = {
                "RN50": 64,
                "ViT-B/16": 48,
                "ViT-L/14": 32,
                "ViT-H/14": 16,
            }
        else:
            # CPU batch sizes
            batch_sizes = {
                "RN50": 8,
                "ViT-B/16": 4,
                "ViT-L/14": 2,
                "ViT-H/14": 1,
            }
        
        return batch_sizes.get(model_type, 16)  # Default fallback
    
    def clear_cache(self):
        """Clear device cache"""
        if self.device.type == "mps":
            torch.backends.mps.empty_cache()
        elif self.device.type == "cuda":
            torch.cuda.empty_cache()
    
    def monitor_memory(self) -> Dict[str, float]:
        """Monitor memory usage"""
        if self.device.type == "mps":
            memory = psutil.virtual_memory()
            return {
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percentage": memory.percent,
            }
        elif self.device.type == "cuda":
            return {
                "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
                "cached_gb": torch.cuda.memory_reserved() / (1024**3),
                "percentage": (torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()) * 100,
            }
        else:
            memory = psutil.virtual_memory()
            return {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percentage": memory.percent,
            }
    
    def print_device_info(self):
        """Print comprehensive device information"""
        print("=" * 50)
        print("🖥️  DEVICE CONFIGURATION")
        print("=" * 50)
        
        for key, value in self.device_info.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        memory_info = self.monitor_memory()
        print(f"\n💾 MEMORY STATUS:")
        for key, value in memory_info.items():
            if isinstance(value, float):
                print(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
        print("=" * 50)


def patch_dassl_for_mps():
    """
    Patch DaSsL library calls to work with MPS
    This modifies the device selection in Li et al.'s code
    """
    
    # Create a monkey patch for CUDA checks
    original_cuda_available = torch.cuda.is_available
    
    def enhanced_device_check():
        """Enhanced device availability check"""
        if torch.backends.mps.is_available():
            return True  # Treat MPS as CUDA for compatibility
        return original_cuda_available()
    
    # Apply the patch
    torch.cuda.is_available = enhanced_device_check
    
    print("✅ Applied MPS compatibility patch for DaSsL")


def get_model_device_config(cfg, model_name: str = "RN50") -> Dict[str, Any]:
    """
    Get optimized device configuration for model training
    
    Args:
        cfg: DaSsL configuration object
        model_name: Name of the model backbone
        
    Returns:
        Dictionary with optimized configuration
    """
    device_manager = M4DeviceManager()
    
    # Update configuration for optimal performance
    config = {
        "device": device_manager.device,
        "batch_size": device_manager.get_optimal_batch_size(model_name),
        "precision": "fp32",  # MPS works better with fp32 currently
        "num_workers": min(8, os.cpu_count()),  # Optimal for M4 Max
        "pin_memory": device_manager.device.type != "mps",  # Pin memory not needed for MPS
    }
    
    # Apply to cfg if provided
    if hasattr(cfg, 'DATALOADER'):
        if hasattr(cfg.DATALOADER, 'TRAIN_X'):
            cfg.DATALOADER.TRAIN_X.BATCH_SIZE = config["batch_size"]
        if hasattr(cfg.DATALOADER, 'TEST'):
            cfg.DATALOADER.TEST.BATCH_SIZE = config["batch_size"] * 2  # Can use larger batch for inference
    
    if hasattr(cfg, 'TRAINER') and hasattr(cfg.TRAINER, 'COCOOP'):
        cfg.TRAINER.COCOOP.PREC = config["precision"]
    
    return config


class MPS_SafeTensor:
    """
    Wrapper for safe tensor operations on MPS
    Some operations might need fallback to CPU
    """
    
    @staticmethod
    def safe_operation(operation, tensor, *args, **kwargs):
        """
        Safely execute tensor operation with MPS fallback
        """
        try:
            return operation(tensor, *args, **kwargs)
        except RuntimeError as e:
            if "MPS" in str(e):
                print(f"⚠️  MPS operation failed, falling back to CPU: {e}")
                cpu_tensor = tensor.cpu()
                result = operation(cpu_tensor, *args, **kwargs)
                return result.to(tensor.device) if hasattr(result, 'to') else result
            else:
                raise e


def setup_m4_training_environment():
    """
    Complete setup for M4 Max training environment
    """
    print("🚀 Setting up M4 Max training environment...")
    
    # Initialize device manager
    device_manager = M4DeviceManager()
    device_manager.print_device_info()
    
    # Apply compatibility patches
    patch_dassl_for_mps()
    
    # Set environment variables for optimal performance
    os.environ['OMP_NUM_THREADS'] = str(min(8, os.cpu_count()))
    os.environ['MKL_NUM_THREADS'] = str(min(8, os.cpu_count()))
    
    print("✅ M4 Max environment setup complete!")
    return device_manager


# Example usage and testing functions
def test_device_setup():
    """Test device setup and basic operations"""
    print("🧪 Testing device setup...")
    
    device_manager = setup_m4_training_environment()
    
    # Test basic tensor operations
    test_tensor = torch.randn(100, 100).to(device_manager.device)
    result = torch.mm(test_tensor, test_tensor.t())
    
    print(f"✅ Matrix multiplication test passed on {device_manager.device}")
    print(f"   Result shape: {result.shape}")
    
    # Test memory monitoring
    memory_info = device_manager.monitor_memory()
    print(f"💾 Memory usage after test: {memory_info['percentage']:.1f}%")
    
    # Clean up
    device_manager.clear_cache()
    
    return device_manager


if __name__ == "__main__":
    # Run device setup test
    device_manager = test_device_setup()
    
    # Print optimal configurations for different models
    print("\n📊 OPTIMAL CONFIGURATIONS:")
    models = ["RN50", "ViT-B/16", "ViT-L/14"]
    for model in models:
        batch_size = device_manager.get_optimal_batch_size(model)
        print(f"{model}: Batch size {batch_size}")
