# Experiment Results Summary

## Baseline (RN50 + CoCoOp @ 224)
- Dataset: NIFlags (2,288 images, 70 classes)
- Splits (auto): Train 1,573 / Val 348 / Test 367
- Command:
  ```
  python train_minimal_mps.py --clean --trainer CoCoOp \
    --config-file configs/trainers/CoCoOp/rn50.yaml \
    --dataset-config-file configs/datasets/niflags.yaml \
    --output-dir experiments/niflags_rn50_full \
    TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0 OPTIM.MAX_EPOCH 50
  ```
- Result (test):
  - Accuracy: 18.0%
  - Macro-F1: 4.3%
  - Time: ~2.3 min (MPS)
- Log: `experiments/niflags_rn50_full/log.txt`

## Data composition / quality
- From `data/ni_flags/dataset_stats.json`:
  - total_images: 2288, total_classes: 70
  - hierarchical_structure: 8 categories, 11 contexts, 25 specific_flags
- Source audit (see CSV): `MSc-Themed-Research-Project/data/ni_flags/image_sources_report.csv`
  - public/images preferred, decorated excluded, min-side upscaled to 224 when needed

## Overfit sanity (tiny subset)
- To run:
  ```
  python scripts/create_overfit_subset.py --source ../data/ni_flags --dest ../data/ni_flags_overfit \
    --num-classes 3 --samples-per-class 20
  python train_minimal_mps.py --clean --trainer CoCoOp \
    --config-file configs/trainers/CoCoOp/rn50.yaml \
    --dataset-config-file configs/datasets/niflags.yaml \
    --root ../data/ni_flags_overfit \
    --output-dir experiments/overfit_test \
    TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0 OPTIM.MAX_EPOCH 100 OPTIM.LR 0.002
  ```
- Expect near-perfect fit (>90%) if pipeline is healthy.

### Runs performed (current project)
- Overfit (baseline-like, earlier): RN50 + CoCoOp @ 224, default train/test transforms, SGD LR 0.002, N_CTX 16
  - Result (train-as-test on same split): Accuracy ~71.4%, Macro-F1 ~70.4%
  - Log: `experiments/overfit_easy/log.txt` (epoch 300 eval)

- Overfit (no-aug, Adam, higher prompt capacity): RN50 + CoCoOp @ 224, train transform `('random_resized_crop','normalize')`, RRCROP_SCALE (1.0,1.0), Adam LR 0.01, WD 0.0, N_CTX 32, 500 epochs
  - Train-split eval: Accuracy 64.3%, Macro-F1 59.1%
  - Commands:
    - Train:
      ```
      python train_minimal_mps.py --clean --trainer CoCoOp \
        --config-file configs/trainers/CoCoOp/rn50.yaml \
        --dataset-config-file configs/datasets/niflags.yaml \
        --root ../data/ni_flags_overfit_easy \
        --output-dir experiments/overfit_easy_push_n32 \
        TRAINER.COCOOP.PREC fp32 TRAINER.COCOOP.N_CTX 32 \
        INPUT.TRANSFORMS "('random_resized_crop','normalize')" \
        INPUT.RRCROP_SCALE "(1.0,1.0)" INPUT.SIZE "(224,224)" \
        DATALOADER.NUM_WORKERS 0 OPTIM.NAME adam OPTIM.MAX_EPOCH 500 \
        OPTIM.LR 0.01 OPTIM.WEIGHT_DECAY 0.0
      ```
    - Eval (train split):
      ```
      python train_minimal_mps.py --eval-only \
        --model-dir experiments/overfit_easy_push_n32 --load-epoch 500 \
        --trainer CoCoOp \
        --config-file configs/trainers/CoCoOp/rn50.yaml \
        --dataset-config-file configs/datasets/niflags.yaml \
        --root ../data/ni_flags_overfit_easy \
        TEST.SPLIT train TRAINER.COCOOP.PREC fp32 TRAINER.COCOOP.N_CTX 32 \
        DATALOADER.TEST.BATCH_SIZE 1
      ```
  - Log: `experiments/overfit_easy_push_n32/log.txt`

## Planned experiments
- ViT-B/32 @ 224:
  ```
  python train_minimal_mps.py --clean --trainer CoCoOp \
    --config-file configs/trainers/CoCoOp/vit_b32.yaml \
    --dataset-config-file configs/datasets/niflags.yaml \
    --output-dir experiments/vit_b32_224 \
    TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0
  ```
- ViT-B/16 @ 224:
  ```
  python train_minimal_mps.py --clean --trainer CoCoOp \
    --config-file configs/trainers/CoCoOp/vit_b16.yaml \
    --dataset-config-file configs/datasets/niflags.yaml \
    --output-dir experiments/vit_b16_224 \
    TRAINER.COCOOP.PREC fp32 DATALOADER.NUM_WORKERS 0
  ```

## Notes for write-up
- Uncropped originals preferred; decorated files excluded; min-side upscaling to 224 enabled.
- Class imbalance significant; consider balanced sampling/focal loss in follow-ups.
- Reproducibility: keep command lines, configs, seed, env details.

## Next steps (lightweight)
- Per-class metrics + confusion matrix on overfit subset:
  ```
  python train_minimal_mps.py --eval-only \
    --model-dir experiments/overfit_easy_push_n32 --load-epoch 500 \
    --trainer CoCoOp \
    --config-file configs/trainers/CoCoOp/rn50.yaml \
    --dataset-config-file configs/datasets/niflags.yaml \
    --root ../data/ni_flags_overfit_easy \
    TEST.SPLIT train TEST.PER_CLASS_RESULT True TEST.COMPUTE_CMAT True 
  ```
- Optional baselines for discussion: linear probe on CLIP features; small fully-finetuned head.

