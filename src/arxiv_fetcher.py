"""
arXiv API 检索器
支持多关键词组并行检索、AND/OR 逻辑、排除关键词、自动分页。
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import arxiv

logger = logging.getLogger(__name__)


class ArxivFetcher:
    """arXiv API 论文检索器。"""

    # 默认每页结果数（arxiv 库内部 max_results 控制总条数而非单页）
    PAGE_SIZE = 100

    def __init__(self, config: Any):
        """
        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.categories: List[str] = config.get("search.categories", [])
        self.keyword_groups: List[Dict] = config.get("search.keyword_groups", [])
        self.exclude_keywords: List[str] = config.get("search.exclude_keywords", [])
        self.max_results: int = config.get("search.max_results", 100)
        self.sort_by_str: str = config.get("search.sort_by", "lastUpdatedDate")
        self.sort_order: str = config.get("search.sort_order", "descending")

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def fetch(self, lookback_days: Optional[int] = None) -> List[Dict]:
        """
        执行检索，返回论文元数据列表。

        Args:
            lookback_days: 覆盖配置中的回溯天数

        Returns:
            去重后的论文列表，每项为包含标题、作者、摘要等字段的字典
        """
        days = lookback_days or self.config.get("freshness.since_days", 3)
        cutoff_date = datetime.now() - timedelta(days=days)
        logger.info(f"检索 arXiv 论文，回溯 {days} 天，截止日期: {cutoff_date.date()}")

        all_papers: Dict[str, Dict] = {}  # arxiv_id -> paper

        for group in self.keyword_groups:
            group_papers = self._fetch_group(group, cutoff_date)
            for paper in group_papers:
                arxiv_id = paper["arxiv_id"]
                if arxiv_id not in all_papers:
                    all_papers[arxiv_id] = paper

        # 无关键词组时，按分类检索全部
        if not self.keyword_groups:
            all_papers = self._fetch_all_categories(cutoff_date)

        # 排除关键词过滤
        if self.exclude_keywords:
            all_papers = self._apply_exclude_filter(all_papers)

        papers = list(all_papers.values())
        logger.info(f"检索完成，去重后共 {len(papers)} 篇论文")
        return papers

    # ------------------------------------------------------------------
    # 内部：关键词组检索
    # ------------------------------------------------------------------

    def _fetch_group(self, group: Dict, cutoff_date: datetime) -> List[Dict]:
        """针对单个关键词组检索。"""
        keywords: List[str] = group.get("keywords", [])
        sub_keywords: List[str] = group.get("sub_keywords", [])
        logic: str = group.get("logic", "OR")
        group_name: str = group.get("name", ",".join(keywords[:2]))
        logger.info(f"关键词组 [{group_name}]: logic={logic}")

        papers: Dict[str, Dict] = {}

        if logic == "AND" and sub_keywords:
            # AND 逻辑：分别检索两组，取交集
            primary = self._search_keywords(keywords, cutoff_date)
            secondary = self._search_keywords(sub_keywords, cutoff_date)
            primary_ids = {p["arxiv_id"] for p in primary}
            for p in secondary:
                if p["arxiv_id"] in primary_ids:
                    papers[p["arxiv_id"]] = p
        else:
            # OR 逻辑：所有关键词混合检索
            all_kw = keywords + sub_keywords
            for p in self._search_keywords(all_kw, cutoff_date):
                papers[p["arxiv_id"]] = p

        logger.info(f"  组 [{group_name}] 检索到 {len(papers)} 篇")
        return list(papers.values())

    def _search_keywords(self, keywords: List[str], cutoff_date: datetime) -> List[Dict]:
        """按关键词列表检索 arXiv。"""
        if not keywords:
            return []

        # 构建查询：各关键词用 OR 连接
        query_parts = [f"(all:{kw})" for kw in keywords]
        query = " OR ".join(query_parts)

        # 分类过滤
        if self.categories:
            cat_parts = [f"cat:{c}" for c in self.categories]
            query = f"({' OR '.join(cat_parts)}) AND ({query})"

        return self._execute_query(query, cutoff_date)

    def _fetch_all_categories(self, cutoff_date: datetime) -> Dict[str, Dict]:
        """无关键词组时，按分类检索近期全部论文。"""
        if not self.categories:
            return {}

        cat_parts = [f"cat:{c}" for c in self.categories]
        query = " OR ".join(cat_parts)
        papers = self._execute_query(query, cutoff_date)
        result: Dict[str, Dict] = {}
        for p in papers:
            result[p["arxiv_id"]] = p
        return result

    # ------------------------------------------------------------------
    # 内部：API 调用与解析
    # ------------------------------------------------------------------

    def _execute_query(self, query: str, cutoff_date: datetime) -> List[Dict]:
        """执行 arXiv API 查询并解析结果。"""
        try:
            sort_criterion = (
                arxiv.SortCriterion.LastUpdatedDate
                if self.sort_by_str == "lastUpdatedDate"
                else arxiv.SortCriterion.SubmittedDate
            )
            sort_order_flag = (
                arxiv.SortOrder.Descending
                if self.sort_order == "descending"
                else arxiv.SortOrder.Ascending
            )

            client = arxiv.Client(
                page_size=self.PAGE_SIZE,
                delay_seconds=3.0,
                num_retries=3,
            )

            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=sort_criterion,
                sort_order=sort_order_flag,
            )

            results: List[Dict] = []
            for r in client.results(search):
                # 时间过滤
                updated = r.updated.replace(tzinfo=None)
                published = r.published.replace(tzinfo=None)
                effective_date = max(updated, published)
                if effective_date < cutoff_date:
                    continue

                paper = self._parse_result(r)
                results.append(paper)

                if len(results) >= self.max_results:
                    break

            return results

        except Exception as e:
            logger.error(f"arXiv API 查询失败: {e}")
            return []

    def _parse_result(self, r: arxiv.Result) -> Dict:
        """解析单个 arXiv 结果为字典。"""
        # 提取 arXiv ID（去掉版本号）
        arxiv_id = r.entry_id.split("/")[-1]
        if "v" in arxiv_id:
            arxiv_id = arxiv_id.split("v")[0]

        # 提取 GitHub / 项目链接
        github_link = ""
        project_link = ""
        for link in r.links:
            href = link.href or ""
            if "github.com" in href.lower():
                github_link = href
            elif href != r.entry_id and href != r.pdf_url:
                project_link = href

        # 从 comment 中提取期刊/会议信息
        journal_ref = r.journal_ref or ""
        if not journal_ref and r.comment:
            comment = r.comment.lower()
            for venue in ["cvpr", "iccv", "eccv", "neurips", "icml", "iclr", "aaai", "tPAMI", "ijcv"]:
                if venue.lower() in comment:
                    journal_ref = r.comment
                    break

        return {
            "arxiv_id": arxiv_id,
            "title": r.title.strip(),
            "authors": [str(a) for a in r.authors],
            "first_author": str(r.authors[0]) if r.authors else "",
            "abstract": r.summary.strip().replace("\n", " "),
            "categories": [str(c) for c in r.categories],
            "published": r.published.isoformat() if r.published else "",
            "updated": r.updated.isoformat() if r.updated else "",
            "pdf_url": r.pdf_url or "",
            "entry_url": r.entry_id or "",
            "journal_ref": journal_ref,
            "comment": r.comment or "",
            "doi": r.doi or "",
            "github_link": github_link,
            "project_link": project_link,
            "source": "arxiv",
        }

    # ------------------------------------------------------------------
    # 内部：过滤
    # ------------------------------------------------------------------

    def _apply_exclude_filter(self, papers: Dict[str, Dict]) -> Dict[str, Dict]:
        """排除包含排除关键词的论文。"""
        filtered: Dict[str, Dict] = {}
        for arxiv_id, paper in papers.items():
            text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
            excluded = False
            for kw in self.exclude_keywords:
                if kw.lower() in text:
                    excluded = True
                    logger.debug(f"排除论文 {arxiv_id}: 命中排除关键词 '{kw}'")
                    break
            if not excluded:
                filtered[arxiv_id] = paper
        logger.info(f"排除关键词过滤: {len(papers)} -> {len(filtered)}")
        return filtered
