# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import yaml
import logging
import subprocess

def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def load_yaml(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data


def write_json(data, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Failed to write {filename}: {e}")
        return False

def get_service_cluster_ip(service_name):
    try:
        # Run the kubectl command to get the services
        result = subprocess.run(['kubectl', 'get', 'svc'], capture_output=True, text=True, check=True)

        # Parse the output
        lines = result.stdout.splitlines()
        headers = lines[0].split()

        # Find the indices for the columns we are interested in
        name_idx = headers.index('NAME')
        cluster_ip_idx = headers.index('CLUSTER-IP')
        port_idx = headers.index('PORT(S)')

        for line in lines[1:]:
            columns = line.split()
            if columns[name_idx] == service_name:
                cluster_ip = columns[cluster_ip_idx]
                ports = columns[port_idx]

                main_part = ports.split('/')[0]
                port = main_part.split(':')[0]
                return cluster_ip, port

        raise ValueError(f"Service {service_name} not found.")

    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl command: {e}")
        return None
