#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function generate_header {
    echo "### Model test summary" >>$GITHUB_STEP_SUMMARY
    echo "|device|model|tasks|datasets|acc|" >>$GITHUB_STEP_SUMMARY
    echo "| :----: | :----: | :----: | :----: | :----: |" >>$GITHUB_STEP_SUMMARY
}

function preprocessing {
    for file_path in log/*; do
        if [[ -d ${file_path} ]] && [[ -f ${file_path}/summary.log ]]; then
            cat ${file_path}/summary.log >>$GITHUB_STEP_SUMMARY
        fi
    done
}

function main {
    generate_header
    preprocessing
}

main
