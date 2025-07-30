# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import csv
import os
import threading
from datetime import datetime

from api_schema import RAGStage
from components.connect_utils import get_active_pipeline, get_ragqna, get_retrieval, load_prompt, update_active_pipeline
from components.pilot.base import ContextItem, ContextType, Metrics, RAGPipeline, RAGResults


def update_rag_pipeline(rag_pipeline: RAGPipeline):
    ecrag_pipeline = rag_pipeline.export_pipeline()
    ret = update_active_pipeline(ecrag_pipeline)
    prompt = rag_pipeline.get_prompt()
    if prompt:
        load_prompt(prompt)
        # TODO load_prompt() error check
    return ret


def get_rag_results(results_out: RAGResults, results_in: RAGResults, hit_threshold, is_retrieval=False):
    if results_in is None:
        return None

    # Update each rag_result in rag_results and add to new instance
    for result in results_in.results:
        query = result.query
        ragqna = None
        if is_retrieval:
            ragqna = get_retrieval(query)
        else:
            ragqna = get_ragqna(query)
        if ragqna is None:
            continue

        # Create a new result object to avoid modifying the input
        new_result = result.copy()
        for key, nodes in ragqna.contexts.items():
            for node in nodes:
                node_node = node.get("node", {})
                metadata = node_node.get("metadata", {})
                possible_file_keys = ["file_name", "filename"]
                file_name = next(
                    (metadata[key] for key in possible_file_keys if key in metadata),
                    None,
                )
                text = node_node.get("text", "")
                context_item = ContextItem(file_name=file_name, text=text)
                if key == "retriever":
                    new_result.add_context(ContextType.RETRIEVAL, context_item)
                else:
                    new_result.add_context(ContextType.POSTPROCESSING, context_item)

        new_result.update_metadata_hits(hit_threshold)
        new_result.set_response(ragqna.response)
        new_result.finished = True
        results_out.add_result(new_result)

    results_out.finished = True


class Pilot:
    rag_pipeline_dict: dict[int, RAGPipeline] = {}
    rag_results_dict: dict[int, RAGResults] = {}
    curr_pl_id: int = None

    rag_results_sample: RAGResults = None
    hit_threshold: float

    base_folder: str
    _run_lock = threading.Lock()
    _run_done_event = threading.Event()

    def __init__(self, rag_results_sample=None, hit_threshold=1):
        self.rag_results_sample = rag_results_sample
        self.hit_threshold = hit_threshold

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_folder = os.path.join(os.getcwd(), f"rag_pilot_{timestamp}")

    def update_rag_results_sample(self, rag_results_sample):
        self.rag_results_sample = rag_results_sample
        return True

    def add_rag_pipeline(self, rag_pipeline):
        id = rag_pipeline.get_id()
        self.rag_pipeline_dict[id] = rag_pipeline
        if not self.curr_pl_id:
            self.curr_pl_id = id

    def set_curr_pl_by_id(self, pl_id):
        if pl_id in self.rag_pipeline_dict:
            curr_rag_pl = self.rag_pipeline_dict[pl_id]
            if update_rag_pipeline(curr_rag_pl) is not None:
                self.curr_pl_id = pl_id
                return True
            else:
                return False
        else:
            return False

    def set_curr_pl(self, rag_pipeline):
        id = rag_pipeline.get_id()
        if id not in self.rag_pipeline_dict:
            self.rag_pipeline_dict[id] = rag_pipeline
        return self.set_curr_pl_by_id(id)

    def add_rag_results(self, pl_id):
        if pl_id not in self.rag_results_dict:
            # Create a new instance of RAGResults
            self.rag_results_dict[pl_id] = RAGResults()

        return self.rag_results_dict[pl_id]

    def clear_rag_result_dict(self):
        self.rag_results_dict = {}

    def _execute_pipeline(self, pipeline, is_retrieval=False):
        if not self.rag_results_sample:
            print("[ERROR] RAG result sample file is not initiated")
            return False

        print("[Pilot] Trying to acquire run lock (non-blocking)...")
        if not self._run_lock.acquire(blocking=False):
            print("[Pilot] Pipeline is already running. Skipping execution.")
            return False

        self._run_done_event.clear()
        try:
            print("[Pilot] Acquired run lock.")
            if self.set_curr_pl(pipeline):

                rag_results = self.add_rag_results(self.curr_pl_id)

                get_rag_results(rag_results, self.rag_results_sample, self.hit_threshold, is_retrieval)

                return True
            return False
        finally:
            print("[Pilot] Releasing run lock and setting done event.")
            self._run_lock.release()
            self._run_done_event.set()

    def run_pipeline(self, rag_pipeline=None, is_retrieval=False):
        pipeline = rag_pipeline or self.get_curr_pl()
        thread = threading.Thread(
            target=self._execute_pipeline,
            args=(pipeline, is_retrieval),
            daemon=True,  # ensures thread exits when the process exits
            name=f"{pipeline.id}"[:15],
        )
        thread.start()
        if thread.ident is None:
            return False
        return "Pipeline {thread.ident} is running"

    def run_pipeline_blocked(self, rag_pipeline=None, is_retrieval=False):
        if not self.rag_results_sample:
            print("[Pilot] Skipping pipeline run — rag_results_sample not set.")
            return False

        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        pipeline = rag_pipeline or self.get_curr_pl()

        print(f"[Pilot][{thread_name}:{thread_id}] Waiting for current pipeline run to complete (if any)...")
        while not self._execute_pipeline(pipeline, is_retrieval):
            self._run_done_event.wait(timeout=0.5)
        print(f"[Pilot][{thread_name}:{thread_id}] Pipeline run completed.")
        return True

    def get_curr_pl(self):
        if self.curr_pl_id:
            return self.rag_pipeline_dict[self.curr_pl_id]
        else:
            pl_raw = get_active_pipeline()
            if pl_raw:
                active_pl = RAGPipeline(pl_raw)
                active_pl.regenerate_id()
                pilot.add_rag_pipeline(active_pl)
                return self.rag_pipeline_dict[self.curr_pl_id]
            else:
                return None

    def restore_curr_pl(self):
        pilot.curr_pl_id = None
        pl_raw = get_active_pipeline()
        if pl_raw:
            active_pl = RAGPipeline(pl_raw)
            active_pl.regenerate_id()
            pilot.add_rag_pipeline(active_pl)
            return self.rag_pipeline_dict[self.curr_pl_id]
        else:
            return None

    def get_curr_pl_id(self):
        if self.curr_pl_id:
            return self.curr_pl_id
        else:
            if self.get_curr_pl():
                return self.curr_pl_id
            else:
                return None

    def get_pl(self, id):
        return self.rag_pipeline_dict[id] if id in self.rag_pipeline_dict else None

    def get_results(self, id):
        return self.rag_results_dict[id] if id in self.rag_results_dict else None

    def get_curr_results(self):
        return self.get_results(self.curr_pl_id)

    def get_results_metrics(self, id):
        return self.rag_results_dict[id].get_metrics() if id in self.rag_results_dict else None

    def update_result_metrics(self, id, query_id, metrics):
        if id in self.rag_results_dict:
            return self.rag_results_dict[id].update_result_metrics(query_id, metrics)
        else:
            return False

    def change_best_recall_pl(self, stage: RAGStage = None):
        if stage is RAGStage.GENERATION:
            print(f"Stage {stage}: Skip change_best_recall_pl()")
            return None

        best_pl_id = None
        best_avg_recall = float("-inf")
        best_total_score = float("-inf")  # tie-breaker metric

        for pl_id, rag_results in self.rag_results_dict.items():
            if not rag_results or not rag_results.metadata:
                continue

            if stage is RAGStage.RETRIEVAL:
                recall_rate = rag_results.get_metric(Metrics.RETRIEVAL_RECALL)
            elif stage is RAGStage.POSTPROCESSING:
                recall_rate = rag_results.get_metric(Metrics.POSTPROCESSING_RECALL)
            else:
                recall_rate = float("-inf")

            total_score = sum(
                v
                for k, v in rag_results.get_metrics().items()
                if k in {metric.value for metric in Metrics} and isinstance(v, (int, float))
            )

            if recall_rate > best_avg_recall or (recall_rate == best_avg_recall and total_score > best_total_score):
                best_avg_recall = recall_rate
                best_total_score = total_score
                best_pl_id = pl_id

        if best_pl_id is not None:
            self.set_curr_pl_by_id(best_pl_id)

        print(f"Stage {stage}: Pipeline is set to {self.get_curr_pl_id()}")
        self.get_curr_results().check_metadata()
        return self.get_curr_pl()

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
        return parent_folder

    def export_config_and_metadata_csv(self, save_path: str):
        rows = []
        fieldnames = ["pipeline_id"]

        for pl_id, pipeline in self.rag_pipeline_dict.items():
            config = pipeline.pl.dict()
            rag_results = self.rag_results_dict.get(pl_id)
            rates = {}

            if rag_results:
                for metric in Metrics:
                    rate = rag_results.get_metric(metric, None)
                    if rate:
                        rates[metric.value] = rate

            for key in config.keys():
                key = f"config_{key}"
                if key not in fieldnames:
                    fieldnames.append(key)

            for recall_key in rates.keys():
                if recall_key not in fieldnames:
                    fieldnames.append(recall_key)

            row = {
                "pipeline_id": pl_id,
                **{f"config_{key}": value for key, value in config.items()},
                **rates,
            }

            rows.append(row)

        # Write to CSV
        with open(save_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(fieldnames))
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


pilot = Pilot()


def init_active_pipeline():
    pl_raw = get_active_pipeline()
    if pl_raw:
        active_pl = RAGPipeline(pl_raw)
        active_pl.regenerate_id()
        pilot.add_rag_pipeline(active_pl)
