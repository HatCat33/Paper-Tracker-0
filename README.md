# Paper Tracker — arXiv 论文每日追踪与推荐系统

> 面向开源的 arXiv 论文每日追踪与推荐系统，运行在 GitHub Actions 上，
> 定时检索 arXiv + Semantic Scholar，支持多关键词组、期刊白名单过滤、
> 本地论文库 embedding 推荐、LLM 双语摘要、语义相似度过滤，
> 结果通过 QQ 邮箱 SMTP 推送 HTML 日报，并生成 GitHub Pages 网页归档。

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  arXiv API  │──▶ │  检索 & 过滤  │──▶ │  S2 引用量   │
└─────────────┘    └──────┬───────┘    └──────┬───────┘
                          │                    │
                          ▼                    ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  本地 .bib   │──▶ │ 推荐 (cosine)│──▶ │  LLM 摘要    │
└─────────────┘    └──────┬───────┘    └──────┬───────┘
                          │                    │
          ┌───────────────┴────────────────────┘
          ▼                        ▼
┌──────────────────┐    ┌──────────────────┐
│  QQ 邮箱 HTML 日报 │    │ GitHub Pages 站点 │
└──────────────────┘    └──────────────────┘
```

---

## 特性

| 功能 | 状态 | 说明 |
|------|:----:|------|
| 多关键词组 AND/OR 检索 | ✅ | 每组独立检索，支持 keywords × sub_keywords 逻辑组合 |
| arXiv 分类过滤 | ✅ | cs.CV / cs.LG / cs.AI 等 |
| 排除关键词 | ✅ | 命中则过滤（如 medical image） |
| 期刊/会议白名单过滤 | ✅ 默认开启 | 顶会/顶刊/一区/自定义四个等级 |
| 跨天去重 | ✅ | 基于 seen.json 持久化，防重复推送 |
| Semantic Scholar 引用量 | ⬜ 默认关闭 | 拉取引用量丰富论文元数据 |
| 本地论文库推荐 | ⬜ 默认关闭 | 基于 BGE embedding 余弦相似度匹配 |
| LLM 双语摘要 | ⬜ 默认关闭 | DeepSeek / OpenAI / SiliconFlow |
| 语义相似度过滤 | ⬜ 默认关闭 | embedding 去重，过滤过于相似的论文 |
| QQ 邮箱 SMTP 推送 | ⬜ 默认关闭 | HTML 日报，响应式设计 |
| GitHub Pages 网页归档 | ✅ | 自动生成历史日报站点 |
| Vue 3 前端管理界面 | ✅ | 可视化配置、历史查看 |

---

## 快速开始

### 1. Fork 本仓库

点击 GitHub 页面右上角的 `Fork` 按钮。

### 2. 配置 GitHub Secrets

在 `Settings → Secrets and variables → Actions` 中添加：

| Secret | 说明 | 必填 |
|--------|------|:----:|
| `EMAIL_USER` | QQ 邮箱账号（如 `123456789@qq.com`） | 发邮件时必填 |
| `EMAIL_PASSWORD` | QQ 邮箱授权码（非密码；QQ 邮箱 → 设置 → 账户 → POP3/SMTP 服务） | 发邮件时必填 |
| `EMAIL_SENDER` | 发件人地址（默认同 EMAIL_USER） | 可选 |
| `EMAIL_RECIPIENT` | 收件人地址（默认同 EMAIL_USER） | 可选 |
| `LLM_API_KEY` | LLM API Key | 开启摘要时必填 |

### 3. 修改配置文件

编辑 `config.yaml`，设置你的关键词组和期刊偏好。详见下方「配置详解」。

### 4. 启用 GitHub Actions

进入仓库的 `Actions` 标签页，点击 `I understand my workflows...` 启用 Workflow。

### 5. 手动触发一次运行

在 `Actions → Daily Paper Digest → Run workflow` 手动触发，验证配置是否正常。

### 6. 查看 GitHub Pages

在 `Settings → Pages` 中，Source 选择 `Deploy from a branch`，Branch 选择 `main`，目录 `/docs`，保存后自动部署。

---

## 配置详解

配置文件位于 `config.yaml`，完整配置项如下：

### 检索设置 (`search`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `categories` | list | `[cs.CV, cs.LG, cs.AI]` | arXiv 学科分类 |
| `keyword_groups` | list | 见示例 | 多关键词组，每组含 name/keywords/sub_keywords/logic |
| `exclude_keywords` | list | `[]` | 排除关键词，命中任一即过滤 |
| `max_results` | int | `100` | 每页抓取上限 |
| `sort_by` | string | `lastUpdatedDate` | 排序方式 (submittedDate / lastUpdatedDate) |
| `sort_order` | string | `descending` | 排序方向 |

### 时间范围 (`freshness`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `since_days` | int | `3` | 检索近 N 天的论文 |
| `unique_only` | bool | `true` | 跨天去重 |
| `state_path` | string | `.state/seen.json` | 去重状态文件路径 |
| `fallback_when_empty` | bool | `false` | 当天无新增时是否回退 |

### 期刊过滤 (`journal_filter`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `true` | 总开关 |
| `levels.top_conference` | list | CVPR/ICCV/NeurIPS... | 顶会列表 |
| `levels.top_journal` | list | TPAMI/IJCV/TIP... | 顶刊列表 |
| `levels.q1_journal` | list | PR/CVIU/TMM... | 一区期刊 |
| `active_levels` | list | `[top_conference, top_journal, q1_journal]` | 生效等级 |

### 语义相似度过滤 (`semantic_filter`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `false` | 总开关 |
| `model` | string | `BAAI/bge-small-en-v1.5` | Embedding 模型 |
| `threshold` | float | `0.5` | 相似度阈值 (0~1) |
| `batch_size` | int | `32` | 批量处理大小 |

### 本地推荐 (`local_recommend`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `false` | 总开关 |
| `data_dir` | string | `data` | .bib 文件存放目录 |
| `embedding_model` | string | `BAAI/bge-small-en-v1.5` | Embedding 模型 |
| `top_k_neighbors` | int | `5` | 每篇新论文匹配几篇本地论文 |
| `max_recommend` | int | `10` | 最多推荐几篇 |
| `require_abstract` | bool | `true` | 要求 .bib 条目含 abstract |

### Semantic Scholar (`semantic_scholar`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `false` | 总开关 |
| `include_citations` | bool | `true` | 拉取引用量 |

### LLM 摘要 (`llm_summary`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `false` | 总开关 |
| `provider` | string | `deepseek` | 模型服务商 (deepseek / openai / siliconflow) |
| `base_url` | string | `https://api.deepseek.com` | API 地址 |
| `model` | string | `deepseek-chat` | 模型名称 |
| `api_key_env` | string | `LLM_API_KEY` | 环境变量名 |
| `lang` | string | `both` | 摘要语言 (zh / en / both) |
| `scope` | string | `tldr` | 摘要长度 (tldr / full / both) |
| `max_tokens` | int | `200` | 最大 Token |

### 邮件推送 (`email`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `false` | 总开关 |
| `subject_prefix` | string | `[arXiv Daily]` | 邮件主题前缀 |
| `smtp_server` | string | `smtp.qq.com` | SMTP 服务器 |
| `smtp_port` | int | `465` | SMTP 端口 |
| `tls` | string | `ssl` | 加密方式 (ssl / starttls) |
| `max_items` | int | `15` | 邮件最多展示论文数 |
| `include_pdf_links` | bool | `true` | 是否包含 PDF 链接 |
| `include_score` | bool | `true` | 是否显示推荐分数 |
| `detail` | string | `full` | 详情模式 (simple / full) |

### 站点 (`site`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `true` | 是否生成站点 |
| `dir` | string | `docs` | 站点输出目录 |
| `title` | string | `Paper Tracker...` | 站点标题 |
| `keep_runs` | int | `30` | 保留最近 N 次运行 |
| `theme` | string | `light` | 主题 (light / dark) |
| `accent` | string | `#2563eb` | 主题色 |

---

## 本地运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/paper-tracker.git
cd paper-tracker

# 安装依赖
pip install -r requirements.txt

# 运行一次
python -m src.cli run --config config.yaml

# 测试检索
python -m src.cli test-search --lookback-days 3

# 测试邮件
python -m src.cli test-email

# 查看配置
python -m src.cli config

# Dry run (不发邮件、不写状态)
python -m src.cli run --dry-run
```

---

## 前端管理界面

前端使用 Vue 3 + Vite 构建。

```bash
cd frontend
npm install
npm run dev       # 开发模式 (http://localhost:3000)
npm run build     # 生产构建
```

前端部署在 `gh-pages` 分支，由 `deploy-frontend.yml` 自动构建部署。

---

## 项目结构

```
paper-tracker/
├── config.yaml              # 配置文件
├── requirements.txt         # Python 依赖
├── LICENSE                  # MIT License
├── README.md                # 中文说明
├── README_EN.md             # 英文说明
├── .gitignore
│
├── src/                     # Python 核心引擎
│   ├── __init__.py
│   ├── cli.py               # 命令行入口
│   ├── config.py            # 配置管理器
│   ├── pipeline.py          # 主流程编排
│   ├── arxiv_fetcher.py     # arXiv API 检索
│   ├── semantic_scholar.py  # Semantic Scholar 客户端
│   ├── bib_loader.py        # BibTeX 加载器
│   ├── embedder.py          # Embedding 计算器
│   ├── cache.py             # Embedding 缓存
│   ├── recommender.py       # 本地论文推荐
│   ├── filter_engine.py     # 过滤引擎
│   ├── dedup.py             # 去重管理器
│   ├── summarizer.py        # LLM 摘要生成
│   ├── emailer.py           # 邮件发送
│   └── site_builder.py      # 站点生成
│
├── frontend/                # Vue 3 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── stores/config.js
│       ├── views/           # 7 个页面
│       ├── components/      # 4 个组件
│       └── assets/styles.css
│
├── .github/workflows/       # GitHub Actions
│   ├── digest.yml           # 定时检索
│   └── deploy-frontend.yml  # 前端部署
│
├── skills/paper-tracker/    # Skill 定义
│   ├── SKILL.md
│   └── README.md
│
├── data/                    # .bib 文件目录
├── outputs/                 # 运行结果 JSON
├── docs/                    # GitHub Pages 站点
├── .cache/                  # 缓存目录
└── .state/                  # 去重状态
```

---

## 常见问题

### Q: 邮件发送失败，提示 SMTP 认证错误？
A: 确认 `EMAIL_PASSWORD` 使用的是 QQ 邮箱**授权码**而非登录密码。获取方式：QQ 邮箱 → 设置 → 账户 → POP3/SMTP 服务 → 生成授权码。

### Q: arXiv API 返回为空？
A: arXiv API 对过于宽泛或过于窄的关键词可能返回空。建议先用 `test-search` 命令验证检索结果。

### Q: 如何添加更多关键词组？
A: 编辑 `config.yaml` 中的 `search.keyword_groups`，参照已有格式添加新组。支持 AND/OR 逻辑。

### Q: 本地推荐不生效？
A: 确保 `local_recommend.enabled: true`，且 `data/` 目录下有有效的 `.bib` 文件（需包含 abstract 字段）。

### Q: 如何调整运行时间？
A: 修改 `.github/workflows/digest.yml` 中的 cron 表达式。注意 GitHub Actions 使用 UTC 时间。

### Q: GitHub Pages 不更新？
A: 确认 `Settings → Pages → Source` 选择 `Deploy from a branch`，Branch 为 `main`，目录为 `/docs`。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 致谢

本项目参考和借鉴了以下优秀项目：

- [arXiv API](https://info.arxiv.org/help/api/) - arXiv 官方 API
- [Semantic Scholar API](https://api.semanticscholar.org/) - 学术搜索引擎
- [sentence-transformers](https://www.sbert.net/) - Embedding 模型
- [BGE](https://github.com/FlagOpen/FlagEmbedding) - BAAI 通用 Embedding

---

## License

MIT License. 详见 [LICENSE](LICENSE) 文件。
