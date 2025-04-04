# Toxicity Detection Accuracy

Toxicity detection plays a critical role in guarding the inputs and outputs of large language models (LLMs) to ensure safe, respectful, and responsible content. Given the widespread use of LLMs in applications like customer service, education, and social media, there's a significant risk that they could inadvertently produce or amplify harmful language if toxicity is not detected effectively. 

To evaluate a target toxicity detection LLM, we use multiple datasets: BeaverTails, Jigsaw Unintended Bias, OpenAI Moderation, SurgeAI Toxicity, ToxicChat, ToxiGen, and XSTest. We also employ the most commonly used metrics in toxicity classification to provide a comprehensive assessment. Currently, the benchmark script supports benchmarking only one dataset at a time. Future work includes enabling benchmarking on multiple datasets simultaneously. The Gaudi 2 accelerator is deployed in the benchmark to address the high demand of the AI workload while balancing power efficiency.

- Supported Datasets
    - [BeaverTails](https://huggingface.co/datasets/PKU-Alignment/BeaverTails)
    - [Jigsaw Unintended Bias](https://www.kaggle.com/c/jigsaw-unintended-bias-in-toxicity-classification)
    - [OpenAI Moderation](https://github.com/openai/moderation-api-release/tree/main)
    - [SurgeAI Toxicity](https://github.com/surge-ai/toxicity)
    - [ToxicChat](https://huggingface.co/datasets/lmsys/toxic-chat)
    - [ToxiGen](https://huggingface.co/datasets/toxigen/toxigen-data)
    - [XSTest](https://huggingface.co/datasets/walledai/XSTest)
    - More datasets to come...
    
- Supported Metrics
    - accuracy
    - auprc (area under precision recall curve)
    - auroc
    - f1
    - fpr (false positive rate)
    - precision
    - recall

## Get Started on Gaudi 2 Accelerator
### Requirements
If you are using an `hpu` device, then clone the `optimum-habana` and the `GenAIEval` repositories.
```bash
git clone https://github.com/huggingface/optimum-habana.git --depth=1
git clone https://github.com/opea-project/GenAIEval --depth=1
```

### Setup
If you're running behind corporate proxy, run Gaudi Docker with additional proxies and volume mount.
```bash
DOCKER_RUN_ENVS="--env http_proxy=${http_proxy} --env HTTP_PROXY=${HTTP_PROXY} --env https_proxy=${https_proxy} --env HTTPS_PROXY=${HTTPS_PROXY} --env no_proxy=${no_proxy} --env NO_PROXY=${NO_PROXY}"

docker run --disable-content-trust ${DOCKER_RUN_ENVS} \
    -d --rm -it --name toxicity-detection-benchmark \
    -v ${PWD}:/workdir \
    --runtime=habana \
    -e HABANA_VISIBLE_DEVICES=all \
    -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
    --cap-add=sys_nice \
    --net=host \
    --ipc=host \
    vault.habana.ai/gaudi-docker/1.19.0/ubuntu22.04/habanalabs/pytorch-installer-2.5.1:latest
```

### Evaluation
#### Execute interactive container
```bash
docker exec -it toxicity-detection-benchmark bash
```
#### Navigate to `workdir` and install required packages
```bash
cd /workdir
cd optimum-habana && pip install . && cd ../GenAIEval
pip install -r requirements.txt
pip install -e .
```

In case of [Jigsaw Unintended Bias](https://www.kaggle.com/c/jigsaw-unintended-bias-in-toxicity-classification), [OpenAI Moderation](https://github.com/openai/moderation-api-release), and [Surge AI Toxicity](https://github.com/surge-ai/toxicity) datasets, make sure the datasets are downloaded and stored in current working directory.

#### Test the model and confirm the results are saved correctly
Navigate to the toxicity evaluation directory:
```bash
cd evals/evaluation/toxicity_eval
```

Replace `MODEL_PATH` and `DATASET` with the appropriate path for the model and the name of the dataset.
```bash
MODEL_PATH=Intel/toxic-prompt-roberta
DATASET=tc
python benchmark_classification_metrics.py -m ${MODEL_PATH} -d ${DATASET}
cat results/${MODEL_PATH##*/}_${DATASET}_accuracy/metrics.json
```

If you are using an `hpu` device, you can instantiate the Gaudi configuration by passing the `GAUDI_CONFIG_NAME` variable with the appropriate configuration name. The default value for the device name (`device`) is `hpu`.
```bash
MODEL_PATH=Intel/toxic-prompt-roberta
DATASET=tc
GAUDI_CONFIG_NAME=Habana/roberta-base
DEVICE_NAME=hpu
python benchmark_classification_metrics.py -m ${MODEL_PATH} -d ${DATASET} -g_config ${GAUDI_CONFIG_NAME} --device ${DEVICE_NAME}
cat results/${MODEL_PATH##*/}_${DATASET}_accuracy/metrics.json 
```

For the Jigsaw Unintended Bias, OpenAI Moderation, and Surge AI Toxicity datasets, pass the path of the stored dataset path in place of `DATASET_PATH`
```bash
MODEL_PATH=Intel/toxic-prompt-roberta
DATASET=jigsaw
DATASET_PATH=/path/to/dataset
python ./classification_metrics/scripts/benchmark_classification_metrics.py -m ${MODEL_PATH} -d ${DATASET} -p ${DATASET_PATH} 
cat results/${MODEL_PATH##*/}_${DATASET}_accuracy/metrics.json
```

## Get Started on CPU

### Requirements
* Linux system or WSL2 on Windows (validated on Ubuntu* 22.04/24.04 LTS)
* Python >=3.10

### Installation
Follow the GenAIEval installation steps provided in the repository's main [README](https://github.com/daniel-de-leon-user293/GenAIEval/tree/daniel/toxicity-eval?tab=readme-ov-file#installation).

### Evaluation
Navigate to the toxicity evaluation directory:
```bash
cd evals/evaluation/toxicity_eval
```

In case of [Jigsaw Unintended Bias](https://www.kaggle.com/c/jigsaw-unintended-bias-in-toxicity-classification), [OpenAI Moderation](https://github.com/openai/moderation-api-release), and [Surge AI Toxicity](https://github.com/surge-ai/toxicity), make sure the datasets are downloaded and stored in current working directory.

Replace `MODEL_PATH` and `DATASET` with the appropriate path for the model and the name of the dataset. For running the script on cpu device, replace the variable `DEVICE_NAME` with `cpu`.
```bash
MODEL_PATH=Intel/toxic-prompt-roberta
DATASET=tc
DEVICE_NAME=cpu
python benchmark_classification_metrics.py -m ${MODEL_PATH} -d ${DATASET} --device ${DEVICE_NAME}
```
You can find the evaluation results in the results folder:
```bash
cat results/${MODEL_PATH##*/}_${DATASET}_accuracy/metrics.json
```
For the Jigsaw Unintended Bias, OpenAI Moderation, and Surge AI Toxicity datasets, pass the path of the stored dataset path in place of `DATASET_PATH`

```bash
MODEL_PATH=Intel/toxic-prompt-roberta
DATASET=jigsaw
DATASET_PATH=/path/to/dataset
DEVICE_NAME=cpu
python benchmark_classification_metrics.py -m ${MODEL_PATH} -d ${DATASET} -p ${DATASET_PATH} --device ${DEVICE_NAME}
```
You can find the evaluation results in the results folder:
```bash
cat results/${MODEL_PATH##*/}_${DATASET}_accuracy/metrics.json
```
