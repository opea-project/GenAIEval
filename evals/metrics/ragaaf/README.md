# RAGAAF (RAG assessment - Annotation Free) 

We introduce - RAGAAF, Intel's easy-to-use, flexible, opensource and annotation-free RAG evaluation tool using LLM-as-a-judge while benefitting from Intel's Gaudi2 AI accelator chips. 

## Overview
### Data 
RAGAAF is best suited for Long Form Question Answering (LFQA) datasets where you want to gauge quality and factualness of the answer via LLM's intelligence. Here, you can use benchmarking datasets or bring your own custom datasets. Please make sure to set `field_map` to map AutoEval fields such as "question" to your dataset's corresponding field like "query". 
> Note : To use benchmarking datasets, set argument `data_mode=benchmarking`. Similarly, to use custom datasets, set `data_mode=local`.
### Model
AutoEval can run in 3 evaluation modes - 
1. `evaluation_mode="endpoint"` uses HuggingFace endpoint. 
- We recommend launching a HuggingFace endpoint on Gaudi AI accelerator machines to ensure maximum usage and performance. 
- To launch HF endpoint on Gaudi2, please follow the 2-step instructions here - [tgi-gaudi](https://github.com/huggingface/tgi-gaudi). 
- Pass your endpoint url as `model_name` argument. 
2. `evaluation_mode="openai"` uses openai backend. 
- Please set your `openai_key` and your choice of model as `model_name` argument.
3. `evaluation_mode="local"` uses your local hardware. 
- Set `hf_token` argument and set your favourite open-source model in `model_name` argument. 
- GPU usage will be prioritized after checking it's availability. If GPU is unavailable, the model will run on CPU. 
## Metrics
AutoEval provides 4 metrics - factualness, correctness, relevance and readability. You can also bring your own metrics and grading scales. Don't forget to add your metric to `evaluation_metrics` argument. 
## Generation configuration 
We provide recommended generation parameters after experimenting with different LLMs. If you'd like to edit them to your requirement, please set generation parameters in `GENERATION_CONFIG` in `run_eval.py`. 

## Run using HF endpoint 
```python3
# step 1 : choose your dataset -- local or benchmarking
dataset = "explodinggradients/ragas-wikiqa"
data_mode = "benchmarking"
field_map = {"question": "question", "answer": "generated_with_rag", "context": "context"}

# step 2 - choose your favourite LLM and hardware

# evaluation_mode = "openai"
# model_name = "gpt-4o"
# openai_key = "<add your openai key>"

# evaluation_mode = "endpoint"
# model_name = f"http://{host_ip}:{port}"

evaluation_mode = "local"
model_name = "meta-llama/Llama-3.2-1B-Instruct"
hf_token = "<add your HF token>"

# step 3 - choose metrics of your choice, you can also add custom metrics
evaluation_metrics = ["factualness", "relevance", "correctness", "readability"]

# step 4 - run evaluation
evaluator = AnnotationFreeEvaluate(
    dataset=dataset,
    data_mode=data_mode,
    field_map=field_map,
    evaluation_mode=evaluation_mode,
    model_name=model_name,
    evaluation_metrics=evaluation_metrics,
    # openai_key=openai_key,
    hf_token=hf_token,
    debug_mode=True,
)

responses = evaluator.measure()

for response in responses:
    print(response)
```
That's it! For troubleshooting, please submit an issue and we will get right on it. 
