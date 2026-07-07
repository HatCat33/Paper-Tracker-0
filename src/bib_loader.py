"""
BibTeX 加载器
递归扫描 data/ 目录下所有 .bib 文件，解析条目并返回论文列表。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

logger = logging.getLogger(__name__)


class BibLoader:
    """BibTeX 文件加载器，支持 ScholarRead / Zotero 导出的 .bib 文件。"""

    def __init__(self, config: Any):
        """
        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.data_dir: str = config.get("local_recommend.data_dir", "data")
        self.require_abstract: bool = config.get("local_recommend.require_abstract", True)

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def load_all(self) -> List[Dict]:
        """
        递归扫描并加载所有 .bib 文件。

        Returns:
            论文条目列表，每项包含 title / abstract / authors / year / bib_key / source_file
        """
        if not os.path.isdir(self.data_dir):
            logger.warning(f"数据目录不存在: {self.data_dir}")
            return []

        entries: List[Dict] = []
        for root, dirs, files in os.walk(self.data_dir):
            for fname in files:
                if fname.lower().endswith(".bib"):
                    file_path = os.path.join(root, fname)
                    entries.extend(self._parse_bib_file(file_path))

        # 过滤无 abstract 的条目
        if self.require_abstract:
            before = len(entries)
            entries = [e for e in entries if e.get("abstract", "").strip()]
            logger.info(
                f"BibTeX 加载: {before} 条 → {len(entries)} 条 "
                f"(已过滤 {before - len(entries)} 条无摘要)"
            )

        logger.info(f"共加载 {len(entries)} 条本地论文条目")
        return entries

    def get_stats(self) -> Dict:
        """获取本地论文库统计信息。"""
        entries = self.load_all()
        years = [e.get("year", "unknown") for e in entries]
        year_counts: Dict[str, int] = {}
        for y in years:
            year_counts[str(y)] = year_counts.get(str(y), 0) + 1

        return {
            "total_entries": len(entries),
            "source_dir": os.path.abspath(self.data_dir),
            "years": year_counts,
        }

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _parse_bib_file(self, file_path: str) -> List[Dict]:
        """解析单个 .bib 文件。"""
        entries: List[Dict] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"无法读取 {file_path}: {e}")
                return []

        try:
            parser = BibTexParser(common_strings=True)
            parser.customization = convert_to_unicode
            bib_db = bibtexparser.loads(content, parser=parser)
        except Exception as e:
            logger.error(f"解析 BibTeX 失败 {file_path}: {e}")
            return []

        for entry in bib_db.entries:
            paper = self._normalize_entry(entry, file_path)
            if paper.get("title"):
                entries.append(paper)

        return entries

    def _normalize_entry(self, entry: Dict, source_file: str) -> Dict:
        """标准化单个 BibTeX 条目。"""
        return {
            "bib_key": entry.get("ID", ""),
            "title": self._clean_text(entry.get("title", "")),
            "abstract": self._clean_text(entry.get("abstract", "")),
            "authors": self._clean_text(entry.get("author", "")),
            "year": self._extract_year(entry.get("year", "")),
            "journal": self._clean_text(entry.get("journal", entry.get("booktitle", ""))),
            "doi": entry.get("doi", ""),
            "url": entry.get("url", ""),
            "source_file": source_file,
            "entry_type": entry.get("ENTRYTYPE", "misc"),
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理 BibTeX 文本中的 LaTeX 命令和多余空白。"""
        import re
        text = text.replace("{", "").replace("}", "")
        text = re.sub(r"\\[a-zA-Z]+\s?", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _extract_year(year_str: str) -> str:
        """从 year 字段提取四位年份。"""
        import re
        match = re.search(r"(\d{4})", str(year_str))
        return match.group(1) if match else str(year_str)
