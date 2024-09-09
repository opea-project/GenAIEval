import json
import yaml
import logging
import subprocess
import time
from benchmark import send_concurrency_requests


def load_hardware_info(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def load_service_info(file_path):
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


def print_strategy_config(config, tag=None, log_file=None, platform=None):
    llm_microservice_name = {'llm-microservice'}
    llm_dependency_name = {'llm-dependency'}

    guardrails_microservice_name = {'guardrails-microservice'}
    guardrails_dependency_name = {'guardrails-dependency'}

    reranking_microservice_name = {"reranking-microservice"}
    reranking_dependency_name = {"reranking-dependency"}

    embedding_dependency_name = {'embedding-dependency'}
    embedding_microservice_name = {'embedding-microservice'}

    tei_microservice_name = {'embedding-microservice'}
    tei_dependency_name = {'embedding-dependency'}

    vector_db_name = {'vector-db'}
    dataprep_microservice_name = {'dataprep-microservice'}

    retrieval_microservice_name = {'retrieval-microservice'}
    chatqna_mega_service_name = {'chatqna_mega_service'}

    if isinstance(config, str):  # Check if config is a file path
        with open(config, 'r') as f:
            config = json.load(f)

    def get_service_config(service_name_set, config):
        service_name = list(service_name_set)[0]
        service_config = config.get(service_name, {})
        cores = service_config.get('cores', 'N/A')
        replica = service_config.get('replica', 'N/A')
        memory = service_config.get('memory', 'N/A')
        return cores, replica, memory

    def get_hpu_service_config(service_name_set, config):
        service_name = list(service_name_set)[0]
        service_config = config.get(service_name, {})
        cores = service_config.get('cores', 'N/A')
        cards = service_config.get('cards', 'N/A')
        replica = service_config.get('replica', 'N/A')
        memory = service_config.get('memory', 'N/A')
        return cores, cards, replica, memory

    llm_cores, llm_cards, num_llm_replica, llm_memory = get_hpu_service_config(llm_dependency_name, config)
    llm_svc_cores, llm_svc_replica, llm_svc_memory = get_service_config(llm_microservice_name, config)

    embedding_cores, embedding_replica, embedding_memory = get_service_config(embedding_dependency_name, config)
    embedding_svc_cores, embedding_msvc_replica, embedding_svc_memory = get_service_config(
        embedding_microservice_name, config)

    reranking_cores, reranking_cards, reranking_replica, reranking_memory = get_hpu_service_config(
        reranking_dependency_name, config)
    reranking_svc_cores, reranking_svc_replica, reranking_svc_memory = get_service_config(
        reranking_microservice_name, config)

    guardrails_cores, guardrails_cards, guardrails_replica, guardrails_memory = get_hpu_service_config(
        guardrails_dependency_name, config)
    guardrails_svc_cores, guardrails_svc_replica, guardrails_svc_memory = get_service_config(
        guardrails_microservice_name, config)

    vector_db_cores, vector_db_replica, vector_db_memory = get_service_config(vector_db_name, config)

    dataprep_svc_cores, dataprep_svc_replica, dataprep_svc_memory = get_service_config(
        dataprep_microservice_name, config)
    retrieval_cores, retrieval_replica, retrieval_memory = get_service_config(retrieval_microservice_name, config)
    chatqna_cores, chatqna_replica, chatqna_memory = get_service_config(chatqna_mega_service_name, config)

    services = {
        "llm": {
            "cores": llm_cores,
            "cards": llm_cards,
            "replica": num_llm_replica,
            "memory": llm_memory
        },
        "llm_svc": {
            "cores": llm_svc_cores,
            "replica": llm_svc_replica,
            "memory": llm_svc_memory
        },
        "guardrails": {
            "cores": guardrails_cores,
            "cards": guardrails_cards,
            "replica": guardrails_replica,
            "memory": guardrails_memory
        },
        "guardrails-svc": {
            "cores": guardrails_svc_cores,
            "replica": guardrails_svc_replica,
            "memory": guardrails_svc_memory
        },
        "embedding": {
            "cores": embedding_cores,
            "replica": embedding_replica,
            "memory": embedding_memory
        },
        "embedding-svc": {
            "cores": embedding_svc_cores,
            "replica": embedding_msvc_replica,
            "memory": embedding_svc_memory
        },
        "reranking": {
            "cores": reranking_cores,
            "cards": reranking_cards,
            "replica": reranking_replica,
            "memory": reranking_memory
        },
        "reranking-svc": {
            "cores": reranking_svc_cores,
            "replica": reranking_svc_replica,
            "memory": reranking_svc_memory
        },
        "vector_db": {
            "cores": vector_db_cores,
            "replica": vector_db_replica,
            "memory": vector_db_memory
        },
        "dataprep_svc": {
            "cores": dataprep_svc_cores,
            "replica": dataprep_svc_replica,
            "memory": dataprep_svc_memory
        },
        "retrieval": {
            "cores": retrieval_cores,
            "replica": retrieval_replica,
            "memory": retrieval_memory
        },
        "chatqna": {
            "cores": chatqna_cores,
            "replica": chatqna_replica,
            "memory": chatqna_memory
        },
    }

    if log_file:
        with open(log_file, 'a') as f:
            if tag == "deprecated":
                f.write(f"Removed llm cores: {llm_cores:2}, llm cards: {llm_cards:2}, replica: {num_llm_replica}, "
                        f"embedding cores: {embedding_cores:2}, replica: {embedding_replica:2},"
                        f"reranking cores: {reranking_cores:2}, replica: {reranking_replica:2}\n")
            else:
                count = 0
                for service_name, service_info in services.items():
                    if "cards" in service_info:
                        f.write(
                            f"{service_name} cores: {service_info['cores']:2}, cards: {service_info['cards']:2}, replica: {service_info['replica']}, memory: {service_info['memory']} "
                        )
                    else:
                        f.write(
                            f"{service_name} cores: {service_info['cores']:2}, replica: {service_info['replica']}, memory: {service_info['memory']} "
                        )

                    count += 1
                    if count % 2 == 0:
                        f.write("\n")
                f.write("\n\n")
    else:
        if platform == "k8s":
            total_cores = 0
            for _, service_info in config.items():
                if 'cores' in service_info:
                    total_cores += service_info['cores'] * service_info['replica']
            logging.debug(f"total allocated cores: {total_cores:2}")
        if tag == "deprecated":
            logging.debug(
                f"Removed llm cores: {llm_cores:2}, llm cards: {llm_cards:2}, replica: {num_llm_replica}, "
                f"embedding cores: {embedding_cores:2}, replica: {embedding_replica:2}, "
                f"reranking cores: {reranking_cores:2}, replica: {reranking_replica:2}\n")
        else:
            count = 0
            log_message = []

            for service_name, service_info in services.items():
                if "cards" in service_info:
                    log_message.append(
                        f"{service_name:>15} replica: {service_info['replica']:<4} cards: {service_info['cards']:<5} "
                    )
                else:
                    log_message.append(f"{service_name:>15} replica: {service_info['replica']:<17} ")

                count += 1
                if count % 2 == 0:
                    logging.info(" | ".join(log_message))
                    log_message = []  # Reset log_message for the next batch of services

            if log_message:
                logging.info(", ".join(log_message))

            print("")


def check_hpu_device(hardware_info):
    hpu_exist = False
    for device_key, device_info in hardware_info.items():
        # Check for 'cpu' type with 'num_cards' present
        if device_info['type'] == 'cpu' and 'num_cards' in device_info:
            raise ValueError(
                f"Error in {device_key}: 'type' is 'cpu' and 'num_cards' is present in the configuration.")

        if device_info['type'] == 'hpu':
            hpu_exist = True
            break

    return hpu_exist


def get_svc_info(strategy_json_file, service_name):
    strategy = load_hardware_info(strategy_json_file)
    if isinstance(service_name, str):
        service_info = strategy.get(service_name, {})
    else:
        service_info = strategy.get(list(service_name)[0], {})
    result = {
        "replica": service_info.get("replica", None),
        "cards": service_info.get("cards", None),
        "cores": service_info.get("cores", None)
    }
    return result


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


def test_embedding_svc_perf(num_queries_list):
    results = None
    service_names = ["embedding-svc", "embedding-mosec-svc"]
    for service_name in service_names:
        try:
            results = test_service_performance(service_name=service_name,
                                               endpoint="/v1/embeddings",
                                               task="embedding",
                                               num_queries_list=num_queries_list)
            print(f"Successfully tested service: {service_name}")
            return results[0][0], results[0][1]
        except Exception as e:
            print(f"Failed to test service: {service_name} with error: {e}")

    if results is None:
        raise Exception("Both services failed to be tested.")

    return results[0][0], results[0][1]


def test_reranking_svc_perf(num_queries_list):

    results = test_service_performance(service_name="reranking-svc",
                                       endpoint="/v1/reranking",
                                       task="reranking",
                                       num_queries_list=num_queries_list)

    return results[0][0], results[0][1]


def test_llm_svc_perf(num_queries_list):

    results = test_service_performance(service_name="llm-svc",
                                       endpoint="/v1/chat/completions",
                                       task="llm",
                                       num_queries_list=num_queries_list)

    return results[0][0], results[0][1]


def get_chatqna_url():
    svc_ip, port = get_service_cluster_ip("chatqna-backend-server-svc")
    url = f'http://{svc_ip}:{port}/v1/chatqna'
    return url


def test_service_performance(service_name, endpoint, task, num_queries_list):
    svc_ip, port = get_service_cluster_ip(service_name)
    url = f'http://{svc_ip}:{port}{endpoint}'
    print(f'url = {url}, task = {task}, svc_ip = {svc_ip}, port = {port}')

    # Warmup step
    print(f'Performing warmup with 8 queries...')
    send_concurrency_requests(task=task, request_url=url, num_queries=8)
    print('Warmup completed.')

    results = []
    for num_queries in num_queries_list:
        p50, p99 = send_concurrency_requests(task=task, request_url=url, num_queries=num_queries)
        results.append((p50, p99))
        print(f'task = {task}, num_queries = {num_queries}, p50 = {p50}, p99 = {p99}')

    print(f'task = {task} Finished! Bye!')
    return results
