# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import copy
import json
import logging
import os
import shutil
import subprocess
import time

import tuning_utils
from benchmark import send_concurrency_requests
from kubernetes.prepare_manifest import update_k8s_yaml

log_level = os.getenv("LOGLEVEL", "INFO")
logging.basicConfig(level=log_level.upper(), format="%(asctime)s - %(levelname)s - %(message)s")


def generate_base_config(megeservice_info, hardware_info, **kwargs):

    hpu_exist = tuning_utils.check_hpu_device(hardware_info)

    json_content = {}

    def process_microservice(service_name, microservice_info):
        microservice_name = list(microservice_info.keys())[0]
        microservice_details = microservice_info[microservice_name]
        image_name = f"{microservice_name}:{microservice_details['tag']}"
        type = microservice_details["type"]

        def add_dependency(service_key, json_key):
            if "dependency" not in microservice_details:
                return
            dependency = microservice_details["dependency"]

            for key, value in dependency.items():
                if hpu_exist and value["type"] == "hpu":
                    image_name = f"{key}:{value['tag']}"
                    json_content[json_key] = {"type": "hpu", "image": image_name}
                    if "requirements" in value:
                        json_content[json_key]["model_id"] = value["requirements"]["model_id"]
                    return

            for key, value in dependency.items():
                if value["type"] == "cpu":
                    image_name = f"{key}:{value['tag']}"
                    json_content[json_key] = {"type": "cpu", "image": image_name}
                    if "requirements" in value:
                        json_content[json_key]["model_id"] = value["requirements"]["model_id"]
                    break

        if service_name == "data_prep":
            json_content["dataprep-microservice"] = {"type": type, "image": image_name}
            add_dependency(service_name, "vector-db")
        else:
            json_key = f"{service_name}-microservice"
            json_content[json_key] = {"type": type, "image": image_name}

            add_dependency(service_name, f"{service_name}-dependency")

    for service_name, service_info in megeservice_info.get("opea_micro_services", {}).items():
        process_microservice(service_name, service_info)

    for service_name, service_info in megeservice_info.get("opea_mega_service", {}).items():
        image_name = f"{service_name}:{service_info['tag']}"
        json_content["chatqna_mega_service"] = {"image": image_name}
        if "type" in service_info:
            json_content["chatqna_mega_service"]["type"] = service_info["type"]

    return json_content


class ReplicaTuning:
    llm_microservice_name = {"llm-microservice"}
    llm_dependency_name = {"llm-dependency"}

    guardrails_microservice_name = {"guardrails-microservice"}
    guardrails_dependency_name = {"guardrails-dependency"}

    reranking_microservice_name = {"reranking-microservice"}
    reranking_dependency_name = {"reranking-dependency"}

    embedding_dependency_name = {"embedding-dependency"}
    embedding_microservice_name = {"embedding-microservice"}

    tei_microservice_name = {"embedding-microservice"}
    tei_dependency_name = {"embedding-dependency"}

    vector_db_name = {"vector-db"}
    dataprep_microservice_name = {"dataprep-microservice"}

    retrieval_microservice_name = {"retrieval-microservice"}
    chatqna_mega_service_name = {"chatqna_mega_service"}

    def _load_tuning_config(self, file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        replicas_config = {
            "embedding_replicas_granularity": 1,
            "embedding_replicas_min": 1,
            "embedding_replicas_max": 1,
            "reranking_replicas_granularity": 1,
            "reranking_replicas_min": 1,
            "reranking_replicas_max": 1,
            "num_microservice_replca_by_default": 1,
            "microservice_replicas_granularity": 1,
            "microservice_replicas_min": 1,
            "microservice_replicas_max": 1,
        }

        param_defaults = {}
        param_defaults.update(replicas_config)

        # Update the data dictionary with default values if the key is missing
        for param, default_value in param_defaults.items():
            data[param] = data.get(param, default_value)

        return data

    def __init__(self, config, hardware_info, tuning_config_path, platform="k8s"):
        self.config = config
        self.hardware_info = hardware_info
        self.platform = platform

        self.heterogeneous = self._is_heterogeneous(hardware_info)
        if self.heterogeneous:
            self.num_cards = self._get_hpu_num_cards(hardware_info)

        self.reranking_exists = self._check_reranking_exists(config)
        self.reranking_on_hpu = self._check_reranking_on_gaudi(config)
        logging.info(f"Deployed reranking on hpu: {self.reranking_on_hpu}")
        if self.reranking_exists:
            self.tei_dependency_name.add(list(self.reranking_dependency_name)[0])
            self.tei_microservice_name.add(list(self.reranking_microservice_name)[0])

        self.guardrails_exists = self._check_guardrails_exists(config)
        self._load_hardware_info()
        self.tuning_config_data = self._load_tuning_config(tuning_config_path)
        self._load_tuning_parameters(self.tuning_config_data)

        self.reserved_svc_cores = -1

        self.strategy_version = 1

        self.embedding_replicas_list = [
            i
            for i in range(
                self.embedding_replicas_min, self.embedding_replicas_max + 1, self.embedding_replicas_granularity
            )
        ]

        self.microservice_replicas_list = [
            i
            for i in range(
                self.microservice_replicas_min,
                self.microservice_replicas_max + 1,
                self.microservice_replicas_granularity,
            )
        ]

        logging.info(f"embedding_replicas_list: {self.embedding_replicas_list}")
        logging.info(f"microservice_replicas_list: {self.microservice_replicas_list}")

    def _load_hardware_info(self):
        self.reserved_cores_by_default = 4
        self.total_cores, self.physcial_cores, self.max_cores_per_socket, self.total_sockets = self._get_cores_info(
            self.hardware_info
        )

    def _load_tuning_parameters(self, tuning_config_data):

        param_names = list(tuning_config_data.keys())

        for param in param_names:
            setattr(self, param, tuning_config_data.get(param))

        # Log all parameters
        log_info = {param: getattr(self, param) for param in param_names}
        logging.info(f"Tuning Config Parameters: {log_info}")

    def _get_cores_info(self, hardware_info):
        total_cores = 0
        physcial_cores = 0
        max_cores_per_socket = 0
        total_sockets = 0
        for device_key, device_info in hardware_info.items():
            num_devices = len(device_info["ip"])
            cores = device_info["cores_per_socket"]
            sockets = device_info["sockets"]

            total_sockets += sockets * num_devices
            total_cores += cores * sockets * num_devices
            physcial_cores += cores * num_devices
            if cores > max_cores_per_socket:
                max_cores_per_socket = cores

        logging.info(
            f"The total cores: {total_cores}, physcial_cores: {physcial_cores}, max_cores_per_socket: {max_cores_per_socket}, total_sockets: {total_sockets}"
        )

        return total_cores, physcial_cores, max_cores_per_socket, total_sockets

    def _get_hpu_num_cards(self, hardware_info):
        num_cards = 0
        for device_key, device_info in hardware_info.items():
            if device_info["type"] == "hpu":
                num_devices = len(device_info["ip"])
                num_cards = device_info["num_cards"] * num_devices

        return num_cards

    def _check_reranking_exists(self, config):
        reranking_exists = False
        for service_name, service_config in config.items():
            if service_name in self.reranking_dependency_name:
                reranking_exists = True
                break

        return reranking_exists

    def _check_reranking_on_gaudi(self, config):
        on_gaudi = False
        for service_name, service_config in config.items():
            if service_name in self.reranking_dependency_name:
                if self.heterogeneous and service_config["type"] == "hpu":
                    on_gaudi = True
                    break

        return on_gaudi

    def _check_guardrails_exists(self, config):
        exist = False
        for service_name, _ in config.items():
            if service_name in self.guardrails_dependency_name:
                exist = True
        return exist

    def _is_heterogeneous(self, hardware_info):
        hpu_exist = False
        for _, device_info in hardware_info.items():
            if device_info["type"] == "hpu":
                hpu_exist = True
                break

        return hpu_exist

    def apply_strategy(self):
        if self.strategy_version == 1:
            results = []
            for num_replica in self.microservice_replicas_list:
                self._microservice_replicas_allocation_v1(self.config, num_replica)
                if self.platform == "k8s":
                    result = self.k8s_strategy(self.config)

                results.append(result)

            return results

    def _microservice_replicas_allocation_v1(self, config, num_replica=1):
        for service_name, service_config in config.items():
            if service_name in self.chatqna_mega_service_name:
                service_config["replica"] = num_replica

        for service_name, service_config in config.items():
            if service_name in self.vector_db_name or service_name in self.dataprep_microservice_name:
                service_config["replica"] = self.num_microservice_replca_by_default

            elif "microservice" in service_name:
                if service_name in self.retrieval_microservice_name:
                    service_config["replica"] = num_replica
                    continue
                else:
                    # the rest of microservice
                    service_config["replica"] = num_replica

    def _replicas_allocation_on_heterogeneous(self, config):
        output = []
        if self.num_cards == 0:
            logging.error("Please check the number of gaudi cards in the hardware.config.")

        num_cards = self.num_cards
        for service_name, service_config in config.items():
            if service_name in self.guardrails_dependency_name:
                service_config["replica"] = 1
                service_config["cards"] = 1
                num_cards -= 1

        for service_name, service_config in config.items():
            if self.reranking_on_hpu and service_name in self.reranking_dependency_name:
                service_config["replica"] = 1
                service_config["cards"] = 1
                num_cards -= 1

        for service_name, service_config in config.items():
            if service_name in self.llm_dependency_name:
                if service_config["type"] == "cpu":
                    # TODO
                    service_config["replica"] = 1
                    continue
                else:
                    service_config["replica"] = num_cards
                    service_config["cards"] = max(num_cards // service_config["replica"], 1)

        for num_rag_replica in self.embedding_replicas_list:
            for service_name, service_config in config.items():
                if service_name in self.embedding_dependency_name:
                    service_config["replica"] = num_rag_replica

                if service_name in self.reranking_dependency_name and not self.reranking_on_hpu:
                    service_config["replica"] = num_rag_replica

            if num_rag_replica <= 0:
                tuning_utils.print_strategy_config(config, "deprecated", self.platform)
                continue

            output.append(copy.deepcopy(config))

        return output

    def k8s_strategy(self, config):
        output_config = []
        if self.heterogeneous:
            if self.strategy_version == 1:
                tmp_config = self._replicas_allocation_on_heterogeneous(config)

            output_config.extend(tmp_config)

        return output_config


def generate_strategy_files(config, strategy_executor, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    strategy_files_dict = {}
    strategy_dict = {}

    all_strategies = strategy_executor.apply_strategy()

    if len(all_strategies[0]) == 0:
        logging.info(f"{len(strategy_files_dict.keys())} Strategy files have been created.\n")
        return strategy_files_dict, strategy_dict

    all_files_created = False
    index = 0
    for sub_config_list in all_strategies:
        for idx, config in enumerate(sub_config_list):
            output_file = os.path.join(output_folder, f"strategy_{index}.json")
            success = tuning_utils.write_json(config, output_file)
            if success:
                all_files_created = True
                strategy_files_dict[index] = output_file
                strategy_dict[index] = config
            else:
                all_files_created = False
            index += 1

    if all_files_created:
        logging.info(f"{len(strategy_files_dict.keys())} Strategy files have been created successfully.\n")

    return strategy_files_dict, strategy_dict


def update_and_apply_kubernetes_manifest(strategy_file, manifest_dir, timeout=200):
    update_k8s_yaml(strategy_file, manifest_dir)
    bash_script = "kubernetes/prepare_k8s_pods.sh"

    # Ensure script is executable
    subprocess.run(["chmod", "+x", bash_script], check=True)

    # Delete previous deployment
    subprocess.run(
        ["bash", bash_script, "delete", strategy_file, manifest_dir], check=True, text=True, capture_output=False
    )

    time.sleep(100)
    while 0:
        result = subprocess.run(["kubectl", "get", "pods"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "No resources found in default namespace." in result.stderr:
            print("No resources found in default namespace.")
            break
        else:
            print("Still have Pods in the default namespace. Deleting...")
            time.sleep(20)

    # Apply updated deployment
    result = subprocess.run(
        ["bash", bash_script, "apply", strategy_file, manifest_dir], check=True, text=True, capture_output=False
    )

    tuning_utils.print_strategy_config(strategy_file)
    # Sleep to allow deployment to stabilize
    time.sleep(timeout)


def find_best_strategy(perf_data):
    best_strategy = None
    best_p50 = float("inf")
    best_p99 = float("inf")

    for strategy, metrics in perf_data.items():
        if (metrics["p50"] < best_p50) or (metrics["p50"] == best_p50 and metrics["p99"] < best_p99):
            best_strategy = strategy
            best_p50 = metrics["p50"]
            best_p99 = metrics["p99"]

    return best_p50, best_p99, best_strategy


def config_only_print(output_folder, strategy_files_dict, mode="k8s", remove_dir=False):
    log_file = output_folder + "/all_results.txt"
    for _, strategy_file in strategy_files_dict.items():
        tuning_utils.print_strategy_config(strategy_file, platform=mode)
        tuning_utils.print_strategy_config(strategy_file, log_file=log_file)

    if remove_dir:
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

    return


def main():
    parser = argparse.ArgumentParser(description="Read and parse JSON/YAML files and output JSON file")
    parser.add_argument("--hardware_info", help="Path to input JSON file", default="./hardware_info_gaudi.json")
    parser.add_argument(
        "--service_info", help="Path to input YAML file", default="./chatqna_neuralchat_rerank_latest.yaml"
    )
    parser.add_argument(
        "--tuning_config", help="Path to input tuning config file", default="./replica_tuning_config.json"
    )
    parser.add_argument("--output_file", help="Path to output JSON file", default="./strategy.json")
    parser.add_argument("--config_only", help="Generate all strategies", action="store_true")

    parser.add_argument("--benchmark", help="Benchmark", action="store_true")
    parser.add_argument("--task", type=str, default="rag", help="Task to perform")
    parser.add_argument("--mode", help="Deployment mode", default="k8s")
    parser.add_argument(
        "--request_url", type=str, default="http://100.83.111.232:30888/v1/chatqna", help="ChatQnA Service URL"
    )
    parser.add_argument("--num_queries", type=int, default=640, help="Number of queries to be sent")

    parser.add_argument("--strategy_file", help="Given the strategy file")
    parser.add_argument("--manifest_dir", help="Manifest output directory.", default="./baseline")

    args = parser.parse_args()

    if args.mode not in ["k8s"]:
        raise ValueError(f"Unsupported platform: {args.mode}")

    if args.benchmark:
        request_url = tuning_utils.get_chatqna_url()
        logging.info(f"request_url: {request_url}")
        p50, p99 = send_concurrency_requests(task=args.task, request_url=request_url, num_queries=args.num_queries)
        return

    # loading info
    hardware_info = tuning_utils.load_hardware_info(args.hardware_info)
    service_info = tuning_utils.load_service_info(args.service_info)
    config = generate_base_config(service_info, hardware_info)

    # create output folder
    local_time = time.localtime(time.time())
    output_folder = "result_" + time.strftime("%Y_%m_%d_%H_%M_%S", local_time)
    result_file = os.path.join(output_folder, "all_results.txt")
    os.makedirs(output_folder, exist_ok=True)
    with open(result_file, "a") as file:
        file.write(
            f"Benchmark num_queries: {args.num_queries}, mode: {args.mode}, \n\nhardware_info: {hardware_info} \n\n"
        )

    strategy_executor = ReplicaTuning(copy.deepcopy(config), hardware_info, args.tuning_config)

    perf_data = dict()
    strategy_files_dict, _ = generate_strategy_files(config, strategy_executor, output_folder)

    if args.config_only:
        config_only_print(output_folder, strategy_files_dict, mode=args.mode, remove_dir=True)
        return

    # collect the perf info
    for _, strategy_file in strategy_files_dict.items():
        # start services with different deployment modes
        if args.mode == "k8s":
            update_and_apply_kubernetes_manifest(strategy_file, args.manifest_dir, timeout=200)

        logging.info(f"{strategy_file} benchmarking...")
        num_queries = args.num_queries
        request_url = tuning_utils.get_chatqna_url()

        # Warmup step
        logging.info("Performing warmup with 8 queries...")
        try:
            send_concurrency_requests(task="rag", request_url=request_url, num_queries=2)
            send_concurrency_requests(task="rag", request_url=request_url, num_queries=8)
        except Exception as e:
            with open(result_file, "a") as file:
                file.write(f"Recording the {strategy_file} tuning result: \n")
                file.write(f"Warmup Error: {e}\n")
            logging.info(f"Warmup Error: {e}")
            continue
        logging.info("Warmup completed.")

        try:
            p50_0, p99_0 = send_concurrency_requests(
                task="rag",
                request_url=request_url,
                num_queries=args.num_queries // 2,
            )
            p50, p99 = send_concurrency_requests(
                task="rag",
                request_url=request_url,
                num_queries=args.num_queries,
            )
            p50_2, p99_2 = send_concurrency_requests(
                task="rag",
                request_url=request_url,
                num_queries=args.num_queries * 2,
            )
        except Exception as e:
            with open(result_file, "a") as file:
                file.write(f"Recording the {strategy_file} tuning result: \n")
                file.write(f"Exception Error: {e}\n")
            continue

        logging.info(f"num_queries: {num_queries}, request_url: {request_url}, {strategy_file} benchmarking result: ")
        tuning_utils.print_strategy_config(strategy_file)
        perf_data[strategy_file] = {"p50": p50, "p99": p99}

        with open(result_file, "a") as file:
            file.write(f"Recording the {strategy_file} tuning result: \n")
            file.write(f"p50_0 = {p50_0}, p99_0 = {p99_0}\n")
            file.write(json.dumps(perf_data[strategy_file]) + "\n")
            file.write(f"p50_2 = {p50_2}, p99_2 = {p99_2}\n")
        tuning_utils.print_strategy_config(strategy_file, log_file=result_file)

    logging.info(f"Please check the {result_file} in the local directory.")

    # find the best strategy
    best_p50, best_p99, best_strategy = find_best_strategy(perf_data)
    if best_strategy is not None:
        best_strategy_data = {"best_strategy": best_strategy, "p50": best_p50, "p99": best_p99}
        logging.info(f"Best strategy: {best_strategy_data}")
        update_k8s_yaml(json_file=strategy_file, manifest_directory=args.manifest_dir)
        with open(result_file, "a") as file:
            file.write(f"The best strategy file: {best_strategy} \n")
            file.write(json.dumps(best_strategy_data["best_strategy"]) + "\n")
        print("Updated the best manifest Done.")
    else:
        logging.info("The best strategy is None.")

    logging.info("Tuning Done.")


if __name__ == "__main__":
    main()
