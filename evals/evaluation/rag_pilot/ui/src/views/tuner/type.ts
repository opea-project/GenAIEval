// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ContextItem {
  context_idx: number;
  file_name: string;
  text: string;
  metadata?: EmptyObjectType;
  hitRetrieveContexts?: EmptyArrayType;
  [key: string]: any;
}

export interface ResultOut {
  index?: number;
  query_id: number;
  query: string;
  response?: string;
  metadata?: EmptyObjectType;
  ground_truth?: string;
  gt_contexts: ContextItem[];
  retrieval_contexts?: ContextItem[];
  postprocessing_contexts?: ContextItem[];
  base?: EmptyObjectType;
  [key: string]: any;
}

export interface ResultsOut {
  metadata?: EmptyObjectType;
  results: ResultOut[];
  [key: string]: any;
}

export interface TunerOut {
  stage: string;
  name: string;
  targets: string;
  active: boolean;
}
