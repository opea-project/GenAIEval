MODEL="meta-llama/Meta-Llama-3.1-70B-Instruct"
LLMENDPOINT=http://${host_ip}:8085

FILEDIR=$WORKDIR/datasets/crag_qas/
FILENAME=crag_qa_music.jsonl
OUTPUT=$WORKDIR/datasets/crag_results/conv_rag_music.jsonl

export RETRIEVAL_TOOL_URL="http://${host_ip}:8889/v1/retrievaltool"

python3 conventional_rag.py \
--model ${MODEL} \
--llm_endpoint_url ${LLMENDPOINT} \
--filedir ${FILEDIR} \
--filename ${FILENAME} \
--output ${OUTPUT}