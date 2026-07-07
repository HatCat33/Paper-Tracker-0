"""
LLM 摘要生成器
支持 OpenAI Compatible API，生成中英双语摘要（tldr / full 模式）。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class PaperSummarizer:
    """论文摘要生成器，通过 LLM API 生成双语摘要。"""

    def __init__(self, config: Any):
        """
        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.enabled: bool = config.get("llm_summary.enabled", False)
        self.provider: str = config.get("llm_summary.provider", "deepseek")
        self.base_url: str = config.get("llm_summary.base_url", "https://api.deepseek.com")
        self.model: str = config.get("llm_summary.model", "deepseek-chat")
        self.lang: str = config.get("llm_summary.lang", "both")
        self.scope: str = config.get("llm_summary.scope", "tldr")
        self.max_tokens: int = config.get("llm_summary.max_tokens", 200)

        # API Key 优先级：环境变量 > 配置文件
        api_key_env = config.get("llm_summary.api_key_env", "LLM_API_KEY")
        self.api_key: str = os.environ.get(api_key_env, "") or config.get("llm_summary.api_key", "")

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def generate(self, title: str, abstract: str) -> Dict[str, str]:
        """
        为单篇论文生成摘要。

        Args:
            title: 论文标题
            abstract: 论文摘要

        Returns:
            {
                "zh": "中文摘要",
                "en": "英文摘要",
            } 或仅包含其中一个，取决于配置
        """
        if not self.enabled:
            return {"en": abstract[:200] + "..." if len(abstract) > 200 else abstract}

        if not self.api_key:
            logger.warning("LLM API Key 未配置，跳过摘要生成")
            return {"en": self._truncate(abstract)}

        result: Dict[str, str] = {}

        if self.scope == "tldr":
            prompt = self._build_tldr_prompt(title, abstract)
        elif self.scope == "full":
            prompt = self._build_full_prompt(title, abstract)
        else:
            # both: 先 tldr 后 full（简化：只做 tldr）
            prompt = self._build_tldr_prompt(title, abstract)

        try:
            response = self._call_api(prompt)
            result = self._parse_response(response)
        except Exception as e:
            logger.error(f"LLM 摘要生成失败: {e}")
            result = {"en": self._truncate(abstract)}

        return result

    def generate_batch(self, papers: List[Dict]) -> List[Dict]:
        """
        批量为论文列表生成摘要。

        Args:
            papers: 论文列表

        Returns:
            增强后的论文列表，每篇增加了 summary_zh / summary_en 字段
        """
        if not self.enabled:
            return papers

        logger.info(f"批量生成 LLM 摘要: {len(papers)} 篇")
        for i, paper in enumerate(papers):
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            summaries = self.generate(title, abstract)

            if "zh" in summaries:
                paper["summary_zh"] = summaries["zh"]
            if "en" in summaries:
                paper["summary_en"] = summaries["en"]

            if (i + 1) % 10 == 0:
                logger.info(f"摘要进度: {i + 1}/{len(papers)}")

        return papers

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _build_tldr_prompt(self, title: str, abstract: str) -> str:
        """构建 TLDR 模式的 prompt。"""
        lang_instr = []
        if self.lang in ("zh", "both"):
            lang_instr.append("1. 用中文写一句话总结（不超过50字）")
        if self.lang in ("en", "both"):
            lang_instr.append(
                f"{'2.' if len(lang_instr) > 0 else '1.'} Write a one-sentence summary in English (max 30 words)"
            )

        instructions = "\n".join(lang_instr)
        return (
            f"Summarize the following paper in the specified format:\n\n"
            f"Title: {title}\n\n"
            f"Abstract: {abstract}\n\n"
            f"Instructions:\n{instructions}\n\n"
            f"Output only the summary text(s), no extra words."
        )

    def _build_full_prompt(self, title: str, abstract: str) -> str:
        """构建 Full 模式的 prompt。"""
        lang_instr = []
        if self.lang in ("zh", "both"):
            lang_instr.append(
                "1. 中文摘要（3-5句话）：包含研究问题、方法、主要发现和意义"
            )
        if self.lang in ("en", "both"):
            lang_instr.append(
                f"{'2.' if len(lang_instr) > 0 else '1.'} English summary (3-5 sentences): "
                f"problem, method, key findings, significance"
            )

        instructions = "\n".join(lang_instr)
        return (
            f"Provide a structured summary of this paper:\n\n"
            f"Title: {title}\n\n"
            f"Abstract: {abstract}\n\n"
            f"Instructions:\n{instructions}\n\n"
            f"Output only the summaries, no extra commentary."
        )

    def _call_api(self, prompt: str) -> str:
        """调用 OpenAI 兼容 API。"""
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful research assistant. Output ONLY the requested summaries, no extra text."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.3,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"API 请求失败 ({resp.status_code}): {resp.text[:200]}")

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _parse_response(self, response: str) -> Dict[str, str]:
        """解析 LLM 响应为双语摘要字典。"""
        result: Dict[str, str] = {}

        lines = response.strip().split("\n")
        zh_lines = []
        en_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 简单判断：以中文开头 = 中文；否则 = 英文
            if any("\u4e00" <= c <= "\u9fff" for c in line[:5]):
                zh_lines.append(line.lstrip("1234567890.。， "))
            else:
                en_lines.append(line.lstrip("1234567890.- "))

        if self.lang in ("zh", "both") and zh_lines:
            result["zh"] = " ".join(zh_lines)
        elif self.lang == "zh":
            # 仅请求中文但返回无中文，回退
            result["zh"] = self._truncate("")

        if self.lang in ("en", "both") and en_lines:
            result["en"] = " ".join(en_lines)
        elif self.lang == "en":
            result["en"] = response.strip()

        if not result:
            result["en"] = self._truncate(response)

        return result

    @staticmethod
    def _truncate(text: str, max_len: int = 200) -> str:
        """截断文本。"""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."
