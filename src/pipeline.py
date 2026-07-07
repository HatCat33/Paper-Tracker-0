"""
主流程编排器
串联所有模块：检索 → S2 → bib加载 → embedding → 推荐 → 语义过滤 → 期刊过滤 → 去重 → 摘要 → 邮件 → 站点
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import ConfigManager
from .arxiv_fetcher import ArxivFetcher
from .semantic_scholar import SemanticScholarClient
from .bib_loader import BibLoader
from .embedder import PaperEmbedder
from .cache import EmbeddingCache
from .recommender import PaperRecommender
from .filter_engine import FilterEngine
from .dedup import DedupManager
from .summarizer import PaperSummarizer
from .emailer import PaperEmailer
from .site_builder import SiteBuilder

logger = logging.getLogger(__name__)


class Pipeline:
    """论文追踪主流程编排器。"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: 配置文件路径
        """
        self.config = ConfigManager(config_path)
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self._init_logging()

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------

    def run(
        self,
        lookback_days: Optional[int] = None,
        dry_run: Optional[bool] = None,
        no_email: bool = False,
    ) -> Dict:
        """
        执行完整流程。

        Args:
            lookback_days: 回溯天数（覆盖配置）
            dry_run: 是否 dry-run（不发邮件、不写站点）
            no_email: 是否跳过邮件发送

        Returns:
            执行结果摘要
        """
        start_time = datetime.now()
        stats = {
            "date": self.date_str,
            "start_time": start_time.isoformat(),
            "stages": {},
        }

        try:
            # ===== 阶段 1: 检索 arXiv =====
            logger.info("=" * 50)
            logger.info("阶段 1/7: 检索 arXiv")
            logger.info("=" * 50)

            fetcher = ArxivFetcher(self.config)
            papers = fetcher.fetch(lookback_days=lookback_days)
            stats["stages"]["arxiv_fetch"] = {"count": len(papers)}

            if not papers:
                logger.warning("检索结果为空")
                stats["status"] = "empty"
                return stats

            # ===== 阶段 2: 过滤 =====
            logger.info("=" * 50)
            logger.info("阶段 2/7: 过滤引擎")
            logger.info("=" * 50)

            filter_engine = FilterEngine(self.config)
            papers_before = len(papers)

            # 时间过滤
            papers = filter_engine.filter_by_date(papers, lookback_days)

            # 期刊过滤
            papers = filter_engine.filter_by_journal(papers)
            stats["stages"]["filter"] = {
                "before": papers_before,
                "after": len(papers),
            }

            if not papers:
                logger.warning("过滤后无剩余论文")
                stats["status"] = "filtered_empty"
                return stats

            # ===== 阶段 3: 去重 =====
            logger.info("=" * 50)
            logger.info("阶段 3/7: 去重")
            logger.info("=" * 50)

            state_path = self.config.get("freshness.state_path", ".state/seen.json")
            dedup = DedupManager(state_path)
            papers = dedup.filter_new(papers)
            stats["stages"]["dedup"] = {"count": len(papers)}

            if not papers:
                logger.info("无新论文（已全部去重）")
                stats["status"] = "no_new"
                return stats

            # ===== 阶段 4: Semantic Scholar =====
            logger.info("=" * 50)
            logger.info("阶段 4/7: Semantic Scholar 增强")
            logger.info("=" * 50)

            s2 = SemanticScholarClient(self.config)
            papers = s2.enrich_papers(papers)
            stats["stages"]["semantic_scholar"] = {"enriched": len(papers)}

            # ===== 阶段 5: 本地推荐（可选） =====
            logger.info("=" * 50)
            logger.info("阶段 5/7: 本地论文推荐")
            logger.info("=" * 50)

            if self.config.get("local_recommend.enabled", False):
                bib_loader = BibLoader(self.config)
                local_papers = bib_loader.load_all()
                stats["stages"]["local_library"] = {"total": len(local_papers)}

                if local_papers:
                    embedder = PaperEmbedder(
                        self.config.get("local_recommend.embedding_model", "BAAI/bge-small-en-v1.5")
                    )
                    cache = EmbeddingCache(
                        self.config.get("local_recommend.cache_dir", ".cache/recommender")
                    )
                    recommender = PaperRecommender(self.config, embedder, cache)
                    papers = recommender.recommend(papers, local_papers)
                    stats["stages"]["recommend"] = {"papers_with_recs": len(papers)}
            else:
                stats["stages"]["local_library"] = {"enabled": False}

            # ===== 阶段 6: LLM 摘要（可选） =====
            logger.info("=" * 50)
            logger.info("阶段 6/7: LLM 摘要")
            logger.info("=" * 50)

            if self.config.get("llm_summary.enabled", False):
                summarizer = PaperSummarizer(self.config)
                papers = summarizer.generate_batch(papers)
                stats["stages"]["llm_summary"] = {"generated": len(papers)}
            else:
                stats["stages"]["llm_summary"] = {"enabled": False}

            # ===== 阶段 7: 输出 =====
            logger.info("=" * 50)
            logger.info("阶段 7/7: 输出（邮件 + 站点 + JSON）")
            logger.info("=" * 50)

            is_dry = dry_run if dry_run is not None else self.config.get("runtime.dry_run", False)

            # 保存 JSON 结果
            self._save_json(papers)
            stats["stages"]["json_output"] = {"saved": True}

            # 发送邮件
            if not is_dry and not no_email:
                emailer = PaperEmailer(self.config)
                success = emailer.send(papers, self.config.search_categories)
                stats["stages"]["email"] = {"sent": success}
            else:
                stats["stages"]["email"] = {"sent": False, "reason": "dry_run" if is_dry else "no_email"}

            # 生成站点
            if self.config.get("site.enabled", True):
                site_builder = SiteBuilder(self.config)
                daily_path = site_builder.build(papers, self.date_str)
                stats["stages"]["site"] = {"path": daily_path}

            # 提交去重状态
            if not is_dry:
                dedup.commit()
                stats["stages"]["dedup_commit"] = {"committed": True}

            # 完成
            stats["status"] = "success"
            stats["total_papers"] = len(papers)

        except Exception as e:
            logger.exception(f"流程执行异常: {e}")
            stats["status"] = "error"
            stats["error"] = str(e)

        finally:
            end_time = datetime.now()
            stats["end_time"] = end_time.isoformat()
            stats["duration_seconds"] = (end_time - start_time).total_seconds()

        return stats

    # ------------------------------------------------------------------
    # 测试方法
    # ------------------------------------------------------------------

    def test_search(self, lookback_days: Optional[int] = None) -> Dict:
        """测试检索（dry-run，不持久化）。"""
        logger.info("=== 测试检索模式 ===")
        fetcher = ArxivFetcher(self.config)
        papers = fetcher.fetch(lookback_days=lookback_days)

        result = {"total": len(papers), "papers": []}
        for p in papers[:20]:  # 只展示前 20 篇
            result["papers"].append({
                "arxiv_id": p.get("arxiv_id"),
                "title": p.get("title"),
                "authors": p.get("authors", [])[:3],
                "categories": p.get("categories"),
            })

        return result

    def test_email(self) -> bool:
        """测试邮件发送。"""
        logger.info("=== 测试邮件模式 ===")
        emailer = PaperEmailer(self.config)
        return emailer.test_send()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _save_json(self, papers: List[Dict]) -> str:
        """保存论文结果为 JSON 文件。"""
        output_dir = self.config.get("runtime.output_dir", "outputs")
        os.makedirs(output_dir, exist_ok=True)

        fname = f"papers-{self.date_str}.json"
        file_path = os.path.join(output_dir, fname)

        # 精简输出（仅保留关键字段）
        output = {
            "date": self.date_str,
            "generated_at": datetime.now().isoformat(),
            "total": len(papers),
            "categories": self.config.search_categories,
            "papers": papers,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON 结果已保存: {file_path}")
        return file_path

    def _init_logging(self) -> None:
        """初始化日志配置。"""
        log_level = self.config.get("runtime.log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
