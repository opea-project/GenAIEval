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
        "embedding_serving": "/v1/embeddings",
        "retriever": "/v1/retrieval",
        "reranking": "/v1/reranking",
        "reranking_serving": "/rerank",
        "llm": "/v1/chat/completions",
        "llm_serving": "/v1/chat/completions",
        "e2e": "/v1/chatqna",
    },
    "codegen": {"llm": "/v1/chat/completions", "llm_serving": "/v1/chat/completions", "e2e": "/v1/codegen"},
    "codetrans": {"llm": "/v1/chat/completions", "llm_serving": "/v1/chat/completions", "e2e": "/v1/codetrans"},
    "faqgen": {"llm": "/generate", "llm_serving": "/v1/faqgen", "e2e": "/v1/faqgen"},
    "audioqna": {
        "asr": "/v1/audio/transcriptions",
        "llm": "/v1/chat/completions",
        "llm_serving": "/v1/chat/completions",
        "tts": "/v1/audio/speech",
        "e2e": "/v1/audioqna",
    },
    "visualqna": {"lvm": "/v1/chat/completions", "lvm_serving": "/v1/chat/completions", "e2e": "/v1/visualqna"},
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
        "all_case_data": {
            example: content["test_cases"].get(example, {}) for example in test_suite_config.get("examples", [])
        },
    }


def create_run_yaml_content(service_name, base_url, bench_target, concurrency, user_queries, test_suite_config):
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
                "llm-model": test_suite_config["llm_model"],
            },
            "runs": [{"name": "benchmark", "users": concurrency, "max-request": user_queries}],
        }
    }


def create_and_save_run_yaml(example, service_type, service_name, base_url, test_suite_config, index):
    """Create and save the run.yaml file for the service being tested."""
    os.makedirs(test_suite_config["test_output_dir"], exist_ok=True)

    run_yaml_paths = []
    for user_queries in test_suite_config["user_queries"]:
        concurrency = max(1, user_queries // test_suite_config["concurrent_level"])

        bench_target = (
            f"{example}{'bench' if service_type == 'e2e' and test_suite_config['random_prompt'] else 'fixed'}"
        )
        run_yaml_content = create_run_yaml_content(
            service_name, base_url, bench_target, concurrency, user_queries, test_suite_config
        )

        run_yaml_path = os.path.join(
            test_suite_config["test_output_dir"], f"run_{service_name}_{index}_users_{user_queries}.yaml"
        )
        with open(run_yaml_path, "w") as yaml_file:
            yaml.dump(run_yaml_content, yaml_file)

        run_yaml_paths.append(run_yaml_path)

    return run_yaml_paths


def run_service_test(example, service_type, service_name, parameters, test_suite_config):
    svc_ip, port = get_service_cluster_ip(service_name)
    base_url = f"http://{svc_ip}:{port}"
    endpoint = service_endpoints[example][service_type]
    url = f"{base_url}{endpoint}"
    print(f"[OPEA BENCHMARK] 🚀 Running test for {service_name} at {url}")

    # Generate a unique index based on the current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the run.yaml for the service
    run_yaml_paths = create_and_save_run_yaml(
        example, service_type, service_name, base_url, test_suite_config, timestamp
    )

    # Run the test using locust_runtests function
    for index, run_yaml_path in enumerate(run_yaml_paths, start=1):
        print(f"[OPEA BENCHMARK] 🚀 The {index} time test is running, run yaml: {run_yaml_path}...")
        locust_runtests(None, run_yaml_path)

    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")


def process_service(example, service_name, case_data, test_suite_config):
    service = case_data.get(service_name)
    if service and service.get("run_test"):
        print(f"[OPEA BENCHMARK] 🚀 Example: {example} Service: {service.get('service_name')}, Running test...")
        run_service_test(
            example, service_name, service.get("service_name"), service.get("parameters", {}), test_suite_config
        )


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
        "test_output_dir": parsed_data["test_output_dir"],
    }

    # Mapping of example names to service types
    example_service_map = {
        "chatqna": [
            "embedding",
            "embedding_serving",
            "retriever",
            "reranking",
            "reranking_serving",
            "llm",
            "llm_serving",
            "e2e",
        ],
        "codegen": ["llm", "llm_serving", "e2e"],
        "codetrans": ["llm", "llm_serving", "e2e"],
        "faqgen": ["llm", "llm_serving", "e2e"],
        "audioqna": ["asr", "llm", "llm_serving", "tts", "e2e"],
        "visualqna": ["lvm", "lvm_serving", "e2e"],
    }

    # Process each example's services
    for example in parsed_data["examples"]:
        case_data = parsed_data["all_case_data"].get(example, {})
        service_types = example_service_map.get(example, [])
        for service_type in service_types:
            process_service(example, service_type, case_data, test_suite_config)
