# Auto-Tuning for ChatQnA: Optimizing Resource Allocation in Kubernetes

This document describes the Auto-Tuning Framework, a tool designed to streamline deployment strategies for resource-intensive services, particularly in ChatQnA environments. It leverages Kubernetes for container orchestration and integrates experimental data with prior knowledge to fine-tune deployments for optimal performance.

## Key Features
* Hardware Efficiency: Focuses on adjusting replica counts and effectively utilizing CPU and HPU (Habana Processing Unit) resources.
* Theoretical and Experimental Optimization: Combines theoretical best practices with real-world data to ensure services receive appropriate resource allocations.
* Targeted Services: Primarily optimizes deployments for Embedding Service, Reranking Service, and LLM Service (most resource-demanding).

# Usage

To generate the strategy.json configuration file for deployment, use the following command:


```python
# Kubernetes Deployment
python3 tuning.py --tuning_config replica_tuning_config.json --hardware_info hardware_info_gaudi.json --service_info chatqna_neuralchat_rerank_latest.yaml
```

## Configuration Files
1. hardware_info_gaudi.json: Provides the hardware details (CPU, HPU, etc.).
2. chatqna_neuralchat_rerank_latest.yaml: Contains service deployment information.
3. tuning_config.json: Customize tuning parameters for replica counts and granularity.

### Hardrware_info.json 
This file includes details of all hardware devices that will be used for deployment.

Please only list devices in the config that you want to use.

```json
{
    "device_0": {
        "ip": ["10.239.1.1", "10.239.10.2"],
        "type": "cpu",
        "sockets": 2,
        "cores_per_socket": 64
    },
    "device_1": {
        "ip": ["10.239.1.3"],
        "type": "cpu",
        "sockets": 2,
        "cores_per_socket": 56
    },
    "device_2": {
        "ip": ["10.239.1.5", "10.239.10.6"],
        "type": "hpu",
        "sockets": 2,
        "cores_per_socket": 64,
        "num_cards": 8
    }
}
```

### chatqna_neuralchat_rerank_latest.yaml
This file includes all services which will be deployed.
```yaml
opea_micro_services:
    data_prep:
        ... ...
    embedding:
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
                ghcr.io/huggingface/text-generation-inference:
                    tag: 1.4
                    type: cpu
                    requirements:
                        model_id: "Intel/neural-chat-7b-v3-3"

opea_mega_service:
    opea/chatqna:
        tag: latest
        type: cpu
```
Refer to chatqna_neuralchat_rerank_latest.yaml for more details on service configurations.

### Tuning Config Parameters

`embedding_replicas_granularity = 1`
* This defines the step size or increment for scaling the number of replicas for the embedding server.
* Value (1): Each scaling operation increases or decreases the number of replicas by 1 at a time.

`embedding_replicas_min = 1`
* This sets the minimum number of replicas allowed for the embedding server.
* Value (1): The service will always have at least 1 replica running, ensuring that it is available for deployment.

`embedding_replicas_max = 4`
* This defines the maximum number of replicas allowed for the embedding-service.
* Value (4): The service can be scaled up to a maximum of 4 replicas, limiting resource consumption and avoiding over-provisioning.

`microservice_replicas_granularity = 1`
* This specifies the scaling step size for other microservices like reranking, retrieval, and llm-service.
* Value (1): Similar to the embedding_replicas_granularity, the number of replicas for these microservices will scale by 1 replica at a time.

`microservice_replicas_min = 1`
* This parameter sets the minimum number of replicas for these microservices.
* Value (1): Ensures that each microservice always has at least 1 replica running for high availability.

`microservice_replicas_max = 4`
* This defines the upper limit for scaling replicas for these microservices.
* Value (4): The maximum number of replicas allowed for the microservices is capped at 4, ensuring efficient use of resources.


If you want to adjust the default tuning parameters, create a tuning_config.json file. For example:

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
The system will apply these parameters during the tuning process.

## Output:
The output of the auto-tuning process includes two key components: strategy_files and K8S manifests. 

The strategy_files contain optimized configurations for deploying services, such as the number of replicas and resource allocations, while the K8S manifests provide the necessary Kubernetes deployment specifications, including pod definitions and resource limits, ready for deployment in a Kubernetes environment.

For examples:
```
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

The K8S manifests are generated in the current directory, alongside the strategy_files, which contain the deployment configurations. 
