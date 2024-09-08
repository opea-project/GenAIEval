#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

CKPT_NAME="llava-v1.6-mistral-7b-hf"
CKPT="checkpoints/${CKPT_NAME}"
SPLIT="llava_gqa_testdev_balanced"
EVAL="vqa_eval"
GQADIR="${EVAL}/gqa/data"

python3 -m vqa_generation \
        --question-file ${EVAL}/gqa/$SPLIT.jsonl \
        --image-folder ${EVAL}/gqa/data/images \
        --answers-file ${EVAL}/gqa/answers/$SPLIT/${CKPT_NAME}/llava_eval.jsonl

wait

output_file=${EVAL}/gqa/answers/$SPLIT/${CKPT_NAME}/merge.jsonl

# Clear out the output file if it exists.
> "$output_file"

cat ${EVAL}/gqa/answers/$SPLIT/${CKPT_NAME}/llava_eval.jsonl >> "$output_file"


mkdir -p $GQADIR/$SPLIT/${CKPT_NAME}
python3 scripts/convert_gqa_for_eval.py --src $output_file --dst $GQADIR/$SPLIT/${CKPT_NAME}/testdev_balanced_predictions.json

cd $GQADIR
python3 eval/eval_gqa.py --tier $SPLIT/${CKPT_NAME}/testdev_balanced \
                         --questions ${EVAL}/gqa/data/questions1.2/testdev_balanced_questions.json
