# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, Template


class Prompt:
    """Class to customize prompt template using user-defined list of metrics."""

    def __init__(self, metrics, input_fields, prompt_dir):
        self.metrics = metrics
        self.input_fields = input_fields
        self.define_template_paths(prompt_dir)
        self.template = self.load_prompt_template()

    def define_template_paths(self, prompt_dir):
        self.opening_prompt_path = os.path.join(prompt_dir, "opening_prompt.md")
        metric_prompt_names = ["{}_prompt.md".format(metric) for metric in self.metrics]
        local_metric_prompt_paths = [os.path.join("metric_prompt_templates", m) for m in metric_prompt_names]
        self.metric_prompt_paths = [os.path.join(prompt_dir, p) for p in local_metric_prompt_paths]

    def create_grading_format(self):
        grading_format = (
            "You must ALWAYS provide every single one of the scores and reasonings in the following JSON format:"
        )
        grading_format += "\n" + "{" + "\n"
        content = []
        reasoning_prompt = "Reasoning for {}: [your one line step by step reasoning about the {} of the answer]"
        scoring_prompt = "Score for {}: [your score number for the {} of the answer]"
        for metric in self.metrics:
            reasoning = reasoning_prompt.format(metric, metric)
            score = scoring_prompt.format(metric, metric)
            content += (reasoning + "\n" + score,)
        grading_format += "\n\n".join(content)
        grading_format += "\n" + "}"
        return grading_format

    def create_closing_prompt(self):
        closing_prompt = ["Let's begin!"]
        for f in self.input_fields:
            closing_prompt += ("Provided {}:".format(f) + "\n" + "{{" + f + "}}",)
        return "\n\n".join(closing_prompt)

    @staticmethod
    def load_template(template_path):
        dir = os.path.dirname(os.path.abspath(__file__))
        env = Environment(loader=FileSystemLoader(dir))
        return env.get_template(template_path)

    def load_prompt_template(self):
        content = [self.load_template(self.opening_prompt_path).render()]
        for path in self.metric_prompt_paths:
            content += (self.load_template(path).render(),)
        content += (self.create_grading_format(),)
        content += (self.create_closing_prompt(),)
        return Template("\n\n".join(content))

    def render_prompt(self, **kwargs) -> str:
        text = self.template.render(**kwargs)
        return text


if __name__ == "__main__":

    """Here, we test implementation of Prompt class."""

    # step 0 - user input
    metrics = ["factualness", "relevance", "correctness", "readability"]
    input_fields = ["question", "answer", "context"]
    prompt_dir = "./auto_eval_metrics/"

    # step 1 - load jinja2 environment
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

    # step 2 - load prompt using Prompt class
    prompt = Prompt(metrics=metrics, input_fields=input_fields, prompt_dir=prompt_dir)

    example = {
        "question": "Who is wife of Barak Obama",
        "context": "Michelle Obama, wife of Barak Obama (former President of the United States of America) is an attorney. Barak and Michelle Obama have 2 daughters - Malia and Sasha",
        "answer": "Michelle Obama",
        "ground_truth": "Wife of Barak Obama is Michelle Obama",
    }

    rendered_prompt = prompt.render_prompt(
        question=example["question"], answer=example["answer"], context=example["context"]
    )

    print(rendered_prompt)
