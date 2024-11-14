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
        output.append(
            {
                "question": [row["query"]],
                "answer": [row["answer"]],
                "ground_truth": [row["ref_answer"]],
                "contexts": [["dummy_context"]],
            }
        )
    return output


def grade_answers(args, test_case):
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings

    print("==============getting embeddings==============")
    embeddings = HuggingFaceBgeEmbeddings(model_name=args.embed_model)
    print("==============initiating metric==============")
    metric = RagasMetric(threshold=0.5, metrics=["answer_correctness"], model=args.llm_endpoint, embeddings=embeddings)
    print("==============start grading==============")

    if args.batch_grade:
        metric.measure(test_case)
        return metric.score["answer_correctness"]
    else:
        scores = []
        for case in test_case:
            metric.measure(case)
            scores.append(metric.score["answer_correctness"][0])
            print(metric.score["answer_correctness"][0])
            print("-" * 50)
        return scores


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--llm_endpoint", type=str, default="http://localhost:8008")
    parser.add_argument("--filedir", type=str, help="Path to the file containing the data")
    parser.add_argument("--filename", type=str, help="Name of the file containing the data")
    parser.add_argument(
        "--batch_grade",
        action="store_true",
        help="Grade the answers in batch and get an aggregated score for the entire dataset",
    )
    args = parser.parse_args()

    data = pd.read_csv(os.path.join(args.filedir, args.filename))

    if args.batch_grade:
        test_case = convert_data_format_for_ragas(data)
    else:
        test_case = make_list_of_test_cases(data)

    # print(test_case)

    scores = grade_answers(args, test_case)
    print(scores)

    # save the scores
    if args.batch_grade:
        print("Aggregated answer correctness score: ", scores)
    else:
        data["answer_correctness"] = scores
        output_file = args.filename.replace(".csv", "_graded.csv") 
        data.to_csv(os.path.join(args.filedir, output_file), index=False)
        print("Scores saved to ", os.path.join(args.filedir, output_file))

        print("Average answer correctness score: ", data["answer_correctness"].mean())
