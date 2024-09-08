#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"

python3 -m vqa_generation \
        --question-file ${EVAL}/seed_bench/llava-seed-bench.jsonl \
        --image-folder ${EVAL}/seed_bench \
        --answers-file ${EVAL}/seed_bench/answers/seed_eval.jsonl

wait

output_file=${EVAL}/seed_bench/answers/${CKPT_NAME}/merge.jsonl

# Clear out the output file if it exists.
> "$output_file"

cat ${EVAL}/seed_bench/answers/seed_eval.jsonl >> "$output_file"


# Evaluate
python scripts/convert_seed_for_submission.py \
    --annotation-file ${EVAL}/seed_bench/SEED-Bench.json \
    --result-file $output_file \
    --result-upload-file ${EVAL}/seed_bench/answers_upload/${CKPT_NAME}.jsonl

