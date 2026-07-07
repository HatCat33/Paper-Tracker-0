"""
Embedding 缓存管理器
缓存本地论文库和 arXiv 历史论文的 embedding，支持增量更新。
"""

import logging
import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Embedding 缓存管理器。"""

    def __init__(self, cache_dir: str = ".cache/recommender"):
        """
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 库缓存（本地论文库 embedding）
    # ------------------------------------------------------------------

    @property
    def library_cache_path(self) -> str:
        return os.path.join(self.cache_dir, "library_cache.pkl")

    def load_library_cache(self) -> Dict:
        """
        加载本地论文库的 embedding 缓存。

        Returns:
            {
                "embeddings": np.ndarray,
                "papers": List[Dict],
                "model_name": str,
                "count": int,
            }
        """
        return self._load(self.library_cache_path)

    def save_library_cache(
        self, embeddings: np.ndarray, papers: List[Dict], model_name: str
    ) -> None:
        """保存本地论文库 embedding 缓存。"""
        data = {
            "embeddings": embeddings,
            "papers": papers,
            "model_name": model_name,
            "count": len(papers),
        }
        self._save(self.library_cache_path, data)
        logger.info(f"库缓存已保存: {len(papers)} 条")

    def is_library_cache_valid(self, model_name: str) -> bool:
        """
        检查库缓存是否有效（文件存在且模型名称匹配）。
        """
        cache = self.load_library_cache()
        if cache is None:
            return False
        return cache.get("model_name") == model_name

    # ------------------------------------------------------------------
    # arXiv 缓存（历史 arXiv 论文 embedding）
    # ------------------------------------------------------------------

    @property
    def arxiv_cache_path(self) -> str:
        return os.path.join(self.cache_dir, "arxiv_cache.pkl")

    def load_arxiv_cache(self) -> Dict:
        """
        加载 arXiv 历史论文 embedding 缓存。

        Returns:
            {
                "embeddings": np.ndarray,
                "arxiv_ids": List[str],
                "papers": List[Dict],
                "model_name": str,
                "count": int,
            }
        """
        return self._load(self.arxiv_cache_path)

    def save_arxiv_cache(
        self, embeddings: np.ndarray, papers: List[Dict], model_name: str
    ) -> None:
        """保存 arXiv 论文 embedding 缓存。"""
        arxiv_ids = [p.get("arxiv_id", "") for p in papers]
        data = {
            "embeddings": embeddings,
            "arxiv_ids": arxiv_ids,
            "papers": papers,
            "model_name": model_name,
            "count": len(papers),
        }
        self._save(self.arxiv_cache_path, data)
        logger.info(f"arXiv 缓存已保存: {len(papers)} 条")

    def update_arxiv_cache(
        self,
        new_embeddings: np.ndarray,
        new_papers: List[Dict],
        model_name: str,
    ) -> None:
        """
        增量更新 arXiv 缓存：合并新旧数据并保存。

        Args:
            new_embeddings: 新论文的 embedding (shape = N x D)
            new_papers: 新论文列表
            model_name: 当前模型名
        """
        old_cache = self.load_arxiv_cache()
        if old_cache is None or old_cache.get("model_name") != model_name:
            # 缓存无效，全量覆盖
            self.save_arxiv_cache(new_embeddings, new_papers, model_name)
            return

        # 合并
        old_embeddings: np.ndarray = old_cache["embeddings"]
        old_papers: List[Dict] = old_cache.get("papers", [])
        old_ids: set = set(old_cache.get("arxiv_ids", []))

        # 过滤掉已存在的
        new_indices = []
        for i, p in enumerate(new_papers):
            if p.get("arxiv_id", "") not in old_ids:
                new_indices.append(i)

        if not new_indices:
            logger.info("arXiv 缓存无需更新（无新增论文）")
            return

        filtered_new_embeddings = new_embeddings[new_indices]
        filtered_new_papers = [new_papers[i] for i in new_indices]

        merged_embeddings = np.vstack([old_embeddings, filtered_new_embeddings])
        merged_papers = old_papers + filtered_new_papers

        self.save_arxiv_cache(merged_embeddings, merged_papers, model_name)
        logger.info(
            f"arXiv 缓存增量更新: {len(old_papers)} + {len(filtered_new_papers)} "
            f"= {len(merged_papers)} 条"
        )

    # ------------------------------------------------------------------
    # 底层 IO
    # ------------------------------------------------------------------

    def _load(self, path: str) -> Optional[Dict]:
        """从 pickle 文件加载缓存。"""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"缓存加载失败 {path}: {e}")
            return None

    def _save(self, path: str, data: Dict) -> None:
        """保存缓存到 pickle 文件。"""
        try:
            with open(path, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"缓存保存失败 {path}: {e}")
