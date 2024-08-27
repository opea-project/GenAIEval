# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os

import pandas as pd
import requests


def get_test_data(args):
    if args.query_file.endswith(".jsonl"):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith(".csv"):
        df = pd.read_csv(args.query_file)
    return df


def generate_answer(url, prompt):
    proxies = {"http": ""}
    payload = {
        "query": prompt,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    answer = response.json()["text"]
    return answer


def save_results(output_file, output_list):
    with open(output_file, "w") as f:
        for output in output_list:
            f.write(json.dumps(output))
            f.write("\n")


def save_as_csv(output):
    df = pd.read_json(output, lines=True, convert_dates=False)
    df.to_csv(output.replace(".jsonl", ".csv"), index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint_url", type=str, default=None, help="url of the agent QnA system endpoint")
    parser.add_argument("--query_file", type=str, default=None, help="query jsonl file")
    parser.add_argument("--output_file", type=str, default="output.jsonl", help="output jsonl file")
    args = parser.parse_args()

    url = args.endpoint_url

    df = get_test_data(args)
    # df = df.head() # for validation purpose

    output_list = []
    n = 0
    for _, row in df.iterrows():
        q = row["query"]
        t = row["query_time"]
        prompt = "Question: {}\nThe question was asked at: {}".format(q, t)
        print("******Query:\n", prompt)
        print("******Agent is working on the query")
        answer = generate_answer(url, prompt)
        print("******Answer from agent:\n", answer)
        print("=" * 50)
        output_list.append(
            {
                "query": q,
                "query_time": t,
                "ref_answer": row["answer"],
                "answer": answer,
                "question_type": row["question_type"],
                "static_or_dynamic": row["static_or_dynamic"],
            }
        )
        save_results(args.output_file, output_list)
        # n += 1
        # if n > 1:
        #     break
    save_results(args.output_file, output_list)
    save_as_csv(args.output_file)
