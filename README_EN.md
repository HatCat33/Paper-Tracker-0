# Paper Tracker — arXiv Daily Paper Tracking & Recommendation System

> An open-source arXiv daily paper tracking and recommendation system running on GitHub Actions.
> Scheduled arXiv + Semantic Scholar retrieval, multi-keyword-group filtering, journal whitelist,
> local library embedding recommendation, LLM bilingual summaries, semantic similarity filtering,
> HTML digest delivered via QQ Mail SMTP, with GitHub Pages web archive.

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  arXiv API  │──▶ │ Fetch&Filter │──▶ │  S2 Citations│
└─────────────┘    └──────┬───────┘    └──────┬───────┘
                          │                    │
                          ▼                    ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Local .bib  │──▶ │  Recommender │──▶ │  LLM Summary │
└─────────────┘    └──────┬───────┘    └──────┬───────┘
                          │                    │
          ┌───────────────┴────────────────────┘
          ▼                        ▼
┌──────────────────┐    ┌──────────────────┐
│  QQ Mail HTML     │    │ GitHub Pages Site│
└──────────────────┘    └──────────────────┘
```

---

## Features

| Feature | Status | Description |
|---------|:------:|-------------|
| Multi-keyword-group AND/OR search | ✅ | Independent groups with keyword × sub_keyword logic |
| arXiv category filter | ✅ | cs.CV / cs.LG / cs.AI etc. |
| Exclude keywords | ✅ | Filter out papers matching exclusion terms |
| Journal whitelist filter | ✅ On | Top conference/journal/Q1/custom tiers |
| Cross-day dedup | ✅ | Persistent seen.json to prevent duplicate pushes |
| Semantic Scholar citations | ⬜ Off | Enrich paper metadata with citation counts |
| Local library recommendation | ⬜ Off | Cosine similarity via BGE embeddings |
| LLM bilingual summary | ⬜ Off | DeepSeek / OpenAI / SiliconFlow |
| Semantic similarity filter | ⬜ Off | Embedding-based dedup |
| QQ Mail SMTP delivery | ⬜ Off | Responsive HTML digest |
| GitHub Pages archive | ✅ | Auto-generated historical digest site |
| Vue 3 management UI | ✅ | Visual config, history viewer |

---

## Quick Start

### 1. Fork this repository

Click the `Fork` button on the top-right.

### 2. Configure GitHub Secrets

Add under `Settings → Secrets and variables → Actions`:

| Secret | Description | Required |
|--------|-------------|:--------:|
| `EMAIL_USER` | QQ Mail account (e.g. `123456789@qq.com`) | For email |
| `EMAIL_PASSWORD` | QQ Mail auth code (NOT login password) | For email |
| `EMAIL_SENDER` | Sender address (defaults to EMAIL_USER) | Optional |
| `EMAIL_RECIPIENT` | Recipient address (defaults to EMAIL_USER) | Optional |
| `LLM_API_KEY` | LLM API Key | For summaries |

### 3. Modify configuration

Edit `config.yaml` to set your keyword groups and journal preferences.

### 4. Enable GitHub Actions

Go to the `Actions` tab and click `I understand my workflows...`.

### 5. Trigger a manual run

`Actions → Daily Paper Digest → Run workflow` to verify your setup.

### 6. Set up GitHub Pages

`Settings → Pages → Source: Deploy from a branch → Branch: main, folder: /docs → Save`.

---

## Local Usage

```bash
git clone https://github.com/YOUR_USERNAME/paper-tracker.git
cd paper-tracker
pip install -r requirements.txt

# Run once
python -m src.cli run --config config.yaml

# Test search
python -m src.cli test-search --lookback-days 3

# Test email
python -m src.cli test-email

# View config
python -m src.cli config

# Dry run
python -m src.cli run --dry-run
```

---

## Frontend UI

```bash
cd frontend
npm install
npm run dev       # Dev mode (http://localhost:3000)
npm run build     # Production build
```

The frontend is deployed to the `gh-pages` branch via `deploy-frontend.yml`.

---

## Project Structure

```
paper-tracker/
├── config.yaml
├── requirements.txt
├── README.md / README_EN.md
├── src/                     # Python engine
│   ├── cli.py               # CLI entry
│   ├── config.py            # Config manager
│   ├── pipeline.py          # Pipeline orchestrator
│   ├── arxiv_fetcher.py     # arXiv API client
│   ├── semantic_scholar.py  # S2 client
│   ├── bib_loader.py        # BibTeX loader
│   ├── embedder.py          # Embedding computer
│   ├── cache.py             # Embedding cache
│   ├── recommender.py       # Local recommender
│   ├── filter_engine.py     # Filter engine
│   ├── dedup.py             # Dedup manager
│   ├── summarizer.py        # LLM summarizer
│   ├── emailer.py           # Email sender
│   └── site_builder.py      # Site builder
├── frontend/                # Vue 3 frontend
├── .github/workflows/       # GitHub Actions
├── skills/paper-tracker/    # Skill definition
├── data/                    # .bib files
├── outputs/                 # JSON results
├── docs/                    # GitHub Pages
└── .state/                  # Dedup state
```

---

## FAQ

### Q: Email fails with SMTP auth error?
A: Ensure `EMAIL_PASSWORD` is the QQ Mail **authorization code**, not your login password. Generate it at QQ Mail → Settings → Account → POP3/SMTP.

### Q: arXiv API returns empty?
A: Try `test-search` first with different keywords. Queries that are too broad or narrow may return nothing.

### Q: How to add more keyword groups?
A: Edit `search.keyword_groups` in `config.yaml`. Each group supports AND/OR logic.

### Q: Local recommendations not working?
A: Set `local_recommend.enabled: true` and ensure `data/` contains valid `.bib` files with abstracts.

### Q: How to change the schedule?
A: Modify the cron expression in `.github/workflows/digest.yml`. GitHub Actions uses UTC.

---

## Contributing

Issues and PRs are welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Acknowledgments

- [arXiv API](https://info.arxiv.org/help/api/)
- [Semantic Scholar API](https://api.semanticscholar.org/)
- [sentence-transformers](https://www.sbert.net/)
- [BGE](https://github.com/FlagOpen/FlagEmbedding)

---

## License

MIT License. See [LICENSE](LICENSE).
