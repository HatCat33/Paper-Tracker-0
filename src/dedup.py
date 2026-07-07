"""
去重管理器
基于 seen.json 持久化去重，按 arXiv ID 去重。
仅在成功输出后写入，防止重复推送。
"""

import json
import logging
import os
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class DedupManager:
    """去重管理器，按 arXiv ID 去重。"""

    def __init__(self, state_path: str = ".state/seen.json"):
        """
        Args:
            state_path: 状态文件路径
        """
        self.state_path = state_path
        self._seen_ids: Set[str] = set()
        self._new_ids: Set[str] = set()
        self._load()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def filter_new(self, papers: List[Dict]) -> List[Dict]:
        """
        过滤出未见过的论文。

        Args:
            papers: 论文列表

        Returns:
            新论文列表
        """
        new_papers: List[Dict] = []
        for paper in papers:
            arxiv_id = paper.get("arxiv_id", "")
            if arxiv_id and arxiv_id not in self._seen_ids:
                new_papers.append(paper)
                self._new_ids.add(arxiv_id)

        logger.info(
            f"去重: {len(papers)} -> {len(new_papers)} 篇新论文 "
            f"(已见 {len(self._seen_ids)} 篇)"
        )
        return new_papers

    def commit(self) -> None:
        """提交去重状态（将本轮新论文写入持久化存储）。"""
        self._seen_ids.update(self._new_ids)
        self._save()
        logger.info(f"去重状态已保存: {len(self._seen_ids)} 篇已见")

    def is_new(self, arxiv_id: str) -> bool:
        """检查某篇论文是否为新论文。"""
        return arxiv_id not in self._seen_ids

    def get_stats(self) -> Dict:
        """获取去重统计信息。"""
        return {
            "total_seen": len(self._seen_ids),
            "new_this_run": len(self._new_ids),
        }

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """从文件加载已见 ID 集合。"""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ids = data.get("seen_ids", [])
                    self._seen_ids = set(ids)
                logger.debug(f"加载去重状态: {len(self._seen_ids)} 篇已见")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"去重状态文件损坏，将重建: {e}")
                self._seen_ids = set()
        else:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

    def _save(self) -> None:
        """保存已见 ID 集合到文件。"""
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        data = {"seen_ids": sorted(self._seen_ids)}
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
