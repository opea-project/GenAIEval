#!/bin/bash
# This script is used to run benchmarks on all databases

function stop_agent_container(){
    docker compose -f ../opea_sql_agent_llama/sql_agent_llama.yaml down
}

stop_agent_container

for db in california_schools codebase_community debit_card_specializing european_football_2 formula_1
do
    echo "Running benchmark on $db"
    bash ../opea_sql_agent_llama/launch_sql_agent.sh $db
    sleep 1m
    bash run_benchmark.sh $db
    sleep 10s
    echo "Done generating answers for $db"

    echo "Grading answers for $db"
    bash run_grading.sh $db
    echo "Done grading answers for $db"

    echo "stop sql agent for $db"
    stop_agent_container
    echo "Benchmark on $db done"
    sleep 5s
    echo "---------------------------------"
done