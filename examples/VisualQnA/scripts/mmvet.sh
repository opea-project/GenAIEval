#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"


python3 -m vqa_generation \
    --question-file ${EVAL}/mm-vet/llava-mm-vet.jsonl \
    --image-folder ${EVAL}/mm-vet/images \
    --answers-file ${EVAL}/mm-vet/answers/${CKPT_NAME}.jsonl

mkdir -p ${EVAL}/mm-vet/results

python3 scripts/convert_mmvet_for_eval.py \
    --src ${EVAL}/mm-vet/answers/${CKPT_NAME}.jsonl \
    --dst ${EVAL}/mm-vet/results/${CKPT_NAME}.json


python3 evals/evaluation/llava/eval_gpt_mmvet.py \
    --mmvet_path ${EVAL}/mm-vet \
    --ckpt_name ${CKPT_NAME} \
    --result_path ${EVAL}/mm-vet/results
