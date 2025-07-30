# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional, Type

from pydantic import BaseModel

from components.tuner.base import TargetUpdate
from components.tuner.adaptor import Adaptor
from components.tuner.tuner import (
    Tuner,
    EmbeddingTuner,
    NodeParserTuner,
    RerankerTopnTuner,
    RetrievalTopkTuner,
    SimpleNodeParserChunkTuner,
    PromptTuner,
)
from components.utils import read_yaml
from api_schema import RAGStage, TunerOut, TunerUpdateOut, RunningStatus
import uuid


class TunerRecord(BaseModel):
    base_pipeline_id: Optional[uuid.UUID] = None
    best_pipeline_id: Optional[uuid.UUID] = None
    all_pipeline_ids: List[uuid.UUID] = []
    targets: List[Dict[str, TargetUpdate]] = []


class TunerMgr:
    def __init__(self):
        self._tuners_by_name: Dict[str, Tuner] = {}
        self._tuners_by_stage: Dict[RAGStage, List[str]] = {}
        self._records: Dict[str, TunerRecord] = {}
        self.adaptor: Adaptor = None

    def init_adaptor(self, rag_module_yaml):
        self.adaptor = Adaptor(rag_module_yaml)

    def update_adaptor(self, pl):
        self.adaptor.update_all_module_functions(pl)

    def register_tuner(self, stage: RAGStage, tuner_cls: Type[Tuner]):
        tuner = tuner_cls(self.adaptor)
        name = tuner.name
        self._tuners_by_name[name] = tuner
        self._tuners_by_stage.setdefault(stage, []).append(name)
        self._records[name] = TunerRecord()

    def get_tuner_stage(self, name: str) -> Optional[RAGStage]:
        for stage, tuner_names in self._tuners_by_stage.items():
            if name in tuner_names:
                return stage
        return None

    def get_tuners_by_stage(self, stage: RAGStage) -> List[str]:
        return self._tuners_by_stage.get(stage, [])

    def get_tuner_out(self, name: str, stage: RAGStage = None) -> TunerOut:
        tuner = self._tuners_by_name[name] if name in self._tuners_by_name else None
        if tuner:
            targets_str = ", ".join([target.as_string() for target in tuner.targets.values()])
            if stage is None:
                stage = self.get_tuner_stage(name)
            tunerOut = TunerOut(
                stage=stage.value if hasattr(stage, "value") else str(stage),
                name=name,
                targets=targets_str,
                status=tuner.get_status().value
            )
        else:
            tunerOut = None
        return tunerOut

    def get_tuner_update_outs_by_name(self, name: str) -> TunerUpdateOut:
        record = self.get_tuner_record(name)
        if record is None:
            return []
        tunerUpdateOuts = []
        for pl_id, params in zip(record.all_pipeline_ids, record.targets):
            targets = {}
            for attr, update in params.items():
                parts = [update.node_type]
                if update.module_type:
                    parts.append(update.module_type)
                parts.append(update.attribute)
                target_key = ".".join(parts)  # e.g., "postprocessor.reranker.top_n"
                targets[target_key] = update.val
            tunerUpdateOuts.append(
                TunerUpdateOut(
                    tuner_name=name,
                    base_pipeline_id=record.base_pipeline_id,
                    pipeline_id=pl_id,
                    targets=targets,
                )
            )
        return tunerUpdateOuts

    def get_stage_status(self, stage):
        tuner_names = self.get_tuners_by_stage(stage)
        statuses = []

        for tuner_name in tuner_names:
            tuner = self.get_tuner(tuner_name)
            if tuner:
                statuses.append(tuner.get_status())

        if all(status in (RunningStatus.NOT_STARTED, RunningStatus.INACTIVE) for status in statuses):
            return RunningStatus.NOT_STARTED
        elif all(status in (RunningStatus.COMPLETED, RunningStatus.INACTIVE) for status in statuses):
            return RunningStatus.COMPLETED
        else:
            return RunningStatus.IN_PROGRESS

    def get_tuner_status(self, tuner_name):
        tuner = self.get_tuner(tuner_name)
        if tuner:
            return tuner.get_status()
        else:
            return None

    def set_tuner_status(self, tuner_name, status):
        tuner = self.get_tuner(tuner_name)
        if tuner:
            tuner.set_status(status)

    def reset_tuners_by_stage(self, stage):
        tuner_names = tunerMgr.get_tuners_by_stage(stage)
        for tuner_name in tuner_names:
            tunerMgr.set_tuner_status(tuner_name, RunningStatus.NOT_STARTED)

    def complete_tuner(self, tuner_name: str, best_pipeline_id: int = None):
        tuner = self.get_tuner(tuner_name)
        if tuner:
            tuner.set_status_completed()
            record = self.get_tuner_record(tuner_name)
            record.best_pipeline_id = best_pipeline_id

    def get_all_tuner_outs_by_stage(self, stage: RAGStage) -> List[TunerOut]:
        return [self.get_tuner_out(name, stage) for name in self.get_tuners_by_stage(stage)]

    def get_pipeline_best(self, name: str) -> Optional[uuid.UUID]:
        return self._records[name].best_pipeline_id if name in self._records else None

    def get_pipeline_base(self, name: str) -> Optional[uuid.UUID]:
        return self._records[name].base_pipeline_id if name in self._records else None

    def set_base_pipeline(self, name, pipeline_id):
        if name in self._records:
            self._records[name].base_pipeline_id = pipeline_id

    def set_best_pipeline(self, name, pipeline_id):
        if name in self._records:
            self._records[name].best_pipeline_id = pipeline_id

    def get_tuner(self, name):
        return self._tuners_by_name[name] if name in self._records else None

    def get_tuner_record(self, name) -> Optional[TunerRecord]:
        return self._records[name] if name in self._records else None

    def set_tuner_record(self, name, tunerRecord):
        self._records[name] = tunerRecord

    def run_tuner(self, name: str, pl):
        tuner = self.get_tuner(name)
        pl_list, params_candidates = tuner.run(pl)

        if tuner.get_status() is not RunningStatus.INACTIVE:
            tunerRecord = TunerRecord(
                name=name,
                base_pipeline_id=pl.get_id(),
                best_pipeline_id=None,
                all_pipeline_ids=[],
                targets=[],
            )
            self.set_tuner_record(name, tunerRecord)

            for pl, params in zip(pl_list, params_candidates):
                tunerRecord.all_pipeline_ids.append(pl.get_id())
                tunerRecord.targets.append(params)

        return pl_list, params_candidates


tunerMgr = TunerMgr()


def init_tuners(adaptor_yaml="configs/ecrag.yaml"):
    tunerMgr.init_adaptor(read_yaml(adaptor_yaml))
    tunerMgr.register_tuner(RAGStage.RETRIEVAL, EmbeddingTuner)
    tunerMgr.register_tuner(RAGStage.RETRIEVAL, NodeParserTuner)
    tunerMgr.register_tuner(RAGStage.RETRIEVAL, SimpleNodeParserChunkTuner)
    tunerMgr.register_tuner(RAGStage.RETRIEVAL, RetrievalTopkTuner)

    tunerMgr.register_tuner(RAGStage.POSTPROCESSING, RerankerTopnTuner)

    tunerMgr.register_tuner(RAGStage.GENERATION, PromptTuner)
