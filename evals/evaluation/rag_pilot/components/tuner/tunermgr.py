# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Any, Dict, List, Optional, Tuple

import yaml
from api_schema import RAGStage, RunningStatus, TunerOut, TunerUpdateOut
from components.tuner.base import Tuner
from pydantic import BaseModel


class TunerRecord(BaseModel):
    base_pipeline_id: Optional[uuid.UUID] = None
    best_pipeline_id: Optional[uuid.UUID] = None
    all_pipeline_ids: List[uuid.UUID] = []
    # TODO: Change Any type
    targets: Dict[uuid.UUID, Any] = {}


class TunerMgr:
    def __init__(self):
        self._tuners_by_name: Dict[str, Tuner] = {}
        self._tuners_by_stage: Dict[RAGStage, List[str]] = {}
        self._records: Dict[str, TunerRecord] = {}

    def clear_stage(self, stage: RAGStage):
        names = self._tuners_by_stage.get(stage, [])
        for name in names:
            self._tuners_by_name.pop(name, None)
            self._records.pop(name, None)
        self._tuners_by_stage.pop(stage, None)

    def _register_tuner(self, stage: RAGStage, tuner_dict: dict):
        tuner = Tuner(tuner_dict)
        name = tuner.name
        self._tuners_by_name[name] = tuner
        self._tuners_by_stage.setdefault(stage, []).append(name)
        self._records[name] = TunerRecord()

    def get_stages(self) -> List[RAGStage]:
        return self._tuners_by_stage.keys()

    def get_stage_and_tuner_name_list(self) -> Dict[RAGStage, List[str]]:
        return self._tuners_by_stage

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
                status=tuner.get_status().value,
            )
        else:
            tunerOut = None
        return tunerOut

    def get_tuner_update_outs_by_name(self, name: str) -> TunerUpdateOut:
        tuner = self._tuners_by_name[name]
        return tuner.tunerUpdateOuts

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
        tuner_names = self.get_tuners_by_stage(stage)
        for tuner_name in tuner_names:
            tuner = self.get_tuner(tuner_name)
            if tuner:
                tuner.reset()
            self.clear_tuner_record(tuner_name)

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

    def get_tuners(self):
        tuners = []
        for v in self._tuners_by_name.values():
            tuners.append(v)
        return tuners

    def get_tuner_record(self, name) -> Optional[TunerRecord]:
        return self._records[name] if name in self._records else None

    def set_tuner_record(self, name, tunerRecord):
        self._records[name] = tunerRecord

    def clear_tuner_record(self, name):
        self._records[name] = TunerRecord()

    def run_tuner(self, name: str, pl):
        tuner = self.get_tuner(name)
        pl_list = tuner.run(pl)

        if tuner.get_status() is not RunningStatus.INACTIVE:
            tunerRecord = TunerRecord(
                name=name,
                base_pipeline_id=pl.get_id(),
                best_pipeline_id=None,
                all_pipeline_ids=[],
                targets={},
            )
            self.set_tuner_record(name, tunerRecord)

            for p in pl_list:
                tunerRecord.all_pipeline_ids.append(p.get_id())
                tunerRecord.targets[p.get_id()] = p

        return pl_list

    def parse_tuner_config(self, config_path: str) -> Tuple[List[Tuple[str, str]], dict]:
        """Parse YAML configuration file and return stage and tuner name pairs.

        Args:
            config_path (str): Path to the YAML configuration file

        Returns:
            List[Tuple[str, str]]: List of (stage_name, tuner_name) tuples
            dict: {tuner_name:tuner}
        """
        config = {}
        # Read the YAML file
        with open(config_path, "r") as file:
            for doc in yaml.safe_load_all(file):
                config.update(doc)

        # Collect stage and tuner pairs
        stage_tuner_list = []
        tuner_dict = {}

        for stage_name, tuners in config["stage"].items():
            for tuner_name in tuners:
                stage_tuner_list.append((stage_name, tuner_name))

        for tuner in config["tuner"]:
            tuner_dict[tuner["params"]["name"]] = tuner

        return stage_tuner_list, tuner_dict

    def init_tuner_from_file(self, config_path: str) -> None:
        """Initialize tuners by parsing config file and registering them with tuner manager.

        Args:
            config_path (str): Path to the YAML configuration file
        """
        # Parse the configuration file
        stage_tuner_list, tuner_dict = self.parse_tuner_config(config_path)
        self.init_tuner(stage_tuner_list, tuner_dict)

    def init_tuner(self, stage_tuner_list, tuner_dict):
        # Register each tuner with the tuner manager
        # (stage_name, tuner_name)
        for s_t_pair in stage_tuner_list:

            # Map string stage names to enum values
            stage_enum = getattr(RAGStage, s_t_pair[0].upper(), None)
            tuner_name = s_t_pair[1]

            try:
                # Assuming tuners are imported in the current namespace
                self._register_tuner(stage_enum, tuner_dict[tuner_name])
                print(f"Registered tuner {s_t_pair[1]} for stage {s_t_pair[0]}")
            except KeyError:
                print(f"Warning: Could not find tuner definition {s_t_pair[1]}")
                return False
            except Exception as e:
                print(f"Error registering tuner {s_t_pair[1]}: {e}")
                return False

        return True
