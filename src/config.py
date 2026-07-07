"""
Paper Tracker 配置管理器
从 config.yaml 加载配置，提供 get/set 方法，支持环境变量覆盖敏感信息。
"""

import os
import yaml
from typing import Any, Dict, List, Optional


class ConfigManager:
    """配置管理器，负责加载、验证和访问配置项。"""

    # 敏感配置项 -> 环境变量名映射
    SENSITIVE_ENV_MAP = {
        ("email", "password"): "EMAIL_PASSWORD",
        ("email", "user"): "EMAIL_USER",
        ("email", "sender"): "EMAIL_SENDER",
        ("email", "recipient"): "EMAIL_RECIPIENT",
        ("llm_summary", "api_key"): "LLM_API_KEY",
    }

    # 必填配置项（路径格式：(section, key)）
    REQUIRED_KEYS = [
        ("search", "categories"),
        ("search", "max_results"),
        ("runtime", "output_dir"),
    ]

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置管理器。

        Args:
            config_path: 配置文件路径，默认为 config.yaml
        """
        self.config_path = config_path
        self._data: Dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------
    # 加载 / 保存
    # ------------------------------------------------------------------

    def load(self, config_path: Optional[str] = None) -> None:
        """
        从 YAML 文件加载配置。

        Args:
            config_path: 可选，覆盖默认路径
        """
        path = config_path or self.config_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

        self._resolve_env_vars()
        self._set_defaults()

    def save(self, config_path: Optional[str] = None) -> None:
        """
        将当前配置写入 YAML 文件。
        注意：敏感信息不会写回文件，仅保留其占位符或环境变量引用。

        Args:
            config_path: 可选，覆盖默认路径
        """
        path = config_path or self.config_path
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # ------------------------------------------------------------------
    # 访问方法
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        支持点号分隔的嵌套键访问，如 'search.categories'。

        Args:
            key: 配置键，支持 '.' 分隔的嵌套路径
            default: 默认值
        """
        keys = key.split(".")
        node: Any = self._data
        for k in keys:
            if isinstance(node, dict):
                node = node.get(k)
                if node is None:
                    return default
            else:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值，支持嵌套路径。

        Args:
            key: 配置键，支持 '.' 分隔
            value: 新值
        """
        keys = key.split(".")
        node = self._data
        for k in keys[:-1]:
            if k not in node or not isinstance(node[k], dict):
                node[k] = {}
            node = node[k]
        node[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """返回完整配置字典（只读副本）。"""
        import copy
        return copy.deepcopy(self._data)

    # ------------------------------------------------------------------
    # 验证
    # ------------------------------------------------------------------

    def validate(self) -> List[str]:
        """
        验证配置完整性。

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors: List[str] = []
        for section, key in self.REQUIRED_KEYS:
            value = self.get(f"{section}.{key}")
            if value is None or (isinstance(value, (list, str)) and len(value) == 0):
                errors.append(f"必填配置项缺失: {section}.{key}")
        return errors

    @property
    def is_valid(self) -> bool:
        """配置是否通过验证。"""
        return len(self.validate()) == 0

    # ------------------------------------------------------------------
    # 便捷属性（常用配置快速访问）
    # ------------------------------------------------------------------

    @property
    def search_categories(self) -> List[str]:
        return self.get("search.categories", [])

    @property
    def keyword_groups(self) -> List[Dict]:
        return self.get("search.keyword_groups", [])

    @property
    def exclude_keywords(self) -> List[str]:
        return self.get("search.exclude_keywords", [])

    @property
    def max_results(self) -> int:
        return self.get("search.max_results", 100)

    @property
    def since_days(self) -> int:
        return self.get("freshness.since_days", 3)

    @property
    def output_dir(self) -> str:
        return self.get("runtime.output_dir", "outputs")

    @property
    def dry_run(self) -> bool:
        return self.get("runtime.dry_run", False)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _resolve_env_vars(self) -> None:
        """从环境变量覆盖敏感配置项。"""
        for (section, key), env_var in self.SENSITIVE_ENV_MAP.items():
            env_value = os.environ.get(env_var, "")
            if env_value:
                if section not in self._data:
                    self._data[section] = {}
                self._data[section][key] = env_value

    def _set_defaults(self) -> None:
        """为缺失的非必填项设置合理默认值。"""
        defaults: Dict[str, Any] = {
            "search": {
                "max_results": 100,
                "sort_by": "lastUpdatedDate",
                "sort_order": "descending",
            },
            "freshness": {
                "since_days": 3,
                "unique_only": True,
                "state_path": ".state/seen.json",
                "fallback_when_empty": False,
            },
            "semantic_filter": {
                "enabled": False,
                "model": "BAAI/bge-small-en-v1.5",
                "threshold": 0.5,
                "batch_size": 32,
            },
            "local_recommend": {
                "enabled": False,
                "data_dir": "data",
                "embedding_model": "BAAI/bge-small-en-v1.5",
                "top_k_neighbors": 5,
                "max_recommend": 10,
                "require_abstract": True,
            },
            "runtime": {
                "output_dir": "outputs",
                "log_level": "INFO",
                "dry_run": False,
            },
        }
        for section, values in defaults.items():
            if section not in self._data:
                self._data[section] = {}
            for k, v in values.items():
                if k not in self._data[section]:
                    self._data[section][k] = v
