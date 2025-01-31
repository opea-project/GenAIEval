# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

db_name=$1
if [ -z "$db_name" ]; then
    db_name="california_schools"
fi

FILEDIR=$WORKDIR/sql_agent_output/
FILENAME=${db_name}_agent_test_result.csv
LLM_ENDPOINT=http://${host_ip}:8085 # change host_ip to the IP of LLM endpoint
MODEL_NAME="meta-llama/Meta-Llama-3.1-70B-Instruct"

python3 grade_answers.py \
--filedir $FILEDIR \
--filename $FILENAME \
--llm_endpoint $LLM_ENDPOINT \
--model_name $MODEL_NAME \
--use_vllm
