# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import ast
import json
import os
import time

import pandas as pd
from dotenv import load_dotenv
from huggingface_hub import login
from jinja2 import Environment, FileSystemLoader

from evals.evaluation.auto_eval.prompt_engineering import Prompt
from evals.evaluation.auto_eval.rag_dataset import RAGDataset
from evals.evaluation.auto_eval.utils.helper import *
from evals.evaluation.auto_eval.utils.model import *


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_data", type=str, default="explodinggradients/ragas-wikiqa", help="path of the input data"
    )
    parser.add_argument(
        "--data_mode", type=str, default="benchmarking", help="mode of data can be local or benchmarking"
    )
    parser.add_argument(
        "--field_map",
        type=dict,
        default={"question": "question", "answer": "generated_with_rag", "context": "context"},
        help="field map that will be used while loading the dataset",
    )
    parser.add_argument("--template_dir", type=str, default="auto_eval_metrics", help="path to dir of prompt templates")
    parser.add_argument("--hf_token", type=str, default="<add your HF token>", help="Please provide your HF token")
    parser.add_argument(
        "--openai_key", type=str, default="<add your OpenAI token>", help="please provide your OpenAI key"
    )
    parser.add_argument(
        "--evaluation_mode", type=str, default="endpoint", help="evaluation mode can be openai / endpoint / local"
    )
    parser.add_argument(
        "--model_name", type=str, default="http://localhost:8085", help="the model to be used for evaluation"
    )
    parser.add_argument(
        "--evaluation_metrics",
        type=list,
        default=["factualness", "relevance", "correctness", "readability"],
        help="metrics to be used for evaluation of RAG",
    )
    parser.add_argument("--log_path", type=str, default="./exp1.log", help="path of the log file")
    args = parser.parse_args()
    return args


def load_template(template_path):
    template = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)))).get_template(
        template_path
    )
    return template


def log_responses(responses, args):
    sep = "\n" + "-" * 100 + "\n"
    text = sep.join(responses)
    with open(args.log_path, "w") as f:
        f.write(text)


class AutoEvaluate:

    def __init__(
        self,
        dataset,
        data_mode,
        field_map,
        template_dir,
        evaluation_mode,
        model_name,
        evaluation_metrics,
        hf_token=None,
        openai_key=None,
        debug_mode=None,
    ):
        self.GENERATION_CONFIG = {
            "openai": {"temperature": 0.1},
            "endpoint": {"max_tokens": 500},
            "local": {"max_new_tokens": 500},
        }
        self.load_env()
        self.data = RAGDataset(dataset=dataset, field_map=field_map, mode=data_mode)
        self.evaluator = self.get_evaluator(evaluation_mode, model_name, openai_key, hf_token)
        self.prompt_template = self.get_template(evaluation_metrics, field_map, template_dir)
        self.debug_mode = debug_mode
        self.generation_config = self.GENERATION_CONFIG[evaluation_mode]

    def load_env(
        self,
    ):
        dot_env_path = os.path.join(os.path.dirname(__file__), ".env")
        print("Loading dot environment from {}".format(dot_env_path))
        load_dotenv(dot_env_path, override=True)

    def get_evaluator(self, evaluation_mode, model_name, openai_key=None, hf_token=None):
        if evaluation_mode == "openai":
            # assert args.model_name in ALLOWED_OPENAI_MODELS, "please provide a openai model from the given list of allowed models"
            print("Using {} openai key".format(openai_key))
            evaluator = OAIEvaluator(openai_key, model_name)
        elif evaluation_mode == "endpoint":
            print("Loading HF endpoint at {}".format(model_name))
            evaluator = EndpointEvaluator(model_name)
        else:
            assert args.evaluation_mode == "local", "evaluation mode must be openai / endpoint / local"
            print("Loading {} model locally".format(model_name))
            login(token=hf_token)
            evaluator = HFEvaluator(args.model_name)
        return evaluator

    def get_template(self, evaluation_metrics, field_map, template_dir):

        return Prompt(metrics=evaluation_metrics, input_fields=field_map, prompt_dir=template_dir).template

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


# if __name__ == "__main__":

#     dataset = "explodinggradients/ragas-wikiqa"
#     data_mode = "benchmarking"
#     field_map = {
#                 'question' : 'question',
#                 'answer' : 'generated_with_rag',
#                 'context' : 'context'
#                 }

#     template_dir = "auto_eval_metrics"

#     evaluation_mode = "endpoint"
#     model_name = "http://localhost:8085"

#     evaluation_metrics = ["factualness",
#                             "relevance",
#                                 "correctness",
#                                 "readability"]

#     evaluator = AutoEvaluate(dataset=dataset,
#                             data_mode=data_mode,
#                             field_map=field_map,
#                             template_dir=template_dir,
#                             evaluation_mode=evaluation_mode,
#                             model_name=model_name,
#                             evaluation_metrics=evaluation_metrics,
#                             debug_mode=True)

#     responses = evaluator.measure()

#     for response in responses:
#         print(response)
#         print("-"*100)
