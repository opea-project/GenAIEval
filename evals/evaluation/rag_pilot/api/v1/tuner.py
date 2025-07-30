# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from fastapi import Path
from typing import List, Optional

from fastapi import FastAPI
import asyncio

from components.tuner.tunermgr import tunerMgr
from api_schema import RAGStage, TunerOut, RunningStatus
from components.pilot.pilot import pilot
from components.pilot.base import Metrics

tuner_app = FastAPI()


def get_best_pl_id(pl_id_list: List[int], stage=None):
    best_pl_id = None
    best_metric = float("-inf")

    if stage is RAGStage.RETRIEVAL:
        metric = Metrics.RETRIEVAL_RECALL
    elif stage is RAGStage.POSTPROCESSING:
        metric = Metrics.POSTPROCESSING_RECALL
    else:
        return None

    metric_dict = {}
    for pl_id in pl_id_list:
        rate = pilot.rag_results_dict[pl_id].get_metric(metric) if pl_id in pilot.rag_results_dict else float("-inf")
        metric_dict[pl_id] = rate
        if rate > best_metric:
            best_metric = rate
            best_pl_id = pl_id

    return best_pl_id


@tuner_app.get(path="/v1/tuners/stage/{stage}", response_model=List[TunerOut])
async def get_tuners_by_stage(stage: RAGStage = Path(...)):
    active_pl = pilot.get_curr_pl()
    tunerMgr.update_adaptor(active_pl)
    tuner_names = tunerMgr.get_tuners_by_stage(stage)
    tuners_out = []

    for name in tuner_names:
        tuners_out.append(tunerMgr.get_tuner_out(name, stage))

    return tuners_out


@tuner_app.get(path="/v1/tuners/stage/{stage}/status")
async def get_stage_status(stage: RAGStage = Path(...)):
    return {stage: tunerMgr.get_stage_status(stage).value}


pipeline_run_lock = asyncio.Lock()


async def run_tuners_in_background(stage: Optional[RAGStage], tuner_names: List[str]):
    for tuner_name in tuner_names:
        status = tunerMgr.get_tuner_status(tuner_name)
        if status is not RunningStatus.NOT_STARTED:
            print(f"[Tuner {tuner_name}] Skipped, current status {status}.")
            continue

        async with pipeline_run_lock:
            try:
                tunerMgr.set_tuner_status(tuner_name, RunningStatus.IN_PROGRESS)
                print(f"[Tuner {tuner_name}] Starting...")

                pl = pilot.get_curr_pl()
                tunerMgr.update_adaptor(pl)

                pl_list, params_candidates = tunerMgr.run_tuner(tuner_name, pl)
                if tunerMgr.get_tuner_status(tuner_name) is RunningStatus.INACTIVE:
                    print(f"[Tuner {tuner_name}] is inactive. Skipped")

                for new_pl in pl_list:
                    pilot.add_rag_pipeline(new_pl)

                for pl, params in zip(pl_list, params_candidates):
                    print(f"[Tuner {tuner_name}]: Running {pl.get_id()}")
                    for attr, tunerUpdate in params.items():
                        print(f"[Tuner {tuner_name}][{pl.get_id()}]: Setting {tunerUpdate.node_type}.{tunerUpdate.module_type}.{attr} to {tunerUpdate.val}")
                    if stage == RAGStage.RETRIEVAL or stage == RAGStage.POSTPROCESSING:
                        await asyncio.to_thread(pilot.run_pipeline_blocked, pl, True)
                    else:
                        await asyncio.to_thread(pilot.run_pipeline_blocked, pl)

                actual_stage = stage or tunerMgr.get_tuner_stage(tuner_name)
                best_pl = await asyncio.to_thread(pilot.change_best_recall_pl, actual_stage)
                best_pl_id = best_pl.get_id() if best_pl else None
                tunerMgr.complete_tuner(tuner_name, best_pl_id)
                print(f"[Tuner {tuner_name}] Completed. Best pipeline ID: {best_pl_id or 'None'}")

            except Exception as e:
                print(f"[Tuner {tuner_name}] Error while running pipelines: {e}")


@tuner_app.post(path="/v1/tuners/stage/{stage}/run")
async def run_stage_tuner(stage: RAGStage = Path(...)):
    tuner_names = tunerMgr.get_tuners_by_stage(stage)
    tuner_outs = [tunerMgr.get_tuner_out(tuner_name, stage) for tuner_name in tuner_names]

    asyncio.create_task(run_tuners_in_background(stage, tuner_names))
    return tuner_outs


@tuner_app.post(path="/v1/tuners/stage/{stage}/reset")
async def reset_stage_tuner(stage: RAGStage = Path(...)):
    tunerMgr.reset_tuners_by_stage(stage)
    return "Done"


@tuner_app.get(path="/v1/tuners/stage/{stage}/results")
async def get_stage_results(stage: RAGStage = Path(...)):
    tuner_names = tunerMgr.get_tuners_by_stage(stage)
    results_dict = {}
    for tuner_name in tuner_names:
        record = tunerMgr.get_tuner_record(tuner_name)
        if record is not None:
            all_pipeline_ids = list(record.all_pipeline_ids)
            for pl_id in all_pipeline_ids:
                results_dict[pl_id] = pilot.get_results(pl_id)

    return results_dict


@tuner_app.get(path="/v1/tuners/stage/{stage}/results/metrics")
async def get_stage_results_metrics(stage: RAGStage = Path(...)):
    tuner_names = tunerMgr.get_tuners_by_stage(stage)
    metrics_dict = {}
    for tuner_name in tuner_names:
        record = tunerMgr.get_tuner_record(tuner_name)
        if record is not None:
            all_pipeline_ids = list(record.all_pipeline_ids)
            for pl_id in all_pipeline_ids:
                metrics_dict[pl_id] = pilot.get_results_metrics(pl_id)

    return metrics_dict


@tuner_app.get(path="/v1/tuners/stage/{stage}/pipelines")
async def get_stage_pipelines(stage: RAGStage = Path(...)):
    tuner_names = tunerMgr.get_tuners_by_stage(stage)
    pipeline_list = []
    for tuner_name in tuner_names:
        record = tunerMgr.get_tuner_record(tuner_name)
        if record is not None and record.best_pipeline_id is None:
            pl_id_list = list(record.all_pipeline_ids)
            if record.base_pipeline_id not in pl_id_list:
                pl_id_list.append(record.base_pipeline_id)
            best_pl_id = get_best_pl_id(record.all_pipeline_ids, stage)
            record.best_pipeline_id = best_pl_id
        pipeline_list.append(tunerMgr.get_tuner_update_outs_by_name(tuner_name))
    return pipeline_list


@tuner_app.get(path="/v1/tuners/stage/{stage}/pipelines/best/id")
async def get_stage_pipelines_best(stage: RAGStage = Path(...)):
    tuner_names = tunerMgr.get_tuners_by_stage(stage)
    pl_id_list = []
    for tuner_name in tuner_names:
        record = tunerMgr.get_tuner_record(tuner_name)
        if record is not None:
            pl_id_list.extend(list(record.all_pipeline_ids))
            if record.base_pipeline_id not in pl_id_list:
                pl_id_list.append(record.base_pipeline_id)
    pl_id_list = list(set(pl_id_list))
    best_pl_id = get_best_pl_id(pl_id_list, stage)
    return best_pl_id


@tuner_app.get(path="/v1/tuners/{tuner_name}/pipelines/best")
async def get_pipeline_best(tuner_name):
    record = tunerMgr.get_tuner_record(tuner_name)
    if record is not None and record.best_pipeline_id is None:
        stage = tunerMgr.get_tuner_stage(tuner_name)
        pl_id_list = list(record.all_pipeline_ids)
        if record.base_pipeline_id not in pl_id_list:
            pl_id_list.append(record.base_pipeline_id)
        best_pl_id = get_best_pl_id(pl_id_list, stage)
        record.best_pipeline_id = best_pl_id

    return tunerMgr.get_pipeline_best(tuner_name)


@tuner_app.get(path="/v1/tuners/{tuner_name}/pipelines/base")
async def get_pipeline_base(tuner_name):
    return tunerMgr.get_pipeline_base(tuner_name)


@tuner_app.post(path="/v1/tuners/{tuner_name}/run")
async def run_tuner(tuner_name: str):
    stage = tunerMgr.get_tuner_stage(tuner_name)
    asyncio.create_task(run_tuners_in_background(stage, [tuner_name]))
    tunerOut = tunerMgr.get_tuner_out(tuner_name)
    return tunerOut


@tuner_app.post(path="/v1/tuners/{tuner_name}/reset")
async def reset_tuner(tuner_name):
    tunerMgr.set_tuner_status(tuner_name, RunningStatus.NOT_STARTED)
    return "Done"


@tuner_app.get(path="/v1/tuners/{tuner_name}")
async def get_tuner(tuner_name):
    record = tunerMgr.get_tuner_record(tuner_name)
    if record is not None and record.best_pipeline_id is None:
        stage = tunerMgr.get_tuner_stage(tuner_name)
        pl_id_list = list(record.all_pipeline_ids)
        if record.base_pipeline_id not in pl_id_list:
            pl_id_list.append(record.base_pipeline_id)
        best_pl_id = get_best_pl_id(record.all_pipeline_ids, stage)
        record.best_pipeline_id = best_pl_id
    return tunerMgr.get_tuner_update_outs_by_name(tuner_name)


@tuner_app.get(path="/v1/tuners/{tuner_name}/status")
async def get_stage_status_by_tuner_name(tuner_name):
    status = tunerMgr.get_tuner_status(tuner_name)
    return status.value if status else f"Invalid tuner {tuner_name}"


@tuner_app.get(path="/v1/tuners/{tuner_name}/pipelines")
async def get_tuner_pipelines(tuner_name):
    record = tunerMgr.get_tuner_record(tuner_name)
    if record is not None and record.best_pipeline_id is None:
        stage = tunerMgr.get_tuner_stage(tuner_name)
        pl_id_list = list(record.all_pipeline_ids)
        if record.base_pipeline_id not in pl_id_list:
            pl_id_list.append(record.base_pipeline_id)
        best_pl_id = get_best_pl_id(record.all_pipeline_ids, stage)
        record.best_pipeline_id = best_pl_id
    return tunerMgr.get_tuner_update_outs_by_name(tuner_name)


@tuner_app.get(path="/v1/tuners/{tuner_name}/results")
async def get_tuner_results(tuner_name):
    record = tunerMgr.get_tuner_record(tuner_name)
    results_dict = {}
    if record is not None:
        all_pipeline_ids = list(record.all_pipeline_ids)
        for pl_id in all_pipeline_ids:
            results_dict[pl_id] = pilot.get_results(pl_id)

    return results_dict


@tuner_app.get(path="/v1/tuners/{tuner_name}/results/metrics")
async def get_tuner_results_metrics(tuner_name):
    record = tunerMgr.get_tuner_record(tuner_name)
    metrics_dict = {}
    if record is not None:
        all_pipeline_ids = list(record.all_pipeline_ids)
        for pl_id in all_pipeline_ids:
            metrics_dict[pl_id] = pilot.get_results_metrics(pl_id)

    return metrics_dict
