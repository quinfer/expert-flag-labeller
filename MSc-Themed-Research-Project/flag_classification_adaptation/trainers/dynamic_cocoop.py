#!/usr/bin/env python3
"""
Dynamic CoCoOp Trainer with Automatic Class Weight Calculation
Fixes hardcoded dataset paths and provides flexible class balancing
"""

import torch
import torch.nn as nn
from torch.nn import functional as F

from dassl.engine import TRAINER_REGISTRY, TrainerX
from dassl.metrics import compute_accuracy
from dassl.utils import load_pretrained_weights, load_checkpoint
from dassl.optim import build_optimizer, build_lr_scheduler

from clip import clip
from clip.simple_tokenizer import SimpleTokenizer as _Tokenizer

from trainers.cocoop import PromptLearner, CustomCLIP, load_clip_to_cpu

_tokenizer = _Tokenizer()


@TRAINER_REGISTRY.register()
class DynamicCoCoOp(TrainerX):
    """
    Dynamic Context Optimization (CoCoOp) with automatic class weight calculation
    
    Improvements over original CoCoOp:
    1. Automatic class weight calculation from current dataset
    2. Multiple class balancing strategies
    3. Dynamic focal loss parameters
    4. No hardcoded dataset paths
    """
    
    def __init__(self, cfg):
        super().__init__(cfg)
        self.class_balance_method = cfg.get('CLASS_BALANCE_METHOD', 'uniform')
        self.focal_loss_alpha = cfg.get('FOCAL_ALPHA', 0.5)
        self.focal_loss_gamma = cfg.get('FOCAL_GAMMA', 1.0)
        self.use_focal_loss = cfg.get('USE_FOCAL_LOSS', True)
    
    def check_cfg(self, cfg):
        # Handle both COCOOP and DYNAMIC_COCOOP config keys
        if hasattr(cfg.TRAINER, 'COCOOP'):
            assert cfg.TRAINER.COCOOP.PREC in ["fp16", "fp32", "amp"]
        elif hasattr(cfg.TRAINER, 'DYNAMIC_COCOOP'):
            assert cfg.TRAINER.DYNAMIC_COCOOP.PREC in ["fp16", "fp32", "amp"]

    def build_model(self):
        cfg = self.cfg
        classnames = self.dm.dataset.classnames
        num_classes = len(classnames)

        print(f"Loading CLIP (backbone: {cfg.MODEL.BACKBONE.NAME})")
        clip_model = load_clip_to_cpu(cfg)
        
        # Get precision setting from either COCOOP or DYNAMIC_COCOOP config
        if hasattr(cfg.TRAINER, 'COCOOP'):
            prec = cfg.TRAINER.COCOOP.PREC
        elif hasattr(cfg.TRAINER, 'DYNAMIC_COCOOP'):
            prec = cfg.TRAINER.DYNAMIC_COCOOP.PREC
        else:
            prec = "fp32"  # Default
        
        if prec == "fp32" or prec == "amp":
            clip_model.float()

        print("Building custom CLIP")
        self.model = CustomCLIP(cfg, classnames, clip_model)

        print("Turning off gradients in both the image and the text encoder")
        for name, param in self.model.named_parameters():
            if "prompt_learner" not in name:
                param.requires_grad_(False)

        # Enable fp16 training for memory efficiency
        if prec == "fp16":
            self.model.half()

        self.model.to(self.device)
        
        # Calculate dynamic class weights
        self.class_weights = self._calculate_dynamic_class_weights(classnames)
        
        # Print trainable parameters
        enabled = set()
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                enabled.add(name)
        print(f"Parameters to be updated: {enabled}")

        if cfg.MODEL.INIT_WEIGHTS:
            load_pretrained_weights(self.model.prompt_learner, cfg.MODEL.INIT_WEIGHTS)

        self.optim = build_optimizer(self.model.prompt_learner, cfg.OPTIM)
        self.sched = build_lr_scheduler(self.optim, cfg.OPTIM)

        self.register_model("prompt_learner", self.model.prompt_learner, self.optim, self.sched)

        # Initialize scaler based on precision setting
        if hasattr(cfg.TRAINER, 'COCOOP'):
            use_amp = cfg.TRAINER.COCOOP.PREC == "amp"
        elif hasattr(cfg.TRAINER, 'DYNAMIC_COCOOP'):
            use_amp = cfg.TRAINER.DYNAMIC_COCOOP.PREC == "amp"
        else:
            use_amp = False
        self.scaler = torch.cuda.amp.GradScaler() if use_amp else None

        device_count = torch.cuda.device_count()
        if device_count > 1:
            print(f"Multiple GPUs detected (n_gpus={device_count}), use all of them!")
            self.model = nn.DataParallel(self.model)

    def _calculate_dynamic_class_weights(self, classnames):
        """
        Calculate class weights dynamically based on current dataset distribution
        """
        print(f"\n🎯 Dynamic Class Weight Calculation")
        print(f"   Method: {self.class_balance_method}")
        print(f"   Classes: {len(classnames)}")
        
        # Try to get class distribution from dataset
        class_distribution = self._get_class_distribution_from_dataset()
        
        if class_distribution is None:
            print(f"   ⚠️ Could not determine class distribution, using uniform weights")
            return torch.ones(len(classnames))
        
        # Calculate weights based on selected method
        weights = self._compute_weights(class_distribution, classnames)
        
        # Print weight statistics
        print(f"   Weight range: {weights.min():.3f} - {weights.max():.3f}")
        print(f"   Weight ratio: {weights.max()/weights.min():.1f}:1")
        
        return weights
    
    def _get_class_distribution_from_dataset(self):
        """Extract class distribution from current dataset"""
        try:
            # Method 1: Try to get from dynamic dataset
            if hasattr(self.dm.dataset, 'class_distribution'):
                return self.dm.dataset.class_distribution
            
            # Method 2: Calculate from train data
            if hasattr(self.dm.dataset, 'train_x'):
                from collections import Counter
                class_counts = Counter()
                for item in self.dm.dataset.train_x:
                    class_counts[item.classname] += 1
                return dict(class_counts)
            
            # Method 3: Try to load from dataset directory
            dataset_dir = getattr(self.dm.dataset, 'dataset_dir', None)
            if dataset_dir:
                import json
                from pathlib import Path
                stats_file = Path(dataset_dir) / "consolidation_stats.json"
                if stats_file.exists():
                    with open(stats_file, 'r') as f:
                        stats = json.load(f)
                    return stats.get('class_distribution', None)
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error getting class distribution: {e}")
            return None
    
    def _compute_weights(self, class_distribution, classnames):
        """Compute class weights using specified method"""
        weights = torch.zeros(len(classnames))
        total_samples = sum(class_distribution.values())
        
        for idx, class_name in enumerate(classnames):
            class_count = class_distribution.get(class_name, 1)  # Default to 1 if missing
            
            if self.class_balance_method == 'uniform':
                weight = 1.0
            elif self.class_balance_method == 'inverse_frequency':
                weight = total_samples / (len(classnames) * class_count)
            elif self.class_balance_method == 'sqrt_inverse':
                weight = (total_samples / (len(classnames) * class_count)) ** 0.5
            elif self.class_balance_method == 'log_inverse':
                import math
                weight = math.log(total_samples / class_count)
            else:
                weight = 1.0
            
            weights[idx] = weight
        
        # Normalize weights to prevent extreme values
        if self.class_balance_method != 'uniform':
            weights = weights / weights.mean()
            # Cap maximum weight to prevent instability
            max_weight = 10.0
            weights = torch.clamp(weights, max=max_weight)
        
        return weights

    def forward_backward(self, batch):
        image, label = self.parse_batch_train(batch)
        
        # Get precision setting
        if hasattr(self.cfg.TRAINER, 'COCOOP'):
            prec = self.cfg.TRAINER.COCOOP.PREC
        elif hasattr(self.cfg.TRAINER, 'DYNAMIC_COCOOP'):
            prec = self.cfg.TRAINER.DYNAMIC_COCOOP.PREC
        else:
            prec = "fp32"
        if prec == "amp":
            with torch.cuda.amp.autocast():
                output = self.model(image)
                loss = self._compute_loss(output, label)
            self.optim.zero_grad()
            self.scaler.scale(loss).backward()
            self.scaler.step(self.optim)
            self.scaler.update()
        else:
            output = self.model(image)
            loss = self._compute_loss(output, label)
            self.optim.zero_grad()
            loss.backward()
            self.optim.step()

        loss_summary = {
            "loss": loss.item(),
            "acc": compute_accuracy(output, label)[0].item(),
        }

        if (self.batch_idx + 1) == self.num_batches:
            self.update_lr()

        return loss_summary

    def _compute_loss(self, logits, labels):
        """Compute loss with dynamic class weighting and optional focal loss"""
        # Move weights to same device as logits
        weights = self.class_weights.to(logits.device)
        
        # Compute weighted cross-entropy loss
        ce_loss = F.cross_entropy(logits, labels, weight=weights, reduction='none')
        
        if self.use_focal_loss and hasattr(self, '_focal_logged'):
            # Apply focal loss
            pt = torch.exp(-ce_loss)
            alpha = self.focal_loss_alpha
            gamma = self.focal_loss_gamma
            
            focal_loss = alpha * (1 - pt) ** gamma * ce_loss
            loss = focal_loss.mean()
        else:
            loss = ce_loss.mean()
        
        # Debug logging for first batch
        if not hasattr(self, '_focal_logged'):
            print(f"\n🎯 Dynamic Loss Configuration:")
            print(f"   Class balance method: {self.class_balance_method}")
            print(f"   Use focal loss: {self.use_focal_loss}")
            if self.use_focal_loss:
                print(f"   Focal alpha: {self.focal_loss_alpha}")
                print(f"   Focal gamma: {self.focal_loss_gamma}")
            print(f"   Batch CE loss: {ce_loss.mean().item():.4f}")
            print(f"   Final loss: {loss.item():.4f}")
            if self.use_focal_loss:
                print(f"   Focal reduction: {loss.item()/ce_loss.mean().item():.3f}x")
            print()
            self._focal_logged = True
        
        return loss

    def parse_batch_train(self, batch):
        input = batch["img"]
        label = batch["label"]
        input = input.to(self.device)
        label = label.to(self.device)
        return input, label

    def load_model(self, directory, epoch=None):
        if not directory:
            print("Note that load_model() is skipped as no pretrained model is given")
            return

        names = self.get_model_names()

        # By default, the best model is loaded
        model_file = "model-best.pth.tar"

        if epoch is not None:
            model_file = "model.pth.tar-" + str(epoch)

        for name in names:
            model_path = os.path.join(directory, name, model_file)

            if not os.path.exists(model_path):
                raise FileNotFoundError('Model not found at "{}"'.format(model_path))

            checkpoint = load_checkpoint(model_path)
            state_dict = checkpoint["state_dict"]
            epoch = checkpoint["epoch"]

            # Ignore fixed token vectors
            if "token_prefix" in state_dict:
                del state_dict["token_prefix"]

            if "token_suffix" in state_dict:
                del state_dict["token_suffix"]

            print("Loading weights to {} " 'from "{}" (epoch = {})'.format(name, model_path, epoch))
            # set strict=False
            self._models[name].load_state_dict(state_dict, strict=False)


def create_dynamic_config(dataset_name, class_balance_method='inverse_frequency', 
                         use_focal_loss=True, focal_alpha=0.5, focal_gamma=1.0):
    """
    Create a dynamic configuration for the trainer
    
    Args:
        dataset_name: Name of the dataset to use
        class_balance_method: 'uniform', 'inverse_frequency', 'sqrt_inverse', 'log_inverse'
        use_focal_loss: Whether to use focal loss
        focal_alpha: Focal loss alpha parameter
        focal_gamma: Focal loss gamma parameter
    
    Returns:
        dict: Configuration dictionary
    """
    return {
        'DATASET': {'NAME': dataset_name},
        'TRAINER': {'NAME': 'DynamicCoCoOp'},
        'CLASS_BALANCE_METHOD': class_balance_method,
        'USE_FOCAL_LOSS': use_focal_loss,
        'FOCAL_ALPHA': focal_alpha,
        'FOCAL_GAMMA': focal_gamma,
    }


if __name__ == "__main__":
    """Test dynamic trainer configuration"""
    print("🧪 Testing Dynamic CoCoOp Trainer")
    
    # Test configuration creation
    config = create_dynamic_config(
        dataset_name='NIFlagsConsolidatedDynamic',
        class_balance_method='inverse_frequency',
        use_focal_loss=True
    )
    
    print(f"✅ Created dynamic config: {config}")
    print(f"   Dataset: {config['DATASET']['NAME']}")
    print(f"   Trainer: {config['TRAINER']['NAME']}")
    print(f"   Class balance: {config['CLASS_BALANCE_METHOD']}")
    print(f"   Focal loss: {config['USE_FOCAL_LOSS']}")