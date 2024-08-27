host_ip=$(hostname -I | awk '{print $1}') # change this to the IP of the agent
port=9095 # change this to the port of the agent
endpoint=${port}/v1/chat/completions # change this to the endpoint of the agent
URL="http://${host_ip}:${endpoint}"
echo "AGENT ENDPOINT URL: ${URL}"

QUERYFILE=$WORKDIR/datasets/crag_qas/crag_qa_music_sampled.jsonl
OUTPUTFILE=$WORKDIR/datasets/crag_results/results.jsonl

python3 generate_answers.py \
--endpoint_url ${URL} \
--query_file $QUERYFILE \
--output_file $OUTPUTFILE
