# OPEA Benchmark Tool

This Tool provides a microservice benchmarking framework that uses YAML configurations to define test cases for different services. It executes these tests using `stresscli`, built on top of [locust](https://github.com/locustio/locust), a performance/load testing tool for HTTP and other protocols and logs the results for performance analysis and data visualization.

## Features

- **Services load testing**: Simulates high concurrency levels to test services like LLM, reranking, ASR, E2E and more.
- **YAML-based configuration**: Define test cases, service endpoints, and testing parameters in YAML.
- **Service metrics collection**: Optionally collect service metrics for detailed performance analysis.
- **Flexible testing**: Supports various test cases like chatqna, codegen, codetrans, faqgen, audioqna, and visualqna.
- **Data analysis and visualization**: After tests are executed, results can be analyzed and visualized to gain insights into the performance and behavior of each service. Performance trends, bottlenecks, and other key metrics are highlighted for decision-making.

## Table of Contents

- [Workload Deployment in Kubernetes](#workload-deployment-in-kubernetes)
  - [Prerequisites](#prerequisites)
  - [Deployment](#deployment)
    - [1. Deploy with CPUs only](#1-deploy-with-cpus-only)
    - [2. Deploy with Gaudi Devices](#2-deploy-with-gaudi-devices)
    - [3. Deploy with Multiple Pod Instances](#3-deploy-with-multiple-pod-instances)
    - [4. Deploy with a Specific Namespace](#4-deploy-with-a-specific-namespace)
    - [5. Deploy with Proxy](#5-deploy-with-proxy)
  - [Destroy](#destroy)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
  - [Test Suite Configuration](#test-suite-configuration)
  - [Test Cases](#test-cases)

## Workload Deployment in Kubernetes

### Prerequisites

- Kubernetes installation: Use [kubespray](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md) or other official Kubernetes installation guides.
- Helm installation: Follow the [Helm documentation](https://helm.sh/docs/intro/install/#helm) to install Helm.
- Install the OPEA Helm Chart:

  ```bash
  helm repo add opea https://opea-project.github.io/GenAIInfra
  ```
- Setup Hugging Face Token
  To access models and APIs from Hugging Face, set your token as environment variable.
  ```bash
  export HFTOKEN="insert-your-huggingface-token-here"
  ```

### Deployment

#### 1. Deploy with CPUs only

This setup ensures that all services in the opea/chatqna workload run with CPU resources only.

```bash
# Get the list of available charts:
helm search repo opea

# Deploy the opea/chatqna chart
helm install chatqna opea/chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN}
```
Verify deployment status:
- Deployed Kubernetes services:

  These are the actual services running in the cluster. Use the following command to list their runtime names:
  ```bash
  kubectl get svc
  ```
- Check the status of pods and ensure they are ready before proceeding:
  ```bash
  kubectl get pods
  ```

#### 2. Deploy with Gaudi Devices

To offload TEI embedding and TGI inference to Intel Gaudi devices, use the specific values file.

```bash
# Extract chart contents to access provided configuration files.
helm pull opea/chatqna --untar

# Deploy using the Gaudi-specific configuration.
helm install chatqna opea/chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f chatqna/gaudi-values.yaml 

```

#### 3. Deploy with Multiple Pod Instances

To effectively deploy your workload across multiple nodes, follow these steps.

##### Preload Shared Models
Downloading models simultaneously to multiple nodes in your cluster can overload resources such as network bandwidth, memory and storage. To prevent resource exhaustion, it's recommended to preload the models in advance.

```bash
pip install -U "huggingface_hub[cli]"
sudo mkdir -p /mnt/models
sudo chmod 777 /mnt/models
huggingface-cli download --cache-dir /mnt/models Intel/neural-chat-7b-v3-3
export MODELDIR=/mnt/models
```
Once the models are downloaded, you can consider the following methods for sharing them across nodes:
- Persistent Volume Claim (PVC): This is the recommended approach for production setups. For more details on using PVC, refer to [PVC](https://github.com/opea-project/GenAIInfra/blob/main/helm-charts/README.md#using-persistent-volume).
- Local Host Path: For simpler testing, ensure that each node involved in the deployment follows the steps above to locally prepare the models. After preparing the models, use `--set global.modelUseHostPath=${MODELDIR}` in the deployment command.

##### Get the Chart-Defined Service Names
These are the logical services defined in the Helm chart, such as `retriever-usvc`, `tei`, and `teirerank`, you can retrieve the full list with:
```bash
helm show readme opea/chatqna
```
##### Get the Node Names
Get the node name for each of the nodes for deployment.
```bash
kubectl get nodes --show-labels
```

##### Configure Multiple Pod Instances

If you plan to deploy the workload across multiple nodes, specify the target node names and the number of pod instances for each service in a custom YAML file (e.g., cluster.yaml), use the chart-defined service names to ensure proper configuration. Below is an example configuration for deploying the workload across two nodes:
```
# cluster.yaml - Example configuration for multiple instances
tgi:                          # Chart-defined service name
  replicaCount: 12            # Number of pod instances to deploy (default is 1 if not specified)
  evenly_distributed: true    # Distribute instances evenly across hardware nodes
  affinity:                   # Schedule pods on specific nodes
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                  - node1     # Node name
                  - node2
```
##### Deploy with Your Custom Configuration
Use the following command to deploy the workload with multiple instances:

```bash
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  --set global.modelUseHostPath=${MODELDIR} \
  -f chatqna/gaudi-values.yaml -f cluster.yaml
```

#### 4. Deploy with a Specific Namespace

To deploy the workload in a specific namespace:

```bash
export NAMESPACE=“insert-your-workload-namespace”
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  -f chatqna/gaudi-values.yaml \
  --namespace ${NAMESPACE} --create-namespace
```

When using a custom namespace, remember to specify it when interacting with Kubernetes:

```bash
kubectl get pods -n ${NAMESPACE}
```

#### 5. Deploy with Proxy

If your environment requires proxy settings:

```bash
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  --set global.http_proxy=${http_proxy} \
  --set global.https_proxy=${https_proxy} \
  -f chatqna/gaudi-values.yaml
```

### Destroy

Uninstall `opea/chatqna` chart when it's no longer needed.
 
```bash
helm uninstall chatqna
```

## Installation

### Prerequisites

- Python 3.x
- Install the required Python packages:

```bash
pip install -r ../../requirements.txt
```

## Usage

1 Define the test cases and configurations in the benchmark.yaml file.

2 Temporarily increase the file descriptor limit before run test:

```bash
ulimit -n 100000
```

This command increases the maximum number of file descriptors (which represent open files, network connections, etc.) that a single process can use. By default, many systems set a conservative limit, such as 1024, which may not be sufficient for high-concurrency applications or large-scale load testing. Raising this limit ensures that the process can handle a larger number of open connections or files without running into errors caused by insufficient file descriptors.

3 Run the benchmark script:

```bash
python benchmark.py
```

The results will be stored in the directory specified by `test_output_dir` in the configuration.


## Configuration

The benchmark.yaml file defines the test suite and individual test cases. Below are the primary sections:

### Test Suite Configuration

```yaml
test_suite_config: 
  examples: ["chatqna"]  # Test cases to be run (e.g., chatqna, codegen)
  deployment_type: "k8s"  # Default is "k8s", can also be "docker"
  service_ip: None  # Leave as None for k8s, specify for Docker
  service_port: None  # Leave as None for k8s, specify for Docker
  load_shape:              # Tenant concurrency pattern
    name: constant           # poisson or constant(locust default load shape)
    params:                  # Loadshape-specific parameters
      constant:                # Poisson load shape specific parameters, activate only if load_shape is poisson
        concurrent_level: 4      # If user_queries is specified, concurrent_level is target number of requests per user. If not, it is the number of simulated users
      poisson:                 # Poisson load shape specific parameters, activate only if load_shape is poisson
        arrival-rate: 1.0        # Request arrival rate
  warm_ups: 0  # Number of test requests for warm-ups
  run_time: 60m  # Total runtime for the test suite
  seed:  # The seed for all RNGs
  user_queries: [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]  # Number of test requests
  query_timeout: 120  # Number of seconds to wait for a simulated user to complete any executing task before exiting. 120 sec by defeult.
  random_prompt: false  # Use random prompts if true, fixed prompts if false
  collect_service_metric: false  # Enable service metrics collection
  data_visualization: false # Enable data visualization
  test_output_dir: "/home/sdp/benchmark_output"  # Directory for test outputs
```

### Test Cases

Each test case includes multiple services, each of which can be toggled on/off using the `run_test` flag. You can also change specific parameters for each service for performance tuning.

Example test case configuration for `chatqna`, you can retrieve the deployed kubernetes service name by running `kubectl get svc` for kubernetes deployment.

```yaml
test_cases:
  chatqna:
    embedding:
      run_test: false
      service_name: "embedding-svc"
    retriever:
      run_test: false
      service_name: "retriever-svc"
      parameters:
        search_type: "similarity"
        k: 4
        fetch_k: 20
        lambda_mult: 0.5
        score_threshold: 0.2
    llm:
      run_test: false
      service_name: "llm-svc"
      parameters:
        model_name: "Intel/neural-chat-7b-v3-3"
        max_new_tokens: 128
        temperature: 0.01
        streaming: true
    e2e:
      run_test: true
      service_name: "chatqna-backend-server-svc"
      service_list:  # Replace with your k8s service names if deploy with k8s
                     # or container names if deploy with Docker for metrics collection,
                     # activate if collect_service_metric is true
        - "chatqna-backend-server-svc"
      dataset: # Activate if random_prompt=true: leave blank = default dataset(WebQuestions) or sharegpt
```
If you'd like to use sharegpt dataset, please download the dataset according to the [guide](https://github.com/lm-sys/FastChat/issues/90#issuecomment-1493250773). Merge all downloaded data files into one file named sharegpt.json and put the file at `evals/benchmark/stresscli/dataset`.
