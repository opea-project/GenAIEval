# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import time

import requests
from kubernetes import client, config

# Setup logs
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logging.basicConfig(level=getattr(logging, log_level))

# Load Kubernetes config
config.load_kube_config()

# Create Kubernetes Client
v1 = client.CoreV1Api()


class MetricsCollector:
    def __init__(self):
        self.v1 = client.CoreV1Api()

    def get_service_selector(self, namespace, service_name):
        service = self.v1.read_namespaced_service(service_name, namespace)
        return service.spec.selector

    def get_pod_names_and_ips(self, namespace, labels):
        label_selector = ",".join([f"{key}={value}" for key, value in labels.items()])
        logging.debug(f"Listing pods in namespace: {namespace} with label: {label_selector}")
        pods = self.v1.list_namespaced_pod(namespace, label_selector=label_selector)
        pod_info = [(pod.metadata.name, pod.status.pod_ip) for pod in pods.items]
        logging.debug(f"Found pods: {pod_info}")
        return pod_info

    def restart_pods(self, namespace, labels):
        pod_names = [name for name, _ in self.get_pod_names_and_ips(namespace, labels)]
        for pod_name in pod_names:
            logging.info(f"Restarting pod {pod_name} in namespace {namespace}")
            self.v1.delete_namespaced_pod(pod_name, namespace)
            logging.info(f"Pod {pod_name} has been restarted.")

    def wait_for_pods(self, namespace, labels, timeout=300):
        label_selector = ",".join([f"{key}={value}" for key, value in labels.items()])
        end_time = time.time() + timeout
        while time.time() < end_time:
            pods = self.v1.list_namespaced_pod(namespace, label_selector=label_selector)
            if all(pod.status.phase == "Running" for pod in pods.items):
                logging.info("All pods are running.")
                return True
            time.sleep(5)
        logging.error("Timeout waiting for pods to be running.")
        return False

    def get_pod_port(self, pod):
        port = pod.spec.containers[0].ports[0].container_port
        logging.debug(f"Using port {port} for pod {pod.metadata.name}")
        return port

    def collect_metrics(self, pod_ip, pod_port, metrics_path):
        service_url = f"http://{pod_ip}:{pod_port}{metrics_path}"
        logging.debug(f"Collecting metrics from {service_url}")
        try:
            response = requests.get(service_url)
            response.raise_for_status()
            logging.debug(f"Metrics collected from {service_url}")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error collecting metrics from {service_url}: {e}")
            return None

    def start_collecting_data(self, namespace, services, output_dir="/data", restart_pods_flag=True):
        timestamp = int(time.time())
        metrics_path = "/metrics"

        for service_name in services:
            service_labels = self.get_service_selector(namespace, service_name)

            pod_infos = self.get_pod_names_and_ips(namespace, service_labels)

            for pod_name, pod_ip in pod_infos:
                pod_info = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
                pod_port = self.get_pod_port(pod_info)
                metrics = self.collect_metrics(pod_ip, pod_port, metrics_path)
                if metrics:
                    pod_output_path = os.path.join(output_dir, f"{service_name}@{pod_name}_{timestamp}.txt")
                    logging.debug(f"Writing metrics to {pod_output_path}")
                    with open(pod_output_path, "w") as f:
                        f.write(metrics)
                else:
                    logging.error(f"No metrics collected for pod {pod_name}")

            # Restart pods if the flag is set
            if restart_pods_flag:
                self.restart_pods(namespace, service_labels)
                logging.info(f"Pods for service {service_name} have been restarted.")

        # Wait for Service Pods Running after restart
        if restart_pods_flag:
            for service_name in services:
                service_labels = self.get_service_selector(namespace, service_name)
                if not self.wait_for_pods(namespace, service_labels):
                    logging.error(f"Pods for service {service_name} did not become ready in time.")
                    return {
                        "status": "error",
                        "message": f"Pods for service {service_name} did not become ready in time.",
                    }

        return {"status": "success"}


if __name__ == "__main__":
    collector = MetricsCollector()
    result = collector.start_collecting_data(
        namespace="chatqna",
        services=["chatqna-tgi", "chatqna-tei", "chatqna-teirerank"],
        output_dir="/path/to/data",
        restart_pods_flag=False,
    )
    print(result)
