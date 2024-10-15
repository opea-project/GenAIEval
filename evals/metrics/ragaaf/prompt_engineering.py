# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from jinja2 import Template

from .prompt_templates import *
from .prompt_templates import NAME2METRIC


class Prompt:
    """Class to customize prompt template using user-defined list of metrics."""

    def __init__(self, metrics, input_fields):
        self.metrics = metrics
        self.input_fields = input_fields
        self.template = self.load_prompt_template()

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

    def load_prompt_template(self):
        content = []
        for metric_name in ["opening_prompt"] + self.metrics:
            metric_instance = NAME2METRIC[metric_name]
            content += (metric_instance.template,)
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

    # step 1 - load prompt using Prompt class
    prompt = Prompt(metrics=metrics, input_fields=input_fields)

    example = {
        "question": "Who is wife of Barak Obama",
        "context": "Michelle Obama, wife of Barak Obama (former President of the United States of America) is an attorney. Barak and Michelle Obama have 2 daughters - Malia and Sasha",
        "answer": "Michelle Obama",
        "ground_truth": "Wife of Barak Obama is Michelle Obama",
    }

    # step 2 - render prompt with given inputs
    rendered_prompt = prompt.render_prompt(
        question=example["question"], answer=example["answer"], context=example["context"]
    )

    print(rendered_prompt)
