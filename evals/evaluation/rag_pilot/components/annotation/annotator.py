# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
import uuid
from typing import List, Dict, Optional
import asyncio
import logging

from .schemas import (
    AnnotationRequest, AnnotationResponse, GTMatchResult, SuggestionItem, QueryGTMatchResults
)
from .matcher import Matcher, default_matcher
from llama_index.core.schema import TextNode

logger = logging.getLogger(__name__)


class Annotator:

    def __init__(self, matcher: Optional[Matcher] = None):
        self.matcher = matcher or default_matcher
        self._node_cache: Dict[str, List[TextNode]] = {}
        self.matched_results: Dict[int, QueryGTMatchResults] = {}

    def annotate(self, request: AnnotationRequest) -> AnnotationResponse:
        try:
            available_nodes = self._get_available_nodes(request.gt_file_name)
            match_result = self.matcher.match_gt_chunks(request, available_nodes)
            self._merge_match_result(request.query_id, request.query, match_result)
            return AnnotationResponse(
                success = match_result.matched_chunk is not None,
                message="Annotation completed successfully",
                suggestion_items=match_result.suggestion_items
            )

        except Exception as e:
            logger.error(f"[Annotator] Error in annotation process: {e}")

            empty_result = GTMatchResult(
                context_id=request.context_id,
                context_text=request.gt_text_content,
                matched_chunk=None,
                suggestion_items=[]
            )

            self._merge_match_result(request.query_id, request.query, empty_result)

            return AnnotationResponse(
                success=False,
                message=f"Annotation failed: {str(e)}",
                suggestion_items=[]
            )

    def _merge_match_result(self, query_id: int, query: str, new_result: GTMatchResult):
        ctx_id = new_result.context_id
        container = self.matched_results.get(query_id)
        if container is None:
            container = QueryGTMatchResults(query_id=query_id, query=query, context_map={})
            self.matched_results[query_id] = container
            logger.info(f"[Annotator] Created QueryGTMatchResults for query_id {query_id}")

        is_replace = ctx_id in container.context_map
        container.context_map[ctx_id] = new_result
        action = 'Replaced' if is_replace else 'Added'
        logger.info(f"[Annotator] {action} match result query_id={query_id} context_id={ctx_id}")


    def _get_available_nodes(self, file_name: str) -> List[TextNode]:
        from components.pilot.pilot import pilot
        # Check exist cache
        if file_name in self._node_cache:
            return self._node_cache[file_name]

        # Get TextNode objects directly from EdgeCraftRAG (now returns List[TextNode])
        nodes = pilot.adaptor.get_document_chunks(file_name)
        # Save Cache results
        self._node_cache[file_name] = nodes
        return nodes

    def clear_caches(self):
        self.matched_results.clear()
        self._node_cache.clear()


    def get_all_match_results(self) -> Dict[int, QueryGTMatchResults]:
        return self.matched_results.copy()


annotator = Annotator(default_matcher)
