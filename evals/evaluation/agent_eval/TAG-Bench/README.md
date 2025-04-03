# TAG-Bench for evaluating SQL agents
## Overview of TAG-Bench
[TAG-Bench](https://github.com/TAG-Research/TAG-Bench) is a benchmark published in 2024 by Stanford University and University of California Berkeley and advocated by Databricks to evaluate GenAI systems in answering challenging questions over SQL databases. The questions in TAG-Bench require the GenAI systems to not only able to translate natural language queries into SQL queries, but to combine information from other sources and do reasoning. There are 80 questions in total with 20 in each sub-category of match-based, comparison, ranking, and aggregation queries. The questions are about 5 databases selected from Alibaba's [BIRD](https://bird-bench.github.io/) Text2SQL benchmark: california_schools, debit_card_specializing, formula_1, codebase_community, and european_football_2. For more information, please read the [paper](https://arxiv.org/pdf/2408.14717).

## Getting started
1. Set up the environment
```bash
export WORKDIR=<your-work-directory>
mkdir $WORKDIR/hf_cache 
export HF_CACHE_DIR=$WORKDIR/hf_cache
export HF_HOME=$HF_CACHE_DIR
export HF_TOKEN=<your-huggingface-api-token>
export HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN
export PYTHONPATH=$PYTHONPATH:$WORKDIR/GenAIEval/
```
2. Download this repo in your work directory
```bash
cd $WORKDIR
git clone https://github.com/opea-project/GenAIEval.git
```
3. Create a conda environment
```bash
conda create -n agent-eval-env python=3.10
conda activate agent-eval-env
pip install -r $WORKDIR/GenAIEval/evals/evaluation/agent_eval/docker/requirements.txt
```
4. Download data
```bash
cd $WORKDIR
git clone https://github.com/TAG-Research/TAG-Bench.git
cd TAG-Bench/setup
chmod +x get_dbs.sh
./get_dbs.sh
```
5. Preprocess data
```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/TAG-Bench/preprocess_data/
bash run_data_split.sh
```
6. Generate hints file for each database in TAG-Bench
```bash
python3 generate_hints.py
```
The hints are generated from the description files that come with the TAG-Bench dataset. The hints are simply the column descriptions provided in the dataset. They can be used by the SQL agent to improve performance.

7. Launch LLM endpoint on Gaudi.

This LLM will be used by agent as well as used as LLM-judge in scoring agent's answers. By default, `meta-llama/Meta-Llama-3.1-70B-Instruct` model will be served using 4 Gaudi cards.
```bash
# First build vllm image for Gaudi
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/vllm-gaudi
bash build_image.sh
```
Then launch vllm endpoint with the command below.
```bash
bash launch_vllm_gaudi.sh
```

8. Validate vllm endpoint is working properly.
```bash
python3 test_vllm_endpoint.py
```

## Launch your SQL agent
You can create and launch your own SQL agent. Here we show an example of OPEA `sql_agent_llama`. Follow the steps below to launch OPEA `sql_agent_llama`.
1. Download OPEA GenAIComps repo
```bash
cd $WORKDIR
git clone https://github.com/opea-project/GenAIComps.git
```
2. Build docker image for OPEA agent
```bash
cd $WORKDIR/GenAIComps
export agent_image="opea/agent:comps"
docker build --no-cache -t $agent_image --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/agent/src/Dockerfile .
``` 
3. Set up environment for the `search_web` tool for agent.
```bash
export GOOGLE_CSE_ID=<your-GOOGLE_CSE_ID>
export GOOGLE_API_KEY=<your-GOOGLE_API_KEY>
```
For instructions on how to obtain your `GOOGLE_CSE_ID` and `your-GOOGLE_API_KEY`, refer to instructions [here](https://python.langchain.com/docs/integrations/tools/google_search/).

5. Launch SQL agent
```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/TAG-Bench/opea_sql_agent_llama
bash launch_sql_agent.sh california_schools
```
The command above will launch a SQL agent that interacts with the `california_schools` database. We also have a script to run benchmarks on all databases.

## Run the benchmark
1. Generate answers
```bash
cd $WORKDIR/GenAIEval/evals/evaluation/agent_eval/TAG-Bench/run_benchmark
bash run_generate_answer.sh california_schools
```
2. Grade the answers
```bash
bash run_grading.sh california_schools
```
Here we use ragas `answer_correctness` metric to measure the performance. By default, we use `meta-llama/Meta-Llama-3.1-70B-Instruct` as the LLM judge. We use the vllm endpoint launched in the previous [section](#launch-your-sql-agent).

3. Run the benchmark on all databases

If you want to run all the 80 questions spanning all the 5 different databases, run the command below.
```bash
bash run_all_databases.sh
```
This script will iteratively generate answers and grade answers for questions regarding each database.

## Benchmark results
We tested OPEA `sql_agent_llama` on all 80 questions in TAG-Bench. 

Human grading criteria:
- Score 1: exact match with golden answer
- Score 0.7: match with golden answer except for the ordering of the entities
- Score 0.5: missing info, and does not contain info not present in the golden answer
- Score 0: otherwise

|Database|Average human score|Average ragas `answer_correctness`|
|--------|-------------------|----------------------------------|
|california_schools|0.264|0.415|
|codebase_community|0.262|0.404|
|debit_card_specializing|0.75|0.753|
|formula_1|0.389|0.596|
|european_football_2|0.25|0.666|
|**Overall Average (ours)**|0.31 (0.28 if strict exact match)|0.511|
|**Text2SQL (TAG-Bench paper)**|0.17||
|**Human performance (TAG-Bench paper)**|0.55||

We can see that our SQL agent achieved much higher accuracy than Text2SQL, although still lower than human experts.
