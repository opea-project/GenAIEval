#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"

python3 -m vqa_generation \
    --question-file ${EVAL}/llava-bench-in-the-wild/questions.jsonl \
    --image-folder ${EVAL}/llava-bench-in-the-wild/images \
    --answers-file ${EVAL}/llava-bench-in-the-wild/answers/${CKPT_NAME}.jsonl

mkdir -p ${EVAL}/llava-bench-in-the-wild/reviews

python3 evals/evaluation/llava/eval_gpt_review_bench.py \
    --question ${EVAL}/llava-bench-in-the-wild/questions.jsonl \
    --context ${EVAL}/llava-bench-in-the-wild/context.jsonl \
    --rule moellava/eval/table/rule.json \
    --answer-list ${EVAL}/llava-bench-in-the-wild/answers_gpt4.jsonl \
                  ${EVAL}/llava-bench-in-the-wild/answers/${CKPT_NAME}.jsonl \
    --output ${EVAL}/llava-bench-in-the-wild/reviews/${CKPT_NAME}.jsonl

python3 evals/evaluation/llava/summarize_gpt_review.py -f ${EVAL}/llava-bench-in-the-wild/reviews/${CKPT_NAME}.jsonl
