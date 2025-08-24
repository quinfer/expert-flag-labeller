import os.path as osp
from collections import OrderedDict
import math
from vitaev2 import ViTAEv2
from timm.models import load_checkpoint, create_model

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
import timm
_tokenizer = _Tokenizer()

import open_clip


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

        x = x[torch.arange(x.shape[0]),
              tokenized_prompts.argmax(dim=-1)] @ self.text_projection

        return x


class FlagPromptLearner(nn.Module):
    """
    Modified PromptLearner for hierarchical flag classification
    
    Hierarchical structure:
    Level 1: "a photo of a flag, category is [National/Fraternal/Sport/Military/Historical/International/Proscribed]"
    Level 2: "display context is [building_mounted/pole_mounted/hand_carried/vehicle_mounted]" 
    Level 3: "specific flag is [Union_Jack/Irish_Tricolor/etc.]"
    """
    
    def __init__(self, cfg, classnames, clip_model):
        super().__init__()
        n_cls = len(classnames)
        n_ctx = cfg.TRAINER.COCOOP.N_CTX
        ctx_init = cfg.TRAINER.COCOOP.CTX_INIT
        
        # FLAG-SPECIFIC HIERARCHICAL PROMPTS
        ctx_init2 = 'display context is'  # Level 2: Context information
        ctx_init3 = 'specific flag is'    # Level 3: Specific flag identification
        
        dtype = clip_model.dtype
        ctx_dim = clip_model.ln_final.weight.shape[0]
        vis_dim = clip_model.visual.output_dim
        clip_imsize = clip_model.visual.input_resolution
        cfg_imsize = cfg.INPUT.SIZE[0]
        assert cfg_imsize == clip_imsize, f"cfg_imsize ({cfg_imsize}) must equal to clip_imsize ({clip_imsize})"

        # Parse hierarchical classnames (format: "category-context-specific_flag")
        classnames = [name.replace("_", " ") for name in classnames]
        classnames = [name.split("-") for name in classnames]
        
        print(f"Processing {len(classnames)} hierarchical flag classes")
        print(f"Example classes: {classnames[:3]}")
        
        if ctx_init:
            # FLAG-SPECIFIC INITIAL CONTEXT
            ctx_init = 'a photo of a flag, category is'  # Level 1: Flag category
            ctx_init = ctx_init.replace(" {}.", "")
            ctx_init = ctx_init.replace("_", " ")
            prompt_n_ctx = len(ctx_init.split(" "))

            assert n_ctx >= prompt_n_ctx, f"#tokens ({n_ctx}) should be >= #initial prompt tokens ({prompt_n_ctx}, {ctx_init})"

            prompt = clip.tokenize(ctx_init)
            with torch.no_grad():
                embedding = clip_model.token_embedding(prompt).type(dtype)

            ctx_vectors = torch.zeros(n_ctx, ctx_dim, dtype=dtype)
            ctx_vectors[n_ctx - prompt_n_ctx:, :] = embedding[0, 1:1 + prompt_n_ctx, :]
            prompt_prefix = " ".join(["X"] * (n_ctx - prompt_n_ctx))
            prompt_prefix = f"{prompt_prefix} {ctx_init}"
        else:
            # Random initialization
            ctx_vectors = torch.empty(n_ctx, ctx_dim, dtype=dtype)
            nn.init.normal_(ctx_vectors, std=0.02)
            prompt_prefix = " ".join(["X"] * n_ctx)

        print(f'Initial context: "{prompt_prefix}"')
        print(f"Number of context words (tokens): {n_ctx}")

        self.ctx = nn.Parameter(ctx_vectors)

        # Meta-network for conditional context generation
        self.meta_net = nn.Sequential(
            OrderedDict([("linear1", nn.Linear(vis_dim, vis_dim // 16)),
                         ("relu", nn.ReLU(inplace=True)),
                         ("linear2", nn.Linear(vis_dim // 16, ctx_dim))]))

        if cfg.TRAINER.COCOOP.PREC == "fp16":
            self.meta_net.half()
        
        # Create hierarchical prompts for each flag class
        # Format: "X X X a photo of a flag, category is [category], display context is [context], specific flag is [specific_flag]."
        prompts = []
        for name in classnames:
            if len(name) >= 3:
                category, context, specific_flag = name[0], name[1], name[2]
            else:
                # Handle edge cases where hierarchical structure might be incomplete
                category = name[0] if len(name) > 0 else "unknown"
                context = name[1] if len(name) > 1 else "unknown"
                specific_flag = name[2] if len(name) > 2 else "unknown"
            
            prompt = f"{prompt_prefix} {category}, {ctx_init2} {context}, {ctx_init3} {specific_flag}."
            prompts.append(prompt)

        print(f"Example prompts:")
        for i, prompt in enumerate(prompts[:3]):
            print(f"  {i+1}: {prompt}")

        tokenized_prompts = torch.cat([clip.tokenize(p) for p in prompts])
        with torch.no_grad():
            embedding = clip_model.token_embedding(tokenized_prompts).type(dtype)

        # Save token vectors for prompt construction
        self.register_buffer("token_prefix", embedding[:, :1, :])  # SOS
        self.register_buffer("token_suffix", embedding[:, 1 + n_ctx:, :])  # CLS, EOS

        self.n_cls = n_cls
        self.n_ctx = n_ctx
        self.tokenized_prompts = tokenized_prompts

    def construct_prompts(self, ctx, prefix, suffix, label=None):
        if label is not None:
            prefix = prefix[label]
            suffix = suffix[label]

        prompts = torch.cat([prefix, ctx, suffix], dim=1)
        return prompts

    def forward(self, im_features):
        prefix = self.token_prefix
        suffix = self.token_suffix
        ctx = self.ctx  # (n_ctx, ctx_dim)
        bias = self.meta_net(im_features)  # (batch, ctx_dim)
        bias = bias.unsqueeze(1)  # (batch, 1, ctx_dim)
        ctx = ctx.unsqueeze(0)  # (1, n_ctx, ctx_dim)
        ctx_shifted = ctx + bias  # (batch, n_ctx, ctx_dim)

        # Use instance-conditioned context tokens for all classes
        prompts = []
        for ctx_shifted_i in ctx_shifted:
            ctx_i = ctx_shifted_i.unsqueeze(0).expand(self.n_cls, -1, -1)
            pts_i = self.construct_prompts(ctx_i, prefix, suffix)
            prompts.append(pts_i)
        prompts = torch.stack(prompts)

        return prompts


# Custom templates for different domains (for reference - you can customize these)
CUSTOM_TEMPLATES = {
    "NIFlags": "a photo of a flag, category is {}.",
    "OxfordPets": "a type of pet, a photo of a {}.",
    "OxfordFlowers": "a type of flower, a photo of a {}.",
    "FGVCAircraft": "a type of aircraft, a photo of a {}.",
    "DescribableTextures": "a texture of {}.",
    "EuroSAT": "a centered satellite photo of {}.",
    "StanfordCars": "a photo of a {}.",
    "Food101": "a type of food, a photo of {}.",
    "SUN397": "a photo of a {}.",
    "Caltech101": "a photo of a {}.",
    "UCF101": "a photo of a person doing {}.",
    "ImageNet": "a photo of a {}.",
}


class CustomCLIP(nn.Module):
    def __init__(self, cfg, classnames, clip_model):
        super().__init__()
        self.prompt_learner = FlagPromptLearner(cfg, classnames, clip_model)  # Use flag-specific prompt learner
        self.tokenized_prompts = self.prompt_learner.tokenized_prompts
        self.image_encoder = clip_model.visual
        self.text_encoder = TextEncoder(clip_model)
        self.logit_scale = clip_model.logit_scale
        self.dtype = clip_model.dtype
        
        print('Loading remote sensing model for enhanced feature extraction...')
        
        # Load RS5M model (ensure this path is correct for your setup)
        ckpt_path = "/root/autodl-tmp/RS5M_ViT-H-14.pt"  # Update this path!
        
        if os.path.exists(ckpt_path):
            model, _, _ = open_clip.create_model_and_transforms("ViT-H/14", pretrained="laion2b_s32b_b79k")
            checkpoint = torch.load(ckpt_path, map_location="cpu")
            
            remote_model = model.visual
            remote_model_dict = remote_model.state_dict()
            
            # Update with pretrained weights
            new_dict = {}
            for k, v in checkpoint.items():
                if "visual" in k and "ln_post" not in k: 
                    new_dict[k[7:]] = v
            remote_model_dict.update(new_dict)
            remote_model.load_state_dict(remote_model_dict)
            self.remote_model = remote_model
        else:
            print(f"Warning: RS5M model not found at {ckpt_path}. Using standard CLIP features only.")
            self.remote_model = None

        # Visual feature adaptation network
        self.visual_net = nn.Sequential(OrderedDict([
            ("linear1", nn.Linear(1024, 1024 // 16)),
            ("relu", nn.ReLU(inplace=True)),
            ("linear2", nn.Linear(1024 // 16, 1024))
        ]))
        
        if cfg.TRAINER.COCOOP.PREC == "fp16":
            self.visual_net.half()

    def forward(self, image, label=None):
        tokenized_prompts = self.tokenized_prompts
        logit_scale = self.logit_scale.exp()

        # Standard CLIP image features
        image_features = self.image_encoder(image.type(self.dtype))
        
        # Enhanced features from remote sensing model (if available)
        if self.remote_model is not None:
            with torch.no_grad():
                remote_feature = self.remote_model(image)
            
            # Generate conditioned prompts using remote features
            prompts = self.prompt_learner(remote_feature.type(self.dtype))
            
            # Enhance image features with remote sensing information
            image_features_bias = self.visual_net(remote_feature.type(self.dtype))
            image_features = image_features + image_features_bias
        else:
            # Fallback: use standard CLIP features for prompt conditioning
            prompts = self.prompt_learner(image_features)
        
        # Normalize image features
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        # Compute logits for each image-prompt pair
        logits = []
        for pts_i, imf_i in zip(prompts, image_features):
            text_features = self.text_encoder(pts_i, tokenized_prompts)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            l_i = logit_scale * imf_i @ text_features.t()
            logits.append(l_i)
        logits = torch.stack(logits)

        if self.prompt_learner.training:
            return F.cross_entropy(logits, label)

        return logits


@TRAINER_REGISTRY.register()
class CoCoOpFlags(TrainerX):
    """
    Conditional Context Optimization for Flag Classification
    
    This trainer adapts Li et al.'s CoCoOp for hierarchical flag classification
    with Northern Ireland cultural context.
    """
    
    def check_cfg(self, cfg):
        assert cfg.TRAINER.COCOOP.PREC in ["fp16", "fp32", "amp"]

    def build_model(self):
        cfg = self.cfg
        classnames = self.dm.dataset.classnames

        print(f"Loading CLIP (backbone: {cfg.MODEL.BACKBONE.NAME})")
        clip_model = load_clip_to_cpu(cfg)

        if cfg.TRAINER.COCOOP.PREC == "fp32" or cfg.TRAINER.COCOOP.PREC == "amp":
            clip_model.float()

        print("Building custom CLIP for flag classification")
        self.model = CustomCLIP(cfg, classnames, clip_model)

        print("Turning off gradients in both the image and the text encoder")
        name_to_update = "prompt_learner"

        for name, param in self.model.named_parameters():
            if name_to_update not in name:
                param.requires_grad_(False)
            if "visual_net" in name:
                param.requires_grad_(True)

        # Check which parameters will be updated
        enabled = set()
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                enabled.add(name)
        print(f"Parameters to be updated: {enabled}")

        if cfg.MODEL.INIT_WEIGHTS:
            load_pretrained_weights(self.model, cfg.MODEL.INIT_WEIGHTS)

        self.model.to(self.device)
        self.optim = build_optimizer(self.model, cfg.OPTIM)
        self.sched = build_lr_scheduler(self.optim, cfg.OPTIM)
        self.register_model("prompt_learner", self.model, self.optim, self.sched)

        self.scaler = GradScaler() if cfg.TRAINER.COCOOP.PREC == "amp" else None

        # Multi-GPU support
        device_count = torch.cuda.device_count()
        if device_count > 1:
            print(f"Multiple GPUs detected (n_gpus={device_count}), use all of them!")
            self.model = nn.DataParallel(self.model)

    def forward_backward(self, batch):
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
        model_file = "model-best.pth.tar"

        if epoch is not None:
            model_file = "model.pth.tar-" + str(epoch)

        for name in names:
            model_path = osp.join(directory, name, model_file)

            if not osp.exists(model_path):
                raise FileNotFoundError(f'Model not found at "{model_path}"')

            checkpoint = load_checkpoint(model_path)
            state_dict = checkpoint["state_dict"]
            epoch = checkpoint["epoch"]

            # Ignore fixed token vectors (they will be recomputed for current classes)
            if "prompt_learner.token_prefix" in state_dict:
                del state_dict["prompt_learner.token_prefix"]

            if "prompt_learner.token_suffix" in state_dict:
                del state_dict["prompt_learner.token_suffix"]

            print(f"Loading weights to {name} from \"{model_path}\" (epoch = {epoch})")
            self._models[name].load_state_dict(state_dict, strict=False)
