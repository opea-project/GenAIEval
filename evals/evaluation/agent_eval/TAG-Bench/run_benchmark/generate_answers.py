# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os

import pandas as pd
import requests


def generate_answer_agent_api(url, prompt):
    proxies = {"http": ""}
    payload = {"messages": prompt, "stream": False}
    response = requests.post(url, json=payload, proxies=proxies)
    answer = response.json()["text"]
    return answer


def save_json_lines(json_lines, args):
    outfile = f"sql_agent_{args.db_name}_results.json"
    output = os.path.join(args.output_dir, outfile)
    with open(output, "w") as f:
        for line in json_lines:
            f.write(str(line) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_file", type=str)
    parser.add_argument("--output_dir", type=str)
    parser.add_argument("--output_file", type=str)
    parser.add_argument("--db_name", type=str)
    parser.add_argument("--port", type=str, default="9095")
    args = parser.parse_args()

    df = pd.read_csv(args.query_file)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    ip_address = os.getenv("host_ip", "localhost")
    port = args.port
    url = f"http://{ip_address}:{port}/v1/chat/completions"

    json_lines = []
    answers = []
    for _, row in df.iterrows():
        query = row["Query"]
        ref_answer = row["Answer"]
        print("******Query:\n", query)
        res = generate_answer_agent_api(url, query)
        answers.append(res)
        print("******Answer:\n", res)
        json_lines.append({"query": query, "ref_answer": ref_answer, "answer": res})
        save_json_lines(json_lines, args)
        print("=" * 20)

    df.rename(columns={"Answer": "ref_answer", "Query": "query"}, inplace=True)
    df["answer"] = answers
    df.to_csv(os.path.join(args.output_dir, args.output_file), index=False)
