#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# PATH_PREFIX="./manifest"

function apply_yamls() {
    JSON_FILE="$1"
    PATH_PREFIX="$2"

    kubectl apply -f "$PATH_PREFIX/chatqna_config_map.yaml"
    echo "chatqna_config_map.yaml is applied."

    # Build and run k8s pods for each service
    sudo jq -c '. | to_entries[]' $JSON_FILE | while read -r service; do
        SERVICE_NAME=$(echo $service | jq -r '.key')
        echo "Applying manifest from ${SERVICE_NAME}_run.yaml"
        kubectl apply -f "$PATH_PREFIX/${SERVICE_NAME}_run.yaml"
    done

    echo "All services have been applied."
}


function delete_yamls() {
    JSON_FILE="$1"
    PATH_PREFIX="$2"

    # Build and run k8s pods for each service
    sudo jq -c '. | to_entries[]' $JSON_FILE | while read -r service; do
        SERVICE_NAME=$(echo $service | jq -r '.key')
        echo "Deleting manifest from ${SERVICE_NAME}_run.yaml"
        kubectl delete -f "$PATH_PREFIX/${SERVICE_NAME}_run.yaml"
    done

    echo "All services have been deleted."
}


function main() {

    # Check if a task is provided as an argument
    if [ "$#" -ne 3 ]; then
        echo "Please pass a task argument."
        exit 1
    fi

    local TASK="$1"
    local JSON_FILE="$2"
    local PATH_PREFIX="$3"


    case "$TASK" in
        *apply*)
            apply_yamls $JSON_FILE $PATH_PREFIX
            echo "[ apply ] Succeed"
        ;;
        *delete*)
            delete_yamls $JSON_FILE $PATH_PREFIX
            echo "[ delete ] Succeed"
        ;;
        *)
            echo "Task $TASK is not supported"
            exit 1
            ;;
    esac

}

main "$@"


