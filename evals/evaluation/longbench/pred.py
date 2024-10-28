import os
from datasets import load_dataset
import json
from transformers import AutoTokenizer
from tqdm import tqdm
import numpy as np
import random
import argparse
import time
import requests
from requests.exceptions import RequestException

def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', type=str, required=True)
    parser.add_argument('--model_name', type=str, required=True)
    parser.add_argument('--backend', type=str, default="tgi", choices=["tgi","llm"])
    parser.add_argument('--dataset', type=str, help="give dataset name, if not given, will evaluate on all datasets", default=None)
    parser.add_argument('--e', action='store_true', help="Evaluate on LongBench-E")
    parser.add_argument('--max_input_length', type=int, default=2048, help="max input length")
    return parser.parse_args(args)

def get_query(backend, prompt, max_new_length):
    header = {"Content-Type": "application/json"}
    query = {
        "tgi": {"inputs": prompt, "parameters": {"max_new_tokens":max_new_length, "do_sample": False}},
        "llm": {"query": prompt, "max_tokens":max_new_length} 
    }
    return header, query[backend]

def get_pred(data, dataset_name, backend, endpoint, model_name, max_input_length,  max_new_length, prompt_format, out_path):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    for json_obj in tqdm(data):
        prompt = prompt_format.format(**json_obj)

        # truncate to fit max_input_length (we suggest truncate in the middle, since the left and right side may contain crucial instructions)
        tokenized_prompt = tokenizer(prompt, truncation=False, return_tensors="pt").input_ids[0]
        if len(tokenized_prompt) > max_input_length:
            half = int(max_input_length/2)
            prompt = tokenizer.decode(tokenized_prompt[:half], skip_special_tokens=True)+tokenizer.decode(tokenized_prompt[-half:], skip_special_tokens=True)
        
        header, query = get_query(backend, prompt, max_new_length)
        print("query: ", query)
        try:
            start_time = time.perf_counter()
            res = requests.post(endpoint, headers=header, json=query)
            res.raise_for_status()
            res = res.json()
            cost = time.perf_counter() - start_time
        except RequestException as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

        if backend == "tgi":
            result = res["generated_text"] 
        else:
            result = res["text"]
        print("result: ", result)
        with open(out_path, "a", encoding="utf-8") as f:
            json.dump({"pred": result, "answers": json_obj["answers"], "all_classes": json_obj["all_classes"], "length": json_obj["length"]}, f, ensure_ascii=False)
            f.write('\n')

if __name__ == '__main__':
    args = parse_args()
    endpoint = args.endpoint
    model_name = args.model_name
    backend = args.backend
    dataset = args.dataset
    max_input_length=args.max_input_length

    dataset_list = ["narrativeqa", "qasper", "multifieldqa_en", "multifieldqa_zh", "hotpotqa", "2wikimqa", "musique", \
                    "dureader", "gov_report", "qmsum", "multi_news", "vcsum", "trec", "triviaqa", "samsum", "lsht", \
                    "passage_count", "passage_retrieval_en", "passage_retrieval_zh", "lcc", "repobench-p"]
    datasets_e_list = ["qasper", "multifieldqa_en", "hotpotqa", "2wikimqa", "gov_report", "multi_news", \
            "trec", "triviaqa", "samsum", "passage_count", "passage_retrieval_en", "lcc", "repobench-p"]
    if args.e:
        if dataset is not None:
            if dataset in datasets_e_list:
                datasets = [dataset]  
            else:
                raise NotImplementedError(f"{dataset} are not supported in LongBench-e dataset list: {datasets_e_list}")
        else:
            datasets = datasets_e_list
        if not os.path.exists(f"pred_e/{model_name}"):
            os.makedirs(f"pred_e/{model_name}")
    else:
        datasets = [dataset] if dataset is not None else dataset_list
        if not os.path.exists(f"pred/{model_name}"):
            os.makedirs(f"pred/{model_name}")

    for dataset in datasets:
        if args.e:
            out_path = f"pred_e/{model_name}/{dataset}.jsonl"
            data = load_dataset('THUDM/LongBench', f"{dataset}_e", split='test') 
        else:
            out_path = f"pred/{model_name}/{dataset}.jsonl"
            data = load_dataset('THUDM/LongBench', dataset, split='test')
            
        # we design specific prompt format and max generation length for each task, feel free to modify them to optimize model output
        dataset2prompt = json.load(open("config/dataset2prompt.json", "r"))
        dataset2maxlen = json.load(open("config/dataset2maxlen.json", "r"))
        prompt_format = dataset2prompt[dataset]
        max_new_length = dataset2maxlen[dataset]

        data_all = [data_sample for data_sample in data]
        get_pred(data_all, dataset, backend, endpoint, model_name, max_input_length, max_new_length, prompt_format, out_path)