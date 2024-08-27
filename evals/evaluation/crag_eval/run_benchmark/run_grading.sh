FILEDIR=$WORKDIR/datasets/crag_results/
FILENAME=results.csv
LLM_ENDPOINT=http://${host_ip}:8085

python3 grade_answers.py \
--filedir $FILEDIR \
--filename $FILENAME \
--llm_endpoint $LLM_ENDPOINT \
