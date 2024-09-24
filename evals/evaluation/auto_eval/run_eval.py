import argparse
import ast
from dataset import RAGDataset
from dotenv import load_dotenv
from huggingface_hub import login
from jinja2 import Environment, FileSystemLoader
import json
import os
import pandas as pd
from prompt_engineering import Prompt
import time 
from utils.model import *
from utils.helper import *

GENERATION_CONFIG = {
    "openai" : {"temperature" : 0.1},
    "endpoint" : {"max_new_tokens" : 500},
    "local" : {"max_new_tokens" : 500}
}

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_data", type=str, 
        default="explodinggradients/ragas-wikiqa", 
        help="path of the input data"
    )
    parser.add_argument(
        "--data_mode", type=str, 
        default="benchmarking", 
        help="mode of data can be local or benchmarking"
    )
    parser.add_argument(
        "--field_map", type=dict, 
        default={'question' : 'question','answer' : 'generated_with_rag','context' : 'context'}, 
        help="field map that will be used while loading the dataset"
    )
    parser.add_argument(
        "--template_dir", type=str, default="auto_eval_metrics", 
        help="path to dir of prompt templates"
    )
    parser.add_argument(
        "--hf_token", type=str, default="<add your HF token>", 
        help="Please provide your HF token"
    )
    parser.add_argument(
        "--openai_key", type=str, 
        default="add your OpenAI token", 
        help="please provide your OpenAI key"
    )
    parser.add_argument(
        "--evaluation_mode", type=str, 
        default="openai", 
        help="evaluation mode can be openai / endpoint / local"
    )
    parser.add_argument(
        "--model_name", type=str, 
        default="gpt-4o", 
        help="the model to be used for evaluation"
    )
    parser.add_argument(
        "--evaluation_metrics", type=list, 
        default=["factualness", "relevance", "correctness", "readability"], 
        help="metrics to be used for evaluation of RAG"
    )
    parser.add_argument(
        "--log_path", type=str, default="./exp1.log", 
        help="path of the log file"
    )
    args = parser.parse_args()
    return args


def load_template(template_path):
    template = Environment(
                    loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)))
    ).get_template(template_path)
    return template 


def generate(evaluator, data, template, generation_config, args):
    responses = []
    for sample in data:
        print(sample['question'])
        prompt = render_prompt(template, query=sample['question'], answer=sample['answer'], context=sample['context'])
        messages = [{"role": "user", "content": prompt}]
        response = evaluator.generate(messages, **generation_config)
        print(response)
        responses.append(response)
        print("-"*100)
        break
    return responses 


def log_responses(responses, args):
    sep = '\n' + '-'*100 + '\n'
    text = sep.join(responses)
    with open(args.log_path, 'w') as f:
        f.write(text)


if __name__ == "__main__":

    very_start = time.time()

    # step 1 : load dot environment 
    dot_env_path = os.path.join(os.path.dirname(__file__), ".env")
    print("Loading dot environment from {}".format(dot_env_path))
    load_dotenv(dot_env_path, override=True)
    
    # step 2 : validate and load input args 
    args = get_args()

    # step 3 : load dataset
    data = RAGDataset(dataset=args.input_data, 
                    field_map=args.field_map, 
                    mode=args.data_mode)

    # step 4 : load LLM
    if args.evaluation_mode == "openai":
        # assert args.model_name in ALLOWED_OPENAI_MODELS, "please provide a openai model from the given list of allowed models"
        print("Using {} openai key".format(args.openai_key))
        evaluator = OAIEvaluator(args.openai_key, args.model_name)
    elif args.evaluation_mode == "endpoint":
        print("Loading HF endpoint at {}".format(args.model_name))
        evaluator = EndpointEvaluator(args.model_name)
    else:
        assert args.evaluation_mode == "local", "evaluation mode must be openai / endpoint / local"
        print("Loading {} model locally".format(args.model_name))
        login(token=args.hf_token)
        evaluator = HFEvaluator(args.model_name)

    # step 5 : load prompt
    prompt = Prompt(metrics=args.evaluation_metrics, input_fields=args.field_map, prompt_dir=args.template_dir)
    prompt_template = prompt.template

    # step 6 : start scoring
    generation_config = GENERATION_CONFIG[args.evaluation_mode]
    tic = time.time()
    responses = generate(evaluator, data, prompt_template, generation_config, args)
    toc = time.time()
    print("Generation time for {} examples = {:.2f} seconds".format(len(data), toc - tic))
    log_responses(args=args, responses=responses)

    print(f"this script took {time.time() - very_start}s.")
    