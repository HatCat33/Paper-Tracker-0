#!/usr/bin/env python3
"""
Paper Tracker 命令行入口

用法:
    python -m src.cli run [--config PATH] [--lookback-days N] [--dry-run] [--no-email] [--verbose]
    python -m src.cli test-email [--config PATH]
    python -m src.cli test-search [--config PATH] [--lookback-days N]
    python -m src.cli config [--config PATH]
"""

import argparse
import json
import logging
import sys
from datetime import datetime

logger = logging.getLogger("paper-tracker.cli")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="paper-tracker",
        description="arXiv 论文每日追踪与推荐系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  paper-tracker run                            # 运行一次完整流程
  paper-tracker run --dry-run                  # 预览模式（不发邮件）
  paper-tracker run --lookback-days 7          # 检索近 7 天
  paper-tracker test-email                     # 测试邮件发送
  paper-tracker test-search --lookback-days 3  # 测试检索
  paper-tracker config                         # 查看当前配置
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="运行一次完整流程")
    run_parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    run_parser.add_argument("--dry-run", action="store_true", help="预览模式，不发送邮件")
    run_parser.add_argument("--no-email", action="store_true", help="跳过邮件发送")
    run_parser.add_argument("--lookback-days", type=int, default=None, help="回溯天数")
    run_parser.add_argument("--verbose", action="store_true", help="详细日志")

    # --- test-email ---
    email_parser = subparsers.add_parser("test-email", help="测试邮件发送")
    email_parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    email_parser.add_argument("--verbose", action="store_true", help="详细日志")

    # --- test-search ---
    search_parser = subparsers.add_parser("test-search", help="测试检索（dry-run）")
    search_parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    search_parser.add_argument("--lookback-days", type=int, default=None, help="回溯天数")
    search_parser.add_argument("--verbose", action="store_true", help="详细日志")

    # --- config ---
    config_parser = subparsers.add_parser("config", help="查看/验证当前配置")
    config_parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    return parser


def setup_logging(verbose: bool = False) -> None:
    """设置日志级别。"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_run(args: argparse.Namespace) -> int:
    """执行 run 子命令。"""
    setup_logging(args.verbose)

    from .pipeline import Pipeline

    pipeline = Pipeline(config_path=args.config)
    stats = pipeline.run(
        lookback_days=args.lookback_days,
        dry_run=args.dry_run,
        no_email=args.no_email,
    )

    print("\n" + "=" * 50)
    print("执行结果")
    print("=" * 50)
    print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

    if stats.get("status") == "success":
        print(f"\n完成: 共 {stats.get('total_papers', 0)} 篇新论文")
        return 0
    elif stats.get("status") == "empty":
        print("\n未检索到论文（检索范围可能太窄或 arXiv API 返回空）")
        return 0
    elif stats.get("status") == "filtered_empty":
        print("\n过滤后无剩余论文（所有论文均被期刊白名单或关键词过滤排除）")
        return 0
    elif stats.get("status") == "no_new":
        print("\n无新论文（全部已去重）")
        return 0
    else:
        print(f"\n错误: {stats.get('error', '未知错误')}")
        return 1


def cmd_test_email(args: argparse.Namespace) -> int:
    """执行 test-email 子命令。"""
    setup_logging(args.verbose)

    from .pipeline import Pipeline

    pipeline = Pipeline(config_path=args.config)
    success = pipeline.test_email()

    if success:
        print("测试邮件发送成功")
        return 0
    else:
        print("测试邮件发送失败，请检查 SMTP 配置和环境变量")
        return 1


def cmd_test_search(args: argparse.Namespace) -> int:
    """执行 test-search 子命令。"""
    setup_logging(args.verbose)

    from .pipeline import Pipeline

    pipeline = Pipeline(config_path=args.config)
    result = pipeline.test_search(lookback_days=args.lookback_days)

    print(f"\n检索到 {result['total']} 篇论文")
    print("-" * 50)
    for i, p in enumerate(result.get("papers", [])):
        print(f"{i + 1}. [{p['arxiv_id']}] {p['title'][:80]}")
        print(f"   Authors: {', '.join(p.get('authors', []))}")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """执行 config 子命令。"""
    import yaml

    from .config import ConfigManager

    config = ConfigManager(args.config)

    print("=" * 50)
    print("配置状态")
    print("=" * 50)

    errors = config.validate()
    if errors:
        print("验证失败:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("验证通过")

    print(f"\n检索分类: {config.search_categories}")
    print(f"关键词组: {len(config.keyword_groups)} 组")
    for g in config.keyword_groups:
        print(f"  - {g.get('name')}: {g.get('logic')} ({len(g.get('keywords', []))}+{len(g.get('sub_keywords', []))} kw)")

    print(f"\n期刊过滤: {'启用' if config.get('journal_filter.enabled') else '关闭'}")
    print(f"语义过滤: {'启用' if config.get('semantic_filter.enabled') else '关闭'}")
    print(f"本地推荐: {'启用' if config.get('local_recommend.enabled') else '关闭'}")
    print(f"LLM 摘要: {'启用' if config.get('llm_summary.enabled') else '关闭'}")
    print(f"邮件推送: {'启用' if config.get('email.enabled') else '关闭'}")
    print(f"站点生成: {'启用' if config.get('site.enabled') else '关闭'}")

    return 0


def main() -> int:
    """主入口。"""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    dispatcher = {
        "run": cmd_run,
        "test-email": cmd_test_email,
        "test-search": cmd_test_search,
        "config": cmd_config,
    }

    handler = dispatcher.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"未知命令: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
