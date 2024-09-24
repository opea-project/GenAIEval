# OPEA adaption of ragas (LLM-as-a-judge evaluation of Retrieval Augmented Generation)
OPEA's adaption of [ragas](https://github.com/explodinggradients/ragas) allows you to use [ragas](https://github.com/explodinggradients/ragas) on Intel's Gaudi AI accelerator chips. 

## User data
Please wrap your input data in `datasets.Dataset` class.  
```python3
from datasets import Dataset

example = {
    "question": "Who is wife of Barak Obama",
    "contexts": [
        "Michelle Obama, wife of Barak Obama (former President of the United States of America) is an attorney",
        "Barak and Michelle Obama have 2 daughters - Malia and Sasha",
    ],
    "answer": "Michelle Obama",
    "ground_truth": "Wife of Barak Obama is Michelle Obama",
}
dataset = Dataset.from_list([example])
```

## Launch HuggingFace endpoint on Intel's Gaudi machines
Please follow instructions mentioned in [TGI Gaudi repo](https://github.com/huggingface/tgi-gaudi) with your desired LLM such as `meta-llama/Meta-Llama-3.1-70B-Instruct`. 

## Run OPEA ragas pipeline using your desired list of metrics
```python3
# note - if you wish to use answer relevancy metric, please set the embedding parameter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en-v1.5")

from ragas import RagasMetric

ragas_metric = RagasMetric(threshold=0.5, model="<set your HF endpoint URL>", embeddings=embeddings)
print(ragas_metric.measure(dataset))
```
That's it! 

## Troubleshooting
Please allow few minutes for HuggingFace endpoint to download model weights and load them. Larger models may take few more minutes. For any other issue, please file an issue and we will get back to you. 
