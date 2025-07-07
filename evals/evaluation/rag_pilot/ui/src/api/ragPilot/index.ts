// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";
export const getActivePipeline = () => {
  return request({
    url: "v1/pilot/pipeline/active/id",
    method: "get",
    showLoading: true,
  });
};

export const getActivePipelineDetail = () => {
  return request({
    url: "v1/pilot/pipeline/active",
    method: "get",
    showLoading: true,
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
    showLoading: true,
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
    showLoading: true,
  });
};

export const requesPipelineRun = () => {
  return request({
    url: "v1/pilot/pipeline/active/run",
    method: "post",
  });
};

export const requesStageRun = (stageName: String) => {
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
export const getBasePipelineByTuner = (tunerName: String) => {
  return request({
    url: `v1/tuners/${tunerName}/pipeline/base`,
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
    showLoading: true,
  });
};

export const requesPromptUpdate = (data: Object) => {
  return request({
    url: `v1/tuners/results/getPromptList`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Prompt update successfully !",
  });
};

export const requesPromptActive = (data: Object) => {
  return request({
    url: `v1/tuners/results/getPromptList`,
    method: "patch",
    data,
  });
};

export const requesTopnUpdate = (top_n: String) => {
  return request({
    url: `v1/pilot/pipeline/active/top_n/${top_n}`,
    method: "patch",
  });
};
export const requesStageReset = (stage: String) => {
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
    successMsg: "Update successful !",
  });
};
export const requestSubmitQueryJson = (data: EmptyArrayType) => {
  return request({
    url: "/v1/pilot/ground_truth",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Create successful !",
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

export const uploadPipelineFileUrl = `${
  import.meta.env.VITE_API_URL
}v1/pilot/pipeline/active/import`;

export const uploadQueryFileUrl = `${
  import.meta.env.VITE_API_URL
}v1/pilot/ground_truth/file`;

export const exportPipelineUrl = (pipelineId: Number) => {
  return `${
    import.meta.env.VITE_API_URL
  }v1/pilot/pipeline/${pipelineId}/export`;
};
