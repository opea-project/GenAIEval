# CRAG Benchmark for Agent QnA systems
## Overview
[Comprehensive RAG (CRAG) benchmark](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024) was introduced by Meta in 2024 as a challenge in KDD conference. The CRAG benchmark has questions across five domains and eight question types, and provides a practical set-up to evaluate RAG systems. In particular, CRAG includes questions with answers that change from over seconds to over years; it considers entity popularity and covers not only head, but also torso and tail facts; it contains simple-fact questions as well as 7 types of complex questions such as comparison, aggregation and set questions to test the reasoning and synthesis capabilities of RAG solutions. Additionally, CRAG also provides mock APIs to query mock knowledge graphs so that developers can benchmark additional API calling capabilities for agents. Moreover, golden answers were provided in the dataset, which makes auto-evaluation with LLMs more robust. Therefore, CRAG benchmark is a realistic and comprehensive benchmark for agents.

## Getting started
1. Setup a work directory and download this repo into your work directory.
```bash
export $WORKDIR=<your-work-directory>
cd $WORKDIR
git clone https://github.com/opea-project/GenAIEval.git
```
<!-- 2. Build docker image
```
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/docker/
bash build_image.sh
``` -->
2. Create a conda environment
```bash
conda create -n agent-eval-env python=3.10
conda activate agent-eval-env
pip install -r $WORKDIR/GenAIEval/evals/evaluation/agent_eval/docker/requirements.txt
```
3. Set environment vars for downloading models from Huggingface
```bash
mkdir $WORKDIR/hf_cache 
export HF_CACHE_DIR=$WORKDIR/hf_cache
export HF_HOME=$HF_CACHE_DIR
export HUGGINGFACEHUB_API_TOKEN=<your-hf-api-token>
export host_ip=$(hostname -I | awk '{print $1}')
export PYTHONPATH=$PYTHONPATH:$WORKDIR/GenAIEval/
```
<!-- 4. Start docker container
This container will be used to preprocess dataset and run benchmark scripts.
```
bash launch_eval_container.sh
``` -->
4. Start vllm container on Intel Gaudi2. 

By default, `meta-llama/Meta-Llama-3.1-70B-Instruct` model will be served using 4 Gaudi cards. This LLM will be used by agent as well as used as LLM-judge in scoring agent's answers.
```bash
# First build vllm image for Gaudi
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/vllm-gaudi
bash build_image.sh
```
Then launch vllm endpoint. The default model is `meta-llama/Meta-Llama-3.1-70B-Instruct`.
```bash
bash launch_vllm_gaudi.sh
```
5. Validate vllm endpoint is working properly.
```bash
python3 test_vllm_endpoint.py
```

## CRAG dataset
1. Download original data and process it with commands below.
You need to create an account on the Meta CRAG challenge [website](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024). After login, go to this [link](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024/problems/meta-kdd-cup-24-crag-end-to-end-retrieval-augmented-generation/dataset_files) and download the `crag_task_3_dev_v4.tar.bz2` file. Then make a `datasets` directory in your work directory using the commands below.
```bash
cd $WORKDIR
mkdir datasets
```
Then put the `crag_task_3_dev_v4.tar.bz2` file in the `datasets` directory, and decompress it by running the command below.
```bash
cd $WORKDIR/datasets
tar -xf crag_task_3_dev_v4.tar.bz2
```
2. Preprocess the CRAG data
Data preprocessing directly relates to the quality of retrieval corpus and thus can have significant impact on the agent QnA system. Here, we provide one way of preprocessing the data where we simply extracts all the web search snippets as-is from the dataset per domain. We also extract all the query-answer pairs along with other meta data per domain. You can run the command below to use our method. The data processing will take some time to finish.
```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/preprocess_data
bash run_data_preprocess.sh
```
**Note**: This is an example of data processing. You can develop and optimize your own data processing for this benchmark.
3. (Optional) Sample queries for benchmark
The CRAG dataset has more than 4000 queries, and running all of them can be very expensive and time-consuming. You can sample a subset for benchmark. Here we provide a script to sample up to 5 queries per question_type per dynamism in each domain. For example, we were able to get 92 queries from the music domain using the script.
```bash
bash run_sample_data.sh
```

## Launch Agent QnA system
Here we showcase an agent system in OPEA GenAIExamples repo. Please refer to the README in the [AgentQnA example](https://github.com/opea-project/GenAIExamples/tree/main/AgentQnA/README.md) for more details.

> **Please note**: This is an example. You can build your own agent systems using OPEA components, then expose your own systems as an endpoint for this benchmark.

To launch the agent in our AgentQnA example on Intel Gaudi accelerators, follow the instructions below.
1. Build images
```bash
export $WORKDIR=<your-work-directory>
cd $WORKDIR
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AgentQnA/tests/
bash step1_build_images.sh
```
2. Start retrieval tool
```bash
bash step2_start_retrieval_tool.sh
```
3. Ingest data into vector database and validate retrieval tool
```bash
# As an example, we will use the index_data.py script in AgentQnA example.
# You can write your own script to ingest data.
# As an example, We will ingest the docs of the music domain.
cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/
export host_ip=$(hostname -I | awk '{print $1}')
python3 index_data.py --host_ip $host_ip --filedir ${WORKDIR}/datasets/crag_docs/ --filename crag_docs_music.jsonl
```

4. Start CRAG API container
```bash
docker run -d --runtime=runc --name=kdd-cup-24-crag-service -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0
```

5. Launch the agent microservices
```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/opea_rag_agent/
bash launch_agent.sh
```
Note: There are two agents in the agent system: a RAG agent (as the worker agent) and a ReAct agent (as the supervisor agent). We can evaluate both agents - just need to specify the agent endpoint url in the scripts - see instructions below.

## Run CRAG benchmark
Once you have your agent system up and running, the next step is to generate answers with agent. Change the variables in the script below and run the script. By default, it will run the entire set of queries in the music domain (in total 373 queries). You can choose to run other domains or just run a sampled subset of music domain.
```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/run_benchmark
# Remember to specify the agent endpoint url in the script.
bash run_generate_answer.sh
```

## Use LLM-as-judge to grade the answers
Grade the answer correctness using LLM judge. We use `answer_correctness` metrics from [ragas](https://github.com/explodinggradients/ragas/blob/main/src/ragas/metrics/_answer_correctness.py).

```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/run_benchmark/
bash run_grading.sh
```
 
### Validation of LLM-as-judge
We validated RAGAS answer correctness as the metric to evaluate agents. We sampled 92 queries from the full music domain dataset (up to 5 questions per sub-category for all 32 sub-categories), and conducted human evaluations on the conventional RAG answers, the single RAG agent answers and the hierarchical ReAct agent answers of the 92 queries. 

We followed the criteria in the [CRAG paper](https://arxiv.org/pdf/2406.04744) to get human scores: 
1. score 1 if the answer matches the golden answer or semantically similar.
2. score 0 if the answer misses information, or is "I don't know", “I’m sorry I can’t find ...”, a system error such as recursion limit is hit, or a request from the system to clarify the original question.
3. score -1 if the answer contains incorrect information.

On the other hand, RAGAS `answer_correctness` score is on a scale of 0-1 and is a weighted average of 1) an F1 score and 2) similarity between answer and golden answer. The F1 score is based on the number of statements in the answer supported or not supported by the golden answer, and the number of statements in the golden answer appeared or did not appear in the answer. Please refer to [RAGAS source code](https://github.com/explodinggradients/ragas/blob/main/src/ragas/metrics/_answer_correctness.py) for the implementation of its `answer_correctness` score. We ran RAGAS on Intel Gaudi2 accelerators. We used `meta-llama/Meta-Llama-3.1-70B-Instruct` as the LLM judge.

|Setup           |Mean Human score|Mean RAGAS `answer_correctness` score|
|----------------|-----------|------------------------------|
|Conventional RAG|0.05       |0.37|
|Single RAG agent|0.18       |0.43|
|Hierarchical ReAct agent|0.22|0.54|

We can see that the human scores and the RAGAS `answer_correctness` scores follow the same trend, although the two scoring methods used different grading criteria and methods. Since LLM-as-judge is more scalable for larger datasets, we decided to use RAGAS `answer_correctness` scores (produced by `meta-llama/Meta-Llama-3-70B-Instruct` as the LLM judge) for the evaluation of OPEA agents on the full CRAG music domain dataset.

We have made available our scripts to calculate the mean RAGAS scores. Refer to the `run_compare_scores.sh` script in the `run_benchmark` folder.


## Benchmark results for OPEA RAG Agents
We have evaluated the agents (`rag_agent_llama` and `react_llama` strategies) in the OPEA AgentQnA example on CRAG music domain dataset (373 questions in total). We used `meta-llama/Meta-Llama-3.1-70B-Instruct` and we served the LLM with tgi-gaudi on 4 Intel Gaudi2 accelerator cards. Refer to the docker compose yaml files in the AgentQnA example for more details on the configurations.

For the tests of conventional RAG, we used the script in the `run_benchmark` folder: `run_conv_rag.sh`. And we used the same LLM, serving configs and generation parameters as the RAG agent.

The Conventional RAG and Single RAG agent use the same retriever. The Hierarchical ReAct agent uses the Single RAG agent as its retrieval tool and also has access to CRAG APIs provided by Meta as part of the CRAG benchmark.


|Setup           |Mean RAGAS `answer_correctness` score|
|----------------|------------------------------|
|Conventional RAG|0.42|
|Single RAG agent|0.43|
|Hierarchical ReAct agent|0.53|

From the results, we can see that the single RAG agent performs better than conventional RAG, while the hierarchical ReAct agent has the highest `answer_correctness` score. The reasons for such performance improvements:
1. RAG agent rewrites query and checks the quality of retrieved documents before feeding the docs to generation. It can get docs that are more relevant to generate answers. It can also decompose complex questions into modular tasks and get related docs for each task and then aggregate info to come up with answers.
2. Hierarchical ReAct agent was supplied with APIs to get information from knowledge graphs, and thus can supplement info to the knowledge in the retrieval vector database. So it can answer questions where conventional RAG or Single RAG agent cannot due to the lack of relevant info in vector database.

Note: The performance result for the hierarchical ReAct agent is with tool selection, i.e., only give a subset of tools to agent based on query, which we found can boost agent performance when the number of tools is large. However, currently OPEA agents do not support tool selection yet. We are in the process of enabling tool selection. 

### Comparison with GPT-4o-mini
Open-source LLM serving libraries (tgi and vllm) have limited capabilities in producing tool-call objects. Although vllm improved its tool-calling capabilities recently, parallel tool calling is still not well supported. Therefore, we had to write our own prompts and output parsers for the `rag_agent_llama` and `react_llama` strategies for using open-source LLMs served with open-source serving frameworks for OPEA agent microservices.

Below we show the comparisons of `meta-llama/Meta-Llama-3.1-70B-Instruct` versus OpenAI's `gpt-4o-mini-2024-07-18` on 20 sampled queries from the CRAG music domain dataset. We used human evaluation criteria outlined above. The numbers are the average scores graged by human. The parenthesis denotes the OPEA agent strategy used.

|Setup|Llama3.1-70B-Instruct|gpt-4o-mini|
|-----|---------------------|-----------|
|Conventional RAG|0.15|0.05|
|Single RAG agent|0.45 (`rag_agent_llama`)|0.65 (`rag_agent`)|
|Hierarchical ReAct agent|0.55 (`react_llama`)|0.75 (`react_langgraph`)|

From the comparisons on this small subset, we can see that OPEA agents using `meta-llama/Meta-Llama-3.1-70B-Instruct` with calibrated prompt templates and output parsers are only slightly behind `gpt-4o-mini-2024-07-18` with proprietary tool-calling capabilities.
