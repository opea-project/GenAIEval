# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from components.constructor.constructor import (
    Constructor, get_ecrag_module_map, COMP_TYPE_MAP, convert_dict_to_pipeline
)
from components.constructor.connector import (
    get_ragqna, reindex_data, get_active_pipeline, update_active_pipeline
)
from components.tuner.tuner import (
    SimpleNodeParserChunkTuner, EmbeddingLanguageTuner, RerankerTopnTuner, NodeParserTypeTuner,
    display_ragqna, input_parser
)
from components.tuner.base import QuestionType, ContentType, RagResult
from components.adaptor.adaptor import Adaptor

from enum import Enum
import json
import yaml
import argparse


def load_qa_list_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        qa_list = []
        for item in data:
            query = item.get("query", "").strip()
            ground_truth = item.get("ground_truth", "").strip()

            if query:
                qa_list.append({"query": query, "ground_truth": ground_truth})

        return qa_list
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in the file '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return []


def load_ragresults_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        qa_list = []
        ragresults = []
        for item in data:
            query = item.get("query", "").strip()
            ground_truth = item.get("ground_truth", "").strip()
            response = item.get("response", "").strip()
            contexts = item.get("contexts", [])

            if query and response:
                qa_list.append({"query": query, "ground_truth": ground_truth})
                ragresults.append(RagResult(query=query, ground_truth=ground_truth, response=response, contexts=contexts))

        return qa_list, ragresults
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in the file '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return [], []


def load_pipeline_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return convert_dict_to_pipeline(data)
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in the file '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        yaml_content = file.read()
    return yaml.safe_load(yaml_content)


class Mode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


def main():
    parser = argparse.ArgumentParser()

    # common
    parser.add_argument("-y", "--rag_module_yaml", default="configs/ecrag.yaml", type=str, #TODO rename
                        help="Path to the YAML file containing all tunable rag configurations.")
    parser.add_argument("-o", "--output_config_json", default="rag_pipeline_out.json", type=str,
                        help="Path to the JSON file containing the list of queries.")

    # online
    parser.add_argument("-q", "--qa_list_json", default="configs/qa_list_sample.json", type=str,
                        help="Path to the JSON file containing the list of queries.")

    # offline
    parser.add_argument("--offline", action="store_true",
                        help="Run offline mode. Default is online mode.")
    parser.add_argument("-c", "--rag_pipeline_json", default="configs/rag_pipeline_sample.json", type=str,
                        help="Path to the JSON file containing the list of queries.")
    parser.add_argument("-r", "--ragresults_json", default="configs/rag_results_sample.json", type=str,
                        help="Path to the JSON file of the ragresult.")

    args = parser.parse_args()

    mode = Mode.OFFLINE if args.offline else Mode.ONLINE
    print(f"Running in {mode.value} mode.")

    constructor = Constructor()
    adaptor = Adaptor(read_yaml(args.rag_module_yaml))
    tuners = [
        EmbeddingLanguageTuner(),
        NodeParserTypeTuner(),
        SimpleNodeParserChunkTuner(),
        RerankerTopnTuner(),
    ]

    if mode == Mode.ONLINE:
        qa_list = load_qa_list_from_json(args.qa_list_json)
    else:
        qa_list, ragresults = load_ragresults_from_json(args.ragresults_json)

    for qa in qa_list:
        query = qa["query"]
        ground_truth = qa["ground_truth"]
        if mode == Mode.ONLINE:
            reindex_data()
        while True:
            if mode == Mode.ONLINE:
                active_pl = get_active_pipeline()
                ragqna = get_ragqna(query)
            else:
                active_pl = load_pipeline_from_json(args.rag_pipeline_json)
                ragqna = next((r for r in ragresults if query == query), None)

            if not ragqna or not active_pl:
                if not ragqna:
                    print(f"Error: RAG result is invalid")
                if not active_pl:
                    print(f"Error: RAG pipeline is invalid")
                break

            constructor.set_pipeline(active_pl)

            print('############################################')
            print(f'Tuning RAG with query: “{query}”')
            display_ragqna(ragqna)
            print(f'Is the response correct or do you want to stop tuning query "{query}"?')
            if ground_truth:
                print(f'\033[90mGround truth for this query is: "{ground_truth}"\033[0m')
            print("y: Completely correct or stop tuning")
            print("n: Not correct and keep tuning")
            valid, correctness = input_parser(QuestionType.BOOL)

            if valid and correctness:
                print("Do you want to check the tuned contexts?")
                valid, confirm = input_parser(QuestionType.BOOL)
                if valid and confirm:
                    display_ragqna(ragqna, ContentType.ALL_CONTEXTS)
                print("Do you want to save the tuned RAG config?")
                valid, save = input_parser(QuestionType.BOOL)
                if valid and save:
                    constructor.save_pipeline_to_json(args.output_config_json)
                print('\n\n')
                break

            adaptor.update_all_module_functions(get_ecrag_module_map(constructor.pl), COMP_TYPE_MAP)
            is_changed = False
            for tuner in tuners:
                # Tuner setup
                module = adaptor.get_module(tuner.node_type, tuner.module_type)
                tuner.update_module(module)
                tuner.init_ragqna(RagResult(**ragqna.model_dump()))

                # Tuning
                if tuner.request_feedback():
                    if tuner.make_suggestions():
                        is_changed = True
                        break

            if not is_changed:
                print("Nothing changed, tune again?")
                valid, cont = input_parser(QuestionType.BOOL)
                if valid and not cont:
                    break
            else:
                if mode == Mode.ONLINE:
                    print("Updating pipeline . . .")
                    pipeline = constructor.export_pipeline()
                    update_active_pipeline(pipeline)
                else:
                    print('\n')
                    constructor.save_pipeline_to_json(args.output_config_json)
                    print(f"\n\nDo you want to continue with previous RAG pipeline file {args.rag_pipeline_json} and rag_results {args.ragresults_json}?")
                    valid, cont = input_parser(QuestionType.BOOL)
                    if valid and not cont:
                        return


if __name__ == "__main__":
    main()
