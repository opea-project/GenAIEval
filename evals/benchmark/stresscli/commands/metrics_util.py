# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import re
from collections import defaultdict

# Setup logs
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logging.basicConfig(level=getattr(logging, log_level))


def parse_metrics(file_path):
    logging.debug(f"Parsing metrics from {file_path}")
    metrics = {}
    with open(file_path, "r") as f:
        for line in f:
            # Ignore comments and empty lines
            if line.startswith("#") or not line.strip():
                continue
            # Split metric name and value
            try:
                metric, value = line.rsplit(" ", 1)
                value = value.strip()
                if "." in value:
                    metrics[metric.strip()] = float(value)
                else:
                    metrics[metric.strip()] = int(value)
            except ValueError:
                logging.warning(f"Skipping invalid line: {line.strip()}")
    logging.debug(f"Parsed metrics: {metrics}")
    return metrics


def write_metrics(file_path, metrics, service_name):
    logging.debug(f"Writing metrics to {file_path}")
    new_metrics = {}
    with open(file_path, "w") as f:
        for metric, value in metrics.items():
            f.write(f"{metric} {value}\n")
            if "count" in metric and "request_duration_count" not in metric:
                f.write("\n")
            # Handle TGI/TEI
            if "request_duration_sum" in metric:
                count_metric = metric.replace("request_duration_sum", "request_duration_count")
                logging.info(f"match {metric} and {count_metric}")
                if count_metric in metrics and metrics[count_metric] != 0:
                    average_latency = metrics[metric] / metrics[count_metric]
                    new_metric = f"{service_name}_average_latency_per_request"
                    new_metrics[new_metric] = average_latency
                    f.write(f"{new_metric} {average_latency}\n")
                    f.write("\n")
            # Handle OPEA microservices
            if "http_request_duration_seconds_sum" in metric:
                # Extract the part after '/v1/' and before comma as handler part
                match = re.search(r'\{handler="/v1/([^"]*?)"', metric)
                if match:
                    handler_part = match.group(1)  # Extract the part after '/v1/' and before comma

                    # Construct prefix
                    sum_metric_prefix = f'http_request_duration_seconds_sum{{handler="/v1/{handler_part}"'
                    count_metric_prefix = f'http_request_duration_seconds_count{{handler="/v1/{handler_part}"'

                    # Find the key begin with prefix and end with '}'
                    sum_metric_key = next(
                        (key for key in metrics if key.startswith(sum_metric_prefix) and key.endswith("}")), None
                    )
                    count_metric_key = next(
                        (key for key in metrics if key.startswith(count_metric_prefix) and key.endswith("}")), None
                    )

                    if sum_metric_key and count_metric_key:
                        metric_value = metrics.get(sum_metric_key, "Not Found")
                        count_metric_value = metrics.get(count_metric_key, "Not Found")
                        logging.info(
                            f"Match {sum_metric_key}: {metric_value} and {count_metric_key}: {count_metric_value}"
                        )

                        if count_metric_value != "Not Found" and count_metric_value != 0:
                            average_latency = metric_value / count_metric_value
                            new_metric = f"{service_name}_average_latency_per_request"
                            new_metrics[new_metric] = average_latency
                            f.write(f"{new_metric} {average_latency}\n")
                            f.write("\n")
                            logging.info(f"{new_metric} {average_latency}")
                        else:
                            logging.info(f"Count metric {count_metric_key} is either not found or zero.")
                    else:
                        logging.info("Could not find matching metrics for sum or count.")
                else:
                    logging.info("Handler part not found in metric.")
            else:
                logging.info("Metric does not contain 'http_request_duration_seconds_sum'.")

    return new_metrics


def calculate_diff(start_dir, end_dir, output_dir, services=None):
    logging.debug(f"Calculating diff between {start_dir} and {end_dir}")

    if services is None:
        logging.info("services is None, exiting.")
        return []

    start_files = os.listdir(start_dir)
    end_files = os.listdir(end_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    average_latency_metrics = []

    if isinstance(services, str):
        services = [services]

    for service_name in services:
        # Create a regex pattern to match files starting with the service_name followed by symbol @
        pattern = rf"^{re.escape(service_name)}@.*\.txt$"

        start_service_files = [f for f in start_files if re.match(pattern, f)]
        end_service_files = [f for f in end_files if re.match(pattern, f)]

        start_metrics = defaultdict(int)
        end_metrics = defaultdict(int)

        for file_name in start_service_files:
            file_path = os.path.join(start_dir, file_name)
            metrics = parse_metrics(file_path)
            for metric, value in metrics.items():
                start_metrics[metric] += value

        for file_name in end_service_files:
            file_path = os.path.join(end_dir, file_name)
            metrics = parse_metrics(file_path)
            for metric, value in metrics.items():
                end_metrics[metric] += value

        # Calculate the difference
        diff_metrics = {}
        for metric in end_metrics:
            if metric in start_metrics:
                if isinstance(end_metrics[metric], int) and isinstance(start_metrics[metric], int):
                    diff_value = end_metrics[metric] - start_metrics[metric]
                elif isinstance(end_metrics[metric], float) and isinstance(start_metrics[metric], float):
                    diff_value = end_metrics[metric] - start_metrics[metric]
                else:
                    logging.warning(f"Type mismatch for metric {metric}, skipping")
                    continue
                diff_metrics[metric] = diff_value

        logging.debug(f"Difference metrics for service {service_name}: {diff_metrics}")

        # Write the diff metrics to the output file
        output_path = os.path.join(output_dir, f"{service_name}.diff")
        new_metrics = write_metrics(output_path, diff_metrics, service_name)

        # Collect average latency metrics
        for metric, value in new_metrics.items():
            if "average_latency" in metric:
                average_latency_metrics.append((metric, value))

        logging.info(f"Diff calculated and saved to {output_path}")

    return average_latency_metrics


def export_metric(start_dir, end_dir, output_dir, json_output, services):
    average_latency_metrics = calculate_diff(start_dir, end_dir, output_dir, services)

    if not average_latency_metrics:
        logging.info("No average latency metrics to export, exiting.")
        return

    if os.path.exists(json_output):
        with open(json_output, "r") as json_file:
            try:
                existing_data = json.load(json_file)
            except json.JSONDecodeError:
                logging.warning(f"Existing JSON file {json_output} is empty or invalid, starting fresh")
                existing_data = {}
    else:
        existing_data = {}

    for metric, value in average_latency_metrics:
        existing_data[metric] = value
        print(f"{metric}: {value}")

    with open(json_output, "w") as json_file:
        json.dump(existing_data, json_file, indent=4)
        json_file.write("\n")

    logging.info(f"Average latency metrics written to {json_output}")


if __name__ == "__main__":
    start_dir = "/path/to/data/start"
    end_dir = "/path/to/data/end"
    output_dir = "/path/to/data"
    services = ["chatqna-tgi", "chatqna-tei", "chatqna-teirerank", "chatqna-xeon-backend"]
    json_output = "/path/to/data/metrics.log"

    export_metric(start_dir, end_dir, output_dir, json_output, services)
