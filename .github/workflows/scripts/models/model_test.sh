#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -o pipefail
set -x
git config --global --add safe.directory /GenAIEval

export TQDM_POSITION=-1    # fix progress bar on tty mode
export TQDM_MININTERVAL=60 # set refresh every 60s

# get parameters
PATTERN='[-a-zA-Z0-9_]*='
PERF_STABLE_CHECK=true
for i in "$@"; do
    case $i in
        --datasets*)
            datasets=`echo $i | sed "s/${PATTERN}//"`;;
        --device=*)
            device=`echo $i | sed "s/${PATTERN}//"`;;
        --model=*)
            model=`echo $i | sed "s/${PATTERN}//"`;;
        --tasks=*)
            tasks=`echo $i | sed "s/${PATTERN}//"`;;
        *)
            echo "Parameter $i not recognized."; exit 1;;
    esac
done

working_dir=""
main() {
    case ${tasks} in
        "text-generation")
            working_dir="/GenAIEval/evals/evaluation/lm_evaluation_harness/examples";;
        "code-generation")
            working_dir="/GenAIEval/evals/evaluation/bigcode_evaluation_harness/examples";;
        *)
            echo "Not supported task"; exit 1;;
    esac
    if [[ ${model} == *"opt"* ]]; then
        pretrained="facebook/${model}"
    else
        pretrained="${model}"
    fi
    if [[ ${device} == "cpu" ]]; then
        model_sourze="hf"
    elif [[ ${device} == "hpu" ]]; then
        model_sourze="gaudi-hf"
    fi
    log_dir="/log/${device}/${model}"
    mkdir -p ${log_dir}
    run_benchmark
    cp ${log_dir}/${device}-${tasks}-${model}-${datasets}.log /GenAIEval/
}

function run_benchmark() {
    echo "::group::evaluation start"
    cd ${working_dir}
    overall_log="${log_dir}/${device}-${tasks}-${model}-${datasets}.log"
    python main.py \
        --model ${model_sourze} \
        --model_args pretrained=${pretrained} \
        --tasks ${datasets} \
        --device ${device} \
        --batch_size 112  2>&1 | tee ${overall_log}
    echo "::endgroup::"

    status=$?
    if [ ${status} != 0 ]; then
        echo "::error::Evaluation process returned non-zero exit code!"
        exit 1
    else
        echo "Evaluation process completed successfully!"
    fi
}

main
