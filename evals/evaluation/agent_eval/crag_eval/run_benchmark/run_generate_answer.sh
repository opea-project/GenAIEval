# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

host_ip=$host_ip # change this to the host IP of the agent
port=9095 # change this to the port of the agent
endpoint=${port}/v1/chat/completions # change this to the endpoint of the agent
URL="http://${host_ip}:${endpoint}"
echo "AGENT ENDPOINT URL: ${URL}"

QUERYFILE=$WORKDIR/datasets/crag_qas/crag_qa_music.jsonl
OUTPUTFILE=$WORKDIR/datasets/crag_results/ragagent_crag_music_results.jsonl

python3 generate_answers.py \
--endpoint_url ${URL} \
--query_file $QUERYFILE \
--output_file $OUTPUTFILE
