# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
from collections import defaultdict
from enum import Enum
from time import sleep

from components.pilot.base import (
    RAGPipeline,
    Metrics
)
from components.connect_utils import get_active_pipeline, reindex_data, load_pipeline_from_json
from components.utils import read_yaml, load_rag_results_from_csv
from components.pilot.pilot import Pilot
from components.tuner.adaptor import Adaptor
from components.tuner.tuner import (
    EmbeddingTuner,
    NodeParserTuner,
    RerankerTopnTuner,
    RetrievalTopkRerankerTopnTuner,
    RetrievalTopkTuner,
    SimpleNodeParserChunkTuner,
    PromptTuner,
    input_parser,
)
from api_schema import RAGStage

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
    prompt_tuner_list = [PromptTuner(adaptor)]
    rag_results = load_rag_results_from_csv(args.qa_list)
    pilot = Pilot(rag_results_sample=rag_results, hit_threshold=0.9)

    active_pl = RAGPipeline(get_active_pipeline())
    active_pl.regenerate_id()

    pilot.add_rag_pipeline(active_pl)
    pilot.run_pipeline()

    def ask_stage_satisfaction(stage) -> bool:
        rag_results = pilot.get_curr_results()
        if stage is RAGStage.RETRIEVAL:
            recall_rate = rag_results.metadata.get(Metrics.RETRIEVAL_RECALL, None)
        elif stage is RAGStage.POSTPROCESSING:
            recall_rate = rag_results.metadata.get(Metrics.POSTPROCESSING_RECALL, None)
        else:
            recall_rate = None

        print(f"\n{BOLD}{YELLOW}[STAGE {stage.value}]{RESET} recall_rate is {recall_rate}")
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
                    is_prompt_tuning = stage == RAGStage.GENERATION and 'prompt_content' in params
                    if pl.id != active_pl.id:
                        pilot.add_rag_pipeline(pl)
                        pilot.curr_pl_id = pl.id
                        if not is_prompt_tuning:
                            reindex_data()
                        pilot.run_pipeline()
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
            sleep(1)
            if ask_stage_satisfaction(RAGStage.POSTPROCESSING):
                print("User satisfied with POSTPROCESSING. Exiting.")
                return

        # Step 3: POSTPROCESSING tuning
        print("\nStarting POSTPROCESSING tuning...")
        _ = run_tuner_stage(postprocessing_tuner_list, RAGStage.POSTPROCESSING)

        # Step 4: Optional PROMPT tuning
        print("\nStarting PROMPT tuning...")
        _ = run_tuner_stage(prompt_tuner_list, RAGStage.GENERATION)

        print(f"\n{BOLD}{GREEN}🎯 Tuning complete.{RESET}")

    run_full_tuning()

    print("Metrics of final pipeline:")
    pilot.get_curr_results().check_metadata()

    pilot.save_dicts()


if __name__ == "__main__":
    main()
