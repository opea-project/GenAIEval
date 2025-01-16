# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_CACHE_DIR=${HF_CACHE_DIR}
docker compose -f docker-compose-llm-judge-gaudi.yaml up -d
