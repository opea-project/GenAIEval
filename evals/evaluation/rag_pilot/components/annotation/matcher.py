# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re
from typing import List, Optional, Tuple, Dict, Any
from difflib import SequenceMatcher
import logging

from .schemas import GTMatchResult, AnnotationRequest, SuggestionItem
from llama_index.core.schema import TextNode

logger = logging.getLogger(__name__)


class Matcher:

    def __init__(self, similarity_threshold: float = 0.8, enable_fuzzy: bool = False, confidence_topn: int = 5):
        self.similarity_threshold = similarity_threshold
        self.enable_fuzzy = enable_fuzzy
        self.confidence_topn = confidence_topn

    def match_gt_chunks(self, request: AnnotationRequest, available_nodes: List[TextNode]) -> GTMatchResult:
        try:
            exact_matches: List[TextNode] = []
            partial_matches: List[TextNode] = []
            self.update_settings(
                similarity_threshold=request.similarity_threshold,
                enable_fuzzy=request.enable_fuzzy,
                confidence_topn=request.confidence_topn,
            )
            # Apply all filtering logic in Matcher(now only have page filter)
            relevant_nodes = self._filter_nodes_for_matching(available_nodes, request)
            # Note: If the issue that duplicate nodes in ecrag solve, then no need to do deduplication here
            relevant_nodes = self._deduplicate_chunks(relevant_nodes)
            # Perform text matching
            node_confidences: Dict[str, float] = {}
            node_lookup: Dict[str, TextNode] = {}
            for node in relevant_nodes:
                match_type, confidence = self.match_texts(node.text, request.gt_text_content)
                node_id = node.node_id
                node_confidences[node_id] = confidence
                node_lookup[node_id] = node

                if match_type == "exact":
                    exact_matches.append(node)
                elif match_type == "partial":
                    partial_matches.append(node)

            match_res = exact_matches + partial_matches
            best_chunk = None
            best_conf = -1.0
            # Select the best matched chunk based on confidence score
            for node in match_res:
                nid = node.node_id
                conf = node_confidences.get(nid, 0.0)
                if conf > best_conf:
                    best_conf = conf
                    best_chunk = node

            # Only create suggestion_items if no matched chunk found
            suggestion_items = []
            if best_chunk is None:
                sorted_conf = sorted(node_confidences.items(), key=lambda x: x[1], reverse=True)
                top_conf = sorted_conf[: self.confidence_topn]
                for nid, score in top_conf:
                    n = node_lookup.get(nid)
                    if not n:
                        continue
                    seg, seg_score = self._extract_best_match_segment(n.text, request.gt_text_content)
                    suggestion_items.append(
                        SuggestionItem(
                            node_id=nid,
                            node_page_label=n.metadata.get('page_label', ''),
                            node_context=n.text,
                            confidence_score=score,
                            best_match_context=seg,
                            best_match_score=seg_score,
                        )
                    )
            logger.info(f"[Matcher] Matching completed for query_id: {request.query_id} , context_id: {request.context_id}")

            return GTMatchResult(
                context_id=request.context_id,
                context_text=request.gt_text_content,
                matched_chunk=best_chunk,
                suggestion_items=suggestion_items,
            )

        except Exception as e:
            logger.error(f"[Matcher] Error matching GT chunks: {e}")
            return GTMatchResult(
                context_id=request.context_id,
                context_text=request.gt_text_content,
                matched_chunk=None,
                suggestion_items=[],
            )

    def _filter_nodes_for_matching(self, nodes: List[TextNode], request: AnnotationRequest) -> List[TextNode]:
        relevant_nodes = nodes
        # Filter by pages if specified
        if request.gt_pages:
            relevant_nodes = self._filter_nodes_by_pages(
                relevant_nodes, request.gt_pages)

        # Future: Add more filtering criteria here
        # if request.gt_section:
        #     relevant_nodes = self._filter_nodes_by_section(relevant_nodes, request.gt_section)
        # if request.date_range:
        #     relevant_nodes = self._filter_nodes_by_date(relevant_nodes, request.date_range)

        return relevant_nodes

    def _filter_nodes_by_pages(self, nodes: List[TextNode], target_pages: List[str]) -> List[TextNode]:
        if not target_pages:
            return nodes

        # Check if any nodes have page_label information
        has_page_info = any(node.metadata.get('page_label') for node in nodes)

        # If no nodes have page information, return all nodes (cannot filter)
        if not has_page_info:
            logger.warning(
                f"[Matcher] No page_label information found in nodes, returning all {len(nodes)} nodes")
            return nodes

        relevant_nodes = []
        for node in nodes:
            page_label = node.metadata.get('page_label', '')
            if page_label and page_label in target_pages:
                relevant_nodes.append(node)
        # If we have page info but no matches, return empty list (strict filtering)
        # If we found matches, return them
        return relevant_nodes

    def _is_filename_match(self, node_filename: str, target_filename: str) -> bool:
        if not node_filename or not target_filename:
            return False

        # 1. Exact match
        if node_filename.lower() == target_filename.lower():
            return True

        # 2. Extract base filename (remove path and extension) for matching
        node_base = self._extract_base_filename(node_filename)
        target_base = self._extract_base_filename(target_filename)

        if node_base.lower() == target_base.lower():
            return True

        # 3. Partial match - check if target filename is contained in node filename
        if target_base.lower() in node_base.lower():
            return True

        # 4. Handle special cases: e.g. "9-TCB Bonder-TCB BKM_v12 1.docx" and "TCB_Bonder_Manual.pdf"
        # Normalize filenames: remove version numbers, special characters, etc.
        node_normalized = self._normalize_filename(node_base)
        target_normalized = self._normalize_filename(target_base)

        if node_normalized in target_normalized or target_normalized in node_normalized:
            return True

        # 5. Keyword matching: extract keywords from filenames for matching
        node_keywords = self._extract_keywords(node_base)
        target_keywords = self._extract_keywords(target_base)

        # If there's sufficient keyword overlap, consider it a match
        common_keywords = node_keywords.intersection(target_keywords)
        if len(common_keywords) >= 2 or (len(common_keywords) >= 1 and len(node_keywords) <= 2):
            return True

        return False

    def _normalize_filename(self, filename: str) -> str:
        # Convert to lowercase
        normalized = filename.lower()

        # Remove common version patterns: v1, v2, _v12, etc.
        normalized = re.sub(r'[_\-\s]*v\d+[._\d]*', '', normalized)

        # Remove numeric suffixes: e.g. "1", "2", etc.
        normalized = re.sub(r'[_\-\s]*\d+$', '', normalized)

        # Unify separators: replace - _ spaces with single separator
        normalized = re.sub(r'[-_\s]+', '_', normalized)

        # Remove leading and trailing separators
        normalized = normalized.strip('_')

        return normalized

    def _extract_keywords(self, filename: str) -> set:
        # Split filename
        words = re.split(r'[-_\s]+', filename.lower())

        # Filter out short words, numbers and common meaningless words
        meaningful_words = set()
        stopwords = {'v', 'ver', 'version', 'doc',
                     'pdf', 'docx', 'manual', 'guide', 'bkm'}

        for word in words:
            # Keep words longer than 2 characters that are not pure numbers and not in stopwords
            if len(word) > 2 and not word.isdigit() and word not in stopwords:
                meaningful_words.add(word)

        return meaningful_words

    def _extract_base_filename(self, filename: str) -> str:
        import os
        base = os.path.basename(filename)
        # Remove extension
        base = os.path.splitext(base)[0]
        return base

    def match_texts(self, node_text: str, gt_text: str) -> Tuple[str, float]:
        # Exact match check
        if self._is_exact_match(node_text, gt_text):
            return "exact", 1.0

        # Partial match check
        similarity = self._calculate_similarity(node_text, gt_text)

        if similarity >= self.similarity_threshold:
            return "partial", similarity

        # If fuzzy matching is enabled, try more lenient matching
        if self.enable_fuzzy:
            fuzzy_similarity = self._fuzzy_match(node_text, gt_text)
            if fuzzy_similarity >= self.similarity_threshold * 0.7:  # Lower threshold
                return "partial", fuzzy_similarity

        return "none", similarity

    def _is_exact_match(self, text1: str, text2: str) -> bool:
        # Normalize text (remove excess whitespace, unify line breaks)
        normalized_text1 = self._normalize_text_for_match(text1)
        normalized_text2 = self._normalize_text_for_match(text2)

        # 1. Complete match
        if normalized_text1 == normalized_text2:
            return True

        # 2. Direct containment match
        if normalized_text1 in normalized_text2 or normalized_text2 in normalized_text1:
            return True

        # 3. More lenient matching: compare after removing all spaces
        text1_no_space = re.sub(r'\s+', '', normalized_text1)
        text2_no_space = re.sub(r'\s+', '', normalized_text2)

        if text1_no_space in text2_no_space or text2_no_space in text1_no_space:
            return True

        # 4. Keyword matching: extract key parts for matching
        # For title-like texts (e.g. "14.14 How to clean nozzle/pedestal/OT camera/Asymetk setup tray")
        shorter, longer = (normalized_text1, normalized_text2) if len(
            normalized_text1) < len(normalized_text2) else (normalized_text2, normalized_text1)

        # Break down into keywords for matching
        shorter_keywords = self._extract_matching_keywords(shorter)
        longer_keywords = self._extract_matching_keywords(longer)

        # If all keywords from shorter text are found in longer text, consider it a match
        if shorter_keywords and all(keyword in longer_keywords for keyword in shorter_keywords):
            return True

        # 5. For shorter texts, check if it's a subset of longer text (lower threshold)
        if len(shorter) < len(longer) * 0.5 and shorter in longer:
            return True

        return False

    def _normalize_text_for_match(self, text: str) -> str:
        # Remove excess whitespace and line breaks
        normalized = re.sub(r'\s+', ' ', text.strip())

        # Remove special Unicode characters like zero-width spaces
        normalized = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', normalized)

        return normalized

    def _extract_matching_keywords(self, text: str) -> set:
        keywords = set()

        # 1. Extract number identifiers (like 14.14)
        number_patterns = re.findall(r'\d+\.?\d*', text)
        keywords.update(number_patterns)

        # 2. Extract English words
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        keywords.update([word for word in english_words if len(word) > 2])

        # 3. Extract Chinese words (simple segmentation)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        for segment in chinese_chars:
            if len(segment) >= 2:
                # Add entire Chinese segment
                keywords.add(segment)
                # Also add longer sub-segments
                for i in range(len(segment)):
                    for length in [4, 3, 2]:
                        if i + length <= len(segment):
                            keywords.add(segment[i:i+length])

        # 4. Extract special symbol-separated terms
        special_terms = re.findall(r'[a-zA-Z]+/[a-zA-Z]+', text.lower())
        keywords.update(special_terms)

        return keywords

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        return SequenceMatcher(None, text1, text2).ratio()

    def _fuzzy_match(self, text1: str, text2: str) -> float:
        # Tokenize and calculate overlap
        words1 = set(self._tokenize_mixed_language(text1.lower()))
        words2 = set(self._tokenize_mixed_language(text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        # Jaccard similarity
        jaccard_sim = intersection / union if union > 0 else 0.0

        # Consider vocabulary coverage
        coverage1 = intersection / len(words1) if words1 else 0.0
        coverage2 = intersection / len(words2) if words2 else 0.0

        # Combined score: Jaccard similarity + weighted maximum coverage
        combined_score = 0.6 * jaccard_sim + 0.4 * max(coverage1, coverage2)

        return combined_score

    def _tokenize_mixed_language(self, text: str) -> List[str]:
        tokens = []

        # 1. Extract English words (including numbers and hyphens)
        english_pattern = r'[a-zA-Z]+(?:[-_][a-zA-Z0-9]+)*'
        english_words = re.findall(english_pattern, text)
        tokens.extend([word.lower()
                      for word in english_words if len(word) > 1])

        # 2. Extract numbers (if meaningful)
        number_pattern = r'\d+\.?\d*'
        numbers = re.findall(number_pattern, text)
        tokens.extend([num for num in numbers if len(num) > 0])

        # 3. Simple character-level tokenization for Chinese (can be improved with tools like jieba)
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_segments = re.findall(chinese_pattern, text)
        for segment in chinese_segments:
            # For Chinese, can split by characters or use advanced tokenization tools
            if len(segment) > 1:
                # Tokenize by 2-3 character combinations
                for i in range(len(segment)):
                    for length in [3, 2, 1]:  # Prefer 3-character words, then 2-character words
                        if i + length <= len(segment):
                            token = segment[i:i+length]
                            tokens.append(token)
            else:
                tokens.append(segment)

        # 4. Extract special technical terms (containing combinations of letters and numbers)
        technical_pattern = r'[a-zA-Z]*\d+[a-zA-Z]*|\d+[a-zA-Z]+[0-9]*'
        technical_terms = re.findall(technical_pattern, text)
        tokens.extend([term.lower()
                      for term in technical_terms if len(term) > 1])

        # Deduplicate and filter
        unique_tokens = []
        seen = set()
        for token in tokens:
            if token not in seen and len(token) > 0:
                unique_tokens.append(token)
                seen.add(token)

        return unique_tokens
    
    def _deduplicate_chunks(self, chunks: List[TextNode]) -> List[TextNode]:
        seen_contents = set()
        unique_chunks = []
        
        for chunk in chunks:
            # Create a signature based on text content and key metadata
            # Use file_path and page info to distinguish legitimate duplicates
            content_signature = (chunk.text.strip())
            if content_signature not in seen_contents:
                seen_contents.add(content_signature)
                unique_chunks.append(chunk)
            else:
                logger.warning(f"[Matcher] Duplicate chunk detected and removed: node_id={chunk.node_id}, "
                               f"file={chunk.metadata.get('file_name', 'unknown')}, "
                               f"page={chunk.metadata.get('page_label', 'unknown')},"
                               f"start_char_ids={chunk.metadata.get('start_char_ids', 'unknown')}, "
                               f"end_char_ids={chunk.metadata.get('end_char_ids', 'unknown')} "
                               )

        logger.info(f"[Matcher] Deduplication: {len(chunks)} -> {len(unique_chunks)} chunks")
        return unique_chunks

    def _tokenize(self, text: str) -> List[str]:
        return self._tokenize_mixed_language(text)

    def update_settings(self,
        similarity_threshold: Optional[float] = None,
        enable_fuzzy: Optional[bool] = None,
        confidence_topn: Optional[int] = None,
    ):
        if similarity_threshold is not None:
            if 0.0 <= similarity_threshold <= 1.0:
                self.similarity_threshold = similarity_threshold
            else:
                raise ValueError("[Matcher] Similarity threshold must be between 0.0 and 1.0")
        if enable_fuzzy is not None:
            self.enable_fuzzy = enable_fuzzy
        if confidence_topn is not None:
            if confidence_topn > 0:
                self.confidence_topn = confidence_topn
            else:
                raise ValueError("[Matcher] confidence_topn must be a positive integer")

    @staticmethod
    def _extract_best_match_segment(node_text: str, gt_text: str) -> Tuple[Optional[str], Optional[float]]:
        if not node_text or not gt_text:
            return None, None
        target_len = len(gt_text)
        if target_len == 0 or len(node_text) < target_len:
            return None, None

        best_score = -1.0
        best_segment = None

        for start in range(0, len(node_text) - target_len + 1):
            window = node_text[start : start + target_len]
            score = SequenceMatcher(None, window, gt_text).ratio()
            if score > best_score:
                best_score = score
                best_segment = window
                if score >= 1.0:
                    break

        if best_segment is None:
            return None, None
        return best_segment, best_score

default_matcher = Matcher(similarity_threshold=0.8, enable_fuzzy=False, confidence_topn=5)
