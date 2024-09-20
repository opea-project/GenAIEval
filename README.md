# GenAIEval
Evaluation, benchmark, and scorecard, targeting for performance on throughput and latency, accuracy on popular evaluation harness, safety, and hallucination

## Installation

- Install from Pypi

```bash
pip install -r requirements.txt
pip install opea-eval
```
> notes: We have to install requirements.txt at first, cause Pypi can't have direct dependency with specific commit.

- Build from Source

```bash
git clone https://github.com/opea-project/GenAIEval
cd GenAIEval
pip install -r requirements.txt
pip install -e .
```

## Evaluation
### lm-evaluation-harness
For evaluating the models on text-generation tasks, we follow the [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness/) and provide the command line usage and function call usage. Over 60 standard academic benchmarks for LLMs, with hundreds of [subtasks and variants](https://github.com/EleutherAI/lm-evaluation-harness/tree/v0.4.2/lm_eval/tasks) implemented, such as `ARC`, `HellaSwag`, `MMLU`, `TruthfulQA`, `Winogrande`, `GSM8K` and so on.
#### command line usage

##### Gaudi2
```shell

# pip install --upgrade-strategy eager optimum[habana]
cd evals/evaluation/lm_evaluation_harness/examples
python main.py \
    --model gaudi-hf \
    --model_args pretrained=EleutherAI/gpt-j-6B \
    --tasks hellaswag \
    --device hpu \
    --batch_size 8
```


##### CPU
```shell

cd evals/evaluation/lm_evaluation_harness/examples
python main.py \
    --model hf \
    --model_args pretrained=EleutherAI/gpt-j-6B \
    --tasks hellaswag \
    --device cpu \
    --batch_size 8
```
#### function call usage
```python
from evals.evaluation.lm_evaluation_harness import LMEvalParser, evaluate

args = LMevalParser(
    model="hf",
    user_model=user_model,
    tokenizer=tokenizer,
    tasks="hellaswag",
    device="cpu",
    batch_size=8,
)
results = evaluate(args)
```

#### remote service usage

1. setup a separate server with [GenAIComps](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/utils/lm-eval)

   ```
   # build cpu docker
   docker build -f Dockerfile.cpu -t opea/lm-eval:latest .

   # start the server
   docker run -p 9006:9006 --ipc=host  -e MODEL="hf" -e MODEL_ARGS="pretrained=Intel/neural-chat-7b-v3-3" -e DEVICE="cpu" opea/lm-eval:latest
   ```

2. evaluate the model

   - set `base_url`, `tokenizer` and `--model genai-hf`

     ```
     cd evals/evaluation/lm_evaluation_harness/examples

     python main.py \
         --model genai-hf \
         --model_args "base_url=http://{your_ip}:9006,tokenizer=Intel/neural-chat-7b-v3-3" \
         --tasks  "lambada_openai" \
         --batch_size 2
     ```

### bigcode-evaluation-harness
For evaluating the models on coding tasks or specifically coding LLMs, we follow the [bigcode-evaluation-harness](https://github.com/bigcode-project/bigcode-evaluation-harness) and provide the command line usage and function call usage. [HumanEval](https://huggingface.co/datasets/openai_humaneval), [HumanEval+](https://huggingface.co/datasets/evalplus/humanevalplus), [InstructHumanEval](https://huggingface.co/datasets/codeparrot/instructhumaneval), [APPS](https://huggingface.co/datasets/codeparrot/apps), [MBPP](https://huggingface.co/datasets/mbpp), [MBPP+](https://huggingface.co/datasets/evalplus/mbppplus), and [DS-1000](https://github.com/HKUNLP/DS-1000/) for both completion (left-to-right) and insertion (FIM) mode are available.
#### command line usage

```shell
cd evals/evaluation/bigcode_evaluation_harness/examples
python main.py \
    --model "codeparrot/codeparrot-small" \
    --tasks "humaneval" \
    --n_samples 100 \
    --batch_size 10 \
    --allow_code_execution
```

#### function call usage
```python
from evals.evaluation.bigcode_evaluation_harness import BigcodeEvalParser, evaluate

args = BigcodeEvalParser(
    user_model=user_model,
    tokenizer=tokenizer,
    tasks="humaneval",
    n_samples=100,
    batch_size=10,
    allow_code_execution=True,
)
results = evaluate(args)
```

### Kubernetes platform optimization

Node resource management helps optimizing AI container performance and
isolation on Kubernetes nodes. See [Platform
optimization](doc/platform-optimization/README.md).


## Benchmark

We provide a OPEA microservice benchmarking tool which is designed for microservice performance testing and benchmarking. It allows you to define test cases for various services based on YAML configurations, run load tests using `stresscli`, built on top of [locust](https://github.com/locustio/locust), and analyze the results for performance insights.

### Features

- **Services load testing**: Simulates high concurrency levels to test services like LLM, reranking, ASR, E2E and more.
- **YAML-based configuration**: Easily define test cases, service endpoints, and parameters.
- **Service metrics collection**: Optionally collect service metrics to analyze performance bottlenecks.
- **Flexible testing**: Supports a variety of tests like chatqna, codegen, codetrans, faqgen, audioqna, and visualqna.
- **Data analysis and visualization**: Visualize test results to uncover performance trends and bottlenecks.

### How to use

**Define Test Cases**: Configure your tests in the [benchmark.yaml](./evals/benchmark/benchmark.py) file.

**Increase File Descriptor Limit (if running large-scale tests)**:

```bash
ulimit -n 100000
```

This ensures the system can handle high concurrency by allowing more open files and connections.

**Run the benchmark script**:

```bash
python evals/benchmark/benchmark.py
```

Results will be saved in the directory specified by `test_output_dir` in the configuration.


For more details on configuring test cases, refer to the [README](./evals/benchmark/README.md).


### Grafana Dashboards
Prometheus metrics collected during the tests can be used to create Grafana dashboards for visualizing performance trends and monitoring bottlenecks. For more information, refer to the [Grafana README](./evals/benchmark/grafana/README.md)

![tgi microservice dashboard](./assets/grafana_dashboard.png)

## Additional Content
- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Contribution](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
