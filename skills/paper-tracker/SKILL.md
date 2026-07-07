# Paper Tracker

## 技能名称
`paper-tracker`

## 描述
arXiv 论文每日追踪与推荐系统。定时检索 arXiv + Semantic Scholar，支持多关键词组、期刊白名单过滤、本地论文库 embedding 推荐、LLM 双语摘要、语义相似度过滤，结果通过 QQ 邮箱 SMTP 推送 HTML 日报，并生成 GitHub Pages 网页归档。项目含 Vue 3 前端管理界面。

## 核心能力
- **多关键词组检索**：支持 AND/OR 逻辑，每组独立检索后合并去重
- **期刊白名单过滤**：按顶会/顶刊/一区/自定义四个等级过滤
- **本地论文库推荐**：基于 embedding 的余弦相似度，匹配你已读论文
- **LLM 双语摘要**：支持 DeepSeek / OpenAI / SiliconFlow 生成中英文摘要
- **语义相似度过滤**：过滤与已有论文过于相似的 arXiv 论文
- **SMTP 邮件推送**：HTML 日报发送到 QQ 邮箱 / 163 / Gmail
- **GitHub Pages 站点**：自动生成带历史归档的静态站点
- **Vue 3 前端**：可视化配置界面（关键词组、期刊、设置）

## 使用方式

### 1. 配置关键词和期刊
用户可以通过对话调整 config.yaml 中的关键词组和期刊白名单。

### 2. 配置邮件推送
通过 GitHub Secrets 设置 EMAIL_USER / EMAIL_PASSWORD 环境变量。

### 3. 触发运行
- **定时运行**：GitHub Actions cron `0 19 * * *`（北京时间次日 03:00）
- **手动运行**：在 GitHub Actions Dashboard 手动触发 workflow_dispatch

### 4. 查看日报
- 邮件推送的 HTML 日报
- GitHub Pages 站点（docs/ 目录）

### 5. 前端管理
- 前端部署在 gh-pages 分支
- 访问 `https://<username>.github.io/<repo>/` 进入管理界面

## 架构
```
paper-tracker/
├── config.yaml          # 配置文件
├── src/                 # Python 核心引擎
│   ├── cli.py           # 命令行入口
│   ├── pipeline.py      # 主流程编排
│   ├── arxiv_fetcher.py # arXiv 检索
│   ├── filter_engine.py # 过滤引擎
│   ├── recommender.py   # 本地推荐
│   ├── emailer.py       # 邮件发送
│   ├── site_builder.py  # 站点生成
│   └── ...
├── frontend/            # Vue 3 前端
├── .github/workflows/   # GitHub Actions
├── skills/              # Skill 定义
└── docs/                # GitHub Pages 站点
```

## 依赖
- Python 3.10+
- arxiv >= 2.1.0
- sentence-transformers >= 3.0.0
- PyYAML, requests, etc.
- Node.js 20+ (前端)
