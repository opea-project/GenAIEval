# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

db_name=$1
FILEDIR=$WORKDIR/sql_agent_output/
FILENAME=${db_name}_agent_test_result.csv
LLM_ENDPOINT=http://${host_ip}:8085 # change host_ip to the IP of LLM endpoint

python3 grade_answers.py \
--filedir $FILEDIR \
--filename $FILENAME \
--llm_endpoint $LLM_ENDPOINT \
