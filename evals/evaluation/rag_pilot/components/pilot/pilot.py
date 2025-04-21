# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import csv
import os
from datetime import datetime

from components.pilot.base import ContextItem, ContextType, RAGPipeline, RAGResults, RAGStage
from components.pilot.connector import get_ragqna, update_active_pipeline


def get_rag_results_with_rag_pipeline(rag_pipeline: RAGPipeline, rag_results_sample: RAGResults, hit_threshold):
    # Update rag_pipeline
    ecrag_pipeline = rag_pipeline.export_pipeline()
    update_active_pipeline(ecrag_pipeline)

    # Create a new instance of RAGResults
    new_rag_results = RAGResults()

    # Update each rag_result in rag_results and add to new instance
    for result in rag_results_sample.results:
        query = result.query
        ragqna = get_ragqna(query)

        # Create a new result object to avoid modifying the input
        new_result = result.copy()
        for key, nodes in ragqna.contexts.items():
            for node in nodes:
                context_item = ContextItem(file_name=node["node"]["metadata"]["file_name"], text=node["node"]["text"])
                if key == "retriever":
                    new_result.add_context(ContextType.RETRIEVAL, context_item)
                else:
                    new_result.add_context(ContextType.POSTPROCESSING, context_item)
        new_result.update_metadata_hits(hit_threshold)
        new_result.set_response(ragqna.response)
        new_rag_results.add_result(new_result)

    return new_rag_results


class Pilot:
    rag_pipeline_dict: dict[int, RAGPipeline] = {}
    rag_results_dict: dict[int, RAGResults] = {}
    curr_pl_id: int = None

    rag_results_sample: RAGResults
    hit_threshold: float

    base_folder: str

    def __init__(self, rag_results_sample, hit_threshold=1):
        self.rag_results_sample = rag_results_sample
        self.hit_threshold = hit_threshold

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_folder = os.path.join(os.getcwd(), f"rag_pilot_{timestamp}")

    def add_rag_pipeline(self, rag_pipeline):
        id = rag_pipeline.id
        self.rag_pipeline_dict[id] = rag_pipeline
        if not self.curr_pl_id:
            self.curr_pl_id = id

    def add_rag_results(self, pl_id, rag_results):
        self.rag_results_dict[pl_id] = rag_results

    def run_curr_pl(self):
        curr_rag_pl = self.rag_pipeline_dict[self.curr_pl_id]
        rag_results = get_rag_results_with_rag_pipeline(curr_rag_pl, self.rag_results_sample, self.hit_threshold)
        self.add_rag_results(self.curr_pl_id, rag_results)

    def get_curr_pl(self):
        return self.rag_pipeline_dict[self.curr_pl_id]

    def get_results(self, id):
        return self.rag_results_dict[id] if id in self.rag_results_dict else None

    def get_curr_results(self):
        return self.get_results(self.curr_pl_id)

    def change_best_recall_pl(self, stage: RAGStage = None):
        best_pl_id = None
        best_avg_recall = float("-inf")

        for pl_id, rag_results in self.rag_results_dict.items():
            if not rag_results or not rag_results.metadata:
                continue

            recall_rate_dict = rag_results.metadata.get("recall_rate", {})
            if stage in [RAGStage.RETRIEVAL, RAGStage.POSTPROCESSING]:
                recall_rate = recall_rate_dict.get(stage, float("-inf"))
            else:
                recall_rate = float("-inf")

            if recall_rate > best_avg_recall:
                best_avg_recall = recall_rate
                best_pl_id = pl_id

        if best_pl_id is not None:
            self.curr_pl_id = best_pl_id

    def save_dicts(self):
        parent_folder = self.base_folder
        os.makedirs(parent_folder, exist_ok=True)

        for key, pipeline in self.rag_pipeline_dict.items():
            subfolder = os.path.join(parent_folder, f"entry_{key}")
            os.makedirs(subfolder, exist_ok=True)

            pipeline_path = os.path.join(subfolder, "pipeline.json")
            pipeline.save_to_json(save_path=pipeline_path)

            rag_results = self.rag_results_dict.get(key)
            if rag_results:
                rag_results.save_to_json(os.path.join(subfolder, "rag_results.json"))
                rag_results.save_to_csv(subfolder)

        self.get_curr_pl().save_to_json(save_path=f"{parent_folder}/curr_pipeline.json")

        curr_results = self.get_curr_results()
        if curr_results:
            curr_results.save_to_json(os.path.join(parent_folder, "curr_rag_results.json"))
            curr_results.save_to_csv(parent_folder)

        self.export_config_and_metadata_csv(save_path=f"{parent_folder}/summary.csv")
        print(f"Saved RAG pipeline and results to {parent_folder}")

    def export_config_and_metadata_csv(self, save_path: str):
        rows = []
        fieldnames = ["pipeline_id"]

        for pl_id, pipeline in self.rag_pipeline_dict.items():
            config = pipeline.pl.dict()
            rag_results = self.rag_results_dict.get(pl_id)
            recall_rates = {}

            if rag_results:
                recall_rate = rag_results.metadata.get("recall_rate", {})
                retrieval_recall_rate = recall_rate.get(ContextType.RETRIEVAL, None)
                postprocessing_recall_rate = recall_rate.get(ContextType.POSTPROCESSING, None)

                if retrieval_recall_rate is not None:
                    recall_rates["retrieval_recall_rate"] = retrieval_recall_rate
                if postprocessing_recall_rate is not None:
                    recall_rates["postprocessing_recall_rate"] = postprocessing_recall_rate

            for key in config.keys():
                key = f"config_{key}"
                if key not in fieldnames:
                    fieldnames.append(key)

            for recall_key in recall_rates.keys():
                if recall_key not in fieldnames:
                    fieldnames.append(recall_key)

            row = {
                "pipeline_id": pl_id,
                **{f"config_{key}": value for key, value in config.items()},
                **recall_rates,  # Add recall rates to the row
            }

            rows.append(row)

        # Write to CSV
        with open(save_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(fieldnames))
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
