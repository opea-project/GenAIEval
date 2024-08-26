# Evaluation Methodology

<!-- TOC -->

- [Evaluation Methodology](#evaluation-methodology)
  - [Introduction](#introduction)
  - [Prerequisites](#prerequisites)
  - [Build and Start the Containers](#build-and-start-the-containers)
  - [Results and Conclusion](#results-and-conclusion)

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
    - LLM-as-a-Judge (
    - Human evaluation


### MultiHop


### CRUD
[CRUD-RAG](https://arxiv.org/abs/2401.17043) is a Chinese benchmark for RAG (Retrieval-Augmented Generation) system. This example utilize CRUD-RAG for evaluating the RAG system.

## Prerequisite

### Environment
```bash
pip install -r requirements.txt
```

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
Please refer to this [guide](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/README.md) to launch the service of RAG system.

## Evaluation
Use below command to run the evaluation, please note that for the first run, argument `--ingest_docs` should be added in the command to ingest the documents into the vector database, while for the subsequent run, this argument should be omitted.
```bash
cd examples
python eval_crud.py --dataset_path ../data/split_merged.json --docs_path ../data/80000_docs --ingest_docs
```

## Acknowledgements
This example is mostly adapted from [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, we thank the authors for their great work!
