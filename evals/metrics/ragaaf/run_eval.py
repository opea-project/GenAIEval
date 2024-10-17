# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time

from huggingface_hub import login

from .prompt_engineering import Prompt
from .rag_dataset import RAGDataset
from .utils.helper import *
from .utils.model import *


class AnnotationFreeEvaluate:

    def __init__(
        self,
        dataset,
        data_mode,
        field_map,
        evaluation_mode,
        model_name,
        evaluation_metrics,
        examples=None,
        hf_token=None,
        openai_key=None,
        debug_mode=None,
    ):
        self.GENERATION_CONFIG = {
            "openai": {"temperature": 0.1},
            "endpoint": {"max_tokens": 500},
            "local": {"max_new_tokens": 500},
        }
        self.data = RAGDataset(dataset=dataset, field_map=field_map, mode=data_mode, examples=examples)
        self.evaluator = self.get_evaluator(evaluation_mode, model_name, openai_key, hf_token)
        self.prompt_template = self.get_template(evaluation_metrics, field_map)
        self.debug_mode = debug_mode
        self.generation_config = self.GENERATION_CONFIG[evaluation_mode]

    def get_evaluator(self, evaluation_mode, model_name, openai_key=None, hf_token=None):
        if evaluation_mode == "openai":
            print("Using {} openai key".format(openai_key))
            evaluator = OAIEvaluator(openai_key, model_name)
        elif evaluation_mode == "endpoint":
            print("Loading HF endpoint at {}".format(model_name))
            evaluator = EndpointEvaluator(model_name)
        else:
            assert evaluation_mode == "local", "evaluation mode must be openai / endpoint / local"
            print("Loading {} model locally".format(model_name))
            login(token=hf_token, add_to_git_credential=True)
            evaluator = HFEvaluator(model_name)
        return evaluator

    def get_template(self, evaluation_metrics, field_map):
        prompt = Prompt(metrics=evaluation_metrics, input_fields=field_map)
        return prompt.template

    def measure(self):
        n_samples = 1 if self.debug_mode else len(self.data)
        responses = [""] * n_samples
        start = time.time()
        for i in range(n_samples):
            prompt = render_prompt(
                self.prompt_template,
                query=self.data[i]["question"],
                answer=self.data[i]["answer"],
                context=self.data[i]["context"],
            )
            messages = [{"role": "user", "content": prompt}]
            response = self.evaluator.generate(messages, **self.generation_config)
            responses[i] = response
        end = time.time()
        print("Generation of scores and reasoning took {:.2f} seconds for {:,} examples".format(end - start, n_samples))
        return responses


if __name__ == "__main__":

    dataset = "explodinggradients/ragas-wikiqa"
    data_mode = "benchmarking"
    field_map = {"question": "question", "answer": "generated_with_rag", "context": "context"}

    # evaluation_mode = "endpoint"
    # model_name = f"http://{host_ip}:{port}"

    evaluation_mode = "openai"
    openai_key = "<add your openai key>"
    model_name = "gpt-4o"

    evaluation_metrics = ["factualness", "relevance", "correctness", "readability"]

    evaluator = AnnotationFreeEvaluate(
        dataset=dataset,
        data_mode=data_mode,
        field_map=field_map,
        evaluation_mode=evaluation_mode,
        model_name=model_name,
        evaluation_metrics=evaluation_metrics,
        openai_key=openai_key,
        debug_mode=True,
    )

    responses = evaluator.measure()

    for response in responses:
        print(response)
