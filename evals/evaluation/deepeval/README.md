
DeepEval is a simple-to-use, open-source LLM evaluation framework, for evaluating large-language model systems. It is similar to Pytest but specialized for unit testing LLM outputs. DeepEval incorporates the latest research to evaluate LLM outputs based on metrics such as G-Eval, hallucination, answer relevancy, RAGAS, etc., which uses LLMs and various other NLP models that runs locally on your machine for evaluation.

We customize models to support more local LLMs services for the evaluation of metrics such as hallucination, answer relevancy, etc.

# 🚀 QuickStart


## Installation

```
pip install ../../../requirements.txt
```

## Launch Service of LLM-as-a-Judge

To setup a LLM model, we can use [tgi-gaudi](https://github.com/huggingface/tgi-gaudi) to launch a service. For example, the follow command is to setup the [mistralai/Mixtral-8x7B-Instruct-v0.1](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) model on 2 Gaudi2 cards:

```
# please set your llm_port and hf_token
docker run -p {your_llm_port}:80 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e HF_TOKEN={your_hf_token} -e PREFILL_BATCH_BUCKET_SIZE=1 -e BATCH_BUCKET_SIZE=8 --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:2.0.5 --model-id mistralai/Mixtral-8x7B-Instruct-v0.1 --max-input-tokens 2048 --max-total-tokens 4096 --sharded true --num-shard 2 --max-batch-total-tokens 65536 --max-batch-prefill-tokens 2048
```

## Writing your first test case

```python
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


def test_case():
    from evals.evaluation.deepeval.models.endpoint_models import TGIEndpointModel

    endpoint = TGIEndpointModel(model="http://localhost:{your_llm_port}/generate")

    answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.5, model=endpoint)
    test_case = LLMTestCase(
        input="What if these shoes don't fit?",
        # Replace this with the actual output from your LLM application
        actual_output="We offer a 30-day full refund at no extra costs.",
        retrieval_context=["All customers are eligible for a 30 day full refund at no extra costs."],
    )
    assert_test(test_case, [answer_relevancy_metric])
```

## Acknowledgements

The evaluation inherits from [deepeval](https://github.com/confident-ai/deepeval) repo. Thank for the founders of Confident AI.
