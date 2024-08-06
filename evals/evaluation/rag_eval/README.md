# CRUD-RAG
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
python run_crud.py --dataset_path ../data/split_merged.json --docs_path ../data/80000_docs --ingest_docs
```

## Acknowledgements
This example is mostly adapted from [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, we thank the authors for their great work!
