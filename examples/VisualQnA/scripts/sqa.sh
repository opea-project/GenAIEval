#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"


python3 -m vqa_generation \
    --question-file ${EVAL}/scienceqa/llava_test_CQM-A.json \
    --image-folder ${EVAL}/scienceqa/images/test \
    --answers-file ${EVAL}/scienceqa/answers/${CKPT_NAME}.jsonl \
    --single-pred-prompt

python3 evals/evaluation/llava/eval_science_qa.py \
    --base-dir ${EVAL}/scienceqa \
    --result-file ${EVAL}/scienceqa/answers/${CKPT_NAME}.jsonl \
    --output-file ${EVAL}/scienceqa/answers/${CKPT_NAME}_output.jsonl \
    --output-result ${EVAL}/scienceqa/answers/${CKPT_NAME}_result.json
