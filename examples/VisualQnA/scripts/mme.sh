#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"


python3 -m vqa_generation \
    --question-file ${EVAL}/MME/llava_mme.jsonl \
    --image-folder ${EVAL}/MME/MME_Benchmark_release_version \
    --answers-file ${EVAL}/MME/answers/${CKPT_NAME}.jsonl

cd ${EVAL}/MME

python convert_answer_to_mme.py --experiment $CKPT_NAME

cd eval_tool

python calculation.py --results_dir answers/$CKPT_NAME
