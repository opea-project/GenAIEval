# Auto (annotation-free) Evaluation of Retrieval Augmented Generation 

We provide easy-to-use, flexible and annotation-free RAG evaluation tool using LLM-as-a-judge while benefitting from Intel's Gaudi2 AI accelator chips. 

## Overview
### Data 
AutoEval is best suited for Long Form Question Answering (LFQA) datasets where you want to gauge quality and factualness of the answer via LLM's intelligence. Here, you can use benchmarking datasets or bring your own custom datasets. Please make sure to set `field_map` to map AutoEval fields such as "question" to your dataset's corresponding field like "query". 
> Note : To use benchmarking datasets, set argument `data_mode=benchmarking`. Similarly, to use custom datasets, set `data_mode=local`.
### Model
AutoEval can run in 3 evaluation modes - 
1. `evaluation_mode=endpoint` uses HuggingFace endpoint. 
- We recommend launching a HuggingFace endpoint on Gaudi AI accelerator machines to ensure maximum usage and performance. 
- To launch HF endpoint on Gaudi2, please follow the 2-step instructions here - [tgi-gaudi](https://github.com/huggingface/tgi-gaudi). 
- Pass your endpoint url as `model_name` argument. 
2. `evaluation_mode=openai` uses openai backend. 
- Please set your `OPEN_API_KEY` and your choice of model as `model_name` argument.
3. `evaluation_mode=local` uses your local hardware. 
- Set `hf_token` argument and set your favourite open-source model in `model_name` argument. 
- GPU usage will be prioritized after checking it's availability. Otherwise the model will run on CPU. 
## Metrics
AutoEval provides 4 metrics - factualness, correctness, relevance and readability. You can also add your own metrics and your own grading scales. Don't forget to add your metric to `evaluation_metrics` argument. 
## Generation configuration 
Please set generation parameters as per your requirement in `GENERATION_CONFIG` in `run_eval.py`. 
## Run 
```bash
python3 run_eval.py --log_path="./exp1.log"
```