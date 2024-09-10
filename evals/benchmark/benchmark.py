# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from datetime import datetime

import yaml
from stresscli.commands.load_test import locust_runtests
from utils import get_service_cluster_ip, load_yaml

service_endpoints = {
    "chatqna": {
        "embedding": "/v1/embeddings",
        "embedserve": "/v1/embeddings",
        "retriever": "/v1/retrieval",
        "reranking": "/v1/reranking",
        "rerankserve": "/rerank",
        "llm": "/v1/chat/completions",
        "llmserve": "/v1/chat/completions",
        "e2e": "/v1/chatqna",
    },
    "codegen": {"llm": "/generate_stream", "llmserve": "/v1/chat/completions", "e2e": "/v1/codegen"},
    "codetrans": {"llm": "/generate", "llmserve": "/v1/chat/completions", "e2e": "/v1/codetrans"},
    "faqgen": {"llm": "/v1/chat/completions", "llmserve": "/v1/chat/completions", "e2e": "/v1/faqgen"},
    "audioqna": {
        "asr": "/v1/audio/transcriptions",
        "llm": "/v1/chat/completions",
        "llmserve": "/v1/chat/completions",
        "tts": "/v1/audio/speech",
        "e2e": "/v1/audioqna",
    },
    "visualqna": {"lvm": "/v1/chat/completions", "lvmserve": "/v1/chat/completions", "e2e": "/v1/visualqna"},
}


def extract_test_case_data(content):
    """Extract relevant data from the YAML based on the specified test cases."""
    # Extract test suite configuration
    test_suite_config = content.get("test_suite_config", {})

    return {
        "examples": test_suite_config.get("examples", []),
        "concurrent_level": test_suite_config.get("concurrent_level"),
        "user_queries": test_suite_config.get("user_queries", []),
        "random_prompt": test_suite_config.get("random_prompt"),
        "test_output_dir": test_suite_config.get("test_output_dir"),
        "run_time": test_suite_config.get("run_time"),
        "collect_service_metric": test_suite_config.get("collect_service_metric"),
        "llm_model": test_suite_config.get("llm_model"),
        "deployment_type": test_suite_config.get("deployment_type"),
        "service_ip": test_suite_config.get("service_ip"),
        "service_port": test_suite_config.get("service_port"),
        "load_shape": test_suite_config.get("load_shape"),
        "all_case_data": {
            example: content["test_cases"].get(example, {}) for example in test_suite_config.get("examples", [])
        },
    }


def create_run_yaml_content(service, base_url, bench_target, concurrency, user_queries, test_suite_config):
    """Create content for the run.yaml file."""
    return {
        "profile": {
            "storage": {"hostpath": test_suite_config["test_output_dir"]},
            "global-settings": {
                "tool": "locust",
                "locustfile": os.path.join(os.getcwd(), "stresscli/locust/aistress.py"),
                "host": base_url,
                "stop-timeout": 120,
                "processes": 2,
                "namespace": "default",
                "bench-target": bench_target,
                "run-time": test_suite_config["run_time"],
                "service-metric-collect": test_suite_config["collect_service_metric"],
                "service-list": service.get("service_list", []),
                "llm-model": test_suite_config["llm_model"],
                "deployment-type": test_suite_config["deployment_type"],
                "load-shape": test_suite_config["load_shape"],
            },
            "runs": [{"name": "benchmark", "users": concurrency, "max-request": user_queries}],
        }
    }


def create_and_save_run_yaml(example, deployment_type, service_type, service, base_url, test_suite_config, index):
    """Create and save the run.yaml file for the service being tested."""
    os.makedirs(test_suite_config["test_output_dir"], exist_ok=True)

    service_name = service.get("service_name")
    run_yaml_paths = []
    for user_queries in test_suite_config["user_queries"]:
        concurrency = max(1, user_queries // test_suite_config["concurrent_level"])

        if service_type == "e2e":
            bench_target = f"{example}{'bench' if test_suite_config['random_prompt'] else 'fixed'}"
        else:
            bench_target = f"{service_type}{'bench' if test_suite_config['random_prompt'] else 'fixed'}"
        run_yaml_content = create_run_yaml_content(
            service, base_url, bench_target, concurrency, user_queries, test_suite_config
        )

        run_yaml_path = os.path.join(
            test_suite_config["test_output_dir"], f"run_{service_name}_{index}_users_{user_queries}.yaml"
        )
        with open(run_yaml_path, "w") as yaml_file:
            yaml.dump(run_yaml_content, yaml_file)

        run_yaml_paths.append(run_yaml_path)

    return run_yaml_paths


def get_service_ip(service_name, deployment_type="k8s", service_ip=None, service_port=None):
    """Get the service IP and port based on the deployment type.

    Args:
        service_name (str): The name of the service.
        deployment_type (str): The type of deployment ("k8s" or "docker").
        service_ip (str): The IP address of the service (required for Docker deployment).
        service_port (int): The port of the service (required for Docker deployment).

    Returns:
        (str, int): The service IP and port.
    """
    if deployment_type == "k8s":
        # Kubernetes IP and port retrieval logic
        svc_ip, port = get_service_cluster_ip(service_name)
    elif deployment_type == "docker":
        # For Docker deployment, service_ip and service_port must be specified
        if not service_ip or not service_port:
            raise ValueError(
                "For Docker deployment, service_ip and service_port must be provided in the configuration."
            )
        svc_ip = service_ip
        port = service_port
    else:
        raise ValueError("Unsupported deployment type. Use 'k8s' or 'docker'.")

    return svc_ip, port


def run_service_test(example, service_type, service, test_suite_config):

    # Get the service name
    service_name = service.get("service_name")

    # Get the deployment type from the test suite configuration
    deployment_type = test_suite_config.get("deployment_type", "k8s")

    # Get the service IP and port based on deployment type
    svc_ip, port = get_service_ip(
        service_name, deployment_type, test_suite_config.get("service_ip"), test_suite_config.get("service_port")
    )

    base_url = f"http://{svc_ip}:{port}"
    endpoint = service_endpoints[example][service_type]
    url = f"{base_url}{endpoint}"
    print(f"[OPEA BENCHMARK] 🚀 Running test for {service_name} at {url}")

    # Generate a unique index based on the current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the run.yaml for the service
    run_yaml_paths = create_and_save_run_yaml(
        example, deployment_type, service_type, service, base_url, test_suite_config, timestamp
    )

    # Run the test using locust_runtests function
    for index, run_yaml_path in enumerate(run_yaml_paths, start=1):
        print(f"[OPEA BENCHMARK] 🚀 The {index} time test is running, run yaml: {run_yaml_path}...")
        locust_runtests(None, run_yaml_path)

    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")


def process_service(example, service_type, case_data, test_suite_config):
    service = case_data.get(service_type)
    if service and service.get("run_test"):
        print(f"[OPEA BENCHMARK] 🚀 Example: {example} Service: {service.get('service_name')}, Running test...")
        run_service_test(example, service_type, service, test_suite_config)


if __name__ == "__main__":
    # Load test suit configuration
    yaml_content = load_yaml("./benchmark.yaml")
    # Extract data
    parsed_data = extract_test_case_data(yaml_content)
    test_suite_config = {
        "concurrent_level": parsed_data["concurrent_level"],
        "user_queries": parsed_data["user_queries"],
        "random_prompt": parsed_data["random_prompt"],
        "run_time": parsed_data["run_time"],
        "collect_service_metric": parsed_data["collect_service_metric"],
        "llm_model": parsed_data["llm_model"],
        "deployment_type": parsed_data["deployment_type"],
        "service_ip": parsed_data["service_ip"],
        "service_port": parsed_data["service_port"],
        "test_output_dir": parsed_data["test_output_dir"],
        "load_shape": parsed_data["load_shape"]
    }

    # Mapping of example names to service types
    example_service_map = {
        "chatqna": [
            "embedding",
            "embedserve",
            "retriever",
            "reranking",
            "rerankserve",
            "llm",
            "llmserve",
            "e2e",
        ],
        "codegen": ["llm", "llmserve", "e2e"],
        "codetrans": ["llm", "llmserve", "e2e"],
        "faqgen": ["llm", "llmserve", "e2e"],
        "audioqna": ["asr", "llm", "llmserve", "tts", "e2e"],
        "visualqna": ["lvm", "lvmserve", "e2e"],
    }

    # Process each example's services
    for example in parsed_data["examples"]:
        case_data = parsed_data["all_case_data"].get(example, {})
        service_types = example_service_map.get(example, [])
        for service_type in service_types:
            process_service(example, service_type, case_data, test_suite_config)
