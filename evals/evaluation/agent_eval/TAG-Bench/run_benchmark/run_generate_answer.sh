# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

db_name=$1
if [ -z "$db_name" ]; then
    db_name="california_schools"
fi
query_file=${WORKDIR}/TAG-Bench/query_by_db/query_${db_name}.csv
outdir=$WORKDIR/sql_agent_output
outfile=${db_name}_agent_test_result.csv
python3 generate_answers.py --query_file $query_file --output_dir $outdir --output_file $outfile --db_name $db_name