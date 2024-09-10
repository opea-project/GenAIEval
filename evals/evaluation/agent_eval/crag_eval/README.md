# CRAG Benchmark for Agent QnA systems
## Overview
[Comprehensive RAG (CRAG) benchmark](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024) was introduced by Meta in 2024 as a challenge in KDD conference. The CRAG benchmark has questions across five domains and eight question types, and provides a practical set-up to evaluate RAG systems. In particular, CRAG includes questions with answers that change from over seconds to over years; it considers entity popularity and covers not only head, but also torso and tail facts; it contains simple-fact questions as well as 7 types of complex questions such as comparison, aggregation and set questions to test the reasoning and synthesis capabilities of RAG solutions. Additionally, CRAG also provides mock APIs to query mock knowledge graphs so that developers can benchmark additional API calling capabilities for agents. Moreover, golden answers were provided in the dataset, which makes auto-evaluation with LLMs more robust. Therefore, CRAG benchmark is a realistic and comprehensive benchmark for agents.

## Getting started
1. Setup a work directory and download this repo into your work directory.
```
export $WORKDIR=<your-work-directory>
cd $WORKDIR
git clone https://github.com/opea-project/GenAIEval.git
```
2. Build docker image
```
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/docker/
bash build_image.sh
```
3. Set environment vars for downloading models from Huggingface
```
mkdir $WORKDIR/hf_cache 
export HF_CACHE_DIR=$WORKDIR/hf_cache
export HF_HOME=$HF_CACHE_DIR
export HUGGINGFACEHUB_API_TOKEN=<your-hf-api-token>
```
4. Start docker container
This container will be used to preprocess dataset and run benchmark scripts.
```
bash launch_eval_container.sh
```

## CRAG dataset
1. Download original data and process it with commands below.
You need to create an account on the Meta CRAG challenge [website](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024). After login, go to this [link](https://www.aicrowd.com/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024/problems/meta-kdd-cup-24-crag-end-to-end-retrieval-augmented-generation/dataset_files) and download the `crag_task_3_dev_v4.tar.bz2` file. Then make a `datasets` directory in your work directory using the commands below.
```
cd $WORKDIR
mkdir datasets
```
Then put the `crag_task_3_dev_v4.tar.bz2` file in the `datasets` directory, and decompress it by running the command below.
```
cd $WORKDIR/datasets
tar -xf crag_task_3_dev_v4.tar.bz2
```
2. Preprocess the CRAG data
Data preprocessing directly relates to the quality of retrieval corpus and thus can have significant impact on the agent QnA system. Here, we provide one way of preprocessing the data where we simply extracts all the web search snippets as-is from the dataset per domain. We also extract all the query-answer pairs along with other meta data per domain. You can run the command below to use our method. The data processing will take some time to finish.
```
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/preprocess_data
bash run_data_preprocess.sh
```
**Note**: This is an example of data processing. You can develop and optimize your own data processing for this benchmark.
3. Sample queries for benchmark
The CRAG dataset has more than 4000 queries, and running all of them can be very expensive and time-consuming. You can sample a subset for benchmark. Here we provide a script to sample up to 5 queries per question_type per dynamism in each domain. For example, we were able to get 92 queries from the music domain using the script.
```
bash run_sample_data.sh
```

## Launch agent QnA system
Here we showcase a RAG agent in GenAIExample repo. Please refer to the README in the [AgentQnA example](https://github.com/opea-project/GenAIExamples/tree/main/AgentQnA) for more details. </br>
**Please note**: This is an example. You can build your own agent systems using OPEA components, then expose your own systems as an endpoint for this benchmark.</br>
To launch the agent in our AgentQnA example, open another terminal and build images and launch agent system there.
1. Build images
```
export $WORKDIR=<your-work-directory>
cd $WORKDIR
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AgentQnA/tests/
bash 1_build_images.sh
```
2. Start retrieval tool
```
bash 2_start_retrieval_tool.sh
```
3. Ingest data into vector database and validate retrieval tool
```
# As an example, we will use the index_data.py script in AgentQnA example.
# You can write your own script to ingest data.
# As an example, We will ingest the docs of the music domain.
# We will use the crag-eval docker container to run the index_data.py script.
# The index_data.py is a client script.
# it will send data-indexing requests to the dataprep server that is part of the retrieval tool.
# So you need to switch back to the terminal where the crag-eval container is running.
cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/
python3 index_data.py --host_ip $host_ip --filedir ${WORKDIR}/datasets/crag_docs/ --filename crag_docs_music.jsonl
```
4. Launch and validate agent endpoint
```
# Go to the terminal where you launched the AgentQnA example
cd $WORKDIR/GenAIExamples/AgentQnA/tests/
bash 4_launch_and_validate_agent.sh
```

## Run CRAG benchmark
Once you have your agent system up and running, the next step is to generate answers with agent. Change the variables in the script below and run the script. By default, it will run a sampled set of queries in music domain.
```
# Come back to the interactive crag-eval docker container
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/run_benchmark
bash run_generate_answer.sh
```

## Use LLM-as-judge to grade the answers
1. Launch llm endpoint with HF TGI: in another terminal, run the command below. By default, `meta-llama/Meta-Llama-3-70B-Instruct` is used as the LLM judge.
```
cd llm_judge
bash launch_llm_judge_endpoint.sh
```
2. Validate that the llm endpoint is working properly.
```
export host_ip=$(hostname -I | awk '{print $1}')
curl ${host_ip}:8085/generate_stream \
    -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":20}}' \
    -H 'Content-Type: application/json'
```
And then go back to the interactive crag-eval docker, run command below.
```
# Inside the crag-eval container
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/run_benchmark/llm_judge/
python3 test_llm_endpoint.py
```
3. Grade the answer correctness using LLM judge. We use `answer_correctness` metrics from [ragas](https://github.com/explodinggradients/ragas/blob/main/src/ragas/metrics/_answer_correctness.py).
```
# Inside the crag-eval container
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/crag_eval/run_benchmark/
bash run_grading.sh
```
