import os.path as osp
from collections import OrderedDict
import math

import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.cuda.amp import GradScaler, autocast

from dassl.engine import TRAINER_REGISTRY, TrainerX
from dassl.metrics import compute_accuracy
from dassl.utils import load_pretrained_weights, load_checkpoint
from dassl.optim import build_optimizer, build_lr_scheduler

from clip import clip
from clip.simple_tokenizer import SimpleTokenizer as _Tokenizer

_tokenizer = _Tokenizer()


def load_clip_to_cpu(cfg):
    backbone_name = cfg.MODEL.BACKBONE.NAME
    url = clip._MODELS[backbone_name]
    model_path = clip._download(url)

    try:
        model = torch.jit.load(model_path, map_location="cpu").eval()
        state_dict = None
    except RuntimeError:
        state_dict = torch.load(model_path, map_location="cpu")

    model = clip.build_model(state_dict or model.state_dict())
    return model


class TextEncoder(nn.Module):
    def __init__(self, clip_model):
        super().__init__()
        self.transformer = clip_model.transformer
        self.positional_embedding = clip_model.positional_embedding
        self.ln_final = clip_model.ln_final
        self.text_projection = clip_model.text_projection
        self.dtype = clip_model.dtype

    def forward(self, prompts, tokenized_prompts):
        x = prompts + self.positional_embedding.type(self.dtype)
        x = x.permute(1, 0, 2)  # NLD -> LND
        x = self.transformer(x)
        x = x.permute(1, 0, 2)  # LND -> NLD
        x = self.ln_final(x).type(self.dtype)

        x = x[torch.arange(x.shape[0]), tokenized_prompts.argmax(dim=-1)] @ self.text_projection

        return x


class PromptLearner(nn.Module):
    def __init__(self, cfg, classnames, clip_model):
        super().__init__()
        n_cls = len(classnames)
        n_ctx = cfg.TRAINER.COCOOP.N_CTX
        ctx_init = cfg.TRAINER.COCOOP.CTX_INIT
        dtype = clip_model.dtype
        ctx_dim = clip_model.ln_final.weight.shape[0]
        vis_dim = clip_model.visual.output_dim
        clip_imsize = clip_model.visual.input_resolution
        cfg_imsize = cfg.INPUT.SIZE[0]
        assert cfg_imsize == clip_imsize, f"cfg_imsize ({cfg_imsize}) must equal to clip_imsize ({clip_imsize})"

        if ctx_init:
            # use given words to initialize context vectors
            ctx_init = ctx_init.replace("_", " ")
            n_ctx = len(ctx_init.split(" "))
            prompt = clip.tokenize(ctx_init)
            with torch.no_grad():
                embedding = clip_model.token_embedding(prompt).type(dtype)
            ctx_vectors = embedding[0, 1 : 1 + n_ctx, :]
            prompt_prefix = ctx_init
        else:
            # random initialization
            ctx_vectors = torch.empty(n_ctx, ctx_dim, dtype=dtype)
            nn.init.normal_(ctx_vectors, std=0.02)
            prompt_prefix = " ".join(["X"] * n_ctx)

        print(f'Initial context: "{prompt_prefix}"')
        print(f"Number of context words (tokens): {n_ctx}")

        self.ctx = nn.Parameter(ctx_vectors)

        self.meta_net = nn.Sequential(OrderedDict([
            ("linear1", nn.Linear(vis_dim, vis_dim // 16)),
            ("relu", nn.ReLU(inplace=True)),
            ("linear2", nn.Linear(vis_dim // 16, ctx_dim))
        ]))

        if cfg.TRAINER.COCOOP.PREC == "fp16":
            self.meta_net.half()

        classnames = [name.replace("_", " ") for name in classnames]
        name_lens = [len(_tokenizer.encode(name)) for name in classnames]
        prompts = [prompt_prefix + " " + name + "." for name in classnames]

        tokenized_prompts = torch.cat([clip.tokenize(p) for p in prompts])
        with torch.no_grad():
            embedding = clip_model.token_embedding(tokenized_prompts).type(dtype)

        # These token vectors will be saved when in save_model(),
        # but they should be ignored in load_model() as we want to use
        # those computed using the current class names
        self.register_buffer("token_prefix", embedding[:, :1, :])  # SOS
        self.register_buffer("token_suffix", embedding[:, 1 + n_ctx :, :])  # CLS, EOS

        self.n_cls = n_cls
        self.n_ctx = n_ctx
        self.tokenized_prompts = tokenized_prompts  # torch.Tensor
        self.name_lens = name_lens

    def construct_prompts(self, ctx, prefix, suffix, label=None):
        # dim0 is either batch_size (during training) or n_cls (during testing)
        # ctx: context tokens, with shape of (dim0, n_ctx, ctx_dim)
        # prefix: the sos token, with shape of (n_cls, 1, ctx_dim)
        # suffix: remaining tokens, with shape of (n_cls, *, ctx_dim)

        if label is not None:
            prefix = prefix[label]
            suffix = suffix[label]

        prompts = torch.cat(
            [
                prefix,  # (dim0, 1, dim)
                ctx,     # (dim0, n_ctx, dim)
                suffix,  # (dim0, *, dim)
            ],
            dim=1,
        )

        return prompts

    def forward(self, im_features):
        prefix = self.token_prefix
        suffix = self.token_suffix
        ctx = self.ctx                     # (n_ctx, ctx_dim)
        bias = self.meta_net(im_features)  # (batch, ctx_dim)
        bias = bias.unsqueeze(1)           # (batch, 1, ctx_dim)
        ctx = ctx.unsqueeze(0)             # (1, n_ctx, ctx_dim)
        ctx_shifted = ctx + bias           # (batch, n_ctx, ctx_dim)
        
        # Use instance-conditioned context tokens for all classes
        prompts = []
        for ctx_shifted_i in ctx_shifted:
            ctx_i = ctx_shifted_i.unsqueeze(0).expand(self.n_cls, -1, -1)
            pts_i = self.construct_prompts(ctx_i, prefix, suffix)  # (n_cls, n_tkn, ctx_dim)
            prompts.append(pts_i)
        prompts = torch.stack(prompts)
        
        return prompts


class CustomCLIP(nn.Module):
    def __init__(self, cfg, classnames, clip_model, class_weights=None):
        super().__init__()
        self.prompt_learner = PromptLearner(cfg, classnames, clip_model)
        self.tokenized_prompts = self.prompt_learner.tokenized_prompts
        self.image_encoder = clip_model.visual
        self.text_encoder = TextEncoder(clip_model)
        self.logit_scale = clip_model.logit_scale
        self.dtype = clip_model.dtype
        
        # USE PROVIDED CLASS WEIGHTS OR CREATE UNIFORM ONES
        if class_weights is not None:
            self.class_weights = class_weights
            print(f"   ✅ Using provided class weights")
        else:
            print(f"   ⚠️ No class weights provided, using uniform weights")
            self.class_weights = torch.ones(len(classnames))

    def _create_class_weights(self, num_classes, classnames):
        """Create inverse frequency weights for class imbalance - DYNAMIC VERSION"""
        import json
        from pathlib import Path
        
        # FIX: Calculate proper class weights from current dataset
        print(f"🎯 Calculating dynamic class weights for {num_classes} classes")
        
        # Try to get class distribution from current dataset
        class_weights = self._calculate_proper_class_weights(num_classes, classnames)
        
        if class_weights is not None:
            print(f"   ✅ Using calculated inverse frequency weights")
            print(f"   Weight range: {class_weights.min():.3f} - {class_weights.max():.3f}")
            return class_weights
        else:
            print(f"   ⚠️ Falling back to uniform weights")
            return torch.ones(num_classes)
        
        # DISABLED: This was causing training failures by loading wrong weights
        # dataset_info_path = Path("../data/ni_flags_v2/dataset_info.json")
        
        if dataset_info_path.exists():
            print(f"📊 Loading class weights from {dataset_info_path}")
            with open(dataset_info_path, 'r') as f:
                info = json.load(f)
            
            if 'class_distribution' in info:
                # Load actual distribution
                class_distribution = info['class_distribution']
                
                # Get class names to maintain order
                classnames_path = Path("../data/ni_flags_v2/classnames.txt")
                if classnames_path.exists():
                    with open(classnames_path, 'r') as f:
                        classnames = [line.strip() for line in f.readlines()]
                    
                    # Create weights based on actual distribution
                    weights = torch.ones(num_classes)
                    total_samples = sum(class_distribution.values())
                    
                    for idx, classname in enumerate(classnames[:num_classes]):
                        if classname in class_distribution:
                            count = class_distribution[classname]
                        else:
                            count = 1
                        
                        # Inverse frequency with square root smoothing
                        weights[idx] = (total_samples / (num_classes * count)) ** 0.5
                    
                    # Normalize
                    weights = weights / weights.mean()
                    
                    print(f"✅ Loaded weights for {num_classes} classes from actual distribution")
                    print(f"   Total samples: {total_samples}")
                    print(f"   Weight range: {weights.min():.2f} - {weights.max():.2f}")
                    
                    return weights
        
        # Fallback to hardcoded weights if file not found
        print("⚠️ Using fallback weights (dataset_info.json not found)")
        
        # Original hardcoded weights for 70 classes
        class_counts = {
            0: 777, 1: 417, 2: 386, 3: 142, 4: 99,
            5: 48, 6: 42, 7: 39, 8: 38, 9: 26,
            # ... rest of original counts
        }
        
        weights = torch.ones(num_classes)
        total_samples = 5490  # Updated total
        
        for idx in range(num_classes):
            count = class_counts.get(idx, 1)
            weights[idx] = (total_samples / (num_classes * count)) ** 0.5
        
        weights = weights / weights.mean()
        print(f"✅ Created fallback weights: min={weights.min():.2f}, max={weights.max():.2f}")
        
        return weights
    
    def _calculate_proper_class_weights(self, num_classes, classnames):
        """Calculate proper class weights from current dataset distribution"""
        try:
            # Access trainer's data manager instead of model's
            trainer = self._get_trainer_instance()
            if trainer and hasattr(trainer, 'dm') and hasattr(trainer.dm, 'dataset'):
                # Method 1: Try to get from dataset consolidation stats
                dataset_dir = getattr(trainer.dm.dataset, 'dataset_dir', None)
                if dataset_dir:
                    stats_file = Path(dataset_dir) / "consolidation_stats.json"
                    if stats_file.exists():
                        with open(stats_file, 'r') as f:
                            stats = json.load(f)
                        
                        class_dist = stats.get('class_distribution', {})
                        if class_dist:
                            return self._compute_inverse_frequency_weights(class_dist, num_classes, classnames)
                
                # Method 2: Calculate from training data directly
                if hasattr(trainer.dm.dataset, 'train_x'):
                    from collections import Counter
                    class_counts = Counter()
                    for item in trainer.dm.dataset.train_x:
                        class_counts[item.classname] += 1
                    
                    if len(class_counts) == num_classes:
                        return self._compute_inverse_frequency_weights(dict(class_counts), num_classes, classnames)
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error calculating class weights: {e}")
            return None
    
    def _get_trainer_instance(self):
        """Get trainer instance through global registry or inspection"""
        import gc
        for obj in gc.get_objects():
            if hasattr(obj, '__class__') and 'CoCoOp' in str(obj.__class__):
                if hasattr(obj, 'dm') and hasattr(obj, 'model'):
                    return obj
        return None
    
    def _compute_inverse_frequency_weights(self, class_distribution, num_classes, classnames):
        """Compute inverse frequency weights from class distribution"""
        import torch
        
        if len(classnames) != num_classes:
            print(f"   ⚠️ Mismatch: {len(classnames)} classnames vs {num_classes} classes")
            return None
        
        weights = torch.zeros(num_classes)
        total_samples = sum(class_distribution.values())
        
        print(f"   📊 Class distribution:")
        for idx, class_name in enumerate(classnames):
            count = class_distribution.get(class_name, 1)
            # Inverse frequency weight
            weight = total_samples / (num_classes * count)
            weights[idx] = weight
            
            percentage = (count / total_samples) * 100
            print(f"      {class_name:25}: {count:4d} samples ({percentage:5.1f}%) → weight: {weight:.3f}")
        
        # Normalize to prevent extreme weights
        weights = weights / weights.mean()
        
        # Cap maximum weight to prevent training instability
        max_weight = 5.0  # Reasonable cap
        weights = torch.clamp(weights, max=max_weight)
        
        return weights

    def forward(self, image, label=None):
        tokenized_prompts = self.tokenized_prompts
        logit_scale = self.logit_scale.exp()

        image_features = self.image_encoder(image.type(self.dtype))
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        prompts = self.prompt_learner(image_features)
        
        logits = []
        for pts_i, imf_i in zip(prompts, image_features):
            text_features = self.text_encoder(pts_i, tokenized_prompts)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            l_i = logit_scale * imf_i @ text_features.t()
            logits.append(l_i)
        logits = torch.stack(logits)

        if self.prompt_learner.training:
            # EXPERIMENT: Try without weights first
            USE_WEIGHTS = True  # Set to False to disable weights completely
            
            if USE_WEIGHTS:
                # Move weights to correct device
                class_weights = self.class_weights.to(logits.device)
                # Weighted focal/CE loss
                ce_loss = F.cross_entropy(logits, label, weight=class_weights, reduction='none')
            else:
                # Standard CE without weights
                ce_loss = F.cross_entropy(logits, label, reduction='none')
            pt = torch.exp(-ce_loss)
            
            # Focal loss parameters - REDUCED for extreme imbalance
            alpha = 0.5   # Higher alpha = less aggressive on rare classes
            gamma = 1.0   # Lower gamma = gentler focusing (was 2.0)
            
            # TEMPORARY: Disable focal loss for expanded dataset
            USE_FOCAL = False  # Changed from True - testing with expanded data
            
            if USE_FOCAL:
                # Apply focal loss formula: FL = α(1-pt)^γ * CE
                focal_loss = alpha * (1 - pt) ** gamma * ce_loss
                loss = focal_loss.mean()
            else:
                # Just use weighted cross-entropy
                loss = ce_loss.mean()
            
            # Debug print for first batch only
            if not hasattr(self, '_focal_logged'):
                print(f"\n✅ Focal Loss Active!")
                print(f"   Alpha (α): {alpha}")
                print(f"   Gamma (γ): {gamma}")
                print(f"   Batch CE Loss: {ce_loss.mean().item():.4f}")
                print(f"   Batch Focal Loss: {loss.item():.4f}")
                print(f"   Reduction factor: {loss.item()/ce_loss.mean().item():.3f}x\n")
                self._focal_logged = True
            
            return loss

        return logits


@TRAINER_REGISTRY.register()
class CoCoOp(TrainerX):
    """
    Context Optimization (CoCoOp).
    
    Learning to Prompt for Vision-Language Models
    https://arxiv.org/abs/2109.01134
    """
    def check_cfg(self, cfg):
        assert cfg.TRAINER.COCOOP.PREC in ["fp16", "fp32", "amp"]

    def build_model(self):
        cfg = self.cfg
        classnames = self.dm.dataset.classnames

        print(f"Loading CLIP (backbone: {cfg.MODEL.BACKBONE.NAME})")
        clip_model = load_clip_to_cpu(cfg)
        
        if cfg.TRAINER.COCOOP.PREC == "fp32" or cfg.TRAINER.COCOOP.PREC == "amp":
            # CLIP's default precision is fp16
            clip_model.float()

        print("Building custom CLIP")
        # Calculate class weights at trainer level before passing to model
        class_weights = self._calculate_class_weights_trainer_level(classnames)
        
        self.model = CustomCLIP(cfg, classnames, clip_model, class_weights=class_weights)

        print("Turning off gradients in both the image and the text encoder")
        name_to_update = "prompt_learner"
        
        for name, param in self.model.named_parameters():
            if name_to_update not in name:
                param.requires_grad_(False)

        # Double check
        enabled = set()
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                enabled.add(name)
        print(f"Parameters to be updated: {enabled}")

        if cfg.MODEL.INIT_WEIGHTS:
            load_pretrained_weights(self.model, cfg.MODEL.INIT_WEIGHTS)

        self.model.to(self.device)
        # NOTE: only give prompt_learner to the optimizer
        self.optim = build_optimizer(self.model, cfg.OPTIM)
        self.sched = build_lr_scheduler(self.optim, cfg.OPTIM)
        self.register_model("prompt_learner", self.model, self.optim, self.sched)

        self.scaler = GradScaler() if cfg.TRAINER.COCOOP.PREC == "amp" else None
    
    def _calculate_class_weights_trainer_level(self, classnames):
        """Calculate class weights at trainer level with access to dataset"""
        try:
            from collections import Counter
            import torch
            
            # Calculate from training data directly
            if hasattr(self.dm.dataset, 'train_x'):
                class_counts = Counter()
                for item in self.dm.dataset.train_x:
                    class_counts[item.classname] += 1
                
                if len(class_counts) == len(classnames):
                    return self._compute_inverse_frequency_weights_trainer(dict(class_counts), len(classnames), classnames)
            
            # Try to get from dataset consolidation stats as fallback
            dataset_dir = getattr(self.dm.dataset, 'dataset_dir', None)
            if dataset_dir:
                from pathlib import Path
                import json
                
                stats_file = Path(dataset_dir) / "consolidation_stats.json"
                if stats_file.exists():
                    with open(stats_file, 'r') as f:
                        stats = json.load(f)
                    
                    class_dist = stats.get('class_distribution', {})
                    if class_dist:
                        return self._compute_inverse_frequency_weights_trainer(class_dist, len(classnames), classnames)
            
            print(f"   ⚠️ Could not calculate class weights, using uniform weights")
            return torch.ones(len(classnames))
            
        except Exception as e:
            print(f"   ⚠️ Error calculating class weights: {e}")
            return torch.ones(len(classnames))
    
    def _compute_inverse_frequency_weights_trainer(self, class_distribution, num_classes, classnames):
        """Compute inverse frequency weights from class distribution (trainer version)"""
        import torch
        
        weights = torch.zeros(num_classes)
        total_samples = sum(class_distribution.values())
        
        print(f"🎯 Calculating dynamic class weights for {num_classes} classes")
        print(f"   📊 Class distribution:")
        
        for idx, class_name in enumerate(classnames):
            count = class_distribution.get(class_name, 1)
            # Inverse frequency weight
            weight = total_samples / (num_classes * count)
            weights[idx] = weight
            
            percentage = (count / total_samples) * 100
            print(f"      {class_name:25}: {count:4d} samples ({percentage:5.1f}%) → weight: {weight:.3f}")
        
        # Normalize to prevent extreme weights
        weights = weights / weights.mean()
        
        # Cap maximum weight to prevent training instability
        max_weight = 5.0  # Reasonable cap
        weights = torch.clamp(weights, max=max_weight)
        
        print(f"   ✅ Final weights - Range: {weights.min():.3f} - {weights.max():.3f}")
        return weights

        # Note that multi-GPU training could be slow because CLIP's size is
        # big, which slows down the copy operation in DataParallel
        device_count = torch.cuda.device_count()
        if device_count > 1:
            print(f"Multiple GPUs detected (n_gpus={device_count}), use all of them!")
            self.model = nn.DataParallel(self.model)
        
        # Line ~160-170, at the END of build_model():
        # FORCE MPS - Add this
        device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
        self.model = self.model.to(device)
        self.device = device
        print(f"🔥 FORCED to {device}: {next(self.model.parameters()).device}")

    def forward_backward(self, batch):
        # Critical debug
        if not hasattr(self, '_mps_check'):
            print("\n" + "="*60)
            print("🚨 CRITICAL MPS CHECK IN FORWARD_BACKWARD:")
            print(f"   self.device = {self.device}")
            print(f"   Model device = {next(self.model.parameters()).device}")
            print(f"   Model on MPS = {next(self.model.parameters()).is_mps}")
            
            # Check each component
            for name, module in self.model.named_children():
                if hasattr(module, 'parameters'):
                    try:
                        param_device = next(module.parameters()).device
                        print(f"   {name} device = {param_device}")
                    except StopIteration:
                        pass
            print("="*60 + "\n")
            self._mps_check = True
        
            image, label = self.parse_batch_train(batch)
            
            model = self.model
            optim = self.optim
            scaler = self.scaler
            
            prec = self.cfg.TRAINER.COCOOP.PREC
            if prec == "amp":
                with autocast():
                    loss = model(image, label)
                optim.zero_grad()
                scaler.scale(loss).backward()
                scaler.step(optim)
                scaler.update()
            else:
                loss = model(image, label)
                optim.zero_grad()
                loss.backward()
                optim.step()

            loss_summary = {"loss": loss.item()}

            if (self.batch_idx + 1) == self.num_batches:
                self.update_lr()

            return loss_summary

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
            model_path = osp.join(directory, name, model_file)

            if not osp.exists(model_path):
                raise FileNotFoundError('Model not found at "{}"'.format(model_path))

            checkpoint = load_checkpoint(model_path)
            state_dict = checkpoint["state_dict"]
            epoch = checkpoint["epoch"]

            # Ignore fixed token vectors (they should be recomputed for the current dataset)
            if "token_prefix" in state_dict:
                del state_dict["token_prefix"]

            if "token_suffix" in state_dict:
                del state_dict["token_suffix"]

            print("Loading weights to {} " 'from "{}" (epoch = {})'.format(name, model_path, epoch))
            # set strict=False
            self._models[name].load_state_dict(state_dict, strict=False)
