# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

# LLM related environment variables
export HF_CACHE_DIR=${HF_CACHE_DIR}
ls $HF_CACHE_DIR
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export LLM_ENDPOINT_URL="http://${ip_address}:8085"
export temperature=0.01
export max_new_tokens=4096

# agent related environment variables
EVALDIR=$WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval
export TOOLSET_PATH=$EVALDIR/opea_rag_agent/tools/
echo "TOOLSET_PATH=${TOOLSET_PATH}"
export recursion_limit_worker=16
export recursion_limit_supervisor=16
export WORKER_AGENT_URL="http://${ip_address}:9095/v1/chat/completions"
export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
export CRAG_SERVER=http://${ip_address}:8080

docker compose -f $EVALDIR/opea_rag_agent/rag_agent.yaml up -d

sleep 20s
echo "Agent microservices started!"
