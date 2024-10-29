[LongBench](https://github.com/THUDM/LongBench) is the benchmark for bilingual, multitask, and comprehensive assessment of long context understanding capabilities of large language models. LongBench includes different languages (Chinese and English) to provide a more comprehensive evaluation of the large models' multilingual capabilities on long contexts. In addition, LongBench is composed of six major categories and twenty one different tasks, covering key long-text application scenarios such as single-document QA, multi-document QA, summarization, few-shot learning, synthetic tasks and code completion.

In this guideline, we evaluate LongBench dataset with OPEA services on Intel hardwares.

# 🚀 QuickStart

## Installation

```
pip install ../../../requirements.txt
```

## Launch a LLM Service

To setup a LLM model, we can use [tgi-gaudi](https://github.com/huggingface/tgi-gaudi) or [OPEA microservices](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/text-generation) to launch a service. 

### Example 1: TGI
For example, the follow command is to setup the [meta-llama/Llama-2-7b-hf](https://huggingface.co/meta-llama/Llama-2-7b-hf) model on  Gaudi:

```
model=meta-llama/Llama-2-7b-hf
hf_token=YOUR_ACCESS_TOKEN
volume=$PWD/data # share a volume with the Docker container to avoid downloading weights every run

docker run -p 8080:80 -v $volume:/data --runtime=habana -e HABANA_VISIBLE_DEVICES=all \
-e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HF_TOKEN=$hf_token \
-e ENABLE_HPU_GRAPH=true -e LIMIT_HPU_GRAPH=true -e USE_FLASH_ATTENTION=true \
-e FLASH_ATTENTION_RECOMPUTE=true --cap-add=sys_nice --ipc=host \
ghcr.io/huggingface/tgi-gaudi:2.0.5 --model-id $model --max-input-tokens 1024 \
--max-total-tokens 2048
```

### Example 2: OPEA LLM
You can also set up a service with OPEA microservices. 

For example, you can refer to [native LLM](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/text-generation/native/langchain) for deployment on native Gaudi without any serving framework.

## Predict 
Please set up the environment variables first.
```
export ENDPOINT="http://{host_ip}:8080/generate" # your LLM serving endpoint
export LLM_MODEL="meta-llama/Llama-2-7b-hf"
export BACKEND="tgi" # "tgi" or "llm"
export DATASET="narrativeqa" # can refer to https://github.com/THUDM/LongBench/blob/main/task.md for full list
export MAX_INPUT_LENGTH=2048 # specify the max input length according to llm services
```
Then get the prediction on the dataset.
```
python pred.py \
    --endpoint ${ENDPOINT} \
    --model_name ${LLM_MODEL} \
    --backend ${BACKEND} \ 
    --dataset ${DATASET} \
    --max_input_length  ${MAX_INPUT_LENGTH}
```
The prediction will be saved to "pred/{LLM_MODEL}/{DATASET.jsonl}".

## Evaluate
Evaluate the prediction with LongBench metrics.
```
git clone https://github.com/THUDM/LongBench
cd LongBench
pip install -r requirements.txt
python eval.py --model ${LLM_MODEL}
```
Then evaluated result will be saved to "pred/{LLM_MODEL}/{result.jsonl}".
