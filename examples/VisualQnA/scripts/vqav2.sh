#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
SPLIT="llava_vqav2_mscoco_test-dev2015"
EVAL="vqa_eval"

python3 -m vqa_generation \
        --question-file ${EVAL}/vqav2/$SPLIT.jsonl \
        --image-folder ${EVAL}/vqav2/test2015 \
        --answers-file ${EVAL}/vqav2/answers/$SPLIT/${CKPT_NAME}/llava_eval.jsonl


wait

output_file=${EVAL}/vqav2/answers/$SPLIT/${CKPT_NAME}/merge.jsonl

# Clear out the output file if it exists.
> "$output_file"

cat ${EVAL}/vqav2/answers/$SPLIT/${CKPT_NAME}/llava_evaljsonl >> "$output_file"

python3 scripts/convert_vqav2_for_submission.py --split $SPLIT --ckpt ${CKPT_NAME} --dir ${EVAL}/vqav2
