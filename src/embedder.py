"""
论文 Embedding 计算器
使用 sentence-transformers 对论文标题+摘要计算 embedding 向量。
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PaperEmbedder:
    """论文 Embedding 计算器。"""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Args:
            model_name: sentence-transformers 模型名称
        """
        self.model_name = model_name
        self._model: Optional[Any] = None

    # ------------------------------------------------------------------
    # 延迟加载
    # ------------------------------------------------------------------

    @property
    def model(self) -> Any:
        """延迟加载模型（首次使用时才加载，节省内存）。"""
        if self._model is None:
            logger.info(f"加载 embedding 模型: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info("模型加载完成")
        return self._model

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def encode_papers(
        self,
        papers: List[Dict],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        对论文列表计算 embedding。

        Args:
            papers: 论文列表，每项需含 title 和 abstract
            batch_size: 批处理大小
            show_progress: 是否显示进度条

        Returns:
            shape = (n_papers, embedding_dim) 的 numpy 数组
        """
        texts = []
        for paper in papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            # BGE 模型推荐加 instruction prefix
            text = f"Represent this paper for retrieval: {title}. {abstract}"
            texts.append(text)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2 归一化，方便直接用点积做余弦相似度
        )

        return embeddings

    def encode_single(self, title: str, abstract: str = "") -> np.ndarray:
        """
        计算单篇论文的 embedding。

        Args:
            title: 论文标题
            abstract: 论文摘要

        Returns:
            shape = (embedding_dim,) 的 numpy 数组
        """
        text = f"Represent this paper for retrieval: {title}. {abstract}"
        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding[0]

    @property
    def embedding_dim(self) -> int:
        """获取 embedding 维度。"""
        return self.model.get_sentence_embedding_dimension()
