#!/bin/bash

cd ..

# custom config
DATA=/root/autodl-tmp/coop/DATA
TRAINER=ZeroshotCLIP
DATASET=$1
CFG=vit_b16_ep100  #vit_b16_ep100  # rn50, rn101, vit_b32 or vit_b16
CTP=end  # class token position (end or middle)
NCTX=16  # number of context tokens
SHOTS=1  # number of shots (1, 2, 4, 8, 16)
CSC=False  # class-specific context (False or True)
SUB=new
SEED=1 

python train.py \
--seed ${SEED} \
--root ${DATA} \
--trainer ${TRAINER} \
--dataset-config-file configs/datasets/${DATASET}.yaml \
--config-file configs/trainers/CoOp/${CFG}.yaml \
--output-dir output/${TRAINER}/${CFG}/seed${SEED}/${DATASET} \
--eval-only\
        TRAINER.COOP.N_CTX ${NCTX} \
        TRAINER.COOP.CSC ${CSC} \
        TRAINER.COOP.CLASS_TOKEN_POSITION ${CTP} \
        DATASET.NUM_SHOTS ${SHOTS} \
        DATASET.SUBSAMPLE_CLASSES ${SUB}