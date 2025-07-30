from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel

from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import (
    build_transformers_prefix_allowed_tokens_fn,
)
import transformers
import json
from .utils_eval import load_huggingface_llm

from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric
)
from .metrics import *
DEEPEVAL_METRIC_FUNC_MAP = {
    context_recall: ContextualRecallMetric,
    context_precision: ContextualPrecisionMetric,
    context_relevancy: ContextualRelevancyMetric,
    answer_relevancy: AnswerRelevancyMetric,
    faithfulness: FaithfulnessMetric,
}

class DeepEvalCustomEvalLLM(DeepEvalBaseLLM):
    def __init__(self, model_name):
        self.model_name = model_name
        self.model, self.tokenizer = load_huggingface_llm(model_name)

    def load_model(self):
        return self.model

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        model = self.load_model()
        pipeline = transformers.pipeline(
            "text-generation",
            model=model,
            tokenizer=self.tokenizer,
            use_cache=True,
            device_map="auto",
            max_new_tokens=1024,
            do_sample=True,
            top_k=5,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        # Create parser required for JSON confinement using lmformatenforcer
        parser = JsonSchemaParser(schema.schema())
        prefix_function = build_transformers_prefix_allowed_tokens_fn(
            pipeline.tokenizer, parser
        )

        # Output and load valid JSON
        output_dict = pipeline(prompt, prefix_allowed_tokens_fn=prefix_function)
        output = output_dict[0]["generated_text"][len(prompt) :]
        try:
            json_result = json.loads(output)
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            with open("debug_output.json", "w") as f:
                f.write(output)
            raise e

        # Return valid JSON object according to the schema DeepEval supplied
        return schema(**json_result)

    # TODO an asynchronous version of generate
    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name
