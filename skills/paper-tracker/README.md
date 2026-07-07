# Paper Tracker Skill

arXiv 论文每日追踪与推荐系统。

## 快速开始

### 1. Fork 仓库
将项目 Fork 到你的 GitHub 账户。

### 2. 配置 Secrets
在 GitHub 仓库 Settings > Secrets and variables > Actions 中添加：
- `EMAIL_USER` - QQ 邮箱账号
- `EMAIL_PASSWORD` - QQ 邮箱授权码
- `LLM_API_KEY` (可选) - LLM API Key

### 3. 修改配置
编辑 `config.yaml`，设置你的关键词组和期刊白名单。

### 4. 启用 Actions
在 Actions 标签页启用 Workflow，系统将在每日 UTC 19:00 自动运行。

### 5. 查看结果
- 邮件日报发送到你的 QQ 邮箱
- GitHub Pages 站点自动更新

## 本地运行
```bash
pip install -r requirements.txt
python -m src.cli run --config config.yaml
```

## 测试
```bash
# 测试检索
python -m src.cli test-search --lookback-days 3

# 测试邮件
python -m src.cli test-email

# 查看配置
python -m src.cli config
```
