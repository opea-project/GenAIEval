# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import subprocess
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
    "docsum": {
        "docsum": "/v1/docsum",
        "docsum-vllm": "/generate",
        "docsum-llm-uservice": "v1/chat/docsum",
        "e2e": "/v1/docsum",
    },
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

    # Ensure the namespace is a string before calling strip()
    raw_namespace = test_suite_config.get("namespace")
    namespace = (raw_namespace.strip() if isinstance(raw_namespace, str) else "") or "default"

    return {
        "examples": test_suite_config.get("examples", []),
        "warm_ups": test_suite_config.get("warm_ups", 0),
        "user_queries": test_suite_config.get("user_queries", []),
        "random_prompt": test_suite_config.get("random_prompt"),
        "test_output_dir": test_suite_config.get("test_output_dir"),
        "run_time": test_suite_config.get("run_time", None),
        "collect_service_metric": test_suite_config.get("collect_service_metric"),
        "llm_model": test_suite_config.get("llm_model"),
        "deployment_type": test_suite_config.get("deployment_type"),
        "service_ip": test_suite_config.get("service_ip"),
        "service_port": test_suite_config.get("service_port"),
        "load_shape": test_suite_config.get("load_shape"),
        "query_timeout": test_suite_config.get("query_timeout", 120),
        "seed": test_suite_config.get("seed", None),
        "namespace": namespace,
        "all_case_data": {
            example: content["test_cases"].get(example, {}) for example in test_suite_config.get("examples", [])
        },
    }


def create_run_yaml_content(service, base_url, bench_target, test_phase, num_queries, test_params):
    """Create content for the run.yaml file."""

    # If a load shape includes the parameter concurrent_level,
    # the parameter will be passed to Locust to launch fixed
    # number of simulated users.
    concurrency = 1
    runs_list = []
    index = 1
    try:
        load_shape = test_params["load_shape"]["name"]
        load_shape_params = test_params["load_shape"]["params"][load_shape]
        if load_shape_params and load_shape_params["concurrent_level"]:
            for query in num_queries:
                if query >= 0:
                    concurrency = max(1, query // load_shape_params["concurrent_level"])
                else:
                    concurrency = load_shape_params["concurrent_level"]
                runs_list.append({"name": f"{test_phase}_{index}", "users": concurrency, "max-request": query})
                index += 1
    except KeyError as e:
        # If the concurrent_level is not specified, load shapes should
        # manage concurrency and user spawn rate by themselves.
        pass

    yaml_content = {
        "profile": {
            "storage": {"hostpath": test_params["test_output_dir"]},
            "global-settings": {
                "tool": "locust",
                "locustfile": os.path.join(os.getcwd(), "stresscli/locust/aistress.py"),
                "host": base_url,
                "stop-timeout": test_params["query_timeout"],
                "processes": 2,
                "namespace": test_params["namespace"],
                "bench-target": bench_target,
                "service-metric-collect": test_params["collect_service_metric"],
                "service-list": service.get("service_list", []),
                "dataset": service.get("dataset", "default"),
                "prompts": service.get("prompts", None),
                "max-output": service.get("max_output", 128),
                "max-new-tokens": service.get("max_new_tokens", 128),
                "seed": test_params.get("seed", None),
                "stream": service.get("stream", True),
                "summary_type": service.get("summary_type", "stuff"),
                "llm-model": test_params["llm_model"],
                "deployment-type": test_params["deployment_type"],
                "load-shape": test_params["load_shape"],
                "retrieval_k": service.get("k"),
                "rerank_top_n": service.get("top_n"),
                "chat_template": service.get("chat_template"),
            },
            "runs": runs_list,
        }
    }

    # For the following scenarios, test will stop after the specified run-time
    # 1) run_time is not specified in benchmark.yaml
    # 2) Not a warm-up run
    # TODO: According to Locust's doc, run-time should default to run forever,
    # however the default is 48 hours.
    if test_params["run_time"] is not None and test_phase != "warmup":
        yaml_content["profile"]["global-settings"]["run-time"] = test_params["run_time"]

    return yaml_content


def generate_stresscli_run_yaml(
    example, case_type, case_params, test_params, test_phase, num_queries, base_url, ts
) -> str:
    """Create a stresscli configuration file and persist it on disk.

    Parameters
    ----------
        example : str
            The name of the example.
        case_type : str
            The type of the test case
        case_params : dict
            The parameters of single test case.
        test_phase : str [warmup|benchmark]
            Current phase of the test.
        num_queries : list
            The list of query numbers of test requests sent to SUT
        base_url : str
            The root endpoint of SUT
        test_params : dict
            The parameters of the test
        ts : str
            Timestamp

    Returns
    -------
        run_yaml_path : str
            The path of the generated YAML file.
    """
    # Get the workload
    if case_type == "e2e":
        bench_target = f"{example}{'bench' if test_params['random_prompt'] else 'fixed'}"
    else:
        bench_target = f"{case_type}{'bench' if test_params['random_prompt'] else 'fixed'}"

    # Generate the content of stresscli configuration file
    stresscli_yaml = create_run_yaml_content(case_params, base_url, bench_target, test_phase, num_queries, test_params)

    # Dump the stresscli configuration file
    service_name = case_params.get("service_name")
    run_yaml_path = os.path.join(test_params["test_output_dir"], f"run_{service_name}_{ts}_{test_phase}.yaml")
    with open(run_yaml_path, "w") as yaml_file:
        yaml.dump(stresscli_yaml, yaml_file)

    return run_yaml_path


def create_and_save_run_yaml(example, deployment_type, service_type, service, base_url, test_suite_config, index):
    """Create and save the run.yaml file for the service being tested."""
    os.makedirs(test_suite_config["test_output_dir"], exist_ok=True)

    run_yaml_paths = []

    # Add YAML configuration of stresscli for warm-ups
    warm_ups = test_suite_config["warm_ups"]
    if warm_ups is not None and warm_ups > 0:
        run_yaml_paths.append(
            generate_stresscli_run_yaml(
                example, service_type, service, test_suite_config, "warmup", [warm_ups], base_url, index
            )
        )

    # Add YAML configuration of stresscli for benchmark
    user_queries_lst = test_suite_config["user_queries"]
    if user_queries_lst is None or len(user_queries_lst) == 0:
        # Test stop is controlled by run time
        run_yaml_paths.append(
            generate_stresscli_run_yaml(
                example, service_type, service, test_suite_config, "benchmark", [-1], base_url, index
            )
        )
    else:
        # Test stop is controlled by request count
        run_yaml_paths.append(
            generate_stresscli_run_yaml(
                example, service_type, service, test_suite_config, "benchmark", user_queries_lst, base_url, index
            )
        )

    return run_yaml_paths


def get_service_ip(service_name, deployment_type="k8s", service_ip=None, service_port=None, namespace="default"):
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
        svc_ip, port = get_service_cluster_ip(service_name, namespace)
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
        service_name,
        deployment_type,
        test_suite_config.get("service_ip"),
        test_suite_config.get("service_port"),
        test_suite_config.get("namespace"),
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
    output_folders = []
    for index, run_yaml_path in enumerate(run_yaml_paths, start=1):
        print(f"[OPEA BENCHMARK] 🚀 The {index} time test is running, run yaml: {run_yaml_path}...")
        output_folders.append(locust_runtests(None, run_yaml_path))

    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")

    return output_folders


def process_service(example, service_type, case_data, test_suite_config):
    service = case_data.get(service_type)
    if service and service.get("run_test"):
        print(f"[OPEA BENCHMARK] 🚀 Example: {example} Service: {service.get('service_name')}, Running test...")
        return run_service_test(example, service_type, service, test_suite_config)


def check_test_suite_config(test_suite_config):
    """Check the configuration of test suite.

    Parameters
    ----------
        test_suite_config : dict
            The name of the example.

    Raises
    -------
        ValueError
            If incorrect configuration detects
    """

    # User must specify either run_time or user_queries.
    if test_suite_config["run_time"] is None and len(test_suite_config["user_queries"]) == 0:
        raise ValueError("Must specify either run_time or user_queries.")


def run_benchmark(report=False, yaml=yaml):
    # Load test suit configuration
    print(yaml)
    yaml_content = load_yaml(yaml)
    # Extract data
    parsed_data = extract_test_case_data(yaml_content)
    test_suite_config = {
        "user_queries": parsed_data["user_queries"],
        "random_prompt": parsed_data["random_prompt"],
        "run_time": parsed_data["run_time"],
        "collect_service_metric": parsed_data["collect_service_metric"],
        "llm_model": parsed_data["llm_model"],
        "deployment_type": parsed_data["deployment_type"],
        "service_ip": parsed_data["service_ip"],
        "service_port": parsed_data["service_port"],
        "test_output_dir": parsed_data["test_output_dir"],
        "load_shape": parsed_data["load_shape"],
        "query_timeout": parsed_data["query_timeout"],
        "warm_ups": parsed_data["warm_ups"],
        "seed": parsed_data["seed"],
        "namespace": parsed_data["namespace"],
    }
    check_test_suite_config(test_suite_config)

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
        "docsum": ["e2e"],
        "faqgen": ["llm", "llmserve", "e2e"],
        "audioqna": ["asr", "llm", "llmserve", "tts", "e2e"],
        "visualqna": ["lvm", "lvmserve", "e2e"],
    }

    all_output_folders = []
    # Process each example's services
    for example in parsed_data["examples"]:
        case_data = parsed_data["all_case_data"].get(example, {})
        service_types = example_service_map.get(example, [])
        for service_type in service_types:
            output_folder = process_service(example, service_type, case_data, test_suite_config)
            if output_folder is not None:
                all_output_folders.append(output_folder)

    if report:
        print(all_output_folders)
        all_results = dict()
        for each_bench_folders in all_output_folders:
            for folder in each_bench_folders:
                from stresscli.commands.report import get_report_results

                results = get_report_results(folder)
                all_results[folder] = results
                print(f"results = {results}\n")

        return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read and parse JSON/YAML files and output JSON file")
    parser.add_argument("--report", help="Return the perf", action="store_true")
    parser.add_argument("--yaml", help="Input benchmark yaml file", action="store", default="./benchmark.yaml")
    args = parser.parse_args()

    run_benchmark(report=args.report, yaml=args.yaml)
