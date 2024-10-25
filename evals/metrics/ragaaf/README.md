# RAGAAF (RAG assessment - Annotation Free) 

Intel's RAGAAF toolkit employs opensource LLM-as-a-judge technique on Intel's Gaudi2 AI accelator chips to perform annotation-free evaluation of RAG. 

## Key features 
✨ Annotation Free evaluation (ground truth answers are not required). </br>
🧠 Provides score and reasoning for each metric allowing a deep dive into LLM's thought process. </br>
🤗 Quick access to latest innovations in opensource Large Language Models. </br>
⏩ Seamlessly boost performance using Intel's powerful AI accelerator chips - Gaudi. </br>
✍️ Flexibility to bring your own metrics, grading rubrics and datasets. 

## Run RAGAAF

### 1. Data 
We provide 3 modes for data loading - `benchmarking`, `unit` and `local` to support benchmarking datasets, unit test cases and your custom datasets. 

Let us see how to load a unit test case. 
```python3
# load your dataset
dataset = "unit_data"  # name of the dataset
data_mode = "unit"  # mode for data loading
field_map = {
    "question": "question",
    "answer": "actual_output",
    "context": "contexts",
}  # map your data field such as "actual_output" to RAGAAF field "answer"

# your desired unit test case
question = "What if these shoes don't fit?"
actual_output = "We offer a 30-day full refund at no extra cost."
contexts = [
    "All customers are eligible for a 30 day full refund at no extra cost.",
    "We can only process full refund upto 30 day after the purchase.",
]
examples = [{"question": question, "actual_output": actual_output, "contexts": contexts}]
```
### 2. Launch endpoint on Gaudi 
Please launch an endpoint on Gaudi2 using the most popular LLMs such as `mistralai/Mixtral-8x7B-Instruct-v0.1` by following the 2 step instructions here - [tgi-gaudi](https://github.com/huggingface/tgi-gaudi). 
### 3. Model 
We provide 3 evaluation modes - `endpoint`, `local` (supports CPU and GPU), `openai`. 
```python3
# choose your favourite LLM and hardware
host_ip = os.getenv("host_ip", "localhost")
port = os.getenv("port", "<your port where the endpoint is active>")
evaluation_mode = "endpoint"
model_name = f"http://{host_ip}:{port}"
```
> `local` evaluation mode uses your local hardware (GPU usage is prioritized over CPU when available). Don't forget to set `hf_token` argument and your favourite open-source model in `model_name` argument. </br>
> `openai` evaluation mode uses openai backend. Please set your `openai_key` as argument and your choice of OpenAI model as `model_name` argument.
### 4. Metrics 
```python3
# choose metrics of your choice, you can also add custom metrics
evaluation_metrics = ["factualness", "relevance", "correctness", "readability"]
```
### 5. Evaluation 
```python3
from evals.metrics.ragaaf import AnnotationFreeEvaluate

evaluator = AnnotationFreeEvaluate(
    dataset=dataset,
    examples=examples,
    data_mode=data_mode,
    field_map=field_map,
    evaluation_mode=evaluation_mode,
    model_name=model_name,
    evaluation_metrics=evaluation_metrics,
    # openai_key=openai_key,
    # hf_token=hf_token,
)

responses = evaluator.measure()

for response in responses:
    print(response)
```
## Customizations 
1. If you'd like to change generation parameters, please see in `GENERATION_CONFIG` in `run_eval.py`. 
2. If you'd like to add a new metric, please mimic an existing metric, e.g., `./prompt_templates/correctness.py`
```python3
class MetricName:
    name = "metric_name"
    required_columns = ["answer", "context", "question"]  # the fields your metric needs
    template = """- <metric_name> : <metric_name> measures <note down what you'd like this metric to measure>.
  - Score 1: <add your grading rubric for score 1>.
  - Score 2: <add your grading rubric for score 2>.
  - Score 3: <add your grading rubric for score 3>.
  - Score 4: <add your grading rubric for score 4>.
  - Score 5: <add your grading rubric for score 5>."""
```
