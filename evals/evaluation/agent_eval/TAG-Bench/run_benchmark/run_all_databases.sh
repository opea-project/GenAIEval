#!/bin/bash
# This script is used to run benchmarks on all databases

EVALDIR=$WORKDIR/GenAIEval/evals/evaluation/agent_eval/TAG-Bench

function stop_agent_container(){
    echo "===========Stopping sql agent container============"
    docker rm sql-agent-endpoint -f
    echo "===========Sql agent container stopped============"
}

stop_agent_container

for db in codebase_community debit_card_specializing european_football_2 formula_1
do
    echo "=================Running benchmark on $db================="
    bash $EVALDIR/opea_sql_agent_llama/launch_sql_agent.sh $db
    sleep 1m
    bash run_generate_answer.sh $db
    sleep 10s
    echo "=================Done generating answers for $db================="

    # echo "Grading answers for $db"
    # bash run_grading.sh $db
    # echo "Done grading answers for $db"

    echo "===============stop sql agent for $db================"
    stop_agent_container
    echo "===============Benchmark on $db done================"
    sleep 5s
done

# combine all scores
# python3 combine_scores.py --filedir $WORKDIR/sql_agent_output/

# echo "All done!"