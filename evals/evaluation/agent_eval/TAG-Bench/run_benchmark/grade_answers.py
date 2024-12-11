# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os

import pandas as pd
from ragas.metrics import answer_correctness

from evals.metrics.ragas import RagasMetric


def convert_data_format_for_ragas(data):
    output = {
        "question": data["query"].tolist(),
        "answer": data["answer"].tolist(),
        "ground_truth": data["ref_answer"].tolist(),
        "contexts": [["dummy_context"] for _ in range(data["query"].shape[0])],
    }
    return output


def make_list_of_test_cases(data):
    output = []
    for _, row in data.iterrows():
        if pd.isnull(row["ref_answer"]):
            print("Skipping as ground_truth is empty")
            continue
        else:
            output.append(
                {
                    "question": [row["query"]],
                    "answer": [row["answer"]],
                    "ground_truth": [row["ref_answer"]],
                    "contexts": [["dummy_context"]],
                }
            )
    return output

def read_data(args):
    data = pd.read_csv(os.path.join(args.filedir, args.filename))
    if "query" not in data.columns:
        if "Query" in data.columns:
            data.rename(columns={"Query": "query"}, inplace=True)
        else:
            raise ValueError("The query column is missing in the data")
    return data

def grade_answers(args, test_case):
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings

    print("==============getting embeddings==============")
    embeddings = HuggingFaceBgeEmbeddings(model_name=args.embed_model)
    print("==============initiating metric==============")
    metric = RagasMetric(threshold=0.5, metrics=["answer_correctness"], model=args.llm_endpoint, model_name=args.model_name,embeddings=embeddings, use_vllm=args.use_vllm)
    print("==============start grading==============")

    if args.batch_grade:
        metric.measure(test_case)
        return metric.score["answer_correctness"]
    else:
        scores = []
        for case in test_case:
            metric.measure(case)
            # print(metric.score)
            score = metric.score["answer_correctness"][0]
            print(score)
            scores.append(score)
                
            print("-" * 50)
        return scores


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--llm_endpoint", type=str, default="http://localhost:8008")
    parser.add_argument("--model_name", type=str, default="meta-llama/Meta-Llama-3.1-70B-Instruct")
    parser.add_argument("--use_vllm", action="store_true", help="Use VLLM endpoint")
    parser.add_argument("--filedir", type=str, help="Path to the file containing the data")
    parser.add_argument("--filename", type=str, help="Name of the file containing the data")
    parser.add_argument(
        "--batch_grade",
        action="store_true",
        help="Grade the answers in batch and get an aggregated score for the entire dataset",
    )
    args = parser.parse_args()

    data = read_data(args)

    if args.batch_grade:
        test_case = convert_data_format_for_ragas(data)
    else:
        test_case = make_list_of_test_cases(data)
        df = pd.DataFrame(test_case)
        print(df.shape)

    scores = grade_answers(args, test_case)

    # save the scores
    if args.batch_grade:
        print("Aggregated answer correctness score: ", scores)
    else:
        df["answer_correctness"] = scores
        output_file = args.filename.replace(".csv", "_graded.csv")
        df.to_csv(os.path.join(args.filedir, output_file), index=False)
        print("Scores saved to ", os.path.join(args.filedir, output_file))

        print("Average answer correctness score: ", df["answer_correctness"].mean())
