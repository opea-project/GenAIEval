# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os

import pandas as pd
import requests


def get_test_dataset(args):
    filepath = os.path.join(args.filedir, args.filename)
    if filepath.endswith(".jsonl"):
        df = pd.read_json(filepath, lines=True, convert_dates=False)
    elif filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        raise ValueError("Invalid file format")
    return df


def save_results(output_file, output_list):
    with open(output_file, "w") as f:
        for output in output_list:
            f.write(json.dumps(output))
            f.write("\n")


def save_as_csv(output):
    df = pd.read_json(output, lines=True, convert_dates=False)
    df.to_csv(output.replace(".jsonl", ".csv"), index=False)
    print(f"Saved to {output.replace('.jsonl', '.csv')}")


def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for a specific query."""
    url = os.environ.get("RETRIEVAL_TOOL_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "text": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    print(response)
    if "documents" in response.json():
        docs = response.json()["documents"]
        context = ""
        for i, doc in enumerate(docs):
            if i == 0:
                context = doc
            else:
                context += "\n" + doc
        # print(context)
        return context
    elif "text" in response.json():
        return response.json()["text"]
    elif "reranked_docs" in response.json():
        docs = response.json()["reranked_docs"]
        context = ""
        for i, doc in enumerate(docs):
            if i == 0:
                context = doc["text"]
            else:
                context += "\n" + doc["text"]
        # print(context)
        return context
    else:
        return "Error parsing response from the knowledge base."


PROMPT = """\
### You are a helpful, respectful and honest assistant.
You are given a Question and the time when it was asked in the Pacific Time Zone (PT), referred to as "Query
Time". The query time is formatted as "mm/dd/yyyy, hh:mm:ss PT".
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Refer to the search results to form your answer.
5. Give concise, factual and relevant answers.

### Search results: {context} \n
### Question: {question} \n
### Query Time: {time} \n
### Answer:
"""


def setup_chat_model(args):
    from langchain_openai import ChatOpenAI

    params = {
        "temperature": args.temperature,
        "max_tokens": args.max_new_tokens,
        "top_p": args.top_p,
        "streaming": False,
    }
    openai_endpoint = f"{args.llm_endpoint_url}/v1"
    llm = ChatOpenAI(
        openai_api_key="EMPTY",
        openai_api_base=openai_endpoint,
        model_name=args.model,
        **params,
    )
    return llm


def generate_answer(llm, query, context, time):
    prompt = PROMPT.format(context=context, question=query, time=time)
    response = llm.invoke(prompt)
    return response.content


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filedir", type=str, default="./", help="test file directory")
    parser.add_argument("--filename", type=str, default="query.csv", help="query_list_file")
    parser.add_argument("--output", type=str, default="output.csv", help="query_list_file")
    parser.add_argument("--llm_endpoint_url", type=str, default="http://localhost:8085", help="llm endpoint url")
    parser.add_argument("--model", type=str, default="meta-llama/Meta-Llama-3.1-70B-Instruct", help="model name")
    parser.add_argument("--temperature", type=float, default=0.01, help="temperature")
    parser.add_argument("--max_new_tokens", type=int, default=8192, help="max_new_tokens")
    parser.add_argument("--top_p", type=float, default=0.95, help="top_p")
    args = parser.parse_args()
    print(args)

    df = get_test_dataset(args)
    print(df.shape)

    if not os.path.exists(os.path.dirname(args.output)):
        os.makedirs(os.path.dirname(args.output))

    llm = setup_chat_model(args)

    contexts = []
    output_list = []
    for _, row in df.iterrows():
        q = row["query"]
        t = row["query_time"]
        print("========== Query: ", q)
        context = search_knowledge_base(q)
        print("========== Context:\n", context)
        answer = generate_answer(llm, q, context, t)
        print("========== Answer:\n", answer)
        contexts.append(context)
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
        save_results(args.output, output_list)

    save_as_csv(args.output)
