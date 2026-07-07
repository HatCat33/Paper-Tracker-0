"""
Semantic Scholar API 客户端
根据 arXiv ID 或标题查询引用量和影响力数据。
"""

import time
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Semantic Scholar API 基础 URL
S2_API_BASE = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarClient:
    """Semantic Scholar API 客户端。"""

    # 批量查询每批最多 ID 数
    BATCH_SIZE = 100

    # 请求间隔（秒），遵守 rate limit
    RATE_LIMIT_DELAY = 1.0

    def __init__(self, config: Any):
        """
        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.enabled: bool = config.get("semantic_scholar.enabled", False)
        self.include_citations: bool = config.get("semantic_scholar.include_citations", True)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "PaperTracker/1.0"})

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def enrich_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        为论文列表补充 Semantic Scholar 元数据（引用量等）。

        Args:
            papers: 论文列表

        Returns:
            增强后的论文列表
        """
        if not self.enabled:
            return papers

        arxiv_ids = [p.get("arxiv_id", "") for p in papers if p.get("arxiv_id")]
        if not arxiv_ids:
            return papers

        logger.info(f"查询 Semantic Scholar，共 {len(arxiv_ids)} 篇论文")
        s2_data = self._batch_lookup(arxiv_ids)

        for paper in papers:
            aid = paper.get("arxiv_id", "")
            data = s2_data.get(aid, {})
            paper["citation_count"] = data.get("citationCount", 0)
            paper["influential_citation_count"] = data.get("influentialCitationCount", 0)
            paper["s2_id"] = data.get("paperId", "")
            paper["s2_url"] = data.get("url", "")

        return papers

    def lookup_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        按 arXiv ID 查询单篇论文。

        Args:
            arxiv_id: arXiv ID（如 2301.12345）

        Returns:
            论文数据字典，失败返回 None
        """
        url = f"{S2_API_BASE}/paper/ArXiv:{arxiv_id}"
        fields = "paperId,title,citationCount,influentialCitationCount,year,url,externalIds"

        try:
            resp = self._session.get(url, params={"fields": fields}, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                logger.debug(f"S2 未找到: {arxiv_id}")
                return None
            else:
                logger.warning(f"S2 API 错误 {resp.status_code}: {arxiv_id}")
                return None
        except Exception as e:
            logger.error(f"S2 查询异常: {e}")
            return None

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _batch_lookup(self, arxiv_ids: List[str]) -> Dict[str, Dict]:
        """批量查询 Semantic Scholar。"""
        result: Dict[str, Dict] = {}
        for i in range(0, len(arxiv_ids), self.BATCH_SIZE):
            batch = arxiv_ids[i : i + self.BATCH_SIZE]
            batch_result = self._lookup_batch(batch)
            result.update(batch_result)
            if i + self.BATCH_SIZE < len(arxiv_ids):
                time.sleep(self.RATE_LIMIT_DELAY)
        return result

    def _lookup_batch(self, arxiv_ids: List[str]) -> Dict[str, Dict]:
        """查询单批 arXiv ID。"""
        url = f"{S2_API_BASE}/paper/batch"
        fields = "paperId,title,citationCount,influentialCitationCount,year,url,externalIds"

        payload = {"ids": [f"ArXiv:{aid}" for aid in arxiv_ids]}

        try:
            resp = self._session.post(
                url, params={"fields": fields}, json=payload, timeout=30
            )
            if resp.status_code != 200:
                logger.error(f"S2 批量查询失败: {resp.status_code}")
                return {}

            data = resp.json()
            result: Dict[str, Dict] = {}
            for item in data:
                if item is None:
                    continue
                ext_ids = item.get("externalIds", {}) or {}
                arxiv_id = ext_ids.get("ArXiv", "")
                if arxiv_id:
                    result[arxiv_id] = item
            return result

        except Exception as e:
            logger.error(f"S2 批量查询异常: {e}")
            return {}
