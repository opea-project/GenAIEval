# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
from collections import defaultdict
from enum import Enum
from time import sleep

import pandas as pd
import yaml
from components.pilot.base import (
    ContextItem,
    ContextType,
    RAGPipeline,
    RAGResult,
    RAGResults,
    RAGStage,
    convert_dict_to_pipeline,
)
from components.pilot.connector import get_active_pipeline, reindex_data
from components.pilot.pilot import Pilot
from components.tuner.adaptor import Adaptor
from components.tuner.tuner import (
    EmbeddingTuner,
    NodeParserTuner,
    RerankerTopnTuner,
    RetrievalTopkRerankerTopnTuner,
    RetrievalTopkTuner,
    SimpleNodeParserChunkTuner,
    input_parser,
)


def load_rag_results_from_csv(file_path):
    rag_results_raw = pd.read_csv(file_path)
    rag_results_dict = defaultdict(lambda: {"gt_contexts": []})

    for _, rag_result in rag_results_raw.iterrows():
        query_id = rag_result.get("query_id")

        if "query" not in rag_results_dict[query_id]:
            rag_results_dict[query_id].update(
                {
                    "query": rag_result.get("query", ""),
                    "ground_truth": rag_result.get("ground_truth", ""),
                }
            )

        gt_context = rag_result.get("gt_context", "")
        file_name = rag_result.get("file_name", "")
        file_name = "" if pd.isna(file_name) else str(file_name)

        if gt_context:
            rag_results_dict[query_id]["gt_contexts"].append(ContextItem(text=gt_context, file_name=file_name))

    rag_results = RAGResults()
    for query_id, data in rag_results_dict.items():
        result = RAGResult(
            query_id=query_id,
            query=data["query"],
            gt_contexts=data["gt_contexts"] if data["gt_contexts"] else None,
            ground_truth=data["ground_truth"],
        )
        result.init_context_idx(ContextType.GT)
        rag_results.add_result(result)

    return rag_results


def load_pipeline_from_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
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
    with open(file_path, "r") as file:
        yaml_content = file.read()
    return yaml.safe_load(yaml_content)


class Mode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"
GREEN = "\033[92m"


def main():
    parser = argparse.ArgumentParser()

    # common
    parser.add_argument(
        "-y",
        "--rag_module_yaml",
        default="configs/ecrag.yaml",
        type=str,
        help="Path to the YAML file containing all tunable rag configurations.",
    )

    # online
    parser.add_argument(
        "-q",
        "--qa_list",
        default="configs/netsec_sample.csv",
        type=str,
        help="Path to the file containing the list of queries.",
    )

    args = parser.parse_args()

    adaptor = Adaptor(read_yaml(args.rag_module_yaml))

    retrieval_tuner_list = [
        EmbeddingTuner(adaptor),
        NodeParserTuner(adaptor),
        SimpleNodeParserChunkTuner(adaptor),
        RetrievalTopkTuner(adaptor),
    ]
    postprocessing_tuner_list = [RerankerTopnTuner(adaptor)]

    rag_results = load_rag_results_from_csv(args.qa_list)
    pilot = Pilot(rag_results_sample=rag_results, hit_threshold=0.9)

    active_pl = RAGPipeline(get_active_pipeline())
    active_pl.regenerate_id()

    pilot.add_rag_pipeline(active_pl)
    pilot.run_curr_pl()

    def ask_stage_satisfaction(stage) -> bool:
        results = pilot.get_curr_results()
        recall_rate = results.metadata.get("recall_rate", {}) if results else {}

        print(f"\n{BOLD}{YELLOW}[STAGE {stage.value}]{RESET} recall_rate is {recall_rate.get(stage)}")
        print("Are you satisfied with this metric?\n 1: Yes and jump to next stage\n 2: No and keep tuning")
        valid, user_input = input_parser(2)
        return valid and user_input == 1

    def run_tuner_stage(tuner_list, stage):
        print(f"\n{BOLD}{YELLOW}🔄 Starting tuning stage: {stage.value}{RESET}")

        for i, tuner in enumerate(tuner_list):
            active_pl = pilot.get_curr_pl()
            adaptor.update_all_module_functions(active_pl)

            pl_list = []
            params_candidates = []

            print("")
            if tuner.request_feedback():
                pl_list, params_candidates = tuner.apply_suggestions()
                for pl, params in zip(pl_list, params_candidates):
                    print(f"Trying to update pipeline to {params}")
                    if pl.id != active_pl.id:
                        pilot.add_rag_pipeline(pl)
                        pilot.curr_pl_id = pl.id
                        reindex_data()
                        pilot.run_curr_pl()
                    print("Metrics of this pipeline:")
                    results = pilot.get_results(pl.id)
                    if results:
                        results.check_metadata()

            pilot.change_best_recall_pl(stage)

            print("")
            for pl, params in zip(pl_list, params_candidates):
                if pl.id == pilot.curr_pl_id:
                    print(f"{BOLD}{GREEN}✅ Changing pipeline to {params} with below metrics:{RESET}")
                    break
            else:
                print(f"{BOLD}{GREEN}↩️ Fallback to previous pipeline with below metrics:{RESET}")
            pilot.get_curr_results().check_metadata()

            # Ask satisfaction only if not the last tuner
            if i < len(tuner_list) - 1:
                if ask_stage_satisfaction(stage):
                    return True
            else:
                print(f"{BOLD}{YELLOW}⏭️ All tuners tried for {stage.value}, proceeding to next stage...{RESET}")

        return False

    def run_full_tuning():
        # Step 1: POSTPROCESSING initial check
        if ask_stage_satisfaction(RAGStage.POSTPROCESSING):
            print("User satisfied with POSTPROCESSING. Exiting.")
            return

        # Step 2: RETRIEVAL
        if ask_stage_satisfaction(RAGStage.RETRIEVAL):
            print("User satisfied with RETRIEVAL. Proceeding to POSTPROCESSING tuning...")
        else:
            _ = run_tuner_stage(retrieval_tuner_list, RAGStage.RETRIEVAL)
            if ask_stage_satisfaction(RAGStage.POSTPROCESSING):
                print("User satisfied with POSTPROCESSING. Exiting.")
                return
            sleep(1)

        # Step 3: POSTPROCESSING tuning
        print("\nStarting POSTPROCESSING tuning...")
        _ = run_tuner_stage(postprocessing_tuner_list, RAGStage.POSTPROCESSING)

        print(f"\n{BOLD}{GREEN}🎯 Tuning complete.{RESET}")

    run_full_tuning()

    print("Metrics of final pipeline:")
    pilot.get_curr_results().check_metadata()

    pilot.save_dicts()


if __name__ == "__main__":
    main()
