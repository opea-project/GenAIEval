# Auto (annotation-free) Evaluation of Retrieval Augmented Generation 

We provide easy-to-use, flexible and annotation-free RAG evaluation tool using LLM-as-a-judge while benefitting from Intel's Gaudi2 AI accelator chips. 

## Overview
### Data 
AutoEval is best suited for Long Form Question Answering (LFQA) datasets where you want to gauge quality and factualness of the answer via LLM's intelligence. Here, you can use benchmarking datasets or bring your own custom datasets. Please make sure to set `field_map` to map AutoEval fields such as "question" to your dataset's corresponding field like "query". 
> Note : To use benchmarking datasets, set argument `data_mode=benchmarking`. Similarly, to use custom datasets, set `data_mode=local`.
### Model
AutoEval can run in 3 evaluation modes - 
1. `evaluation_mode="endpoint"` uses HuggingFace endpoint. 
- We recommend launching a HuggingFace endpoint on Gaudi AI accelerator machines to ensure maximum usage and performance. 
- To launch HF endpoint on Gaudi2, please follow the 2-step instructions here - [tgi-gaudi](https://github.com/huggingface/tgi-gaudi). 
- Pass your endpoint url as `model_name` argument. 
2. `evaluation_mode="openai"` uses openai backend. 
- Please set your `OPEN_API_KEY` and your choice of model as `model_name` argument.
3. `evaluation_mode="local"` uses your local hardware. 
- Set `hf_token` argument and set your favourite open-source model in `model_name` argument. 
- GPU usage will be prioritized after checking it's availability. If GPU is unavailable, the model will run on CPU. 
## Metrics
AutoEval provides 4 metrics - factualness, correctness, relevance and readability. You can also bring your own metrics and grading scales. Don't forget to add your metric to `evaluation_metrics` argument. 
## Generation configuration 
Please set generation parameters as per your requirement in `GENERATION_CONFIG` in `run_eval.py`. 

## Run using HF endpoint 
```python3
dataset = "explodinggradients/ragas-wikiqa"
data_mode = "benchmarking"
field_map = {
            'question' : 'question',
            'answer' : 'generated_with_rag',
            'context' : 'context'
            }

template_dir = "auto_eval_metrics"

evaluation_mode = "endpoint"

host_ip = os.getenv("host_ip", "localhost")
port = os.getenv("port", "<add your port where your endpoint is running>")
model_name = f"http://{host_ip}:{port}"

evaluation_metrics = ["factualness", 
                    "relevance", 
                        "correctness", 
                        "readability"]

evaluator = AutoEvaluate(dataset=dataset,
                        data_mode=data_mode,
                        field_map=field_map,
                        template_dir=template_dir,
                        evaluation_mode=evaluation_mode,
                        model_name=model_name,
                        evaluation_metrics=evaluation_metrics,
                        debug_mode=True)

responses = evaluator.measure()

for response in responses:
    print(response)
```
That's it! For troubleshooting, please submit an issue and we will get right on it. 