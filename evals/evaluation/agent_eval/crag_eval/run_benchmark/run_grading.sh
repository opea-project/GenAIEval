# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FILEDIR=$WORKDIR/datasets/crag_results/
FILENAME=ragagent_crag_music_results.csv
LLM_ENDPOINT=http://${host_ip}:8085 # change host_ip to the IP of LLM endpoint
MODEL_NAME="meta-llama/Meta-Llama-3.1-70B-Instruct"

python3 grade_answers.py \
--filedir $FILEDIR \
--filename $FILENAME \
--llm_endpoint $LLM_ENDPOINT \
--model_name $MODEL_NAME \
--use_vllm
