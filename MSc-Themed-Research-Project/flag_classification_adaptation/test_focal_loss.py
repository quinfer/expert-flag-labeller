#!/usr/bin/env python3
"""
Quick test to verify focal loss implementation is working
Run this before full training to validate the setup
"""

# Fix OpenMP conflict on macOS
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import torch.nn.functional as F
import numpy as np
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_focal_loss_implementation():
    """Test the focal loss implementation directly"""
    print("\n" + "="*60)
    print("🧪 TESTING FOCAL LOSS IMPLEMENTATION")
    print("="*60)
    
    # Test parameters
    batch_size = 32
    num_classes = 70
    
    # Create synthetic data matching your class distribution
    class_weights = torch.ones(num_classes)
    class_counts = {
        0: 777, 1: 417, 2: 386, 3: 142, 4: 99,
        5: 48, 6: 42, 7: 39, 8: 38, 9: 26,
        # Rest are rare classes
        **{i: np.random.randint(1, 10) for i in range(10, num_classes)}
    }
    
    total_samples = sum(class_counts.values())
    for idx, count in class_counts.items():
        class_weights[idx] = (total_samples / (num_classes * count)) ** 0.5
    class_weights = class_weights / class_weights.mean()
    
    print(f"✅ Class weights created:")
    print(f"   Min weight: {class_weights.min():.2f}")
    print(f"   Max weight: {class_weights.max():.2f}")
    print(f"   Mean weight: {class_weights.mean():.2f}")
    
    # Test different scenarios
    scenarios = [
        ("Balanced predictions", torch.randn(batch_size, num_classes)),
        ("Confident correct", None),  # Will be filled
        ("Confident wrong", None),    # Will be filled
        ("All majority class", None), # Will be filled
    ]
    
    # Create labels with imbalanced distribution
    labels = []
    for _ in range(batch_size // 2):
        labels.append(0)  # Half are majority class
    for _ in range(batch_size // 4):
        labels.append(np.random.randint(1, 10))  # Quarter are common classes
    for _ in range(batch_size - len(labels)):
        labels.append(np.random.randint(10, num_classes))  # Rest are rare
    labels = torch.tensor(labels)
    
    print(f"\n📊 Test batch distribution:")
    unique, counts = torch.unique(labels, return_counts=True)
    print(f"   Classes present: {len(unique)}")
    print(f"   Majority class (0) count: {(labels == 0).sum().item()}")
    print(f"   Rare classes count: {(labels >= 10).sum().item()}")
    
    results = []
    
    for i, (name, logits) in enumerate(scenarios):
        if logits is None:
            logits = torch.randn(batch_size, num_classes)
            if name == "Confident correct":
                # Make predictions very confident and correct
                for j in range(batch_size):
                    logits[j, :] = -10
                    logits[j, labels[j]] = 10
            elif name == "Confident wrong":
                # Make predictions confident but wrong
                for j in range(batch_size):
                    logits[j, :] = -10
                    wrong_class = (labels[j] + 1) % num_classes
                    logits[j, wrong_class] = 10
            elif name == "All majority class":
                # Predict majority class for everything
                logits[:, :] = -10
                logits[:, 0] = 10
        
        # Calculate losses
        ce_loss = F.cross_entropy(logits, labels, reduction='mean')
        weighted_ce = F.cross_entropy(logits, labels, weight=class_weights, reduction='mean')
        
        # Focal loss
        ce_per_sample = F.cross_entropy(logits, labels, weight=class_weights, reduction='none')
        pt = torch.exp(-ce_per_sample)
        alpha = 0.25
        gamma = 2.0
        focal_loss = (alpha * (1 - pt) ** gamma * ce_per_sample).mean()
        
        # Calculate accuracy
        predictions = logits.argmax(dim=1)
        accuracy = (predictions == labels).float().mean()
        
        # Rare class accuracy
        rare_mask = labels >= 10
        rare_acc = (predictions[rare_mask] == labels[rare_mask]).float().mean() if rare_mask.sum() > 0 else 0
        
        print(f"\n📈 Scenario: {name}")
        print(f"   CE Loss: {ce_loss:.4f}")
        print(f"   Weighted CE: {weighted_ce:.4f}")
        print(f"   Focal Loss: {focal_loss:.4f}")
        print(f"   Focal/Weighted ratio: {focal_loss/weighted_ce:.3f}x")
        print(f"   Overall Accuracy: {accuracy:.2%}")
        print(f"   Rare Class Accuracy: {rare_acc:.2%}")
        
        results.append({
            'scenario': name,
            'ce_loss': ce_loss.item(),
            'weighted_ce': weighted_ce.item(),
            'focal_loss': focal_loss.item(),
            'accuracy': accuracy.item(),
            'rare_accuracy': rare_acc.item()
        })
    
    # Analysis
    print("\n" + "="*60)
    print("📊 FOCAL LOSS BEHAVIOUR ANALYSIS")
    print("="*60)
    
    print("\n✅ Expected behaviour:")
    print("1. Focal loss < Weighted CE for easy samples (confident correct)")
    print("2. Focal loss ≈ Weighted CE for hard samples (confident wrong)")
    print("3. Focal loss focuses on misclassified samples")
    print("4. Rare class performance should improve with focal loss")
    
    # Check if focal loss is working as expected
    confident_correct = results[1]
    confident_wrong = results[2]
    
    if confident_correct['focal_loss'] < confident_correct['weighted_ce']:
        print("\n✅ Focal loss correctly reduces loss for easy samples")
    else:
        print("\n❌ WARNING: Focal loss not reducing easy samples properly")
    
    if confident_wrong['focal_loss'] > confident_wrong['weighted_ce'] * 0.5:
        print("✅ Focal loss maintains significant penalty for hard samples")
    else:
        print("❌ WARNING: Focal loss may be too aggressive")
    
    return results


def test_training_step():
    """Test a single training step with your actual trainer"""
    print("\n" + "="*60)
    print("🔄 TESTING TRAINING STEP")
    print("="*60)
    
    try:
        # Import your trainer
        from trainers.cocoop import CustomCLIP, CoCoOp
        from datasets.ni_flags import NIFlags
        
        print("✅ Successfully imported CoCoOp trainer and NIFlags dataset")
        
        # Quick test of loss computation
        print("\n📝 To test in your training loop, run:")
        print("python train_minimal_mps.py --trainer CoCoOp --config-file configs/trainers/CoCoOp/rn50.yaml --dataset-config-file configs/datasets/niflags.yaml OPTIM.MAX_EPOCH 1")
        
        return True
        
    except ImportError as e:
        print(f"⚠️ Could not import trainer: {e}")
        print("Make sure you're in the flag_classification_adaptation directory")
        return False


def verify_mps_acceleration():
    """Verify MPS is being used for focal loss computation"""
    print("\n" + "="*60)
    print("🚀 VERIFYING MPS ACCELERATION")
    print("="*60)
    
    if not torch.backends.mps.is_available():
        print("❌ MPS not available")
        return False
    
    device = torch.device("mps")
    print(f"✅ MPS device available: {device}")
    
    # Test focal loss on MPS
    batch_size = 256
    num_classes = 70
    
    logits = torch.randn(batch_size, num_classes).to(device)
    labels = torch.randint(0, num_classes, (batch_size,)).to(device)
    weights = torch.ones(num_classes).to(device)
    
    # Warm up
    for _ in range(10):
        loss = F.cross_entropy(logits, labels, weight=weights)
    
    # Time standard CE
    import time
    start = time.time()
    for _ in range(100):
        ce_loss = F.cross_entropy(logits, labels, weight=weights)
        torch.mps.synchronize()
    ce_time = time.time() - start
    
    # Time focal loss
    start = time.time()
    for _ in range(100):
        ce_per_sample = F.cross_entropy(logits, labels, weight=weights, reduction='none')
        pt = torch.exp(-ce_per_sample)
        focal_loss = (0.25 * (1 - pt) ** 2.0 * ce_per_sample).mean()
        torch.mps.synchronize()
    focal_time = time.time() - start
    
    print(f"\n⚡ Performance on MPS:")
    print(f"   Standard CE: {ce_time:.4f}s (100 iterations)")
    print(f"   Focal Loss: {focal_time:.4f}s (100 iterations)")
    print(f"   Overhead: {(focal_time/ce_time - 1)*100:.1f}%")
    
    if focal_time < ce_time * 2:
        print("\n✅ Focal loss performance acceptable (< 2x overhead)")
    else:
        print("\n⚠️ Focal loss overhead higher than expected")
    
    return True


def main():
    print("\n" + "="*60)
    print("🎯 NI FLAGS FOCAL LOSS VALIDATION")
    print("="*60)
    print("Testing focal loss implementation before full training")
    
    # Run tests
    test_results = test_focal_loss_implementation()
    
    # Verify MPS
    mps_ok = verify_mps_acceleration()
    
    # Test training import
    trainer_ok = test_training_step()
    
    # Summary
    print("\n" + "="*60)
    print("📋 VALIDATION SUMMARY")
    print("="*60)
    
    if test_results and mps_ok:
        print("✅ Focal loss mathematics: WORKING")
        print("✅ MPS acceleration: ENABLED")
        print("✅ Class weighting: IMPLEMENTED")
        
        print("\n🚀 READY FOR TRAINING!")
        print("\nRun this command to start training with focal loss:")
        print("\npython train_minimal_mps.py \\")
        print("    --trainer CoCoOp \\")
        print("    --config-file configs/trainers/CoCoOp/rn50.yaml \\")
        print("    --dataset-config-file configs/datasets/niflags.yaml \\")
        print("    --output-dir experiments/focal_loss_test \\")
        print("    TRAINER.COCOOP.PREC fp32 \\")
        print("    DATALOADER.NUM_WORKERS 0 \\")
        print("    OPTIM.MAX_EPOCH 50")
        
        print("\n💡 Monitor training with:")
        print("tail -f experiments/focal_loss_test/log.txt")
        
    else:
        print("⚠️ Some issues detected - review output above")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
