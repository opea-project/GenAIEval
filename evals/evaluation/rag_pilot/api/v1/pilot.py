# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import StringIO
import json
import uuid
import os
from fastapi import FastAPI, File, HTTPException, UploadFile, Body
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import List
from components.adaptor.ecrag import DataIn
from components.utils import load_rag_results_from_csv, load_rag_results_from_gt
from components.pilot.pilot import pilot
from api_schema import ResultOut, RAGStage, GroundTruth, GroundTruthContext, MatchSettings, AnnotationOutput, PilotSettings

pilot_app = FastAPI()


@pilot_app.post(path="/v1/pilot/settings")
async def update_pilot_settings(settings: PilotSettings):
    try:
        pilot.set_pilot_settings(settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return pilot.pilot_settings


@pilot_app.get(path="/v1/pilot/settings")
async def get_pilot_settings():
    if pilot.pilot_settings:
        return pilot.pilot_settings
    else:
        return PilotSettings()



# @pilot_app.post(path="/v1/pilot/pipeline/active/import")
# async def import_active_pipeline(file: UploadFile = File(...)):
#     try:
#         content = await file.read()
#         request = json.loads(content)
#         pipeline_req = PipelineCreateIn(**request)
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON.")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Invalid pipeline request format: {e}")
#
#     ret = create_pipeline(pipeline_req)
#
#     if hasattr(ret, "status_code") and ret.status_code != 200:
#         raise HTTPException(status_code=ret.status_code, detail=f"Failed to create pipeline: {getattr(ret, 'text', '')}")
#     if hasattr(ret, "text"):
#         try:
#             ret_dict = json.loads(ret.text)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=500, detail="Invalid JSON in pipeline creation response.")
#     elif isinstance(ret, dict):
#         ret_dict = ret
#     else:
#         raise HTTPException(status_code=500, detail="Unexpected return type from create_pipeline.")
#
#     pl = RAGPipeline(convert_dict_to_pipeline(ret_dict))
#     pilot.set_curr_pl(pl)
#     return "Added"
#


@pilot_app.get(path="/v1/pilot/pipeline/active")
async def get_active_pipeline():
    return pilot.get_curr_pl()


@pilot_app.get(path="/v1/pilot/pipeline/active/id")
async def get_active_pipeline_id():
    return pilot.get_curr_pl_id()


@pilot_app.post(path="/v1/pilot/pipeline/{id}/active")
async def activate_pipeline_by_id(id: uuid.UUID):
    try:
        if pilot.set_curr_pl_by_id(id):
            return "Done"
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Error: Pipeline {id} does not exist"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error activating pipeline: {e}"
        )


@pilot_app.post(path="/v1/pilot/pipeline/{id}/run")
async def run_pipeline_by_id(id: uuid.UUID):
    if pilot.set_curr_pl_by_id(id):
        if pilot.run_pipeline():
            return "Done"
        else:
            return f"Error: Pipeline {id} cannot be executed"
    else:
        return f"Error: Pipeline {id} does not exist"


@pilot_app.post(path="/v1/pilot/pipeline/{id}/run/blocked")
async def run_pipeline_by_id_blocked(id: uuid.UUID):
    if pilot.set_curr_pl_by_id(id):
        if pilot.run_pipeline_blocked():
            return "Done"
        else:
            return f"Error: Pipeline {id} cannot be executed"
    else:
        return f"Error: Pipeline {id} does not exist"


@pilot_app.post(path="/v1/pilot/pipeline/{id}/run/retrieval")
async def run_pipeline_by_id_retrieval(id: uuid.UUID):
    if pilot.set_curr_pl_by_id(id):
        if pilot.run_pipeline(is_retrieval=True):
            return "Done"
        else:
            return "ERROR: Current pipeline cannot be executed"
    else:
        return f"Error: Pipeline {id} does not exist"


@pilot_app.get(path="/v1/pilot/pipeline/{id}/results")
async def get_pipeline_by_id_results(id: uuid.UUID):
    try:
        return pilot.get_results(id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pipeline results: {e}"
        )


@pilot_app.get(path="/v1/pilot/pipeline/{id}/results/metrics")
async def get_pipeline_metrics(id: uuid.UUID):
    try:
        return pilot.get_results_metrics(id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pipeline metrics: {e}"
        )


@pilot_app.patch(path="/v1/pilot/pipeline/{id}/results/metrics")
async def update_pipeline_metrics(id: uuid.UUID, request: list[ResultOut] = Body(...)):
    update_results = []
    for result in request:
        success = pilot.update_result_metrics(id, result.query_id, result.metadata)
        update_results.append({
            "query_id": result.query_id,
            "updated": success
        })

    return update_results


@pilot_app.get(path="/v1/pilot/pipeline/{id}")
async def get_pipeline_by_id(id: uuid.UUID):
    return pilot.get_pl(id).to_dict()


@pilot_app.get(path="/v1/pilot/pipeline/{id}/prompt")
async def get_pipeline_prompt_by_id(id: uuid.UUID):
    prompt = pilot.get_pipeline_prompt(id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt for pipeline {id} not found")
    return prompt


@pilot_app.get(path="/v1/pilot/pipeline/{id}/export")
async def export_pipeline_by_id(id: uuid.UUID):
    try:
        pl_dict = pilot.get_curr_pl().export_pipeline().dict()
        json_bytes = json.dumps(pl_dict, indent=2).encode("utf-8")
        return StreamingResponse(
            BytesIO(json_bytes),
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=active_pipeline.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export pipeline: {e}")


@pilot_app.post(path="/v1/pilot/pipeline/reconcil")
async def reconcil_pipeline():
    success = pilot.reconcil_curr_pl()
    if success:
        current_pl = pilot.get_curr_pl()
        return {
            "message": "Pipeline reconcil successfully",
            "pipeline_id": str(current_pl.get_id()) if current_pl else None,
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="Failed to restore pipeline: No active pipeline found or restore operation failed"
        )


@pilot_app.post(path="/v1/pilot/files")
async def add_files(request: DataIn):
    ret = pilot.adaptor.upload_files(request)

    if ret.status_code != 200:
        raise HTTPException(
            status_code=ret.status_code,
            detail=f"Failed to upload files: {ret.text}"
        )

    try:
        return ret.json()
    except ValueError:
        return {"detail": "File uploaded, but response was not valid JSON.", "raw": ret.text}


def load_rag_results_from_uploaded_file(uploaded_file: UploadFile, filetype: str):
    content = uploaded_file.file.read().decode('utf-8')
    if filetype == "csv":
        csv_buffer = StringIO(content)
        return load_rag_results_from_csv(csv_buffer)
    if filetype == "json":
        json_gts = json.loads(content)
        gts = [GroundTruth(**gt) for gt in json_gts]
        return load_rag_results_from_gt(gts)


@pilot_app.get(path="/v1/pilot/ground_truth")
async def get_rag_ground_truth():
    gt_infos = pilot.get_gt_annotate_infos() or []
    return gt_infos


@pilot_app.get(path="/v1/pilot/ground_truth/{query_id}")
async def get_rag_ground_truth_by_id(query_id: int):
    gt_infos = pilot.get_gt_annotate_infos() or []
    for gt in gt_infos:
        if gt.query_id == query_id:
            return gt
    raise HTTPException(status_code=404, detail=f"GroundTruth query_id {query_id} not found")


@pilot_app.post(path="/v1/pilot/ground_truth/clear_cache")
async def clear_rag_ground_truth_cache():
    pilot.clear_gt_annotate_caches()
    pilot.clear_target_query_gt()
    return "Cleared ground truth annotation caches"


@pilot_app.post(path="/v1/pilot/ground_truth")
async def update_rag_ground_truth(gts: List[GroundTruth]):
    try:
        if not gts:
            raise ValueError("No ground truth data provided.")
        pilot.update_gt_annotate_infos(gts)
        rag_results = pilot.process_annotation_batch(gts, clear_cache=False)
        suggested_query_ids = pilot.get_suggested_query_ids()

        if not rag_results or not rag_results.results:
            raise ValueError("No RAG results generated from annotations.")

        if pilot.update_target_query_gt(rag_results):
            pilot.clear_rag_result_dict()
            for stage in RAGStage:
                pilot.tuner_mgr.reset_tuners_by_stage(stage)
            return AnnotationOutput(suggested_query_ids=suggested_query_ids)
        else:
            raise HTTPException(status_code=500, detail="Failed to update target query ground truth")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}")


@pilot_app.get(path="/v1/pilot/ground_truth/suggestions/collect")
async def update_gt_wi_suggestion():
    try:
        gt_infos = pilot.get_gt_annotate_infos() or []
        if not gt_infos:
            return []
        new_gt_map: dict[int, GroundTruth] = {}
        for gt in gt_infos:
            if not gt.contexts:
                continue
            for ctx in gt.contexts:
                sug_list = getattr(ctx, 'suggestions', None)
                if not sug_list:
                    continue
                best_item = max(
                    sug_list,
                    key=lambda s: (s.best_match_score if s.best_match_score is not None else -1.0)
                )
                new_text = best_item.best_match_context or best_item.node_context or ctx.text
                new_ctx = GroundTruthContext(
                    filename=ctx.filename,
                    text=new_text,
                    context_id=ctx.context_id,
                    pages=ctx.pages,
                    section=ctx.section,
                    suggestions=[]
                )
                if gt.query_id not in new_gt_map:
                    new_gt_map[gt.query_id] = GroundTruth(
                        query_id=gt.query_id,
                        query=gt.query,
                        contexts=[new_ctx],
                        answer=gt.answer
                    )
                else:
                    new_gt_map[gt.query_id].contexts.append(new_ctx)
        return list(new_gt_map.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build GT with suggestions: {e}")


@pilot_app.post(path="/v1/pilot/ground_truth/file")
async def update_rag_ground_truth_file(file: UploadFile = File(...)):
    filetype = ""
    if file.filename.endswith('.csv'):
        filetype = "csv"
    elif file.filename.endswith('.json'):
        filetype = "json"
    else:
        raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported.")

    try:
        await file.seek(0)
        rag_results = load_rag_results_from_uploaded_file(file, filetype)

        if not rag_results.results:
            raise ValueError("No results found in the uploaded file.")

        if pilot.update_target_query_gt(rag_results):
            pilot.clear_rag_result_dict()
            for stage in RAGStage:
                pilot.tuner_mgr.reset_tuners_by_stage(stage)
            return "RAG ground truth file updated and database cleared"
        else:
            return "Error"

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@pilot_app.post(path="/v1/pilot/save")
async def save_dicts():
    folder = pilot.save_dicts()
    return f"All results saved in {folder}"


@pilot_app.get("/v1/pilot/get_available_docs")
async def get_available_docs():
    try:
        documents_info = pilot.adaptor.get_available_documents()
        return documents_info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve available documents: {str(e)}")


@pilot_app.post(path="/v1/pilot/match/setting")
async def update_match_settings(settings: MatchSettings):

    try:

        if settings.hit_threshold is not None:
            pilot.hit_threshold = settings.hit_threshold

        if settings.enable_fuzzy is not None:
            pilot.enable_fuzzy = settings.enable_fuzzy

        if settings.confidence_topn is not None:
            pilot.confidence_topn = settings.confidence_topn

        return pilot.get_match_settings()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update match settings: {e}")
