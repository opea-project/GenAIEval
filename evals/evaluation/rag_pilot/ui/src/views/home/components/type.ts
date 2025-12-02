// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface FormType {
  annotation: QueryType[];
}
export interface ContextItem {
  filename: string | undefined;
  text: string;
  section: string;
  pages: string | string[];
  suggestions?: SuggestionItem[];
  context_id?: number;
  isSelected?: boolean;
}
export interface QueryType {
  query_id?: number | undefined;
  query: string;
  answer?: string;
  contexts: ContextItem[];
  isSubmit?: boolean;
  isPass?: boolean;
  collapse?: boolean;
}
export interface SuggestionItem {
  node_id: string;
  node_page_label: string;
  node_context: string;
  best_match_context: string;
  best_match_score: number;
}
