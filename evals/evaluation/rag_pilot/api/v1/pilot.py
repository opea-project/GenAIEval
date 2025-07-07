# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
from io import BytesIO, StringIO
from typing import List

from api_schema import GroundTruth, RAGStage, ResultOut, RunningStatus
from components.connect_utils import create_pipeline, update_active_pipeline, update_pipeline, upload_files
from components.pilot.base import RAGPipeline, convert_dict_to_pipeline
from components.pilot.ecrag.api_schema import DataIn, PipelineCreateIn
from components.pilot.pilot import pilot, update_rag_pipeline
from components.tuner.tunermgr import tunerMgr
from components.utils import load_rag_results_from_csv, load_rag_results_from_gt
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

pilot_app = FastAPI()


@pilot_app.post(path="/v1/pilot/pipeline/active")
async def add_active_pipeline(request: PipelineCreateIn):
    ret = create_pipeline(request)
    if hasattr(ret, "status_code") and ret.status_code != 200:
        raise HTTPException(status_code=ret.status_code, detail=f"Failed to create pipeline: {ret.text}")

    if hasattr(ret, "text"):
        try:
            ret_dict = json.loads(ret.text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON in pipeline creation response.")
    elif isinstance(ret, dict):
        ret_dict = ret
    else:
        raise HTTPException(status_code=500, detail="Unexpected return type from create_pipeline.")

    pipeline_config = convert_dict_to_pipeline(ret_dict)
    pl = RAGPipeline(pipeline_config)
    pilot.set_curr_pl(pl)
    return "Added"


@pilot_app.post(path="/v1/pilot/pipeline/active/import")
async def import_active_pipeline(file: UploadFile = File(...)):
    try:
        content = await file.read()
        request = json.loads(content)
        pipeline_req = PipelineCreateIn(**request)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid pipeline request format: {e}")

    ret = create_pipeline(pipeline_req)

    if hasattr(ret, "status_code") and ret.status_code != 200:
        raise HTTPException(
            status_code=ret.status_code, detail=f"Failed to create pipeline: {getattr(ret, 'text', '')}"
        )
    if hasattr(ret, "text"):
        try:
            ret_dict = json.loads(ret.text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON in pipeline creation response.")
    elif isinstance(ret, dict):
        ret_dict = ret
    else:
        raise HTTPException(status_code=500, detail="Unexpected return type from create_pipeline.")

    pl = RAGPipeline(convert_dict_to_pipeline(ret_dict))
    pilot.set_curr_pl(pl)
    return "Added"


@pilot_app.get(path="/v1/pilot/pipeline/active")
async def get_active_pipeline():
    return pilot.get_curr_pl()


@pilot_app.get(path="/v1/pilot/pipeline/active/prompt")
async def get_active_pipeline_prompt():
    return pilot.get_curr_pl().get_prompt() if pilot.get_curr_pl() else None


@pilot_app.get(path="/v1/pilot/pipeline/active/export")
async def export_active_pipeline():
    try:
        pl_dict = pilot.get_curr_pl().export_pipeline().dict()
        json_bytes = json.dumps(pl_dict, indent=2).encode("utf-8")
        return StreamingResponse(
            BytesIO(json_bytes),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=active_pipeline.json"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export pipeline: {e}")


@pilot_app.get(path="/v1/pilot/pipeline/active/id")
async def get_active_pipeline_id():
    return pilot.get_curr_pl_id()


@pilot_app.patch(path="/v1/pilot/pipeline/active")
async def update_active_pl(request: PipelineCreateIn):
    ret = update_active_pipeline(request)
    pl = RAGPipeline(convert_dict_to_pipeline(ret))
    pilot.set_curr_pl(pl)
    return "Updated"


@pilot_app.post(path="/v1/pilot/pipeline/active/run")
async def run_active_pipeline():
    if pilot.run_pipeline():
        return "Done"
    else:
        return "ERROR: Current pipeline cannot execute"


@pilot_app.patch(path="/v1/pilot/pipeline/active/top_n/{top_n}")
async def update_active_pl_top_n(top_n: int):
    pl_config = pilot.get_curr_pl().export_pipeline()

    reranker_found = False
    for pp in pl_config.postprocessor:
        if pp.processor_type == "reranker":
            pp.top_n = top_n
            reranker_found = True

    if not reranker_found:
        return {"error": "Reranker not found"}, 404

    ret = update_active_pipeline(pl_config)
    pl = RAGPipeline(convert_dict_to_pipeline(ret))
    pl.regenerate_id()
    pilot.set_curr_pl(pl)

    return {"message": "Updated", "new_top_n": top_n}


@pilot_app.get(path="/v1/pilot/pipeline/{id}")
async def get_pipeline_by_id(id: uuid.UUID):
    return pilot.get_pl(id)


@pilot_app.get(path="/v1/pilot/pipeline/{id}/prompt")
async def get_pipeline_prompt_by_id(id: uuid.UUID):
    return pilot.get_pl(id).get_prompt() if pilot.get_pl(id) else None


@pilot_app.get(path="/v1/pilot/pipeline/{id}/export")
async def export_pipeline_by_id(id: uuid.UUID):
    try:
        pl_dict = pilot.get_curr_pl().export_pipeline().dict()
        json_bytes = json.dumps(pl_dict, indent=2).encode("utf-8")
        return StreamingResponse(
            BytesIO(json_bytes),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=active_pipeline.json"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export pipeline: {e}")


@pilot_app.post(path="/v1/pilot/pipeline/{id}/active")
async def set_active_pipeline_by_id(id: uuid.UUID):
    if pilot.set_curr_pl_by_id(id):
        return "Done"
    else:
        return f"Error: Pipeline {id} cannot be set"


@pilot_app.post(path="/v1/pilot/pipeline/{id}/run")
async def run_pipeline_by_id(id: uuid.UUID):
    if pilot.set_curr_pl_by_id(id):
        if pilot.run_pipeline():
            return "Done"
        else:
            return f"Error: Pipeline {id} cannot execute"
    else:
        return f"Error: Pipeline {id} does not exist"


@pilot_app.post(path="/v1/pilot/files")
async def add_files(request: DataIn):
    ret = upload_files(request)

    if ret.status_code != 200:
        raise HTTPException(status_code=ret.status_code, detail=f"Failed to upload files: {ret.text}")

    try:
        return ret.json()
    except ValueError:
        return {"detail": "File uploaded, but response was not valid JSON.", "raw": ret.text}


def load_rag_results_from_uploaded_file(uploaded_file: UploadFile, filetype: str):
    content = uploaded_file.file.read().decode("utf-8")
    if filetype == "csv":
        csv_buffer = StringIO(content)
        return load_rag_results_from_csv(csv_buffer)
    if filetype == "json":
        json_gts = json.loads(content)
        gts = [GroundTruth(**gt) for gt in json_gts]
        return load_rag_results_from_gt(gts)


@pilot_app.get(path="/v1/pilot/ground_truth")
async def get_rag_ground_truth():
    return "Not Implemented"


@pilot_app.post(path="/v1/pilot/ground_truth")
async def update_rag_ground_truth(gts: List[GroundTruth]):
    try:
        rag_results = load_rag_results_from_gt(gts)

        if not rag_results.results:
            raise ValueError("No results found.")

        if pilot.update_rag_results_sample(rag_results):
            pilot.clear_rag_result_dict()
            for stage in RAGStage:
                tunerMgr.reset_tuners_by_stage(stage)
            return "RAG ground truth updated and database cleared"
        else:
            return "Error"

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@pilot_app.post(path="/v1/pilot/ground_truth/file")
async def update_rag_ground_truth_file(file: UploadFile = File(...)):
    filetype = ""
    if file.filename.endswith(".csv"):
        filetype = "csv"
    elif file.filename.endswith(".json"):
        filetype = "json"
    else:
        raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported.")

    try:
        await file.seek(0)
        rag_results = load_rag_results_from_uploaded_file(file, filetype)

        if not rag_results.results:
            raise ValueError("No results found in the uploaded file.")

        if pilot.update_rag_results_sample(rag_results):
            pilot.clear_rag_result_dict()
            for stage in RAGStage:
                tunerMgr.reset_tuners_by_stage(stage)
            return "RAG ground truth file updated and database cleared"
        else:
            return "Error"

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@pilot_app.get(path="/v1/pilot/pipeline/{id}/results")
async def get_pipeline_results(id: uuid.UUID):
    return pilot.get_results(id)


@pilot_app.get(path="/v1/pilot/pipeline/{id}/results/metrics")
async def get_pipeline_metrics(id: uuid.UUID):
    return pilot.get_results_metrics(id)


@pilot_app.patch(path="/v1/pilot/pipeline/{id}/results/metrics")
async def update_pipeline_metrics(id: uuid.UUID, request: list[ResultOut] = Body(...)):
    update_results = []
    for result in request:
        success = pilot.update_result_metrics(id, result.query_id, result.metadata)
        update_results.append({"query_id": result.query_id, "updated": success})

    return update_results


@pilot_app.post(path="/v1/pilot/save")
async def save_dicts():
    folder = pilot.save_dicts()
    return f"All results saved in {folder}"
