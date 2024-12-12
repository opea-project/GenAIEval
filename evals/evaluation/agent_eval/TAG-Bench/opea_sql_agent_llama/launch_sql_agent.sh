#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#set -xe
echo $WORKDIR
EVALDIR=${WORKDIR}/GenAIEval/evals/evaluation/agent_eval/TAG-Bench

# agent vars
export agent_image="opea/agent-langchain:comps"
export recursion_limit=15

# LLM endpoint
export ip_address=$(hostname -I | awk '{print $1}')
vllm_port=8085
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export LLM_ENDPOINT_URL="http://${ip_address}:${vllm_port}"
echo "LLM_ENDPOINT_URL=${LLM_ENDPOINT_URL}"
export temperature=0.01
export max_new_tokens=4096

# Tools
export TOOLSET_PATH=${EVALDIR}/opea_sql_agent_llama/tools/ 
ls ${TOOLSET_PATH}
# for using Google search API
export GOOGLE_CSE_ID=${GOOGLE_CSE_ID}
export GOOGLE_API_KEY=${GOOGLE_API_KEY}

function start_sql_agent_llama_service(){
    export db_name=$1
    export db_path="sqlite:////home/user/TAG-Bench/dev_folder/dev_databases/${db_name}/${db_name}.sqlite"
    docker compose -f ${EVALDIR}/opea_sql_agent_llama/sql_agent_llama.yaml up -d
    # sleep 1m
}

db_name=$1
start_sql_agent_llama_service $db_name
