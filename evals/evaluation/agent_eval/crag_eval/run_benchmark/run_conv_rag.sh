MODEL="meta-llama/Meta-Llama-3.1-70B-Instruct"
LLMENDPOINT=http://${host_ip}:8085

FILEDIR=$WORKDIR/datasets/ragagent_eval/
FILENAME=crag_qa_music.jsonl
OUTPUT=$WORKDIR/datasets/ragagent_eval/val_conv_rag_music_full.jsonl

python3 benchmark.py \
--model ${MODEL} \
--llm_endpoint_url ${LLMENDPOINT} \
--filedir ${FILEDIR} \
--filename ${FILENAME} \
--output ${OUTPUT}