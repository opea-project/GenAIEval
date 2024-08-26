export LLM_MODEL_ID="meta-llama/Meta-Llama-3-70B-Instruct" #"meta-llama/Meta-Llama-3-70B-Instruct" #
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_CACHE_DIR=${HF_CACHE_DIR}
docker compose -f docker-compose-llm-judge-gaudi.yaml up -d