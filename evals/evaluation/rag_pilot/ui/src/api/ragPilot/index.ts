// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";
export const getActivePipeline = () => {
  return request({
    url: "v1/pilot/pipeline/active/id",
    method: "get",
  });
};

export const getActivePipelineDetail = () => {
  return request({
    url: "v1/pilot/pipeline/active",
    method: "get",
  });
};

export const getPipelineDetailById = (pipelineId: Number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}`,
    method: "get",
  });
};

export const requestResultsMetrics = (
  pipelineId: Number,
  data: EmptyArrayType
) => {
  return request({
    url: `/v1/pilot/pipeline/${pipelineId}/results/metrics`,
    method: "patch",
    data,
  });
};

export const getResultsByPipelineId = (pipelineId: Number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}/results`,
    method: "get",
  });
};

export const getMetricsByPipelineId = (pipelineId: Number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}/results/metrics`,
    method: "get",
  });
};

export const requestPipelineRun = (pipelineId: Number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}/run`,
    method: "post",
  });
};

export const requestStageRun = (stageName: String) => {
  return request({
    url: `v1/tuners/stage/${stageName}/run`,
    method: "post",
  });
};

export const getStageDetail = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}`,
    method: "get",
  });
};
export const getStageStatus = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}/status`,
    method: "get",
  });
};

export const getStagePipelines = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}/pipelines`,
    method: "get",
  });
};

export const getResultsByStage = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}/results`,
    method: "get",
  });
};

export const getMetricsByStage = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}/results/metrics`,
    method: "get",
  });
};
export const getPipelinesByTuner = (tunerName: String) => {
  return request({
    url: `v1/tuners/${tunerName}/pipelines`,
    method: "get",
  });
};

export const getTunerStatus = (tuner: String) => {
  return request({
    url: `v1/tuners/${tuner}/status`,
    method: "get",
  });
};
export const getPrompById = (pipelineId: number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}/prompt`,
    method: "get",
  });
};

export const requestPromptUpdate = (data: Object) => {
  return request({
    url: `v1/tuners/results/getPromptList`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Prompt update successfully !",
  });
};

export const requestPromptActive = (data: Object) => {
  return request({
    url: `v1/tuners/results/getPromptList`,
    method: "patch",
    data,
  });
};

export const requestPipelineActive = (pipelineId: Number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}/active`,
    method: "post",
  });
};
export const requestStageReset = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}/reset`,
    method: "post",
  });
};

export const requestPipelineSync = (pipelineId: Number) => {
  return request({
    url: `v1/pilot/pipeline/${pipelineId}/active`,
    method: "post",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.updateSucc",
  });
};

export const getResultStatus = () => {
  return request({
    url: `v1/tuners/stage/reset`,
    method: "post",
  });
};

export const getBestPipelineByStage = (stage: String) => {
  return request({
    url: `v1/tuners/stage/${stage}/pipelines/best/id`,
    method: "get",
  });
};
export const requestPipelineReset = () => {
  return request({
    url: "v1/pilot/pipeline/reconcil",
    method: "post",
  });
};

export const getFileList = () => {
  return request({
    url: "v1/pilot/get_available_docs",
    method: "get",
  });
};

export const requestAnnotateSave = (data: EmptyArrayType) => {
  return request({
    url: "v1/pilot/ground_truth",
    method: "post",
    data,
    showLoading: true,
  });
};

export const getAnnotateGroundTruth = () => {
  return request({
    url: "/v1/pilot/ground_truth",
    method: "get",
  });
};

export const requestAnnotationReset = () => {
  return request({
    url: "v1/pilot/ground_truth/clear_cache",
    method: "post",
    showLoading: true,
  });
};

export const getTunerAllConfiguration = () => {
  return request({
    url: "v1/avail_tuners",
    method: "get",
  });
};
export const getStageTunerConfiguration = (stageName: string) => {
  return request({
    url: `v1/tuners/${stageName}`,
    method: "get",
  });
};
export const getTunerEffectiveConfiguration = () => {
  return request({
    url: "v1/tuners",
    method: "get",
  });
};
export const requestTunerRegister = (data: EmptyObjectType) => {
  return request({
    url: "v1/tuners/register",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.registerSucc",
  });
};

export const getRagEndpoint = () => {
  return request({
    url: "v1/pilot/settings",
    method: "get",
  });
};

export const requestRagEndpointSet = (data: EmptyObjectType) => {
  return request({
    url: "v1/pilot/settings",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.configSucc",
  });
};

export const getPromptlById = (pipelineId: Number) => {
  return request({
    url: `/v1/pilot/pipeline/${pipelineId}/prompt`,
    method: "get",
  });
};

export const uploadQueryFileUrl = `${
  import.meta.env.VITE_API_URL
}v1/pilot/ground_truth/file`;

export const exportPipelineUrl = (pipelineId: Number) => {
  return `${
    import.meta.env.VITE_API_URL
  }v1/pilot/pipeline/${pipelineId}/export`;
};
