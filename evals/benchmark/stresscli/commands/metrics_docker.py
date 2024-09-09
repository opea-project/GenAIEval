# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import time

import requests

import docker

# Setup logs
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logging.basicConfig(level=getattr(logging, log_level))


class DockerMetricsCollector:
    def __init__(self):
        self.docker_client = docker.from_env()

    def get_docker_container(self, container_name):
        """Retrieve Docker container information."""
        try:
            container = self.docker_client.containers.get(container_name)
            logging.info(f"Found Docker container {container_name}")
            return container
        except docker.errors.NotFound:
            logging.error(f"Container {container_name} not found.")
            return None

    def get_exposed_port(self, container):
        """Get the port exposed to the external environment by the Docker container."""
        try:
            # Retrieve ports in JSON format
            ports_json = container.attrs["NetworkSettings"]["Ports"]
            logging.debug(f"Container ports: {ports_json}")

            # Parse the ports to find the host port
            for container_port, host_infos in ports_json.items():
                for host_info in host_infos:
                    host_ip = host_info["HostIp"]
                    host_port = host_info["HostPort"]

                    # Use localhost if the port is mapped to 0.0.0.0 or empty
                    if host_ip in ["0.0.0.0", ""]:
                        logging.debug(
                            f"Found host port {host_port} for container port {container_port} (mapped to all interfaces)"
                        )
                        return ("localhost", host_port)
                    else:
                        logging.debug(
                            f"Found host port {host_port} for container port {container_port} (mapped to {host_ip})"
                        )
                        return (host_ip, host_port)

            logging.error("No valid host port found.")
            return (None, None)
        except KeyError as e:
            logging.error(f"Error retrieving ports: {e}")
            return (None, None)

    def collect_metrics(self, container_name, metrics_path="/metrics"):
        """Collect metrics from the Docker container."""
        container = self.get_docker_container(container_name)
        if container:
            try:
                host_ip, port = self.get_exposed_port(container)  # Get the exposed port
                if not port:
                    logging.error(f"Cannot determine port for container {container_name}")
                    return None

                # Construct the URL
                service_url = f"http://{host_ip}:{port}{metrics_path}"
                logging.debug(f"Collecting metrics from {service_url}")
                response = requests.get(service_url)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logging.error(f"Error collecting metrics from {container_name}: {e}")
        return None

    def start_collecting_data(self, services, output_dir="/data"):
        """Start collecting metrics from services."""
        timestamp = int(time.time())
        for container_name in services:
            metrics = self.collect_metrics(container_name)
            if metrics:
                output_path = os.path.join(output_dir, f"{container_name}@{timestamp}.txt")
                logging.debug(f"Writing Docker metrics to {output_path}")
                with open(output_path, "w") as f:
                    f.write(metrics)
            else:
                logging.error(f"No metrics collected for container {container_name}")
        return {"status": "success"}


if __name__ == "__main__":
    docker_collector = DockerMetricsCollector()
    result = docker_collector.start_collecting_data(
        services=[
            "llm-tgi-server",
            "retriever-redis-server",
            "embedding-tei-server",
            "tei-embedding-server",
            "tgi-service",
            "tei-reranking-server",
        ],
        output_dir="/path/to/data",
    )
    print(result)
