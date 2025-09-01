#!/usr/bin/env python3
"""
Baseline CLIP test - no learning, just zero-shot classification
This establishes the floor performance without any training
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import clip
from PIL import Image
import numpy as np
from pathlib import Path
import json

def test_baseline_clip(data_dir="../data/ni_flags", model_name="RN50"):
    """
    Test zero-shot CLIP performance on your dataset
    No training, just direct classification
    """
    print("\n" + "="*60)
    print("🧪 BASELINE CLIP TEST (Zero-Shot)")
    print("="*60)
    
    # Load CLIP model
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)
    print(f"✅ Loaded CLIP {model_name} on {device}")
    
    # Load class names
    classnames_file = Path(data_dir) / "classnames.txt"
    if not classnames_file.exists():
        print(f"❌ {classnames_file} not found")
        return
    
    with open(classnames_file, 'r') as f:
        classnames = [line.strip() for line in f.readlines()]
    
    print(f"📊 Found {len(classnames)} classes")
    
    # Create text prompts (baseline CLIP style)
    text_prompts = []
    for classname in classnames:
        # Simple prompt - baseline CLIP
        prompt = f"a photo of a {classname.replace('_', ' ').lower()} flag"
        text_prompts.append(prompt)
    
    print("\n📝 Example prompts:")
    for i in range(min(3, len(text_prompts))):
        print(f"   {text_prompts[i]}")
    
    # Encode text
    print("\n🔤 Encoding text prompts...")
    text_tokens = clip.tokenize(text_prompts).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    
    # Test on validation set
    val_file = Path(data_dir) / "val.txt"
    if not val_file.exists():
        print(f"❌ {val_file} not found")
        return
    
    # Read validation images
    val_images = []
    val_labels = []
    with open(val_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                img_path, label = parts
                val_images.append(Path(data_dir) / img_path)
                val_labels.append(int(label))
    
    print(f"\n📸 Testing on {len(val_images)} validation images...")
    
    # Classify images
    correct = 0
    per_class_correct = {i: 0 for i in range(len(classnames))}
    per_class_total = {i: 0 for i in range(len(classnames))}
    
    for img_path, true_label in zip(val_images[:100], val_labels[:100]):  # Test first 100
        if not img_path.exists():
            continue
        
        # Load and preprocess image
        image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
        
        # Get image features
        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Calculate similarity
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        
        # Get prediction
        pred_label = similarity.argmax().item()
        
        # Update counts
        per_class_total[true_label] += 1
        if pred_label == true_label:
            correct += 1
            per_class_correct[true_label] += 1
    
    # Calculate accuracies
    overall_accuracy = correct / min(100, len(val_images)) * 100
    
    # Category-level accuracy
    category_correct = 0
    for img_path, true_label in zip(val_images[:100], val_labels[:100]):
        if not img_path.exists():
            continue
        
        true_category = classnames[true_label].split('-')[0]
        
        # Get prediction
        image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        pred_label = similarity.argmax().item()
        pred_category = classnames[pred_label].split('-')[0]
        
        if pred_category == true_category:
            category_correct += 1
    
    category_accuracy = category_correct / min(100, len(val_images)) * 100
    
    print("\n" + "="*60)
    print("📊 BASELINE CLIP RESULTS (Zero-Shot)")
    print("="*60)
    print(f"Overall Accuracy: {overall_accuracy:.1f}%")
    print(f"Category-Level Accuracy: {category_accuracy:.1f}%")
    
    # Per-class breakdown
    print("\n📈 Per-Class Performance (samples > 0):")
    for class_id in range(min(10, len(classnames))):
        if per_class_total[class_id] > 0:
            acc = per_class_correct[class_id] / per_class_total[class_id] * 100
            print(f"   {classnames[class_id][:30]:30} : {acc:5.1f}% ({per_class_total[class_id]} samples)")
    
    return overall_accuracy, category_accuracy


def compare_prompting_strategies():
    """
    Compare different prompting strategies
    """
    print("\n" + "="*60)
    print("🔬 COMPARING PROMPTING STRATEGIES")
    print("="*60)
    
    strategies = [
        ("baseline", "a photo of a {} flag"),
        ("detailed", "a photo of a {} flag in Northern Ireland"),
        ("hierarchical", "a photo of a flag, type: {}"),
        ("context", "a street view image showing a {} flag"),
    ]
    
    print("\nStrategies to test:")
    for name, template in strategies:
        print(f"   {name:12} : {template}")
    
    print("\n💡 This will show which prompting approach works best")
    print("   before applying learning-based methods like CoCoOp")
    
    return strategies


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 ESTABLISHING BASELINE PERFORMANCE")
    print("="*60)
    print("This tests CLIP without any training to establish floor performance")
    
    # Test baseline
    overall_acc, category_acc = test_baseline_clip()
    
    print("\n" + "="*60)
    print("💡 INTERPRETATION")
    print("="*60)
    
    if overall_acc < 10:
        print("⚠️  Baseline CLIP struggles with your dataset")
        print("   This is expected due to extreme class imbalance")
        print("   CoCoOp should improve on this significantly")
    else:
        print("✅ Baseline provides reasonable starting point")
        print("   CoCoOp should improve by 2-3x with proper training")
    
    print("\n📊 Expected Performance Progression:")
    print(f"   1. Baseline CLIP (zero-shot): {overall_acc:.1f}%")
    print(f"   2. CoOp (learned prompts): {overall_acc * 1.5:.1f}-{overall_acc * 2:.1f}%")
    print(f"   3. CoCoOp (dynamic prompts): {overall_acc * 2:.1f}-{overall_acc * 3:.1f}%")
    print(f"   4. Hierarchical CoCoOp: {overall_acc * 3:.1f}-{overall_acc * 4:.1f}%")
    
    print("\n🎯 Your current CoCoOp training should achieve at least")
    print(f"   {overall_acc * 2:.1f}% if properly configured")
    
    # Show prompting strategies
    compare_prompting_strategies()
