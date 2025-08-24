#!/usr/bin/env python3
"""
Dynamic Training Script for Flag Classification
Automatically handles different consolidation levels and class balancing strategies
"""

import os
import sys
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.append('.')

# Import dynamic components
from datasets.dynamic_dataset_factory import register_dynamic_datasets
from trainers.dynamic_cocoop import DynamicCoCoOp

# Import Dassl components
from dassl.utils import setup_logger, set_random_seed, collect_env_info
from dassl.config import get_cfg_default
from dassl.engine import build_trainer

# Register all dynamic datasets
register_dynamic_datasets()


def setup_cfg(args):
    """Setup configuration with dynamic parameters"""
    cfg = get_cfg_default()
    
    # Load base trainer config
    if args.config_file:
        cfg.merge_from_file(args.config_file)
    
    # Load dataset config
    if args.dataset_config_file:
        cfg.merge_from_file(args.dataset_config_file)
    
    # Override with command line arguments
    cfg.merge_from_list(args.opts)
    
    # Dynamic configuration
    cfg.CLASS_BALANCE_METHOD = args.class_balance_method
    cfg.USE_FOCAL_LOSS = args.use_focal_loss
    cfg.FOCAL_ALPHA = args.focal_alpha
    cfg.FOCAL_GAMMA = args.focal_gamma
    
    # Set output directory
    if args.output_dir:
        cfg.OUTPUT_DIR = args.output_dir
    else:
        # Auto-generate output directory name
        dataset_name = cfg.DATASET.NAME.lower()
        balance_method = args.class_balance_method
        focal_suffix = f"_focal{args.focal_alpha}_{args.focal_gamma}" if args.use_focal_loss else "_nofocal"
        cfg.OUTPUT_DIR = f"experiments/{dataset_name}_{balance_method}{focal_suffix}"
    
    # Device configuration
    cfg.USE_CUDA = not args.force_cpu and torch.cuda.is_available()
    cfg.USE_MPS = not args.force_cpu and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    
    if cfg.USE_MPS:
        cfg.DEVICE = "mps"
    elif cfg.USE_CUDA:
        cfg.DEVICE = "cuda"
    else:
        cfg.DEVICE = "cpu"
    
    # Set trainer to dynamic version
    cfg.TRAINER.NAME = "DynamicCoCoOp"
    
    cfg.freeze()
    return cfg


def print_configuration_summary(cfg, args):
    """Print a summary of the training configuration"""
    print("=" * 80)
    print("🚀 DYNAMIC FLAG CLASSIFICATION TRAINING")
    print("=" * 80)
    
    print(f"📊 Dataset Configuration:")
    print(f"   Dataset: {cfg.DATASET.NAME}")
    print(f"   Root: {cfg.DATASET.ROOT}")
    print(f"   Shots: {cfg.DATASET.NUM_SHOTS}")
    
    print(f"\n🎯 Training Configuration:")
    print(f"   Trainer: {cfg.TRAINER.NAME}")
    print(f"   Epochs: {cfg.OPTIM.MAX_EPOCH}")
    print(f"   Learning rate: {cfg.OPTIM.LR}")
    print(f"   Batch size: {cfg.DATALOADER.TRAIN_X.BATCH_SIZE}")
    
    print(f"\n⚖️ Class Balance Configuration:")
    print(f"   Balance method: {args.class_balance_method}")
    print(f"   Use focal loss: {args.use_focal_loss}")
    if args.use_focal_loss:
        print(f"   Focal alpha: {args.focal_alpha}")
        print(f"   Focal gamma: {args.focal_gamma}")
    
    print(f"\n💻 Device Configuration:")
    print(f"   Device: {cfg.DEVICE}")
    print(f"   Precision: {cfg.TRAINER.COCOOP.PREC}")
    
    print(f"\n📁 Output:")
    print(f"   Directory: {cfg.OUTPUT_DIR}")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser()
    
    # Standard arguments
    parser.add_argument("--root", type=str, default="", help="path to dataset")
    parser.add_argument("--output-dir", type=str, default="", help="output directory")
    parser.add_argument("--config-file", type=str, default="", help="path to config file")
    parser.add_argument("--dataset-config-file", type=str, default="", help="path to dataset config file")
    parser.add_argument("--trainer", type=str, default="DynamicCoCoOp", help="name of trainer")
    parser.add_argument("--backbone", type=str, default="", help="name of CNN backbone")
    parser.add_argument("--head", type=str, default="", help="name of head")
    parser.add_argument("--eval-only", action="store_true", help="evaluation only")
    parser.add_argument("--model-dir", type=str, default="", help="load model from this directory for eval-only mode")
    parser.add_argument("--load-epoch", type=int, help="load model weights at this epoch for evaluation")
    parser.add_argument("--no-train", action="store_true", help="do not call trainer.train()")
    parser.add_argument("--transforms", type=str, nargs="+", help="data augmentation methods")
    parser.add_argument("--seed", type=int, default=-1, help="only positive value enables a fixed seed")
    parser.add_argument("--source-domains", type=str, nargs="+", help="source domains for DA/DG")
    parser.add_argument("--target-domains", type=str, nargs="+", help="target domains for DA/DG")
    parser.add_argument("--resume", type=str, default="", help="checkpoint directory")
    parser.add_argument("--force-cpu", action="store_true", help="force use CPU")
    parser.add_argument("--clean", action="store_true", help="clean output directory")
    
    # Dynamic training arguments
    parser.add_argument("--class-balance-method", type=str, default="uniform",
                       choices=["uniform", "inverse_frequency", "sqrt_inverse", "log_inverse"],
                       help="method for calculating class weights")
    parser.add_argument("--use-focal-loss", action="store_true", default=False,
                       help="use focal loss for handling class imbalance")
    parser.add_argument("--focal-alpha", type=float, default=0.5,
                       help="focal loss alpha parameter")
    parser.add_argument("--focal-gamma", type=float, default=1.0,
                       help="focal loss gamma parameter")
    parser.add_argument("--auto-epochs", action="store_true",
                       help="automatically set epochs based on dataset size")
    
    # Additional options (for compatibility with existing scripts)
    parser.add_argument("opts", default=None, nargs=argparse.REMAINDER,
                       help="modify config options using the command-line")
    
    args = parser.parse_args()
    
    # Setup configuration
    cfg = setup_cfg(args)
    
    # Clean output directory if requested
    if args.clean and os.path.exists(cfg.OUTPUT_DIR):
        import shutil
        print(f"🧹 Cleaning output directory: {cfg.OUTPUT_DIR}")
        shutil.rmtree(cfg.OUTPUT_DIR)
    
    # Create output directory
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    
    # Setup logging
    setup_logger(cfg.OUTPUT_DIR)
    
    # Set random seed
    if args.seed >= 0:
        print(f"Setting fixed seed: {args.seed}")
        set_random_seed(args.seed)
    
    # Print configuration summary
    print_configuration_summary(cfg, args)
    
    # Print environment info
    if cfg.VERBOSE:
        print("Collecting env info ...")
        print("** System info **")
        print(collect_env_info())
    
    # Build trainer
    print(f"Building trainer: {cfg.TRAINER.NAME}")
    trainer = build_trainer(cfg)
    
    # Load model if specified
    if args.model_dir:
        trainer.load_model(args.model_dir, epoch=args.load_epoch)
    
    # Resume training if specified
    if args.resume:
        trainer.resume_model_if_exist(args.resume)
    
    # Training or evaluation
    if args.eval_only:
        print("🔍 Evaluation mode")
        trainer.test()
    else:
        if not args.no_train:
            print("🚀 Starting training...")
            trainer.train()
        
        print("🔍 Final evaluation...")
        trainer.test()
    
    print("✅ Training completed successfully!")


def create_quick_configs():
    """Create quick configuration presets for common scenarios"""
    configs = {
        'balanced_16class': {
            'dataset': 'NIFlagsConsolidatedDynamic',
            'class_balance_method': 'inverse_frequency',
            'use_focal_loss': True,
            'focal_alpha': 0.5,
            'focal_gamma': 1.0,
        },
        'uniform_16class': {
            'dataset': 'NIFlagsConsolidatedDynamic',
            'class_balance_method': 'uniform',
            'use_focal_loss': False,
        },
        'balanced_7class': {
            'dataset': 'NIFlagsSuperConsolidatedDynamic',
            'class_balance_method': 'sqrt_inverse',  # Less aggressive for extreme imbalance
            'use_focal_loss': True,
            'focal_alpha': 0.3,
            'focal_gamma': 2.0,  # Higher gamma for extreme imbalance
        },
        'uniform_7class': {
            'dataset': 'NIFlagsSuperConsolidatedDynamic',
            'class_balance_method': 'uniform',
            'use_focal_loss': False,
        },
    }
    
    return configs


if __name__ == "__main__":
    import torch
    
    # Quick test mode
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        print("🧪 Testing Dynamic Training Script")
        configs = create_quick_configs()
        
        print("Available quick configurations:")
        for name, config in configs.items():
            print(f"  {name}: {config}")
        
        print("✅ Dynamic training script ready!")
        sys.exit(0)
    
    # Normal training mode
    main()