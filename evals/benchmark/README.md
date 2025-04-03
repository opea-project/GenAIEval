# OPEA Benchmark Tool

This Tool provides a microservice benchmarking framework that uses YAML configurations to define test cases for different services. It executes these tests using `stresscli`, built on top of [locust](https://github.com/locustio/locust), a performance/load testing tool for HTTP and other protocols and logs the results for performance analysis and data visualization.

## Features

- **Services load testing**: Simulates high concurrency levels to test services like LLM, reranking, ASR, E2E and more.
- **YAML-based configuration**: Define test cases, service endpoints, and testing parameters in YAML.
- **Service metrics collection**: Optionally collect service metrics for detailed performance analysis.
- **Flexible testing**: Supports various test cases like chatqna, codegen, codetrans, faqgen, audioqna, and visualqna.
- **Data analysis and visualization**: After tests are executed, results can be analyzed and visualized to gain insights into the performance and behavior of each service. Performance trends, bottlenecks, and other key metrics are highlighted for decision-making.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
  - [Test Suite Configuration](#test-suite-configuration)
  - [Test Cases](#test-cases)


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

> NOTE : Add --yaml argument to use a customized benchmark configurationse.

 e.g. 
 ```bash
python benchmark.py --yaml docker.hpu.benchmark.yaml
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
      constant:                # Constant load shape specific parameters, activate only if load_shape.name is constant
        concurrent_level: 4      # If user_queries is specified, concurrent_level is target number of requests per user. If not, it is the number of simulated users
        # arrival_rate: 1.0       # Request arrival rate. If set, concurrent_level will be overridden, constant load will be generated based on arrival-rate
      poisson:                 # Poisson load shape specific parameters, activate only if load_shape.name is poisson
        arrival_rate: 1.0        # Request arrival rate
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

Example test case configuration for `chatqna`:

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
        k: 1
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
      prompts: # User-customized prompts, activate if random_prompt=false.
      max_output: 128  # max number of output tokens
      k: 1 # number of retrieved documents
```
If you'd like to use sharegpt dataset, please download the dataset according to the [guide](https://github.com/lm-sys/FastChat/issues/90#issuecomment-1493250773). Merge all downloaded data files into one file named sharegpt.json and put the file at `evals/benchmark/stresscli/dataset`.
