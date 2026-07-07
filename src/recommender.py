"""
论文推荐器
计算新论文与本地论文库的余弦相似度，推荐最相似的本地论文。
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from .embedder import PaperEmbedder
from .cache import EmbeddingCache

logger = logging.getLogger(__name__)


class PaperRecommender:
    """
    论文推荐器。

    流程：
    1. 加载/计算本地论文库 embedding（优先缓存）
    2. 计算新论文 embedding
    3. 计算余弦相似度（embedding 已 L2 归一化，直接用点积）
    4. 为每篇新论文推荐 top_k 篇最相似的本地论文
    """

    def __init__(
        self,
        config: Any,
        embedder: Optional[PaperEmbedder] = None,
        cache: Optional[EmbeddingCache] = None,
    ):
        """
        Args:
            config: ConfigManager 实例
            embedder: PaperEmbedder 实例（可选，自动创建）
            cache: EmbeddingCache 实例（可选，自动创建）
        """
        self.config = config
        self.top_k: int = config.get("local_recommend.top_k_neighbors", 5)
        self.max_recommend: int = config.get("local_recommend.max_recommend", 10)
        self.model_name: str = config.get("local_recommend.embedding_model", "BAAI/bge-small-en-v1.5")
        self.batch_size: int = config.get("semantic_filter.batch_size", 32)

        self.embedder = embedder or PaperEmbedder(self.model_name)
        self.cache = cache or EmbeddingCache(config.get("local_recommend.cache_dir", ".cache/recommender"))

        self._library_embeddings: Optional[np.ndarray] = None
        self._library_papers: List[Dict] = []

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def recommend(self, new_papers: List[Dict], local_papers: List[Dict]) -> List[Dict]:
        """
        为每篇新论文推荐最相似的本地论文。

        Args:
            new_papers: arXiv 检索到的新论文列表
            local_papers: 本地论文库列表（来自 BibLoader）

        Returns:
            new_papers 增强版，每篇增加了 recommend 字段：
            {
                "score": float,           # 最高匹配分数
                "matches": [
                    {"title": str, "score": float, "source_file": str},
                    ...
                ]
            }
        """
        if not local_papers:
            logger.warning("本地论文库为空，跳过推荐")
            return new_papers

        if not new_papers:
            return new_papers

        # 1. 获取库 embedding（优先缓存）
        self._ensure_library_embeddings(local_papers)

        # 2. 计算新论文 embedding
        logger.info(f"计算 {len(new_papers)} 篇新论文的 embedding")
        new_embeddings = self.embedder.encode_papers(
            new_papers, batch_size=self.batch_size
        )

        # 3. 计算相似度矩阵
        # new_embeddings: N x D, library_embeddings: M x D
        # scores: N x M（余弦相似度 = 点积，因为已归一化）
        scores = new_embeddings @ self._library_embeddings.T  # type: ignore

        # 4. 为每篇新论文取 top_k
        top_k = min(self.top_k, len(local_papers))
        for i, paper in enumerate(new_papers):
            paper_scores = scores[i]
            top_indices = np.argsort(paper_scores)[::-1][:top_k]

            matches = []
            for idx in top_indices:
                score = float(paper_scores[idx])
                if score > 0:
                    local_p = self._library_papers[idx]
                    matches.append({
                        "title": local_p.get("title", ""),
                        "score": round(score, 4),
                        "source_file": local_p.get("source_file", ""),
                        "year": local_p.get("year", ""),
                    })

            paper["recommend"] = {
                "score": round(float(paper_scores.max()), 4),
                "matches": matches,
            }

        # 按最高推荐分数排序
        new_papers.sort(
            key=lambda p: p.get("recommend", {}).get("score", 0.0),
            reverse=True,
        )

        logger.info(f"推荐完成: {len(new_papers)} 篇论文已生成推荐")
        return new_papers

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _ensure_library_embeddings(self, local_papers: List[Dict]) -> None:
        """确保本地论文库 embedding 已加载，优先使用缓存。"""
        if self.cache.is_library_cache_valid(self.model_name):
            cache_data = self.cache.load_library_cache()
            if cache_data:
                cached_count = cache_data.get("count", 0)
                if cached_count == len(local_papers):
                    # 缓存数量匹配，直接使用
                    self._library_embeddings = cache_data["embeddings"]
                    self._library_papers = cache_data["papers"]
                    logger.info(f"从缓存加载库 embedding: {cached_count} 条")
                    return

        # 重新计算
        logger.info("缓存不可用或数量不匹配，重新计算库 embedding")
        self._library_embeddings = self.embedder.encode_papers(
            local_papers, batch_size=self.batch_size
        )
        self._library_papers = local_papers
        self.cache.save_library_cache(
            self._library_embeddings, local_papers, self.model_name
        )

    @property
    def is_ready(self) -> bool:
        """推荐器是否已就绪（库 embedding 已加载）。"""
        return self._library_embeddings is not None and len(self._library_papers) > 0
