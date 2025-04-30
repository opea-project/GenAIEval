# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# stresscli/load_test.py

import logging
import math
import os
import subprocess
from datetime import datetime

import click
import yaml

from .report import export_testdata
from .utilization import MetricFetcher
from .utils import dump_k8s_config, generate_lua_script, generate_random_suffix

# Default load shape
DEFAULT_LOADSHAPE = "constant"

# Define default values
locust_defaults = {
    "locustfile": "locustfile.py",
    "host": "http://127.0.0.1:8888",
    "stop-timeout": 120,
    "run-time": "48h",
    "processes": 2,
    "bench-target": "chatqnafixed",
    "llm-model": "Intel/neural-chat-7b-v3-3",
    "deployment-type": "k8s",
    "users": 10,
    "max-request": 100,
    "namespace": "default",
    "load-shape": {"name": DEFAULT_LOADSHAPE},
    "dataset": "default",
    "max-output": 128,
    "prompts": "none",
    "seed": "none",
}

console_logger = logging.getLogger("opea.eval")


@click.command()
# @click.option('--dataset', type=click.Path(), help='Dataset path')
# @click.option('--endpoint', type=click.Path(), help='Endpoint of the test target service, like "http://192.168.0.12:8888/chatqna"')
@click.option("--profile", type=click.Path(), help="Path to profile YAML file")
@click.pass_context
# @click.option('--kubeconfig', type=click.Path(), help='Configuration file to Kubernetes')
def load_test(ctx, profile):
    """Do load test."""
    kubeconfig = ctx.parent.params["kubeconfig"]
    locust_runtests(kubeconfig, profile)


def locust_runtests(kubeconfig, profile):
    if profile:
        with open(profile, "r") as file:
            profile_data = yaml.safe_load(file)

        global_settings = profile_data["profile"]["global-settings"]
        runs = profile_data["profile"]["runs"]

        # create test log folder
        hostpath = profile_data["profile"]["storage"]["hostpath"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        testtarget = global_settings.get("bench-target", locust_defaults["bench-target"])
        base_folder = os.path.join(hostpath, f"{testtarget}_{timestamp}")
        os.makedirs(base_folder, exist_ok=True)

        # Extract storage path and run details from profile
        index = 1
        for run in runs:
            print(f"===Starting test: {run['name']}")
            run_locust_test(kubeconfig, global_settings, run, base_folder, index)
            print(f"===Completed test: {run['name']}")
            index = index + 1

        click.echo(f"Load test results saved to {base_folder}")

        return base_folder


def collect_metrics(collector, services, output_dir, namespace=None):
    """Collect metrics from the specified services and output directory.

    Args:
        collector: The metrics collector object.
        services (list): A list of services to collect metrics from.
        output_dir (str): The directory where metrics will be saved.
        namespace (str, optional): The namespace for collecting metrics. Defaults to None.
    """
    if namespace:
        # If namespace is provided, call with namespace
        collector.start_collecting_data(
            namespace=namespace,
            services=services,
            output_dir=output_dir,
            restart_pods_flag=False,
        )
    else:
        # If namespace is not provided, call without namespace
        collector.start_collecting_data(
            services=services,
            output_dir=output_dir,
        )


def run_locust_test(kubeconfig, global_settings, run_settings, output_folder, index):
    # Merge settings with priority: run_settings > global_settings > defaults
    runspec = {}
    runspec["tool"] = "locust"
    runspec["locustfile"] = run_settings.get(
        "locustfile", global_settings.get("locustfile", locust_defaults["locustfile"])
    )
    runspec["host"] = run_settings.get("host", global_settings.get("host", locust_defaults["host"]))
    runspec["runtime"] = run_settings.get("run-time", global_settings.get("run-time", locust_defaults["run-time"]))
    runspec["users"] = run_settings.get("users", global_settings.get("users", locust_defaults["users"]))
    runspec["max_requests"] = run_settings.get(
        "max-request", global_settings.get("max-request", locust_defaults["max-request"])
    )
    runspec["stop_timeout"] = run_settings.get(
        "stop-timeout", global_settings.get("stop-timeout", locust_defaults["stop-timeout"])
    )
    runspec["stop_timeout"] = (
        locust_defaults["stop-timeout"] if runspec["stop_timeout"] is None else runspec["stop_timeout"]
    )
    runspec["processes"] = run_settings.get("processes", global_settings.get("processes", locust_defaults["processes"]))
    runspec["bench-target"] = run_settings.get(
        "bench-target", global_settings.get("bench-target", locust_defaults["bench-target"])
    )
    runspec["llm-model"] = run_settings.get("llm-model", global_settings.get("llm-model", locust_defaults["llm-model"]))
    runspec["deployment-type"] = run_settings.get(
        "deployment-type", global_settings.get("deployment-type", locust_defaults["deployment-type"])
    )
    runspec["namespace"] = run_settings.get("namespace", global_settings.get("namespace", locust_defaults["namespace"]))
    runspec["dataset"] = run_settings.get("dataset", global_settings.get("dataset", locust_defaults["dataset"]))
    runspec["dataset"] = locust_defaults["dataset"] if runspec["dataset"] is None else runspec["dataset"]
    runspec["prompts"] = run_settings.get("prompts", global_settings.get("prompts", locust_defaults["prompts"]))
    runspec["prompts"] = locust_defaults["prompts"] if runspec["prompts"] is None else runspec["prompts"]
    runspec["max_output"] = run_settings.get(
        "max-output", global_settings.get("max-output", locust_defaults["max-output"])
    )
    runspec["max_output"] = locust_defaults["max-output"] if runspec["max_output"] is None else runspec["max_output"]
    runspec["seed"] = run_settings.get("seed", global_settings.get("seed", locust_defaults["seed"]))
    runspec["seed"] = locust_defaults["seed"] if runspec["seed"] is None else runspec["seed"]
    runspec["run_name"] = run_settings["name"]
    runspec["summary_type"] = global_settings.get("summary_type", None)
    runspec["stream"] = global_settings.get("stream", None)
    runspec["max-new-tokens"] = global_settings.get("max-new-tokens", locust_defaults["max-output"])
    runspec["retrieval_k"] = global_settings.get("retrieval_k", None)
    runspec["rerank_top_n"] = global_settings.get("rerank_top_n", None)
    runspec["chat_template"] = global_settings.get("chat_template", None)
    # Specify load shape to adjust user distribution
    load_shape_conf = run_settings.get("load-shape", global_settings.get("load-shape", locust_defaults["load-shape"]))
    try:
        load_shape = load_shape_conf["name"]
        runspec["load-shape"] = load_shape_conf
    except KeyError:
        load_shape = DEFAULT_LOADSHAPE

    load_shape_params = None
    try:
        load_shape_params = load_shape_conf["params"][load_shape]
    except KeyError:
        console_logger.info(f"The specified load shape not found: {load_shape}")

    if load_shape == DEFAULT_LOADSHAPE and (load_shape_params is None or "arrival_rate" not in load_shape_params):
        # constant load is Locust's default load shape, do nothing.
        console_logger.info("Use default load shape.")
    else:
        # load a custom load shape
        f_custom_load_shape = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"locust/{load_shape}_load_shape.py"
        )
        if os.path.isfile(f_custom_load_shape):
            # Add the locust file of the custom load shape into classpath
            runspec["locustfile"] += f",{f_custom_load_shape}"
            if load_shape == DEFAULT_LOADSHAPE:
                console_logger.info("Use default load shape based on request arrival rate")
            else:
                console_logger.info("Use custom load shape: {load_shape}")
        else:
            console_logger.error(
                f"Unsupported load shape: {load_shape}."
                f"The Locust file of custom load shape not found: {f_custom_load_shape}. Aborted."
            )
            exit()

    csv_output = os.path.join(output_folder, f"{index}")
    json_output = os.path.join(output_folder, f"{index}_output.log")

    service_metric = global_settings.get("service-metric-collect", False)
    if service_metric:
        metrics_output_folder = os.path.join(output_folder, f"{index}_metrics")
        os.makedirs(metrics_output_folder, exist_ok=True)
        start_output_folder = os.path.join(metrics_output_folder, "start")
        os.makedirs(start_output_folder, exist_ok=True)
        end_output_folder = os.path.join(metrics_output_folder, "end")
        os.makedirs(end_output_folder, exist_ok=True)
        metrics_output = os.path.join(output_folder, f"{index}_metrics.json")

    spawn_rate = 100 if runspec["users"] > 100 else runspec["users"]

    # Dynamically allocate Locust processes to fit different loads
    processes = 2
    if load_shape == "constant" and (load_shape_params is None or "arrival_rate" not in load_shape_params):
        if runspec["max_requests"] > 0:
            processes = 10 if runspec["max_requests"] > 2000 else 5 if runspec["max_requests"] > 1000 else processes
        else:
            concurrent_level = 2
            if load_shape_params and "concurrent_level" in load_shape_params:
                concurrent_level = int(load_shape_params["concurrent_level"])
            processes = 10 if concurrent_level > 400 else 5 if concurrent_level > 200 else processes
    elif load_shape == "poisson":
        if load_shape_params and "arrival_rate" in load_shape_params:
            processes = max(2, math.ceil(int(load_shape_params["arrival_rate"]) / 5))
    else:
        if load_shape_params and "arrival_rate" in load_shape_params:
            processes = max(2, math.ceil(int(load_shape_params["arrival_rate"]) / 5))
        elif runspec["max_requests"] > 0:
            processes = 10 if runspec["max_requests"] > 2000 else 5 if runspec["max_requests"] > 1000 else processes

    cmd = [
        "locust",
        "--locustfile",
        runspec["locustfile"],
        "--host",
        runspec["host"],
        "--run-time",
        runspec["runtime"],
        "--load-shape",
        load_shape,
        "--dataset",
        runspec["dataset"],
        "--prompts",
        runspec["prompts"],
        "--max-output",
        str(runspec["max_output"]),
        "--seed",
        str(runspec["seed"]),
        "--processes",
        str(runspec["processes"]),
        "--users",
        str(runspec["users"]),
        "--spawn-rate",
        str(spawn_rate),
        "--max-request",
        str(runspec["max_requests"]),
        "--bench-target",
        str(runspec["bench-target"]),
        "--llm-model",
        str(runspec["llm-model"]),
        "--stop-timeout",
        str(runspec["stop_timeout"]),
        "--summary_type",
        str(runspec["summary_type"]),
        "--stream",
        str(runspec["stream"]),
        "--max-new-tokens",
        str(runspec["max-new-tokens"]),
        "--csv",
        csv_output,
        "--headless",
        "--only-summary",
        "--loglevel",
        "WARNING",
        "--json",
    ]

    if runspec["retrieval_k"] is not None:
        cmd.append("--retrieval-k")
        cmd.append(str(runspec["retrieval_k"]))
    if runspec["rerank_top_n"] is not None:
        cmd.append("--rerank-top-n")
        cmd.append(str(runspec["rerank_top_n"]))
    if runspec["chat_template"] is not None:
        cmd.append("--chat-template")
        cmd.append(str(runspec["chat_template"]))

    # Get loadshape specific parameters
    if load_shape_params and "concurrent_level" in load_shape_params:
        del load_shape_params["concurrent_level"]

    # Add loadshape-specific parameters to locust parameters
    if load_shape_params is not None:
        for key, value in load_shape_params.items():
            cmd.append(f"--{key}")
            cmd.append(str(value))

    print(f"Running test: {' '.join(cmd)}")
    namespace = runspec["namespace"]

    if service_metric:
        services = global_settings.get("service-list") or []
        if runspec["deployment-type"] == "k8s":
            from .metrics import MetricsCollector

            collector = MetricsCollector()
            collect_metrics(collector, services, start_output_folder, namespace)
        elif runspec["deployment-type"] == "docker":
            from .metrics_docker import DockerMetricsCollector

            collector = DockerMetricsCollector()
            collect_metrics(collector, services, start_output_folder)

    utilization_metric = global_settings.get("utilization-metric-collect", False)
    if utilization_metric:
        services = global_settings.get("service-list") or []
        metrics_endpoints = global_settings.get("utilization-metric-endpoint") or []
        metrics_port = global_settings.get("utilization-metric-port", 9100)
        metric_names = global_settings.get("utilization-metric-names") or []
        fetcher = MetricFetcher(metrics_endpoints, metrics_port)
        print("before start_collect_utilization:")
        start_collect_utilization(fetcher, metric_names, namespace)

    runspec["starttest_time"] = datetime.now().isoformat()
    result = subprocess.run(cmd, capture_output=True, text=True)
    runspec["endtest_time"] = datetime.now().isoformat()

    if utilization_metric:
        util_output_folder = os.path.join(output_folder, f"{index}_utilization")
        print(f"before stop_collect_utilization: {util_output_folder}")
        os.makedirs(util_output_folder, exist_ok=True)
        stop_collect_utilization(fetcher, util_output_folder, metric_names)

    if service_metric:
        from .metrics_util import export_metric

        services = global_settings.get("service-list") or []
        if runspec["deployment-type"] == "k8s":
            collect_metrics(collector, services, end_output_folder, namespace)
        elif runspec["deployment-type"] == "docker":
            collect_metrics(collector, services, end_output_folder)
        export_metric(start_output_folder, end_output_folder, metrics_output_folder, metrics_output, services)

    with open(json_output, "w") as json_file:
        json_file.write(result.stderr)
        json_file.write(result.stdout)
    print(result.stderr)
    print(result.stdout)
    if runspec["deployment-type"] == "k8s":
        dump_test_spec(kubeconfig, runspec, runspec["namespace"], output_folder, index)


def start_collect_utilization(fetcher, metric_names, namespace):
    # Start the MetricFetcher
    fetcher.start(
        metric_names,
        namespace=namespace,
    )


def stop_collect_utilization(fetcher, output_folder, metric_names):
    # Stop the MetricFetcher
    fetcher.stop()
    # Save results to a file
    print("Calculated Average and Max per Container:")
    fetcher.save_results_to_file(output_folder)
    print(f"after save_results_to_folder {output_folder}")


def dump_test_spec(kubeconfig, run, namespace, output_folder, index):
    # Dump the k8s spec
    k8s_spec = dump_k8s_config(kubeconfig, return_as_dict=True, namespace=namespace)
    # Check if k8s_spec contains the expected keys
    hardware_spec = k8s_spec.get("hardwarespec", {})
    workload_spec = k8s_spec.get("workloadspec", {})

    data_output = export_testdata(f"{index}", output_folder, "output.log|stats.csv")
    # Combine both specs into a single YAML file
    combined_spec = {
        "benchmarkspec": run,
        "benchmarkresult": data_output,
        "hardwarespec": hardware_spec,
        "workloadspec": workload_spec,
    }
    combined_spec_path = os.path.join(output_folder, f"{index}_testspec.yaml")
    with open(combined_spec_path, "w") as combined_file:
        yaml.dump(combined_spec, combined_file)


def wrk_runtests(kubeconfig, dataset, endpoint, profile):
    if dataset:
        click.echo(f"Using dataset: {dataset}")

    # Here you would add the logic to perform the load test
    if profile:
        with open(profile, "r") as file:
            profile_data = yaml.safe_load(file)

        # create test log folder
        hostpath = profile_data["profile"]["storage"]["hostpath"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_folder = os.path.join(hostpath, f"{timestamp}")
        os.makedirs(base_folder, exist_ok=True)

        # Extract storage path and run details from profile
        runs = profile_data["profile"]["runs"]

        for run in runs:
            run_name = run["name"]
            namespace = run.get("namespace", "default")
            loop = run.get("loop", 1)
            tool = run.get("tool", "wrk")
            options = run["options"]
            endpoint = run["endpoint"]
            dataset = run.get("dataset", dataset)
            lua_template_path = run.get(
                "luatemplate", "/home/sdp/workspace/OPEAStress/stresscli/lua_template/chatqna.template"
            )

            # Create the folder for the run
            run_folder = os.path.join(base_folder, f"{run_name}")
            os.makedirs(run_folder, exist_ok=True)

            # Generate Lua script
            lua_script_path = os.path.join(run_folder, "wrk_script.lua")
            generate_lua_script(lua_template_path, lua_script_path, dataset)

            for i in range(loop):
                # Generate wrk command and execute it
                wrk_command = f"{tool} {options} --script {lua_script_path} {endpoint}"
                print(wrk_command)
                wrk_log_path = os.path.join(run_folder, f"wrk_{i + 1}.log")
                with open(wrk_log_path, "w") as wrk_log:
                    subprocess.run(wrk_command.split(), stdout=wrk_log, stderr=subprocess.STDOUT)

            dump_test_spec(kubeconfig, run, namespace, run_folder)
        click.echo(f"Load test results saved to {base_folder}")
    else:
        click.echo("Profile is required to run the test.")
