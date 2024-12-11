db_name=$1
query_file=${WORKDIR}/TAG-Bench/query_by_db/query_${db_name}.csv
outdir=$WORKDIR/sql_agent_output
outfile=${db_name}_agent_test_result.csv
python3 generate_answers.py --query_file $query_file --output_dir $outdir --output_file $outfile