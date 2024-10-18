# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import subprocess

import yaml


def load_json(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data


def load_yaml(file_path):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    return data


def write_json(data, filename):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Failed to write {filename}: {e}")
        return False


from kubernetes import client, config


def get_service_cluster_ip(service_name, namespace="default"):
    # Load the Kubernetes configuration
    config.load_kube_config()  # or use config.load_incluster_config() if running inside a Kubernetes pod

    # Create an API client for the core API (which handles services)
    v1 = client.CoreV1Api()

    try:
        # Get the service object
        service = v1.read_namespaced_service(name=service_name, namespace=namespace)

        # Extract the Cluster IP
        cluster_ip = service.spec.cluster_ip

        # Extract the port number (assuming the first port, modify if necessary)
        if service.spec.ports:
            port_number = service.spec.ports[0].port  # Get the first port number
        else:
            port_number = None

        return cluster_ip, port_number
    except client.exceptions.ApiException as e:
        print(f"Error fetching service: {e}")
        return None
