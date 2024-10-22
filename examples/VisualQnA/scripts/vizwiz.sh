#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
EVAL="vqa_eval"

python3 -m vqa_generation \
    --question-file ${EVAL}/vizwiz/llava_test.jsonl \
    --image-folder ${EVAL}/vizwiz/test \
    --answers-file ${EVAL}/vizwiz/answers/${CKPT_NAME}.jsonl

python3 scripts/convert_vizwiz_for_submission.py \
    --annotation-file ${EVAL}/vizwiz/llava_test.jsonl \
    --result-file ${EVAL}/vizwiz/answers/${CKPT_NAME}.jsonl \
    --result-upload-file ${EVAL}/vizwiz/answers_upload/${CKPT_NAME}.json
