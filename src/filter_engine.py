"""
过滤引擎
负责期刊/会议白名单过滤、关键词匹配过滤、语义相似度过滤、时间范围过滤。
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import numpy as np

logger = logging.getLogger(__name__)


class FilterEngine:
    """多层过滤引擎。"""

    def __init__(self, config: Any):
        """
        Args:
            config: ConfigManager 实例
        """
        self.config = config

        # 期刊过滤
        self.journal_enabled: bool = config.get("journal_filter.enabled", True)
        self.journal_levels: Dict = config.get("journal_filter.levels", {})
        self.active_levels: List[str] = config.get("journal_filter.active_levels", [])

        # 语义过滤
        self.semantic_enabled: bool = config.get("semantic_filter.enabled", False)
        self.semantic_threshold: float = config.get("semantic_filter.threshold", 0.5)
        self.semantic_model: str = config.get("semantic_filter.model", "BAAI/bge-small-en-v1.5")

        # 时间
        self.since_days: int = config.get("freshness.since_days", 3)

        # 构建期刊白名单集合
        self._journal_set: Set[str] = self._build_journal_set()

    # ------------------------------------------------------------------
    # 期刊 / 会议过滤
    # ------------------------------------------------------------------

    def filter_by_journal(self, papers: List[Dict]) -> List[Dict]:
        """
        根据期刊/会议白名单过滤。

        Args:
            papers: 论文列表

        Returns:
            通过过滤的论文列表
        """
        if not self.journal_enabled or not self._journal_set:
            return papers

        filtered = []
        for paper in papers:
            journal_ref = paper.get("journal_ref", "").lower()
            comment = paper.get("comment", "").lower()
            combined = journal_ref + " " + comment

            # 检查是否命中白名单
            matched = False
            for venue in self._journal_set:
                if venue.lower() in combined:
                    matched = True
                    paper["matched_journal"] = venue
                    break

            if matched:
                filtered.append(paper)

        logger.info(f"期刊过滤: {len(papers)} -> {len(filtered)} 篇")
        return filtered

    def _build_journal_set(self) -> Set[str]:
        """构建生效的期刊/会议白名单集合。"""
        if not self.active_levels:
            return set()

        journal_set: Set[str] = set()
        for level in self.active_levels:
            venues = self.journal_levels.get(level, [])
            for v in venues:
                journal_set.add(v.strip())

        logger.info(f"期刊白名单: {len(journal_set)} 个期刊/会议 ({self.active_levels})")
        return journal_set

    # ------------------------------------------------------------------
    # 语义相似度过滤
    # ------------------------------------------------------------------

    def filter_by_semantic(
        self,
        new_papers: List[Dict],
        reference_papers: List[Dict],
        embedder: Any = None,
    ) -> List[Dict]:
        """
        基于语义相似度过滤：仅保留与参考论文库有足够差异的论文。

        Args:
            new_papers: 待过滤的新论文列表
            reference_papers: 参考论文库（如本地论文库）
            embedder: PaperEmbedder 实例（如已加载）

        Returns:
            通过过滤的论文列表
        """
        if not self.semantic_enabled or not reference_papers:
            return new_papers

        if embedder is None:
            logger.warning("语义过滤需要 embedder 实例，已跳过")
            return new_papers

        # 计算参考库 embedding
        ref_texts = [
            f"Represent this paper for retrieval: {p.get('title', '')}. {p.get('abstract', '')}"
            for p in reference_papers
        ]
        ref_embeddings = embedder.model.encode(
            ref_texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True
        )

        # 计算新论文 embedding
        new_embeddings = embedder.encode_papers(new_papers, batch_size=32)

        # 计算最大相似度
        max_similarities = (new_embeddings @ ref_embeddings.T).max(axis=1)

        filtered = []
        removed = 0
        for i, paper in enumerate(new_papers):
            if max_similarities[i] < self.semantic_threshold:
                filtered.append(paper)
            else:
                removed += 1

        logger.info(
            f"语义过滤 (threshold={self.semantic_threshold}): "
            f"{len(new_papers)} -> {len(filtered)} 篇 (移除 {removed} 篇相似论文)"
        )
        return filtered

    # ------------------------------------------------------------------
    # 时间范围过滤
    # ------------------------------------------------------------------

    def filter_by_date(self, papers: List[Dict], lookback_days: Optional[int] = None) -> List[Dict]:
        """
        按发布时间过滤。

        Args:
            papers: 论文列表
            lookback_days: 回溯天数，默认使用配置中的值

        Returns:
            过滤后的论文列表
        """
        days = lookback_days or self.since_days
        cutoff_date = datetime.now() - timedelta(days=days)

        filtered = []
        for paper in papers:
            date_str = paper.get("published", "") or paper.get("updated", "")
            if not date_str:
                filtered.append(paper)  # 保留无日期信息的论文
                continue
            try:
                paper_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                paper_date = paper_date.replace(tzinfo=None)
                if paper_date >= cutoff_date:
                    filtered.append(paper)
            except (ValueError, TypeError):
                filtered.append(paper)

        return filtered

    # ------------------------------------------------------------------
    # 组合过滤
    # ------------------------------------------------------------------

    def apply_all(
        self,
        papers: List[Dict],
        local_papers: Optional[List[Dict]] = None,
        embedder: Any = None,
        lookback_days: Optional[int] = None,
    ) -> List[Dict]:
        """
        应用所有已启用的过滤。

        Args:
            papers: 待过滤论文
            local_papers: 本地论文库（用于语义过滤参考）
            embedder: PaperEmbedder 实例
            lookback_days: 回溯天数

        Returns:
            过滤后的论文
        """
        result = papers

        # 1. 时间过滤
        result = self.filter_by_date(result, lookback_days)

        # 2. 期刊过滤
        result = self.filter_by_journal(result)

        # 3. 语义过滤
        if self.semantic_enabled and local_papers:
            result = self.filter_by_semantic(result, local_papers, embedder)

        logger.info(f"组合过滤完成: {len(papers)} -> {len(result)} 篇")
        return result
