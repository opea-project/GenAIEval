# How to  benchmark pubmed datasets by send query randomly 
This README outlines how to prepare the PubMed datasets for benchmarking ChatQnA and creating a query list based on these datasets. It also explains how to randomly send queries from the list to the ChatQnA pipeline in order to obtain performance data that is more consistent with real user scenarios.

## 1. prepare the pubmed datasets

- To simulate a practical user scenario, we have chosen to use industrial data from PubMed. The original PubMed data can be found here: [Hugging Face - MedRAG PubMed](https://huggingface.co/datasets/MedRAG/pubmed/tree/main/chunk). 
- In order to observe and compare the performance of the ChatQnA pipeline with different sizes of ingested datasets, we created four files: pubmed_10.txt, pubmed_100.txt, pubmed_1000.txt, and pubmed_10000.txt. These files contain 10, 100, 1,000, and 10,000 records of data extracted from [pubmed23n0001.jsonl]


### 1.1 get pubmed data
wget https://huggingface.co/datasets/MedRAG/pubmed/resolve/main/chunk/pubmed23n0001.jsonl

### 1.2 use script to extract data
A prepared script, extract_lines.sh, is available to extract lines from the original pubmed file into the dataset and query list.
#### Usage: 
```

$ cd dataset
$./extract_lines.sh input_file output_file begin_id end_id
```



### 1.3 prepare 4 dataset files
The commands below will generate the 4 pubmed dataset files. And the 4 dataset files will be ingested by dataprep before benchmarking:
```
./extract_lines.sh  pubmed23n0001.jsonl pubmed_10.txt pubmed23n0001_0 pubmed23n0001_9
./extract_lines.sh  pubmed23n0001.jsonl pubmed_100.txt pubmed23n0001_0 pubmed23n0001_99
./extract_lines.sh  pubmed23n0001.jsonl pubmed_1000.txt pubmed23n0001_0 pubmed23n0001_999
./extract_lines.sh  pubmed23n0001.jsonl pubmed_10000.txt pubmed23n0001_0 pubmed23n0001_9999
```

### 1.4 prepare the query list
Basically, the random queries will be based on 10% of the ingested dataset, so we only need to prepare a maximum of 1,000 records for the random query list
```
cp pubmed_1000.txt pubmed_q1000.txt
```



## 2. How to use pubmed qlist
> NOTE:<BR>Unlike chatqnafixed.py, which sends a fixed prompt each time, chatqna_qlist_pubmed.py is designed to benchmark the ChatQnA pipeline using the PubMed query list. <BR>
Each time it randomly selects a query from the query list file and sends it to the ChatQnA pipeline

- First make sure use the correct benchmark_target in run.yaml

    ```
    bench-target: "chatqna_qlist_pubmed"
    ```
- Ensure that the environment variables are set correctly:
    - DATASET: The specific name of the query list file. Default: "pubmed_q1000.txt"
    - MAX_LINES: The maximum number of lines from the query list that will be used for random queries. Default: 1000
    - MAX_TOKENS: The parameter sent to the ChatQnA pipeline to specify the maximum number of tokens the language model can generate. Default: 128
    - PROMPT: A user-defined prompt that will be sent to the ChatQnA pipeline.
- Then run the benchmark script,for example:
```
    ./stresscli.py load-test --profile run.yaml
```
For more information, please refer to the [stresscli](./README.md) documentation.
