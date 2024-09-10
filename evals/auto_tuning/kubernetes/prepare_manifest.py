# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import subprocess
import time
from pathlib import Path

import yaml

log_level = os.getenv("LOGLEVEL", "INFO")
logging.basicConfig(level=log_level.upper(), format="%(asctime)s - %(levelname)s - %(message)s")


def update_model_id(service_name, chatqna_config_map, service_info):
    if "embed" in service_name:
        key = "EMBEDDING_MODEL_ID"
    elif "rerank" in service_name:
        key = "RERANK_MODEL_ID"
    elif "llm" in service_name:
        key = "LLM_MODEL_ID"
    elif "guard" in service_name:
        key = "GUARDRAIL_LLM_MODEL_ID"
    else:
        raise Exception(f"Service {service_name} does not support model_id now.")
    # service_info may not include the model_id.
    if "model_id" in service_info:
        chatqna_config_map["data"][key] = service_info["model_id"]


def update_hpu_env(manifest_content, service_info, service_name, chatqna_config_map):

    env_list = [
        {"name": "OMPI_MCA_btl_vader_single_copy_mechanism", "value": "none"},
        {"name": "PT_HPU_ENABLE_LAZY_COLLECTIVES", "value": "true"},
        {"name": "runtime", "value": "habana"},
        {"name": "HABANA_VISIBLE_DEVICES", "value": "all"},
        {"name": "HF_TOKEN", "value": chatqna_config_map["data"]["HUGGINGFACEHUB_API_TOKEN"]},
    ]

    if service_name == "reranking-dependency":
        env_list.append({"name": "MAX_WARMUP_SEQUENCE_LENGTH", "value": "512"})

    manifest_content["spec"]["template"]["spec"]["containers"][0]["env"] = env_list

    if "mosec" in manifest_content["metadata"]["name"]:
        if service_info.get("cards") and service_info["cards"] > 1:
            manifest_content["spec"]["template"]["spec"]["containers"][0]["args"] = []
            manifest_content["spec"]["template"]["spec"]["containers"][0]["args"].extend(
                ["--sharded", "true", "--num-shard", str(service_info["cards"])]
            )
    else:
        if (
            service_info.get("cards")
            and "--sharded" not in manifest_content["spec"]["template"]["spec"]["containers"][0]["args"]
            and service_info["cards"] > 1
        ):
            manifest_content["spec"]["template"]["spec"]["containers"][0]["args"].extend(
                ["--sharded", "true", "--num-shard", str(service_info["cards"])]
            )


def update_deployment_resources(manifest_content, service_info):
    manifest_content["spec"]["replicas"] = service_info["replica"]
    manifest_content["spec"]["template"]["spec"]["containers"][0]["image"] = service_info["image"]

    resources = manifest_content["spec"]["template"]["spec"]["containers"][0].get("resources", {})
    limits = resources.get("limits", {})
    requests = resources.get("requests", {})

    if service_info.get("cores"):
        limits["cpu"] = service_info["cores"]
        requests["cpu"] = service_info["cores"]
    if service_info.get("memory"):
        limits["memory"] = service_info["memory"]
        requests["memory"] = service_info["memory"]
    if service_info.get("cards"):
        limits["habana.ai/gaudi"] = service_info["cards"]

    if limits != {}:
        resources["limits"] = limits
    if requests != {}:
        resources["requests"] = requests
    if resources != {}:
        manifest_content["spec"]["template"]["spec"]["containers"][0]["resources"] = resources


def update_k8s_yaml(json_file, manifest_directory="./manifest/general"):

    # read json file
    with open(json_file, "r") as file:
        services = json.load(file)

    # 01. Updating the chatqna_config_yaml
    config_filepath = Path(manifest_directory) / "chatqna_config_map.yaml"
    with open(config_filepath, "r") as file:
        chatqna_config_map = yaml.safe_load(file)

    for service_name, service_info in services.items():

        # update model_id in config_map.yaml
        if service_name in ["embedding-dependency", "reranking-dependency", "llm-dependency", "guardrails-dependency"]:
            update_model_id(service_name, chatqna_config_map, service_info)

    with open(config_filepath, "w") as file:
        yaml.dump(chatqna_config_map, file, default_flow_style=False, sort_keys=False)
        logging.info(f"YAML file for {config_filepath} has been updated successfully.")

    # 02. Updating the manifest
    for service_name, service_info in services.items():
        manifest_path = Path(manifest_directory) / f"{service_name}.yaml"
        print(manifest_path)

        if manifest_path.exists():
            with open(manifest_path, "r") as file:
                manifest_file = list(yaml.safe_load_all(file))
        else:
            logging.info(f"YAML file for {service_name} does not exist in the specified directory.")

        for manifest_content in manifest_file:
            if manifest_content and manifest_content.get("kind", "") == "Deployment":
                update_deployment_resources(manifest_content, service_info)

                # update habana env variables in manifest
                if service_info.get("type") == "hpu":
                    update_hpu_env(manifest_content, service_info, service_name, chatqna_config_map)

        with open(manifest_directory + "/" + service_name + "_run.yaml", "w") as file:
            yaml.dump_all(manifest_file, file, default_flow_style=False, sort_keys=False)
            logging.info(f"YAML file for {service_name} has been updated successfully.")
