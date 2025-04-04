# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import csv
import json
import logging
import os
import re
import time
from collections import defaultdict
from threading import Event, Thread

import requests
from kubernetes import client, config
from prometheus_client.parser import text_string_to_metric_families

# Configure CONSTANTS Value
METRIX_PREFIX = "rdt_container_"
# Configure logging
log_level = "ERROR"  # Default log level
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)


class MetricFetcher:
    def __init__(self, endpoints, port: int):
        self.endpoints = endpoints
        self.port = port
        self.responses = defaultdict(list)
        self.metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.container_pod = defaultdict(str)
        self.stop_event = Event()
        self.thread = None

    def get_real_metrics(self, metric_names: list[str]):
        # 遍历metric_names 将数组中每一个metric_names添加一个METRIX_PREFIX
        metric_names = [f"{METRIX_PREFIX}{metric_name}" for metric_name in metric_names]
        return metric_names

    def get_all_endpints(self):
        config.load_kube_config()
        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)
        self.endpoints = [
            {
                "node-name": pod.spec.node_name,
                "endpoint": f"http://{pod.status.pod_ip}:{self.port}/metrics",
            }
            for pod in pods.items
            if "memory-bandwidth-exporter" in pod.metadata.name
        ]

    def fetch_metrics(self, metric_names: list[str], namespace: str):
        """Fetches metrics from the specified URL, filters by metric name and namespace, and stores them in the class."""
        if not self.endpoints:
            self.get_all_endpints()
        start_time = time.time()  # Start timer for fetching metrics

        def fetch_endpoint(endpoint):
            response = requests.get(endpoint["endpoint"])
            response.raise_for_status()
            return endpoint["node-name"], response.text

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(fetch_endpoint, endpoint): endpoint for endpoint in self.endpoints}
            for future in concurrent.futures.as_completed(futures):
                endpoint = futures[future]
                try:
                    node_name, response_text = future.result()
                    self.responses[node_name].append(response_text)
                except Exception as e:
                    logger.error(f"Error fetching metrics from {endpoint['endpoint']}: {e}")
        fetch_duration = time.time() - start_time  # Calculate duration
        logger.debug(f"Time taken to fetch metrics: {fetch_duration:.2f} seconds")

    def parse_metrics(self, metric_names: list[str], namespace: str):
        """Parses metrics from the stored responses and stores them in the class."""
        start_time = time.time()
        for node_name, metrics_data_list in self.responses.items():
            for metrics_data in metrics_data_list:
                for family in text_string_to_metric_families(metrics_data):
                    for sample in family.samples:
                        metric_name = sample[0]
                        labels = sample[1]
                        value = sample[2]

                        # Check if the metric name and namespace match
                        if metric_name in metric_names and labels.get("nameSpace") == namespace:
                            container_id = labels.get("containerId")
                            pod_name = labels.get("podName")
                            if container_id not in self.metrics[node_name][metric_name]:
                                self.metrics[node_name][metric_name][container_id] = []
                            self.metrics[node_name][metric_name][container_id].append(value)
                            self.container_pod[container_id] = pod_name
        parse_duration = time.time() - start_time  # Calculate duration
        logger.debug(f"Time taken to parse metrics: {parse_duration:.2f} seconds")

    def save_raw_metrics(self, output_folder: str):
        """Saves the metrics to CSV files with node_name and metrics as granularity."""
        for node_name, metrics in self.metrics.items():
            for metric_name, containers in metrics.items():
                pmetric_name = metric_name
                if pmetric_name.startswith(METRIX_PREFIX):
                    pmetric_name = pmetric_name[len(METRIX_PREFIX) :]
                filename = os.path.join(output_folder, f"{node_name}_{pmetric_name}.csv")
                with open(filename, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    # Write header
                    header = ["container_id"] + [
                        f"collect_num_{i}" for i in range(len(next(iter(containers.values()))))
                    ]
                    writer.writerow(header)
                    # Write rows
                    for container_id, values in containers.items():
                        row = [container_id] + values
                        writer.writerow(row)
                    # Write sum row
                    sum_row = ["sum"] + [
                        sum(values[i] for values in containers.values())
                        for i in range(len(next(iter(containers.values()))))
                    ]
                    writer.writerow(sum_row)
                logger.info(f"Metrics saved to {filename}")

    def save_summary_table(self, output_folder: str):
        """Creates a summary table with container_id_podname as rows and metrics as columns."""
        for node_name, metrics in self.metrics.items():
            summary_table = defaultdict(dict)
            for metric_name, containers in metrics.items():
                pmetric_name = metric_name
                if pmetric_name.startswith(METRIX_PREFIX):
                    pmetric_name = pmetric_name[len(METRIX_PREFIX) :]
                filename = os.path.join(output_folder, f"{node_name}_{pmetric_name}.csv")
                max_sum_index = self.get_max_sum_column_from_csv(filename)
                with open(filename, mode="r") as file:
                    reader = csv.reader(file)
                    header = next(reader)  # Skip header
                    for row in reader:
                        if row[0] != "sum":
                            container_id = row[0]
                            pod_name = self.container_pod.get(container_id, "Unknown")
                            container_id_podname = f"{container_id}({pod_name})"
                            summary_table[container_id_podname][metric_name] = float(row[max_sum_index + 1])
            self.save_summary_table_to_csv(summary_table, output_folder, node_name)

    def get_max_sum_column_from_csv(self, filename: str) -> int:
        """Reads a CSV file and returns the index of the column with the maximum sum value."""
        with open(filename, mode="r") as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip header
            sum_row = None
            for row in reader:
                if row[0] == "sum":
                    sum_row = row[1:]
                    break
            if sum_row is None:
                raise ValueError(f"No sum row found in {filename}")
            max_sum_index = max(range(len(sum_row)), key=lambda i: float(sum_row[i]))
            return max_sum_index

    def save_summary_table_to_csv(self, summary_table: dict[str, dict[str, float]], output_folder: str, node_name: str):
        """Saves the summary table to a CSV file."""
        filename = os.path.join(output_folder, f"{node_name}_sum_metrics_table.csv")
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            # Write header
            metrics = list(next(iter(summary_table.values())).keys())
            pmetrics = [
                metric[len(METRIX_PREFIX) :] if metric.startswith(METRIX_PREFIX) else metric for metric in metrics
            ]
            header = ["containerid(podname)"] + pmetrics
            writer.writerow(header)
            # Write rows
            for container_id_podname, metrics_values in summary_table.items():
                row = [container_id_podname] + [metrics_values[metric] for metric in metrics]
                writer.writerow(row)

    def fetch_metrics_periodically(self, metric_names: list[str], namespace: str, interval: int):
        while not self.stop_event.is_set():
            self.fetch_metrics(metric_names, namespace)
            self.stop_event.wait(interval)
        for node, values in self.responses.items():
            length = len(values)
            print(f"node name: {node}, length of response: {length}")
        self.parse_metrics(metric_names, namespace)
        print(f"metrics: {self.metrics}")

    def start(self, metric_names: list[str], namespace: str, interval: int = 1):
        """Starts the periodic fetching of metrics."""
        real_metrics = self.get_real_metrics(metric_names)
        if self.thread is None or not self.thread.is_alive():
            self.thread = Thread(target=self.fetch_metrics_periodically, args=(real_metrics, namespace, interval))
            self.thread.start()
            logger.info("MetricFetcher started.")

    def stop(self):
        """Stops the periodic fetching of metrics."""
        if self.thread is not None and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()
            self.stop_event.clear()
            logger.info("MetricFetcher stopped.")

    def save_results_to_file(self, output_folder: str):
        """Saves the calculated statistics to files."""
        self.save_raw_metrics(output_folder)
        self.save_summary_table(output_folder)
        logger.info(f"Results saved to: {output_folder}")


# Example usage
if __name__ == "__main__":
    # Define the endpoint URL and result file path
    metrics_endpoint = "http://172.21.195.64:9100/metrics"  # Replace with your endpoint
    result_file_path = "result.txt"  # Replace with your desired result file path
    metric_names = ["cpu_utilization", "memory", "sum_local_memory_bandwidth", "sum_total_memory_bandwidth"]
    namespace = "benchmarking"
    fetcher = MetricFetcher(metrics_endpoint)
    # Start the MetricFetcher
    fetcher.start(metric_names, namespace=namespace)
    # Wait for some time
    time.sleep(15)
    # Stop the MetricFetcher
    fetcher.stop()
    # Save results to a file
    fetcher.save_results_to_file(result_file_path)
