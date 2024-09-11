# Auto-Tuning for ChatQnA: Optimizing Resource Allocation in Kubernetes

This document describes the Auto-Tuning framework, a tool designed to streamline deployment strategies for resource-intensive services, particularly in ChatQnA environments. It leverages Kubernetes for container orchestration and integrates experimental data with out prior knowledge to fine-tune deployments for optimal performance.

## Key Features
* Hardware Efficiency: Focuses on adjusting replica counts and maximizing the utilization of CPU and HPU (Habana Processing Unit) resources.

* Theoretical and Experimental Optimization: Integrates theoretical best practices with our prior knowledge to ensure optimal resource allocation for services.

# Usage

To generate the strategy.json configuration file for deployment, use the following command:


```bash
# Kubernetes Deployment
python3 tuning.py --tuning_config replica_tuning_config.json --hardware_info hardware_info_gaudi.json --service_info chatqna_neuralchat_rerank_latest.yaml

# Note: Add --config_only to output deployment configs only.
```

## Configuration Files
1. hardware_info_gaudi.json: Specifies the hardware details (CPU, HPU, etc.).

2. chatqna_neuralchat_rerank_latest.yaml: Contains service deployment information.

3. tuning_config.json: Customizes tuning parameters for replica counts and granularity.

### Hardrware_info.json 
This file lists only the hardware devices to be used in deployment.

```json
{
    "device_0": {
        "ip": ["10.239.1.5", "10.239.10.6"],
        "type": "hpu",
        "sockets": 2,
        "cores_per_socket": 64,
        "num_cards": 8
    }
}
```
Please refer to `hardware_info_gaudi.json` for more details.

### chatqna_neuralchat_rerank_latest.yaml
This file includes all services that will be deployed.
```yaml
opea_micro_services:
    data_prep:
        ... ...
    embedding:
        ... ...

    reranking:
        ... ...

    llm:
        opea/llm-tgi:
            tag: latest
            type: cpu
            dependency:
                ghcr.io/huggingface/tgi-gaudi:
                    tag: 2.0.4
                    type: hpu
                    requirements:
                        model_id: "Intel/neural-chat-7b-v3-3"

opea_mega_service:
    opea/chatqna:
        tag: latest
        type: cpu
```
Please refer to `chatqna_neuralchat_rerank_latest.yaml` for more details.

### Tuning Config Parameters

`embedding_replicas_granularity = 1`: This defines the step size for scaling the number of replicas for the embedding server.
* Value (1): Each scaling operation increases or decreases the number of replicas by 1 at a time.

`embedding_replicas_min = 1`: This sets the minimum number of replicas allowed for the embedding server.
* Value (1): The service will always have at least 1 replica running, ensuring that it is available for deployment.

`embedding_replicas_max = 4`: This defines the maximum number of replicas allowed for the embedding server.
* Value (4): The service can be scaled up to a maximum of 4 replicas, limiting resource consumption and avoiding over-provisioning.

`microservice_replicas_granularity = 1`: This specifies the scaling step size for other microservices (such as retrieval, dataprep, etc.).
* Value (1): Similar to the embedding_replicas_granularity, the number of replicas for these microservices will scale by 1 replica at a time.

`microservice_replicas_min = 1`: This parameter sets the minimum number of replicas for these microservices.
* Value (1): Ensures that each microservice always has at least 1 replica running.

`microservice_replicas_max = 4`: This defines the upper limit for scaling replicas for these microservices.
* Value (4): The maximum number of replicas allowed for the microservices is 4.


If you want to adjust the default tuning parameters, just create a replica_tuning_config.json file. For example:

```json
{
    "embedding_replicas_granularity": 1,
    "embedding_replicas_min": 1,
    "embedding_replicas_max": 4,

    "microservice_replicas_granularity": 1,
    "microservice_replicas_min": 1,
    "microservice_replicas_max": 4
}
```
Please refer to `replica_tuning_config.json` for more details.

## Output

The output of the auto-tuning process includes two key components: 
1. strategy_files: Contains optimized configurations for deploying services, such as replica counts and hardware resource allocations.

2. K8S manifests: Provides the Kubernetes deployment specifications, including pod definitions and resource limits, ready for deployment.

Example of a strategy file:
```json
{
    "embedding-dependency": {
        "type": "cpu",
        "image": "ghcr.io/huggingface/text-embeddings-inference:cpu-1.5",
        "model_id": "BAAI/bge-base-en-v1.5",
        "replica": 1
    },
    "llm-microservice": {
        "type": "cpu",
        "image": "opea/llm-tgi:latest",
        "replica": 4
    },

    ... ...
    "reranking-dependency": {
        "type": "hpu",
        "image": "opea/tei-gaudi:latest",
        "model_id": "BAAI/bge-reranker-base",
        "replica": 1,
        "cards": 1
    },
    "chatqna_mega_service": {
        "image": "opea/chatqna:latest",
        "type": "cpu",
        "replica": 4
    }
}
```

Both the K8S manifests and strategy files are generated in the current directory, providing everything needed for deployment.

Deployment methods: simply run `kubectl apply -f` on the newly generated *_run.yaml files and the chatqna_config_map.

# Auto-Tuning for ChatQnA: Optimizing Accuracy by Tuning Model Related Parameters

The ChatQnA pipeline contains many components, such as `data_prep/embedding/retrieval/reranking/llm`, and each component has some hyper-parameters that have an impact on accuracy. So, we can create a tuning script to search the best accuracy config.

Most of the hyper-parameters listed below:
- embedding models
- reranking models
- large language models (llms)
- data_prep hyper-parameters
    - chunk_size
    - chunk_overlap
- retrieval hyper-parameters
    - search_types
    - top_k
    - fetch_k
- llms hyper-parameters
    - top_k
    - top_p
    - temperature

## Prepare Dataset

We use the evaluation dataset from [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, use the below command to prepare the dataset.

```
git clone https://github.com/IAAR-Shanghai/CRUD_RAG
mkdir data/
cp CRUD_RAG/data/crud_split/split_merged.json data/
cp -r CRUD_RAG/data/80000_docs/ data/
python ../../evaluation/rag_eval/examples/process_crud_dataset.py
```

## Run the Tuning script

```
python3 acc_tuning.py --tuning_config acc_tuning_config.json --hardware_info hardware_info_gaudi.json --service_info chatqna_neuralchat_rerank_latest.yaml

```
