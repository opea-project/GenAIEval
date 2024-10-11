#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SPLIT="mmbench_dev_cn_20231003"
CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"


python3 -m mmbench_generation \
    --question-file ${EVAL}/mmbench/$SPLIT.tsv \
    --answers-file ${EVAL}/mmbench/answers/$SPLIT/${CKPT_NAME}.jsonl \
    --lang cn \
    --single-pred-prompt

mkdir -p ${EVAL}/mmbench/answers_upload/$SPLIT

python scripts/convert_mmbench_for_submission.py \
    --annotation-file ${EVAL}/mmbench/$SPLIT.tsv \
    --result-dir ${EVAL}/mmbench/answers/$SPLIT \
    --upload-dir ${EVAL}/mmbench/answers_upload/$SPLIT \
    --experiment ${CKPT_NAME}
