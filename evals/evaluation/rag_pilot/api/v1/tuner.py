# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from collections import defaultdict
from typing import List, Optional

from api_schema import RAGStage, RunningStatus, Tuner, TunerOut, TunerRequest
from components.pilot.pilot import pilot
from components.pilot.result import Metrics
from fastapi import FastAPI, HTTPException, Path

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


@tuner_app.post(path="/v1/tuners/register")
async def register_tuner(reg_tuner_req: TunerRequest):
    try:
        pilot.tuner_mgr.clear_stage(reg_tuner_req.stage)
        stage_tuner_list = []
        tuner_name_list = []
        tuners_dict = {}
        for t in reg_tuner_req.tuners:
            if t.type is None:
                raise HTTPException(status_code=422, detail="Error: Tuner.type not specified.")
            if t.params is None:
                raise HTTPException(status_code=422, detail="Error: Tuner.params not specified.")
            if "name" in t.params and t.params["name"] != "":
                stage_tuner_list.append((reg_tuner_req.stage, t.params["name"]))
                tuner_name_list.append(t.params["name"])
                tuners_dict[t.params["name"]] = t.dict()
            else:
                raise HTTPException(status_code=422, detail="Error: Tuner.params.name not specified.")
        if pilot.tuner_mgr.init_tuner(stage_tuner_list, tuners_dict):
            return f"Tuner {tuner_name_list} registered"
        else:
            raise HTTPException(status_code=500, detail=f"Error registering tuner: {tuner_name_list}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering tuner: {e}")


@tuner_app.get(path="/v1/tuners")
async def get_tuners() -> List[TunerRequest]:
    out = []
    stage_and_tuner_list = pilot.tuner_mgr.get_stage_and_tuner_name_list()
    print(stage_and_tuner_list)
    for k, v in stage_and_tuner_list.items():
        r = TunerRequest(stage=k, tuners=[Tuner(**pilot.tuner_mgr.get_tuner(t).node.to_dict()) for t in v])
        out.append(r)
    return out


@tuner_app.get(path="/v1/tuners/{name}")
async def get_tuner_by_name(name: str):
    tuner = pilot.tuner_mgr.get_tuner(name)
    if tuner is None:
        raise HTTPException(status_code=404, detail=f"Tuner {name} not found")
    return tuner.node


@tuner_app.get(path="/v1/avail_tuners", response_model=List[TunerRequest])
async def get_available_tuners():
    # TODO: Extend to more storage for available tuner repo
    try:
        stage_tuner_list, tuner_dict = pilot.tuner_mgr.parse_tuner_config("./configs/tuner.yaml")

        grouped = defaultdict(list)

        for stage, tuner_name in stage_tuner_list:
            data = tuner_dict.get(tuner_name)
            if data is not None:
                grouped[stage].append(Tuner(**data))

        return [TunerRequest(stage=stage, tuners=tuner_list) for stage, tuner_list in grouped.items()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available tuners: {e}")


@tuner_app.get(path="/v1/tuners/stage/{stage}", response_model=List[TunerOut])
async def get_tuners_by_stage(stage: RAGStage = Path(...)):
    tuner_names = pilot.tuner_mgr.get_tuners_by_stage(stage)
    tuners_out = []

    for name in tuner_names:
        tuners_out.append(pilot.tuner_mgr.get_tuner_out(name, stage))

    return tuners_out


@tuner_app.get(path="/v1/tuners/stage/{stage}/status")
async def get_stage_status(stage: RAGStage = Path(...)):
    return {stage: pilot.tuner_mgr.get_stage_status(stage).value}


pipeline_run_lock = asyncio.Lock()


async def run_tuners_in_background(stage: Optional[RAGStage], tuner_names: List[str]):
    for tuner_name in tuner_names:
        status = pilot.tuner_mgr.get_tuner_status(tuner_name)
        if status is not RunningStatus.NOT_STARTED:
            print(f"[Tuner {tuner_name}] Skipped, current status {status}.")
            continue

        async with pipeline_run_lock:
            # try:
            pilot.tuner_mgr.set_tuner_status(tuner_name, RunningStatus.IN_PROGRESS)
            print(f"[Tuner {tuner_name}] Starting...")

            pl_list = pilot.tuner_mgr.run_tuner(tuner_name, pilot.get_curr_pl())
            if pilot.tuner_mgr.get_tuner_status(tuner_name) is RunningStatus.INACTIVE:
                print(f"[Tuner {tuner_name}] is inactive. Skipped")

            for new_pl in pl_list:
                pilot.add_rag_pipeline(new_pl)

            for pl in pl_list:
                print(f"[Tuner {tuner_name}]: Running {pl.get_id()}")
                for node in pl.nodes:
                    for module in node.modules:
                        attr_val = module.attributes[0].params["value"]
                        print(
                            f"[Tuner {tuner_name}][{pl.get_id()}]: Setting {node.type}.{module.type}.{module.attributes[0].type} to {attr_val}"
                        )
                if stage == RAGStage.RETRIEVAL or stage == RAGStage.POSTPROCESSING:
                    await asyncio.to_thread(pilot.run_pipeline_blocked, pl, True)
                else:
                    await asyncio.to_thread(pilot.run_pipeline_blocked, pl)

            actual_stage = stage or pilot.tuner_mgr.get_tuner_stage(tuner_name)
            best_pl = await asyncio.to_thread(pilot.change_best_recall_pl, actual_stage)
            best_pl_id = best_pl.get_id() if best_pl else None
            pilot.tuner_mgr.complete_tuner(tuner_name, best_pl_id)
            print(f"[Tuner {tuner_name}] Completed. Best pipeline ID: {best_pl_id or 'None'}")

            # except Exception as e:
            #     print(f"[Tuner {tuner_name}] Error while running pipelines: {e}")


@tuner_app.post(path="/v1/tuners/stage/{stage}/run")
async def run_stage_tuner(stage: RAGStage = Path(...)):
    tuner_names = pilot.tuner_mgr.get_tuners_by_stage(stage)
    print(f"run_stage_tuner: {tuner_names}")
    tuner_outs = [pilot.tuner_mgr.get_tuner_out(tuner_name, stage) for tuner_name in tuner_names]

    asyncio.create_task(run_tuners_in_background(stage, tuner_names))
    return tuner_outs


@tuner_app.post(path="/v1/tuners/stage/{stage}/reset")
async def reset_stage_tuner(stage: RAGStage = Path(...)):
    pilot.tuner_mgr.reset_tuners_by_stage(stage)
    return "Done"


@tuner_app.get(path="/v1/tuners/stage/{stage}/results")
async def get_stage_results(stage: RAGStage = Path(...)):
    tuner_names = pilot.tuner_mgr.get_tuners_by_stage(stage)
    results_dict = {}
    for tuner_name in tuner_names:
        record = pilot.tuner_mgr.get_tuner_record(tuner_name)
        if record is not None:
            for pl_id in record.all_pipeline_ids:
                results_dict[pl_id] = pilot.get_results(pl_id)

    return results_dict


@tuner_app.get(path="/v1/tuners/stage/{stage}/results/metrics")
async def get_stage_results_metrics(stage: RAGStage = Path(...)):
    tuner_names = pilot.tuner_mgr.get_tuners_by_stage(stage)
    metrics_dict = {}
    for tuner_name in tuner_names:
        record = pilot.tuner_mgr.get_tuner_record(tuner_name)
        if record is not None:
            all_pipeline_ids = list(record.all_pipeline_ids)
            for pl_id in all_pipeline_ids:
                metrics_dict[pl_id] = pilot.get_results_metrics(pl_id)

    return metrics_dict


# TODO: Remove best_pl_id append logic
@tuner_app.get(path="/v1/tuners/stage/{stage}/pipelines")
async def get_stage_pipelines(stage: RAGStage = Path(...)):
    tuner_names = pilot.tuner_mgr.get_tuners_by_stage(stage)
    pipeline_list = []
    for tuner_name in tuner_names:
        record = pilot.tuner_mgr.get_tuner_record(tuner_name)
        if record is not None and record.best_pipeline_id is None:
            pl_id_list = list(record.all_pipeline_ids)
            if record.base_pipeline_id not in pl_id_list:
                pl_id_list.append(record.base_pipeline_id)
            best_pl_id = get_best_pl_id(record.all_pipeline_ids, stage)
            record.best_pipeline_id = best_pl_id
        pipeline_list.append(pilot.tuner_mgr.get_tuner_update_outs_by_name(tuner_name))
    return pipeline_list


# TODO: Remove best_pl_id append logic
@tuner_app.get(path="/v1/tuners/stage/{stage}/pipelines/best/id")
async def get_stage_pipelines_best(stage: RAGStage = Path(...)):
    tuner_names = pilot.tuner_mgr.get_tuners_by_stage(stage)
    pl_id_list = []
    for tuner_name in tuner_names:
        record = pilot.tuner_mgr.get_tuner_record(tuner_name)
        if record is not None:
            pl_id_list.extend(list(record.all_pipeline_ids))
            if record.base_pipeline_id not in pl_id_list:
                pl_id_list.append(record.base_pipeline_id)
    pl_id_list = list(set(pl_id_list))
    best_pl_id = get_best_pl_id(pl_id_list, stage)
    if best_pl_id is None:
        return record.best_pipeline_id
    return best_pl_id


@tuner_app.get(path="/v1/tuners/{tuner_name}/pipelines/best")
async def get_pipeline_best(tuner_name):
    best_pl = pilot.tuner_mgr.get_pipeline_best(tuner_name)
    if not best_pl:
        raise HTTPException(status_code=404, detail=f"Error: Invalid info tuner {tuner_name}")

    return best_pl


@tuner_app.get(path="/v1/tuners/{tuner_name}/pipelines/base")
async def get_pipeline_base(tuner_name):
    base_pl = pilot.tuner_mgr.get_pipeline_base(tuner_name)
    if not base_pl:
        raise HTTPException(status_code=404, detail=f"Error: Invalid info tuner {tuner_name}")

    return base_pl


@tuner_app.post(path="/v1/tuners/{tuner_name}/run")
async def run_tuner(tuner_name: str):
    stage = pilot.tuner_mgr.get_tuner_stage(tuner_name)
    asyncio.create_task(run_tuners_in_background(stage, [tuner_name]))
    tunerOut = pilot.tuner_mgr.get_tuner_out(tuner_name)
    return tunerOut


@tuner_app.post(path="/v1/tuners/{tuner_name}/reset")
async def reset_tuner(tuner_name):
    pilot.tuner_mgr.set_tuner_status(tuner_name, RunningStatus.NOT_STARTED)
    return "Done"


@tuner_app.get(path="/v1/tuners/{tuner_name}")
async def get_tuner(tuner_name):
    tuner = pilot.tuner_mgr.get_tuner(tuner_name)
    if not tuner:
        raise HTTPException(status_code=404, detail=f"Error: Tuner {tuner_name} not found")
    return tuner


@tuner_app.get(path="/v1/tuners/{tuner_name}/status")
async def get_stage_status_by_tuner_name(tuner_name):
    status = pilot.tuner_mgr.get_tuner_status(tuner_name)
    if not status:
        raise HTTPException(status_code=404, detail=f"Error: Invalid info tuner {tuner_name}")
    return status.value


@tuner_app.get(path="/v1/tuners/{tuner_name}/pipelines")
async def get_tuner_pipelines(tuner_name):
    return pilot.tuner_mgr.get_tuner_update_outs_by_name(tuner_name)


@tuner_app.get(path="/v1/tuners/{tuner_name}/results")
async def get_tuner_results(tuner_name):
    record = pilot.tuner_mgr.get_tuner_record(tuner_name)
    results_dict = {}
    if record is not None:
        for pl_id in record.all_pipeline_ids:
            results_dict[pl_id] = pilot.get_results(pl_id)

    return results_dict


@tuner_app.get(path="/v1/tuners/{tuner_name}/results/metrics")
async def get_tuner_results_metrics(tuner_name):
    record = pilot.tuner_mgr.get_tuner_record(tuner_name)
    metrics_dict = {}
    if record is not None:
        for pl_id in record.all_pipeline_ids:
            metrics_dict[pl_id] = pilot.get_results_metrics(pl_id)

    return metrics_dict
