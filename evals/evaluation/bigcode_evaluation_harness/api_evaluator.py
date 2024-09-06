# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
import warnings

import aiohttp
from bigcode_eval import tasks
from bigcode_eval.evaluator import Evaluator


class APIEvaluator(Evaluator):
    def generate_text(self, task_name, intermediate_generations=None):
        task = tasks.get_task(task_name, self.args)
        dataset = task.get_dataset()
        # if args.limit is None, use all samples
        # if args.limit is used, make sure args.limit_start + args.limit <= len(dataset)

        # TODO: Only support running the entire task in its entirety now,
        #       parameters limit or limit_start will result in inaccurate results.
        n_tasks = min(self.args.limit, len(dataset) - self.args.limit_start) if self.args.limit else len(dataset)
        print(n_tasks)
        # when args.limit is None
        # adjust n_tasks by args.limit_start to prevent out of bounds issues
        if not self.args.limit:
            n_tasks -= self.args.limit_start
        references = [
            task.get_reference(dataset[i]) for i in range(self.args.limit_start, self.args.limit_start + n_tasks)
        ]

        if self.args.check_references:
            if "get_solution" in inspect.signature(task.get_reference).parameters:
                solutions = [
                    [task.get_reference(dataset[i], get_solution=True)]
                    for i in range(self.args.limit_start, self.args.limit_start + n_tasks)
                ]
            else:
                solutions = [[ref] for ref in references]
            return solutions, references

        if intermediate_generations:
            curr_generations = [gen for gen in intermediate_generations if gen]
            n_tasks -= len(curr_generations)

        generations = parallel_generations_by_api(
            task,
            dataset,
            self.accelerator,
            n_tasks=n_tasks,
            args=self.args,
        )

        if len(generations[0]) > self.args.n_samples:
            generations = [l[: self.args.n_samples] for l in generations]
            warnings.warn(
                f"Number of tasks wasn't proportional to number of devices, we removed extra predictions to only keep nsamples={self.args.n_samples}"
            )
        return generations, references


def parallel_generations_by_api(
    task,
    dataset,
    accelerator,
    n_tasks,
    args,
):
    if args.load_generations_path:
        # load generated code
        with open(args.load_generations_path) as fp:
            generations = json.load(fp)
            if accelerator.is_main_process:
                print(
                    f"generations loaded, {n_tasks} selected from {len(generations)} with {len(generations[0])} candidates"
                )
        return generations[:n_tasks]

    if codegen_url := args.codegen_url:
        assert "/codegen" in codegen_url, "Only OPEA codegen compatible APIs are supported"
        import asyncio
        import os

        import requests
        from tqdm.asyncio import tqdm

        async def get_res(prompt):
            headers = {"Content-Type": "application/json"}
            data = {
                "messages": prompt,
                "max_tokens": 2048,
                "stream": False,
                "temperature": args.temperature,
                "top_p": args.top_p,
                "top_k": args.top_k,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(codegen_url, json=data, headers=headers, timeout=600) as response:
                    text = await response.text()
                    return text

        prompts = [task.get_prompt(doc) for doc in dataset]
        awaitables = [get_res(prompt=prompt) for prompt in prompts]
        responses = asyncio.run(tqdm.gather(*awaitables))
        generations = []
        for i, (prompt, response) in enumerate(zip(prompts, responses)):
            texts = [prompt + choice["message"]["content"] for choice in json.loads(response)["choices"]]
            generations.append([task.postprocess_generation(text, i) for text in texts])
        return generations
