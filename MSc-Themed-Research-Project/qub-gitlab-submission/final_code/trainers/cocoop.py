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
        # loading JIT archive
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

        # x.shape = [batch_size, n_ctx, transformer.width]
        # take features from the eot embedding (eot_token is the highest number in each sequence)
        x = x[torch.arange(x.shape[0]),
              tokenized_prompts.argmax(dim=-1)] @ self.text_projection

        return x


class PromptLearner(nn.Module):
    def __init__(self, cfg, classnames, clip_model):
        super().__init__()
        n_cls = len(classnames)
        n_ctx = cfg.TRAINER.COCOOP.N_CTX
        ctx_init = cfg.TRAINER.COCOOP.CTX_INIT
        ctx_init2 = 'econdary type is'  #cfg.TRAINER.COCOOP.CTX_INIT3
        ctx_init3 = 'final type is'  #cfg.TRAINER.COCOOP.CTX_INIT2
        dtype = clip_model.dtype
        ctx_dim = clip_model.ln_final.weight.shape[0]
        vis_dim = clip_model.visual.output_dim
        clip_imsize = clip_model.visual.input_resolution
        cfg_imsize = cfg.INPUT.SIZE[0]
        assert cfg_imsize == clip_imsize, f"cfg_imsize ({cfg_imsize}) must equal to clip_imsize ({clip_imsize})"

        classnames = [name.replace("_", " ") for name in classnames]
        classnames = [name.split("-") for name in classnames]
        
        if ctx_init:
            ctx_init =  'a photo of a ship, primary type is'  #CUSTOM_TEMPLATES[cfg.DATASET.NAME]
            ctx_init = ctx_init.replace(" {}.", "")
            ctx_init = ctx_init.replace("_", " ")
            prompt_n_ctx = len(ctx_init.split(" "))

            assert n_ctx >= prompt_n_ctx, f"#tokens ({n_ctx}) should larger equal than #initial prompt tokens ({prompt_n_ctx}, {ctx_init})"

            prompt = clip.tokenize(ctx_init)
            with torch.no_grad():
                embedding = clip_model.token_embedding(prompt).type(dtype)

            ctx_vectors = torch.zeros(n_ctx, ctx_dim, dtype=dtype)

            ctx_vectors[n_ctx - prompt_n_ctx:, :] = embedding[0, 1:1 +
                                                              prompt_n_ctx, :]
            prompt_prefix = " ".join(["X"] * (n_ctx - prompt_n_ctx))
            prompt_prefix = f"{prompt_prefix} {ctx_init}"
        else:
            # random initialization
            ctx_vectors = torch.empty(n_ctx, ctx_dim, dtype=dtype)
            nn.init.normal_(ctx_vectors, std=0.02)
            prompt_prefix = " ".join(["X"] * n_ctx)

        print(f'Initial context: "{prompt_prefix}"')
        print(f"Number of context words (tokens): {n_ctx}")

        self.ctx = nn.Parameter(ctx_vectors)

        self.meta_net = nn.Sequential(
            OrderedDict([("linear1", nn.Linear(vis_dim, vis_dim // 16)), #vis_dim
                         ("relu", nn.ReLU(inplace=True)),
                         ("linear2", nn.Linear(vis_dim // 16, ctx_dim))]))

        if cfg.TRAINER.COCOOP.PREC == "fp16":
            self.meta_net.half()
        
        prompts = [prompt_prefix + " " + name[0] + ", " +ctx_init2 + " " + name[1] + ", " +ctx_init3 + " "+ name[2]+ "." for name in classnames]



        tokenized_prompts = torch.cat([clip.tokenize(p)
                                       for p in prompts])  # (n_cls, n_tkn)
        with torch.no_grad():
            embedding = clip_model.token_embedding(tokenized_prompts).type(
                dtype)

        # These token vectors will be saved when in save_model(),
        # but they should be ignored in load_model() as we want to use
        # those computed using the current class names
        self.register_buffer("token_prefix", embedding[:, :1, :])  # SOS
        self.register_buffer("token_suffix",
                             embedding[:, 1 + n_ctx:, :])  # CLS, EOS

        self.n_cls = n_cls
        self.n_ctx = n_ctx
        self.tokenized_prompts = tokenized_prompts  # torch.Tensor
#         self.name_lens = name_lens

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
                ctx,  # (dim0, n_ctx, dim)
                suffix,  # (dim0, *, dim)
            ],
            dim=1,
        )

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
            pts_i = self.construct_prompts(ctx_i, prefix,
                                           suffix)  # (n_cls, n_tkn, ctx_dim)
            prompts.append(pts_i)
        prompts = torch.stack(prompts)

        return prompts


CUSTOM_TEMPLATES = {
    # "OxfordPets": "a photo of a {}, a type of pet.",
    "OxfordPets": "a type of pet, a photo of a {}.",
    # "OxfordFlowers": "a photo of a {}, a type of flower.",
    "OxfordFlowers": "a type of flower, a photo of a {}.",
    "FGVCAircraft": "a type of aircraft, a photo of a {}.",
    "DescribableTextures": "a texture of {}.",
    "EuroSAT": "a centered satellite photo of {}.",
    "StanfordCars": "a photo of a {}.",
    # "Food101": "a photo of {}, a type of food.",
    "Food101": "a type of food, a photo of {}.",
    "SUN397": "a photo of a {}.",
    "Caltech101": "a photo of a {}.",
    "UCF101": "a photo of a person doing {}.",
    "ImageNet": "a photo of a {}.",
    "ImageNetSketch": "a photo of a {}.",
    "ImageNetV2": "a photo of a {}.",
    "ImageNetA": "a photo of a {}.",
    "ImageNetR": "a photo of a {}.",
}


class CustomCLIP(nn.Module):
    def __init__(self, cfg, classnames, clip_model):
        super().__init__()
        self.prompt_learner = PromptLearner(cfg, classnames, clip_model)
        self.tokenized_prompts = self.prompt_learner.tokenized_prompts
        self.image_encoder = clip_model.visual
        self.text_encoder = TextEncoder(clip_model)
        self.logit_scale = clip_model.logit_scale
        self.dtype = clip_model.dtype
        
        print('loading remote model')
        #self.remote_model= create_model('ViTAEv2_B',num_classes=0)
        
        
        ckpt_path ="/root/autodl-tmp/RS5M_ViT-H-14.pt"
        model, _, _ = open_clip.create_model_and_transforms("ViT-H/14",pretrained="laion2b_s32b_b79k")
        checkpoint = torch.load(ckpt_path, map_location="cpu")

        #remote_model_all = model.load_state_dict(checkpoint, strict=False)
        remote_model =model.visual
        remote_model_dict=remote_model.state_dict()
        
        for k, v in checkpoint.items():
            if "visual" in k and "ln_post" not in k: 
                new_dict= {k[7:]:v}
            else:
                continue
        remote_model_dict.update(new_dict)
#         print(remote_model)
       
        remote_model.load_state_dict(remote_model_dict)
        self.remote_model=remote_model
            
        
#         print(remote_model.items())
#         exit()
    
#         print(model)
#         exit()
#         model = model.to("cuda")
        
        #self.remote_model = timm.create_model('swin_tiny_patch4_window7_224',pretrained=False, num_classes=0)
#         remote_model_dict=self.remote_model.state_dict()
# #         print(self.remote_model)
# #         exit()
#         model_path = '/root/ViTAEv2-B-22k.pth_2.tar' 
#         model1=torch.load(model_path)
# #         print(model1.items())
#         exit()

#         for k, v in model1['model'].items():
#         for k, v in model1['state_dict_ema'].items():
            
#             if k=='head.weight':
#                 continue
#             elif k=='head.bias':
#                 continue
#             else:
#                 new_dict= {k:v} 
#             #print(k)
#         remote_model_dict.update(new_dict)

#         self.remote_model.load_state_dict(remote_model_dict)
#         self.remote_model = timm.create_model('vit_base_patch16_224',pretrained=True, num_classes=0)


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

        image_features = self.image_encoder(image.type(self.dtype))
        
        
        
        with torch.no_grad():
            remote_feature = self.remote_model(image)
#             print('remote_feature1',remote_feature.shape)
#             #remote_feature = remote_feature.mean(dim=1).type(self.dtype)
#         exit()
        prompts = self.prompt_learner(remote_feature.type(self.dtype))
#         print('remote_feature',remote_feature.shape)
#         exit()
        #print('image_features',image_features.shape)

        #Noise+Bias
        #mean = torch.mean(image_features)
        #noise = torch.randn(image_features.shape).cuda().type(self.dtype)*mean
        #Bias
#         print(image_features.shape)
#         print(remote_feature.shape)
#         exit()
        image_features_bias = self.visual_net(remote_feature.type(self.dtype))

        image_features = image_features + image_features_bias 
        image_features = image_features / image_features.norm(dim=-1,
                                                              keepdim=True)
        

        logits = []
        for pts_i, imf_i in zip(prompts, image_features):
            text_features = self.text_encoder(pts_i, tokenized_prompts)
            text_features = text_features / text_features.norm(dim=-1,
                                                               keepdim=True)
            l_i = logit_scale * imf_i @ text_features.t()
            logits.append(l_i)
        logits = torch.stack(logits)

        if self.prompt_learner.training:
            return F.cross_entropy(logits, label)

        return logits


@TRAINER_REGISTRY.register()
class CoCoOp(TrainerX):
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
        self.model = CustomCLIP(cfg, classnames, clip_model)

        print("Turning off gradients in both the image and the text encoder")
        name_to_update = "prompt_learner"

        for name, param in self.model.named_parameters():
            if name_to_update not in name:
                param.requires_grad_(False)
            if "visual_net" in name:
                param.requires_grad_(True)

        # Double check
        enabled = set()
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                enabled.add(name)
        print(f"Parameters to be updated: {enabled}")

        if cfg.MODEL.INIT_WEIGHTS:
            
            load_pretrained_weights(self.model,
                                    cfg.MODEL.INIT_WEIGHTS)

        self.model.to(self.device)
        # NOTE: only give prompt_learner to the optimizer
        self.optim = build_optimizer(self.model, cfg.OPTIM)
        self.sched = build_lr_scheduler(self.optim, cfg.OPTIM)
        self.register_model("prompt_learner", self.model,
                            self.optim, self.sched)

        self.scaler = GradScaler(
        ) if cfg.TRAINER.COCOOP.PREC == "amp" else None

        # Note that multi-gpu training could be slow because CLIP's size is
        # big, which slows down the copy operation in DataParallel
        device_count = torch.cuda.device_count()
        if device_count > 1:
            print(
                f"Multiple GPUs detected (n_gpus={device_count}), use all of them!"
            )
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
            print(
                "Note that load_model() is skipped as no pretrained model is given"
            )
            return

        names = self.get_model_names()

        # By default, the best model is loaded
        model_file = "model-best.pth.tar"

        if epoch is not None:
            model_file = "model.pth.tar-" + str(epoch)

        for name in names:
            model_path = osp.join(directory, name, model_file)

            if not osp.exists(model_path):
                raise FileNotFoundError(
                    'Model not found at "{}"'.format(model_path))

            checkpoint = load_checkpoint(model_path)
            state_dict = checkpoint["state_dict"]
            epoch = checkpoint["epoch"]
#             for k, v in checkpoint['state_dict'].items():
#                 print(k)
#             exit()

            # Ignore fixed token vectors
            if "prompt_learner.token_prefix" in state_dict:
                del state_dict["prompt_learner.token_prefix"]

            if "prompt_learner.token_suffix" in state_dict:
                del state_dict["prompt_learner.token_suffix"]

            print("Loading weights to {} "
                  'from "{}" (epoch = {})'.format(name, model_path, epoch))
            # set strict=False
            self._models[name].load_state_dict(state_dict, strict=False)
