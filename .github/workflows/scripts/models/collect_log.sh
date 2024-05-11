#!/bin/bash
set -eo pipefail
source /GenAIEval/.github/workflows/script/change_color.sh

# get parameters
PATTERN='[-a-zA-Z0-9_]*='
PERF_STABLE_CHECK=true
for i in "$@"; do
    case $i in
        --device=*)
            device=`echo $i | sed "s/${PATTERN}//"`;;
        --model=*)
            model=`echo $i | sed "s/${PATTERN}//"`;;
        --task=*)
            task=`echo $i | sed "s/${PATTERN}//"`;;
        *)
            echo "Parameter $i not recognized."; exit 1;;
    esac
done

output_file="/GenAIEval/${device}/${model}/${device}-${model}-${task}.log"
$BOLD_YELLOW && echo "-------- Collect logs --------" && $RESET

echo "working in"
pwd
if [[ ! -f ${output_file} ]]; then
    echo "${framework},${mode},${model},batch,cores per instance,Troughput,${precision}," >> ${WORKSPACE}/summary.log
else
    throughput=$(grep -A 2 "best," ${output_file} | tail -1 | awk -F "," '{print $1","$3","$4}')
    log_file=$(grep -A 2 "best," ${output_file} | tail -1 | awk -F "=" '{print $NF}' | awk '{print $1}' | sed 's|\"||g')
    logfile=${log_file##*/}
    logfile=${logs_prefix_url}${logfile}
    echo "${framework},${mode},${model},${throughput},${precision},${logfile}" >> ${WORKSPACE}/summary.log
fi