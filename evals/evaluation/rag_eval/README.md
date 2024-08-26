# Evaluation Methodology

<!-- TOC -->

- [Evaluation Methodology](#evaluation-methodology)
  - [Introduction](#introduction)
  - [Prerequisites](#prerequisites)
  - [MultiHop (English dataset)](#multihop)
    - [Launch Service of RAG System](#launch-service-of-rag-system)
    - [Launch Service of LLM-as-a-Judge](launch-service-of-llm)
    - [Prepare Dataset](#prepare-dataset)
    - [Evaluation](#evaluation)
  - [CRUD (Chinese dataset)](#crud)
    - [Launch Service of RAG System](#launch-service-of-rag-system)
    - [Prepare Dataset](#prepare-dataset)
    - [Evaluation](#evaluation)

<!-- /TOC -->

## Introduction

Retrieval-Augmented Generation (RAG) has recently gained traction in natural language processing. Numerous studies and real-world applications are leveraging its ability to enhance generative models through external information retrieval.

For evaluating the accuracy of a RAG pipeline, we use 2 latest published datasets and 10+ metrics which are popular and comprehensive:

- Dataset
  - [MultiHop](https://arxiv.org/pdf/2401.15391) (English dataset)
  - [CRUD](https://arxiv.org/abs/2401.17043) (Chinese dataset)
- metrics (measure accuracy of both the context retrieval and response generation)
  - evaluation for retrieval/reranking
    - MRR@10
    - MAP@10
    - Hits@10
    - Hits@4
    - LLM-as-a-Judge
  - evaluation for the generated response from the end-to-end pipeline
    - BLEU
    - ROUGE(L)
    - LLM-as-a-Judge

## Prerequisite

### Environment
```bash
pip install -r requirements.txt
```

## MultiHop (English dataset)

[MultiHop-RAG](https://arxiv.org/pdf/2401.15391): a QA dataset to evaluate retrieval and reasoning across documents with metadata in the RAG pipelines. It contains 2556 queries, with evidence for each query distributed across 2 to 4 documents. The queries also involve document metadata, reflecting complex scenarios commonly found in real-world RAG applications.

### Launch Service of RAG System
Please refer to this [guide](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/README.md) to launch the service of RAG system.

### Launch Service of LLM-as-a-Judge

To setup a LLM model, we can use [tgi-gaudi](https://github.com/huggingface/tgi-gaudi) to launch a service. For example, the follow command is to setup the [mistralai/Mixtral-8x7B-Instruct-v0.1](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) model on 2 Gaudi2 cards:

```
# please set your llm_port and hf_token

docker run -p {your_llm_port}:80 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HF_TOKEN={your_hf_token} --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:2.0.1 --model-id mistralai/Mixtral-8x7B-Instruct-v0.1 --max-input-tokens 1024 --max-total-tokens 2048 --sharded true --num-shard 2
```

### Prepare Dataset
We use the evaluation dataset from [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) repo, use the below command to prepare the dataset.
```bash
cd examples
git clone https://github.com/yixuantt/MultiHop-RAG.git
```

### Evaluation

Use below command to run the evaluation, please note that for the first run, argument `--ingest_docs` should be added in the command to ingest the documents into the vector database, while for the subsequent run, this argument should be omitted. Set `--retrieval_metrics` to get retrieval related metrics (MRR@10/MAP@10/Hits@10/Hits@4). Set `--ragas_metrics` and `--llm_endpoint` to get end-to-end rag pipeline metrics (faithfulness/answer_relevancy/...), which are judged by LLMs. 

```bash
python eval_multihop.py --docs_path MultiHop-RAG/dataset/corpus.json  --dataset_path MultiHop-RAG/dataset/MultiHopRAG.json --ingest_docs --retrieval_metrics --ragas_metrics --llm_endpoint http://{your_ip}:{your_llm_port}/generate
```

## CRUD (Chinese dataset)
[CRUD-RAG](https://arxiv.org/abs/2401.17043) is a Chinese benchmark for RAG (Retrieval-Augmented Generation) system. This example utilize CRUD-RAG for evaluating the RAG system.


### Prepare Dataset
We use the evaluation dataset from [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, use the below command to prepare the dataset.
```bash
git clone https://github.com/IAAR-Shanghai/CRUD_RAG
mkdir data/
cp CRUD_RAG/data/crud_split/split_merged.json data/
cp -r CRUD_RAG/data/80000_docs/ data/
python examples/process_crud_dataset.py
```

### Launch Service of RAG System
Please refer to this [guide](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/README.md) to launch the service of RAG system. For Chinese dataset, you should replace the English emebdding and llm model with Chinese, for example, `EMBEDDING_MODEL_ID="BAAI/bge-base-zh-v1.5"` and `LLM_MODEL_ID=Qwen/Qwen2-7B-Instruct`.

### Evaluation
Use below command to run the evaluation, please note that for the first run, argument `--ingest_docs` should be added in the command to ingest the documents into the vector database, while for the subsequent run, this argument should be omitted.
```bash
cd examples
python eval_crud.py --dataset_path ../data/split_merged.json --docs_path ../data/80000_docs --ingest_docs
```

## Acknowledgements
This example is mostly adapted from [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) and [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, we thank the authors for their great work!
