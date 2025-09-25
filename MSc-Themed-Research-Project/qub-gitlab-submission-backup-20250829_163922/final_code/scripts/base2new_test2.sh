#!/bin/bash

cd ..

# custom config
DATA=/root/autodl-tmp/coop/DATA
TRAINER=CoOp
DATASET=$1
#CFG=rn50_ep100  # config file
WEIGHT=$2
CFG=vit_b16_ep100
CTP=end  # class token position (end or middle)
NCTX=16  # number of context tokens
#SHOTS=6  # number of shots (1, 2, 4, 8, 16)
CSC=False  # class-specific context (False or True)
DataName=fgscr36
ModelName=baseline

LOADEP=100
SUB=new

for SHOTS in 2 4 6 8
do
for SEED in 1 2 3
do
    COMMON_DIR=${DATASET}/shots_${SHOTS}_${WEIGHT}/${TRAINER}/${CFG}/seed${SEED}
    MODEL_DIR=output-${DataName}/base2new-${ModelName}/train_base/${COMMON_DIR}
    DIR=output-${DataName}/base2new-${ModelName}/test_${SUB}/${COMMON_DIR}


    if [ -d "$DIR" ]; then
        echo "Results are available in ${DIR}. Skip this job"
    else
        echo "Run this job and save the output to ${DIR}"
        python train.py \
        --root ${DATA} \
        --seed ${SEED} \
        --trainer ${TRAINER} \
        --dataset-config-file configs/datasets/${DATASET}.yaml \
        --config-file configs/trainers/${TRAINER}/${CFG}.yaml \
        --output-dir ${DIR} \
        --model-dir ${MODEL_DIR} \
        --load-epoch ${LOADEP} \
        --eval-only \
        TRAINER.COOP.N_CTX ${NCTX} \
        TRAINER.COOP.CSC ${CSC} \
        TRAINER.COOP.CLASS_TOKEN_POSITION ${CTP} \
        DATASET.NUM_SHOTS ${SHOTS} \
        DATASET.SUBSAMPLE_CLASSES ${SUB}
    fi
done
done
