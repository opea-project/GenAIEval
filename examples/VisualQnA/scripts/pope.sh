#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"

python3 -m vqa_generation \
    --question-file ${EVAL}/pope/llava_pope_test.jsonl \
    --image-folder ${EVAL}/pope/val2014 \
    --answers-file ${EVAL}/pope/answers/${CKPT_NAME}.jsonl \

python evals/evaluation/llava/eval_pope.py \
    --annotation-dir ${EVAL}/pope/coco \
    --question-file ${EVAL}/pope/llava_pope_test.jsonl \
    --result-file ${EVAL}/pope/answers/${CKPT_NAME}.jsonl
