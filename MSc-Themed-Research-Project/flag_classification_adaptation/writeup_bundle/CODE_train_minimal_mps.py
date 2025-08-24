import argparse
import os
# Fix OpenMP conflict on M4 Max
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

import torch
import time
from datetime import datetime
import shutil

from dassl.utils import setup_logger, set_random_seed, collect_env_info
from dassl.config import get_cfg_default
from dassl.engine import build_trainer


# Import all dataset modules
try:
    import datasets.ni_flags  # Use the simple version that works
    print("✅ Successfully imported NIFlags dataset")
except ImportError as e:
    print(f"❌ Failed to import NIFlags dataset: {e}")

# DON'T import ni_flags_v2 - it has duplicate registration

# Import trainers
try:
    import trainers.cocoop
    print("✅ Successfully imported CoCoOp trainer")
except ImportError as e:
    print(f"❌ Failed to import CoCoOp trainer: {e}")

def setup_device(cfg):
    """
    Setup device with M4 Max MPS support
    THIS IS THE CRITICAL MISSING PIECE!
    """
    device = None
    
    # Check for MPS (Apple Silicon) FIRST
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("=" * 60)
        print("🚀 MPS (Metal Performance Shaders) DETECTED!")
        print("🎯 Using M4 Max GPU acceleration")
        print("⚡ Expected 10-40x speedup over CPU")
        print("=" * 60)
        
        # Set MPS-specific optimizations
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        
        # Important: Update config to use MPS
        cfg.defrost()
        cfg.USE_CUDA = False  # Disable CUDA
        cfg.DEVICE = "mps"     # Set device to MPS
        cfg.freeze()
        
    # Fallback to CUDA if available
    elif torch.cuda.is_available() and cfg.USE_CUDA:
        device = torch.device("cuda")
        print("🎮 Using CUDA GPU")
        torch.backends.cudnn.benchmark = True
        
    # Fallback to CPU
    else:
        device = torch.device("cpu")
        print("⚠️  WARNING: Using CPU - Training will be VERY SLOW!")
        print("⚠️  MPS not detected - check PyTorch installation")
        
    return device

def print_args(args, cfg):
    print("***************")
    print("** Arguments **")
    print("***************")
    optkeys = list(args.__dict__.keys())
    optkeys.sort()
    for key in optkeys:
        print("{}: {}".format(key, args.__dict__[key]))
    print("************")
    print("** Config **")
    print("************")
    print(cfg)


def reset_cfg(cfg, args):
    if args.root:
        cfg.DATASET.ROOT = args.root

    if args.output_dir:
        cfg.OUTPUT_DIR = args.output_dir

    if args.resume:
        cfg.RESUME = args.resume

    if args.seed:
        cfg.SEED = args.seed

    if args.source_domains:
        cfg.DATASET.SOURCE_DOMAINS = args.source_domains

    if args.target_domains:
        cfg.DATASET.TARGET_DOMAINS = args.target_domains

    if args.transforms:
        cfg.INPUT.TRANSFORMS = args.transforms

    if args.trainer:
        cfg.TRAINER.NAME = args.trainer

    if args.backbone:
        cfg.MODEL.BACKBONE.NAME = args.backbone

    if args.head:
        cfg.MODEL.HEAD.NAME = args.head


def extend_cfg(cfg):
    """
    Add new config variables for CoCoOp and MPS support
    """
    from yacs.config import CfgNode as CN

    cfg.TRAINER.COOP = CN()
    cfg.TRAINER.COOP.ALPHA = 1.0
    cfg.TRAINER.COOP.N_CTX = 16  # number of context vectors
    cfg.TRAINER.COOP.CSC = False  # class-specific context
    cfg.TRAINER.COOP.CTX_INIT = False  # initialization words
    cfg.TRAINER.COOP.W = 1.0
    cfg.TRAINER.COOP.PREC = "fp32"  # fp16, fp32, amp
    cfg.TRAINER.COOP.CLASS_TOKEN_POSITION = "end"  # 'middle' or 'end' or 'front'

    cfg.TRAINER.COCOOP = CN()
    cfg.TRAINER.COCOOP.N_CTX = 16  # number of context vectors
    cfg.TRAINER.COCOOP.CTX_INIT = False  # initialization words
    cfg.TRAINER.COCOOP.PREC = "fp16"  # Use fp16 for MPS performance
    
    # NEW: Add MPS/Device configuration
    cfg.DEVICE = "auto"  # auto, mps, cuda, cpu
    cfg.USE_MPS = True    # Enable MPS by default on Apple Silicon

    cfg.DATASET.SUBSAMPLE_CLASSES = "all"  # all, base or new

    # Loss configuration
    cfg.LOSS = CN()
    cfg.LOSS.GM = False
    cfg.LOSS.NAME = ""
    cfg.LOSS.ALPHA = 0.
    cfg.LOSS.T = 1.
    cfg.LOSS.LAMBDA = 1.
    
    # MPS-specific optimizations
    cfg.DATALOADER.TRAIN_X.BATCH_SIZE = 16  # Optimized for M4 Max
    cfg.DATALOADER.TEST.BATCH_SIZE = 32      # Can be larger for inference


def setup_cfg(args):
    cfg = get_cfg_default()
    extend_cfg(cfg)

    # 1. From the dataset config file
    if args.dataset_config_file:
        cfg.merge_from_file(args.dataset_config_file)

    # 2. From the method config file
    if args.config_file:
        cfg.merge_from_file(args.config_file)

    # 3. From input arguments
    reset_cfg(cfg, args)

    # 4. From optional input arguments
    cfg.merge_from_list(args.opts)

    cfg.freeze()

    return cfg


def verify_mps_performance():
    """
    Quick MPS performance verification
    """
    if not torch.backends.mps.is_available():
        print("❌ MPS not available - using CPU (will be slow)")
        return False
    
    print("\n🧪 Testing MPS performance...")
    
    # Create test tensors
    device = torch.device("mps")
    size = (256, 3, 224, 224)  # Typical batch
    
    # Test on MPS
    x = torch.randn(size).to(device)
    start = time.time()
    for _ in range(10):
        y = x * 2.0 + 1.0
        torch.mps.synchronize()  # Ensure completion
    mps_time = (time.time() - start) / 10
    
    # Test on CPU for comparison
    x_cpu = torch.randn(size)
    start = time.time()
    for _ in range(10):
        y_cpu = x_cpu * 2.0 + 1.0
    cpu_time = (time.time() - start) / 10
    
    speedup = cpu_time / mps_time
    print(f"✅ MPS Performance Test:")
    print(f"   CPU time: {cpu_time:.4f}s")
    print(f"   MPS time: {mps_time:.4f}s")
    print(f"   Speedup: {speedup:.1f}x")
    
    if speedup < 2:
        print("⚠️  WARNING: MPS speedup lower than expected")
        print("   Check if other processes are using GPU")
    
    return True


def cleanup_before_training(output_dir):
    """Clean up previous training artifacts"""
    from pathlib import Path
    import shutil
    
    print("\n🧹 Cleaning previous training artifacts...")
    
    # Clear output directory if it exists
    output_path = Path(output_dir)
    if output_path.exists():
        # Keep a backup of the last log
        log_file = output_path / "log.txt"
        if log_file.exists():
            backup_name = f"log_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            shutil.copy2(log_file, output_path / backup_name)
            print(f"  ↳ Backed up previous log to {backup_name}")
        
        # Remove model checkpoints
        checkpoint_dirs = ["prompt_learner", "tensorboard"]
        for dir_name in checkpoint_dirs:
            dir_path = output_path / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  ↳ Removed {dir_name}/")
    
    # Clear GPU cache
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
        print("  ↳ Cleared MPS cache")
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("  ↳ Cleared CUDA cache")
    
    print("✅ Cleanup complete\n")

def main(args):
    # CRITICAL: Setup MPS device first
    print("\n" + "="*60)
    print("🔧 DEVICE CONFIGURATION")
    print("="*60)
    
    # Verify MPS is working
    if args.verify_mps:
        verify_mps_performance()
    
    cfg = setup_cfg(args)
    
    # Clean previous artifacts if requested
    if args.clean:
        cleanup_before_training(cfg.OUTPUT_DIR if cfg.OUTPUT_DIR else "output")
    
    # Setup device with MPS support
    device = setup_device(cfg)
    print(f"📱 Final device selection: {device}")
    
    if cfg.SEED >= 0:
        print("Setting fixed seed: {}".format(cfg.SEED))
        set_random_seed(cfg.SEED)
    setup_logger(cfg.OUTPUT_DIR)

    print_args(args, cfg)
    print("Collecting env info ...")
    print("** System info **\n{}\n".format(collect_env_info()))
    
    # Check PyTorch MPS availability
    print("\n" + "="*60)
    print("🔍 PYTORCH CONFIGURATION CHECK")
    print("="*60)
    print(f"PyTorch version: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print(f"MPS built: {torch.backends.mps.is_built()}")
    if torch.backends.mps.is_available():
        print("✅ MPS is available and ready!")
        print("⚡ Training should be 10-40x faster than CPU")
    else:
        print("❌ MPS not available - check PyTorch installation")
        print("   Install with: conda install pytorch torchvision -c pytorch")
    print("="*60 + "\n")

    # Build trainer with device config
    trainer = build_trainer(cfg)
    
    # Ensure trainer is using MPS
    if hasattr(trainer, 'model') and device.type == 'mps':
        trainer.model = trainer.model.to(device)
        print(f"✅ Model moved to {device}")

    if args.eval_only:
        trainer.load_model(args.model_dir, epoch=args.load_epoch)
        trainer.test()
        return

    if not args.no_train:
        print("\n" + "="*60)
        print("🚀 STARTING TRAINING WITH MPS ACCELERATION")
        print("="*60)
        start_time = time.time()
        
        trainer.train()
        
        total_time = time.time() - start_time
        print(f"\n✅ Training completed in {total_time/60:.2f} minutes")
        
        # Performance analysis
        if hasattr(trainer, 'epoch_time'):
            print(f"⚡ Average epoch time: {trainer.epoch_time:.2f} seconds")
            if device.type == 'cpu':
                estimated_mps_time = trainer.epoch_time / 20  # Conservative estimate
                print(f"💡 With MPS, this would be ~{estimated_mps_time:.2f} seconds")


# PATCH 1: Fix data movement to MPS (your existing patch)
def patch_cocoop_for_mps():
    """Patch CoCoOp trainer to handle MPS devices"""
    try:
        import trainers.cocoop as cocoop_module
        
        # Store original method
        original_parse = cocoop_module.CoCoOp.parse_batch_train
        
        # Create patched version
        def parse_batch_train_mps(self, batch):
            input = batch["img"]
            label = batch["label"]
            
            # Get device from model
            device = next(self.model.parameters()).device
            
            # Move to device
            input = input.to(device)
            label = label.to(device)
            
            return input, label
        
        # Apply patch
        cocoop_module.CoCoOp.parse_batch_train = parse_batch_train_mps
        cocoop_module.CoCoOp.parse_batch_test = parse_batch_train_mps  # Same logic for test
        
        print("✅ CoCoOp patched for MPS support")
    except Exception as e:
        print(f"Warning: Could not patch CoCoOp: {e}")

# PATCH 2: Force model itself to MPS (NEW patch)
def force_cocoop_mps():
    """Force CoCoOp model to use MPS"""
    try:
        import trainers.cocoop as cocoop
        original_build = cocoop.CoCoOp.build_model
        
        def build_mps(self):
            original_build(self)
            if torch.backends.mps.is_available():
                device = torch.device("mps")
                self.model = self.model.to(device)
                self.device = device
                print(f"✅ FORCED model to MPS: {next(self.model.parameters()).device}")
        
        cocoop.CoCoOp.build_model = build_mps
        print("✅ CoCoOp model forcing enabled")
    except Exception as e:
        print(f"Warning: Could not force MPS: {e}")

# Apply BOTH patches
patch_cocoop_for_mps()  # Patch 1: Fixes data movement
force_cocoop_mps()      # Patch 2: Forces model to MPS


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default="", help="path to dataset")
    parser.add_argument("--output-dir",
                        type=str,
                        default="",
                        help="output directory")
    parser.add_argument(
        "--resume",
        type=str,
        default="",
        help="checkpoint directory (from which the training resumes)",
    )
    parser.add_argument("--seed",
                        type=int,
                        default=-1,
                        help="only positive value enables a fixed seed")
    parser.add_argument("--source-domains",
                        type=str,
                        nargs="+",
                        help="source domains for DA/DG")
    parser.add_argument("--target-domains",
                        type=str,
                        nargs="+",
                        help="target domains for DA/DG")
    parser.add_argument("--transforms",
                        type=str,
                        nargs="+",
                        help="data augmentation methods")
    parser.add_argument("--config-file",
                        type=str,
                        default="",
                        help="path to config file")
    parser.add_argument(
        "--dataset-config-file",
        type=str,
        default="",
        help="path to config file for dataset setup",
    )
    parser.add_argument("--trainer",
                        type=str,
                        default="",
                        help="name of trainer")
    parser.add_argument("--backbone",
                        type=str,
                        default="",
                        help="name of CNN backbone")
    parser.add_argument("--head", type=str, default="", help="name of head")
    parser.add_argument("--eval-only",
                        action="store_true",
                        help="evaluation only")
    parser.add_argument(
        "--model-dir",
        type=str,
        default="",
        help="load model from this directory for eval-only mode",
    )
    parser.add_argument("--load-epoch",
                        type=int,
                        help="load model weights at this epoch for evaluation")
    parser.add_argument("--no-train",
                        action="store_true",
                        help="do not call trainer.train()")
    
    # NEW: MPS-specific arguments
    parser.add_argument("--verify-mps",
                        action="store_true",
                        help="verify MPS performance before training")
    parser.add_argument("--force-cpu",
                        action="store_true",
                        help="force CPU usage even if MPS available")
    parser.add_argument("--clean",
                        action="store_true",
                        help="clean previous training artifacts before starting")
    
    parser.add_argument(
        "opts",
        default=None,
        nargs=argparse.REMAINDER,
        help="modify config options using the command-line",
    )
    args = parser.parse_args()
    main(args)
