FILEDIR=$WORKDIR/datasets/crag_results/
FILENAME=crag_20queries_react_docgradertool_top5apis_v2sysm_gpt4omini.csv
LLM_ENDPOINT=http://${host_ip}:8085

python3 grade_answers.py \
--filedir $FILEDIR \
--filename $FILENAME \
--llm_endpoint $LLM_ENDPOINT \
