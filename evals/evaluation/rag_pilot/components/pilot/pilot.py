# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import csv
import os
from datetime import datetime
import threading
from typing import List, Optional, Tuple

from components.pilot.pipeline import Pipeline
from components.pilot.base import ContextItem, ContextType, ContextGT
from components.pilot.result import RAGResults, Metrics
from components.tuner.tunermgr import TunerMgr
from components.adaptor.adaptor import AdaptorBase

from api_schema import RAGStage, GroundTruth, GroundTruthContextSuggestion, MatchSettings,PilotSettings
from components.annotation.annotator import annotator
from components.annotation.schemas import AnnotationRequest
from components.utils import load_rag_results_from_gt_match_results

class Pilot:
    rag_pipeline_dict: dict[int, Pipeline] = {}
    rag_results_dict: dict[int, RAGResults] = {}
    curr_pl_id: int = None

    target_query_gt: RAGResults = None
    hit_threshold: float
    enable_fuzzy: bool = False
    confidence_topn: int = 5
    gt_annotate_infos: List[GroundTruth] = None
    use_annotation: bool = False
    pilot_settings: PilotSettings = None
    base_folder: str
    _run_lock = threading.Lock()
    _run_done_event = threading.Event()

    def __init__(self, target_query_gt=None, hit_threshold=0.8):
        self.target_query_gt = target_query_gt
        self.hit_threshold = hit_threshold

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_folder = os.path.join(os.getcwd(), f"rag_pilot_{timestamp}")
        self.tuner_mgr = TunerMgr()

    def add_adaptor(self, adaptor: AdaptorBase):
        self.adaptor = adaptor

    def update_target_query_gt(self, target_query_gt):
        self.target_query_gt = target_query_gt
        return True

    def clear_target_query_gt(self):
        self.target_query_gt = None

    def set_gt_annotate_infos(self, gt_annotate_infos):
        self.gt_annotate_infos = gt_annotate_infos
        self.use_annotation = True
        print(f"[Pilot] GT annotation info set with {len(gt_annotate_infos)} queries")
        return True

    def set_pilot_settings(self, settings: PilotSettings):
        endpoint = getattr(settings, 'target_endpoint', None)
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("target_endpoint must be a non-empty string.")

        parts = endpoint.split(':', 1)
        host = parts[0].strip()
        port = parts[1].strip() if len(parts) > 1 and parts[1].strip() else '16010'

        if not host:
            raise ValueError("target_endpoint must include a valid host.")
        if not port.isdigit():
            raise ValueError("port must be a number.")

        normalized = f"{host}:{port}"
        self.adaptor.set_server_addr(f"http://{normalized}")
        self.pilot_settings = PilotSettings(target_endpoint=normalized)
        return True

    def get_gt_annotate_infos(self):
        return self.gt_annotate_infos

    def clear_gt_annotate_caches(self):
        self.gt_annotate_infos = None
        annotator.clear_caches()

    def update_gt_annotate_infos(self, gt_annotate_infos):
        if self.gt_annotate_infos is None:
            self.set_gt_annotate_infos(gt_annotate_infos)
            return True

        existing_by_query = {gt.query_id: gt for gt in self.gt_annotate_infos}
        for incoming in gt_annotate_infos:
            qid = incoming.query_id
            if qid not in existing_by_query:
                self.gt_annotate_infos.append(incoming)
                continue

            existing = existing_by_query[qid]
            # Map existing contexts by context_id for O(1) replace
            existing_ctx_index = {ctx.context_id: idx for idx, ctx in enumerate(existing.contexts)}
            for ctx in incoming.contexts:
                if ctx.context_id in existing_ctx_index:
                    idx = existing_ctx_index[ctx.context_id]
                    existing.contexts[idx] = ctx
                else:
                    existing.contexts.append(ctx)
            if incoming.answer is not None:
                existing.answer = incoming.answer

        print(f"[Pilot] Updated GT annotation infos in pilot.")
        return True

    def get_suggested_query_ids(self) -> List[int]:
        if not self.gt_annotate_infos:
            return []
        suggested_ids = [
            gt.query_id
            for gt in self.gt_annotate_infos
            if gt.contexts and any(getattr(ctx, 'suggestions', None) for ctx in gt.contexts)
        ]
        return suggested_ids

    def process_annotation_batch(self, new_gt_annotate_infos: List[GroundTruth], clear_cache: bool = False ) -> RAGResults:
        if clear_cache:
            annotator.clear_caches()

        for gt_data in new_gt_annotate_infos:
            query_id = gt_data.query_id
            query = gt_data.query
            contexts = gt_data.contexts

            if not query_id or not query or not contexts:
                raise ValueError(f"Missing required fields in gt_data")

            if not isinstance(contexts, list) or not contexts:
                raise ValueError(f"GT contexts must be a non-empty list for query_id {query_id}")

            for context in contexts:
                # Validate context fields
                if not context.filename or not context.text:
                    raise ValueError(
                        f"Missing required field 'filename' or 'text' in GT context for query_id {query_id}")

                # Create annotation request
                annotation_request = AnnotationRequest(
                    query_id=query_id,
                    query=query,
                    context_id=context.context_id,
                    gt_file_name=context.filename,
                    gt_text_content=context.text,
                    gt_section=context.section,
                    gt_pages=context.pages,
                    gt_metadata=getattr(context, 'metadata', None),
                    similarity_threshold=self.hit_threshold,
                    enable_fuzzy=self.enable_fuzzy,
                    confidence_topn=self.confidence_topn
                )

                # Process annotation
                annotation_response = annotator.annotate(annotation_request)
                success = annotation_response.success
                # Locate corresponding context entry once per annotation
                target_ctx_entry = None
                for gt_entry in self.gt_annotate_infos:
                    if gt_entry.query_id == query_id:
                        for ctx_entry in gt_entry.contexts:
                            if ctx_entry.context_id == context.context_id:
                                target_ctx_entry = ctx_entry
                                break
                        break

                if success:
                    # Clear any previous suggestions if annotation succeeded
                    if target_ctx_entry is not None:
                        target_ctx_entry.suggestions = []
                else:
                    suggestions = annotation_response.suggestion_items
                    if suggestions and target_ctx_entry is not None:
                        target_ctx_entry.suggestions = [
                            GroundTruthContextSuggestion(**s.model_dump(exclude_unset=True))
                            for s in suggestions
                        ]

        # Get all matched results and convert to RAG results
        all_matched_results = annotator.get_all_match_results()
        rag_results = None
        if all_matched_results:
            gt_match_results_list = list(all_matched_results.values())
            rag_results = load_rag_results_from_gt_match_results(gt_match_results_list)
        return rag_results

    def re_annotate_gt_results(self, rag_results: RAGResults):
        print("[Pilot] Re-annotate RAG results using stored GT annotation info after parameter changes")
        if not self.use_annotation or not self.gt_annotate_infos:
            print("[Pilot] No annotation info available, skipping re-annotation")
            return rag_results

        try:
            print(
                f"[Pilot] Starting re-annotation for {len(self.gt_annotate_infos)} queries")

            # Use the shared annotation processing method
            annotated_rag_results = self.process_annotation_batch(self.gt_annotate_infos, clear_cache=True)

            if annotated_rag_results and annotated_rag_results.results:
                print(f"[Pilot] Re-annotation completed.")
                return annotated_rag_results
            else:
                print("[Pilot] No results from re-annotation, returning original")
                return rag_results

        except Exception as e:
            print(f"[Pilot] Error during re-annotation: {e}")
            return rag_results

    def add_rag_pipeline(self, rag_pipeline):
        id = rag_pipeline.get_id()
        self.rag_pipeline_dict[id] = rag_pipeline
        if not self.curr_pl_id:
            self.curr_pl_id = id

    def set_curr_pl_by_id(self, pl_id):
        if self.curr_pl_id == pl_id:
            return True
        if pl_id in self.rag_pipeline_dict:
            self.curr_pl_id = pl_id
            curr_rag_pl = self.rag_pipeline_dict[pl_id]
            self.adaptor.apply_pipeline(curr_rag_pl)
            return True
        else:
            return False

    def set_curr_pl(self, rag_pipeline):
        id = rag_pipeline.get_id()
        if id not in self.rag_pipeline_dict:
            self.rag_pipeline_dict[id] = rag_pipeline
        return self.set_curr_pl_by_id(id)

    def get_rag_results(self, pl_id):
        if pl_id not in self.rag_results_dict:
            # Create a new instance of RAGResults
            self.rag_results_dict[pl_id] = RAGResults()

        return self.rag_results_dict[pl_id]

    def clear_rag_result_dict(self):
        self.rag_results_dict = {}

    # TODO: need to refine
    def create_result(self, target, ragqna):
        new_result = target.copy()
        for key, nodes in ragqna.contexts.items():
            for node in nodes:
                node_node = node.get("node", {})
                node_id = node_node.get('id_')
                metadata = node_node.get("metadata", {})
                possible_file_keys = ["file_name", "filename", "docnm_kwd"]
                file_name = next(
                    (metadata[key] for key in possible_file_keys if key in metadata),
                    None,
                )
                text = node_node.get("text", "")
                # TODO: need to fix
                # Support KBadmin node structure
                if text == "":
                    if "text_resource" in node_node:
                        text = node_node["text_resource"]["text"]
                context_item = ContextItem(file_name=file_name, text=text, node_id=node_id)
                if key == "retriever":
                    new_result.add_context(ContextType.RETRIEVAL, context_item)
                else:
                    new_result.add_context(ContextType.POSTPROCESSING, context_item)

        new_result.update_metadata_hits(self.hit_threshold)
        new_result.set_response(ragqna.response)
        new_result.finished = True
        return new_result

    def _execute_pipeline(self, pipeline, is_retrieval=False):
        print("[Pilot] Trying to acquire run lock (non-blocking)...")
        if not self._run_lock.acquire(blocking=False):
            print("[Pilot] Pipeline is already running. Skipping execution.")
            return False

        self._run_done_event.clear()
        try:
            print("[Pilot] Acquired run lock.")
            if self.set_curr_pl(pipeline):

                print(f"[Pilot] Configuring pipeline id: {pipeline.id}")
                rag_results = self.get_rag_results(self.curr_pl_id)

                # Re-annotate if we have stored GT annotation info and this is a parameter change
                if self.use_annotation and self.gt_annotate_infos:
                    print("[Pilot] Re-annotating RAG results after parameter changes...")
                    annotated_gt_results = self.re_annotate_gt_results(rag_results)
                    if annotated_gt_results:
                        # Update pilot.rag_results_sample with newly annotated results
                        self.update_target_query_gt(annotated_gt_results)
                        print("[Pilot] Updated rag_results_sample with re-annotated data")

                for target in self.target_query_gt.results:
                    query = target.query
                    ragqna = None
                    # TODO: Generalize the operations
                    if is_retrieval:
                        ragqna = self.adaptor.get_retrieval(query)
                    else:
                        ragqna = self.adaptor.get_ragqna(query)
                    if ragqna is None:
                        continue

                    new_result = self.create_result(target, ragqna)
                    rag_results.add_result(new_result)

                rag_results.finished = True

                return True
            return False
        finally:
            print("[Pilot] Releasing run lock and setting done event.")
            self._run_lock.release()
            self._run_done_event.set()

    def run_pipeline(self, rag_pipeline=None, is_retrieval=False):
        if not self.target_query_gt:
            print("[ERROR] RAG result sample file is not initiated")
            return False

        pipeline = rag_pipeline or self.get_curr_pl()
        if not pipeline:
            print("[ERROR] Pipeline not activated")
            return False
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
        if not self.target_query_gt:
            print("[Pilot] Skipping pipeline run — target_query_gt not set.")
            return False

        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        pipeline = rag_pipeline or self.get_curr_pl()
        if not pipeline:
            print("[ERROR] Pipeline not activated")
            return False

        print(f"[Pilot][{thread_name}:{thread_id}] Waiting for current pipeline run to complete (if any)...")
        while not self._execute_pipeline(pipeline, is_retrieval):
            self._run_done_event.wait(timeout=0.5)
        print(f"[Pilot][{thread_name}:{thread_id}] Pipeline run completed.")
        return True

    def get_curr_pl(self):
        if not self.curr_pl_id:
            active_pl = self.adaptor.get_active_pipeline()
            if active_pl:
                self.curr_pl_id = active_pl.get_id()
                self.add_rag_pipeline(active_pl)
            else:
                return None
        if self.curr_pl_id not in self.rag_pipeline_dict:
            self.add_rag_pipeline(active_pl)
        return self.rag_pipeline_dict[self.curr_pl_id]

    def reconcil_curr_pl(self):
        active_pl = self.adaptor.get_active_pipeline()
        print(active_pl.to_dict())
        self.add_rag_pipeline(active_pl)
        self.curr_pl_id = active_pl.get_id()
        print(self.curr_pl_id)
        return self.rag_pipeline_dict[self.curr_pl_id]

    def get_match_settings(self):
        return MatchSettings(
            hit_threshold=self.hit_threshold,
            enable_fuzzy=self.enable_fuzzy,
            confidence_topn=self.confidence_topn
        )

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
                v for k, v in rag_results.get_metrics().items()
                if k in {metric.value for metric in Metrics} and isinstance(v, (int, float))
            )

            if recall_rate > best_avg_recall or (
                recall_rate == best_avg_recall and total_score > best_total_score
            ):
                best_avg_recall = recall_rate
                best_total_score = total_score
                best_pl_id = pl_id

        if best_pl_id is not None:
            self.set_curr_pl_by_id(best_pl_id)

        print(f"Stage {stage}: Pipeline is set to {self.get_curr_pl_id()}")
        #self.get_curr_results().check_metadata()
        # Check and update metadata consistency
        curr_results = self.get_curr_results()
        if curr_results is not None:
            curr_results.check_metadata()
        else:
            print(f"Warning: No current results found for pipeline {self.get_curr_pl_id()}")

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

    def get_pipeline_prompt(self, pl_id: int) -> str:
        pipeline = self.get_pl(pl_id).to_dict()
        if not pipeline:
            return ""
        generator = pipeline.get("generator", {})
        prompt = ""
        if isinstance(generator, dict):
            prompt_obj = generator.get("prompt", {})
            if isinstance(prompt_obj, dict):
                prompt = prompt_obj.get("content", "")
        if prompt:
            return prompt
        prompt = self.adaptor.get_default_prompt()
        return prompt

pilot = Pilot()
