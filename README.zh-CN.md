# Paper To Obsidian Skill

[English](README.md) | [简体中文](README.zh-CN.md)

`paper-to-obsidian-skill` 是一个面向 Codex、Claude、WorkBuddy 和兼容 CLI agent runtime 的论文阅读与 Obsidian 发布 skill。它会把论文整理成 Obsidian vault 里的 Markdown 笔记：YAML frontmatter 保存索引字段，正文承载深度阅读报告、公式、图表、代码检查、局限性和复现笔记。

默认工作流不需要 MCP connector、workspace connector、API token，也不要求本机安装 Obsidian 桌面端。Obsidian vault 本质是本地文件夹，所以这个 skill 直接写 Markdown 文件和附件。

默认报告语言是英文。你也可以要求中文报告或中英双语报告。

## 安装

### 方式 1：让 Agent 自动安装

如果你已经在用 Codex，最省事的方式是直接把安装任务交给 agent。它会安装 skill，并继续完成第一次工作流设置。

把下面这段话发给 Codex：

```text
请帮我安装这个 skill：
https://github.com/Guesswhat-Studio/paper-to-obsidian-skill

请把它安装到我的 Codex skills 目录，然后使用 $paper-to-obsidian-skill 设置我的 Obsidian 论文阅读工作流。

Vault path: <我的 Obsidian vault 绝对路径>

请自动完成后续设置：准备本地 Python 环境，校验 Obsidian frontmatter schema，运行 Attention Is All You Need smoke test，保存 .paper-obsidian/config.json，最后只告诉我笔记路径、验证结果，以及还需要我手动处理的事项。
```

### 方式 2：Claude Code Plugin 安装

Claude Code 的 plugin 命令由 Claude Code CLI 自己处理。模型在聊天里不能替你执行 `/plugin marketplace add` 或 `/plugin install`。请你先手动运行安装命令，再让安装好的 skill 继续做 setup。

在 Claude Code 交互会话里逐条输入。每输入一条就按 Enter，等它执行完成后再输入下一条：

```text
/plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill
```

```text
/plugin install paper-to-obsidian@guesswhat-paper-tools
```

```text
/reload-plugins
```

```text
/paper-to-obsidian:paper-to-obsidian-skill set up my Obsidian paper reading workflow
```

从终端运行：

```bash
claude plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill
claude plugin install paper-to-obsidian@guesswhat-paper-tools
claude -p "Use /paper-to-obsidian:paper-to-obsidian-skill to set up my Obsidian paper reading workflow. Vault path: <absolute path to my Obsidian vault>. Keep the setup automatic: prepare the local Python environment, validate the schema, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and only report the note path, validation status, and any action I must take."
```

如果你更喜欢一条终端命令：

```bash
claude plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill && claude plugin install paper-to-obsidian@guesswhat-paper-tools && claude -p "Use /paper-to-obsidian:paper-to-obsidian-skill to set up my Obsidian paper reading workflow. Vault path: <absolute path to my Obsidian vault>. Keep the setup automatic: prepare the local Python environment, validate the schema, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and only report the note path, validation status, and any action I must take."
```

Claude 网页聊天不会直接加载 Claude Code plugin。请使用 Claude Code，或支持 plugin 的兼容 Claude workspace 产品。

### 方式 3：手动安装

#### Codex

Windows 默认 Codex skills 目录：

```cmd
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git "%USERPROFILE%\.codex\skills\paper-to-obsidian-skill"
```

Windows 自定义 `CODEX_HOME`：

```cmd
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git "%CODEX_HOME%\skills\paper-to-obsidian-skill"
```

macOS 或 Linux：

```bash
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git "$HOME/.codex/skills/paper-to-obsidian-skill"
```

安装完成后，在 Codex 里说：

```text
Use $paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <我的 Obsidian vault 绝对路径>
```

#### Claude Code

把仓库添加为 Claude Code plugin marketplace，并安装插件：

```bash
claude plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill
claude plugin install paper-to-obsidian@guesswhat-paper-tools
```

然后启动 Claude Code 并输入：

```text
Use /paper-to-obsidian:paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <我的 Obsidian vault 绝对路径>
```

兼容 plugin 的用户可以添加同一个 GitHub 仓库作为 marketplace，然后从 `guesswhat-paper-tools` 安装 `Paper To Obsidian`。

这个仓库的 marketplace 和 plugin 结构遵循 Claude Code plugin 文档：

- [Discover and install plugins](https://code.claude.com/docs/en/discover-plugins)
- [Create and distribute plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)

## 这个 Skill 能做什么

- 从本地 PDF、arXiv URL、DOI、论文 URL 或论文标题开始阅读。
- 从论文原文或官方来源核对标题、作者、日期、venue、DOI、arXiv、代码仓库等元数据。
- 写报告前先建立 source registry 和 reading pack，减少无来源推断。
- arXiv 论文优先使用官方 HTML 渲染：`https://arxiv.org/html/<arxiv_id>`。
- arXiv HTML 的 figure 图片 URL 只有在可访问性检查通过时，才作为 hosted Markdown 图片使用。
- 抽取并解释关键证据：公式、图、表、算法、定理、模型结构图、实验结果、消融、鲁棒性分析等。
- 生成 Obsidian-ready 报告，保留来源依据和不确定性标记。
- 发布前校验报告深度和模板完整性，避免 payload schema 合法但正文过浅。
- 使用 DOI、arXiv ID 或规范化原始标题去重，创建或更新 Obsidian Markdown 笔记。
- frontmatter 保持轻量，长分析放进 Markdown 正文。
- 附带本地脚本：环境检查、schema 校验、payload 构建、payload 验证、Obsidian 发布和 smoke test。

## 仓库结构

```text
paper-to-obsidian-skill/
  .claude-plugin/marketplace.json  # Claude Code marketplace catalog
  .github/workflows/validate.yml    # GitHub Actions validation workflow
  LICENSE                          # MIT license
  SKILL.md                         # 主 skill 指令
  requirements.txt                 # Python 依赖
  agents/openai.yaml               # agent 配置示例
  config/obsidian_schema.yaml      # 默认 Obsidian frontmatter schema
  plugins/paper-to-obsidian/       # Claude Code plugin package（包含 mirrored skill copy）
  references/                      # 阅读、发布、vault 和环境设置参考
  scripts/                         # 环境、报告质量、payload、校验、发布辅助脚本
  tools/                           # 仓库验证和 plugin 同步工具
```

## 环境要求

- Python 3.10 或更新版本；如果本机还没有 Python，需要能运行 shell bootstrap 脚本来安装 uv-managed Python。
- Codex、Claude、WorkBuddy，或兼容 CLI 的 agent runtime。
- 对目标 Obsidian vault 文件夹的本地文件系统读写权限。
- 可选：`uv`，用于更快地创建本地环境。
- 可选：`gh`、`git`、`tesseract`，用于 GitHub 检查、代码仓库核查和扫描版 PDF OCR。

## 维护者说明

上面的安装部分是普通用户路径。下面这些命令主要用于维护、调试和离线环境。

克隆仓库：

```bash
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git
cd paper-to-obsidian-skill
```

作为 Codex skill 安装时，把整个目录放到 Codex skills 目录下。

macOS 或 Linux：

```bash
mkdir -p "$HOME/.codex/skills"
cp -R . "$HOME/.codex/skills/paper-to-obsidian-skill"
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force $env:USERPROFILE\.codex\skills
Copy-Item -Recurse . $env:USERPROFILE\.codex\skills\paper-to-obsidian-skill
```

从本地 checkout 测试 Claude Code plugin：

```bash
claude plugin validate .
claude plugin validate ./plugins/paper-to-obsidian
claude plugin marketplace add .
claude plugin install paper-to-obsidian@guesswhat-paper-tools
```

修改 `SKILL.md`、`requirements.txt`、`agents/`、`config/`、`references/` 或 `scripts/` 后，同步 Claude plugin 副本：

```bash
python tools/sync_plugin.py
```

发布报告前建议先跑报告质量和 payload 两层校验：

```bash
python scripts/validate_report_quality.py paper-output/report.md --payload paper-output/obsidian_payload.json
python scripts/validate_obsidian_payload.py paper-output/obsidian_payload.json --check-image-urls
```

提交前建议跑这两个检查：

```bash
python tools/sync_plugin.py --check
python tools/validate_repository.py
```

WorkBuddy 或其他兼容 runtime 可以把这个仓库作为 skill/workflow 目录加入，并让 agent 能读取 `SKILL.md`。

## CI

GitHub Actions 会在 push 和 pull request 时运行轻量验证：

- 编译 Python helper scripts 和 repository tools。
- 用 `tools/sync_plugin.py --check` 检查 Claude plugin 副本是否保持字节级同步。
- 用 `tools/validate_repository.py` 检查仓库打包结构和 mirror 约束。
- 校验 Obsidian frontmatter schema。
- 检查 helper CLI 入口。

arXiv network smoke test 只在手动 `workflow_dispatch` 且设置 `run_network_smoke=true` 时运行，避免临时网络或 arXiv 波动阻塞普通 PR。

## Agent 会自动设置什么

安装完成后，Codex 或 Claude 应该根据 `SKILL.md` 继续完成这些设置：

- 检测当前 runtime 和本地文件系统访问能力。
- 记录目标 Obsidian vault 路径。
- 校验 `config/obsidian_schema.yaml`。
- 在工作目录准备 Python 环境（`.paper-obsidian/.venv`）。
- 网络可用时运行 `Attention Is All You Need` smoke test。
- 在工作区保存 `.paper-obsidian/config.json`。
- 验证 Obsidian payload 可以 build、validate，并 dry-run 发布到 vault。

## 手动环境命令

如果本机已经有 Python，在工作目录创建虚拟环境（`.paper-obsidian/.venv`）并安装依赖：

```bash
python scripts/setup_environment.py --use-uv --install --json-report .paper-obsidian/environment-check.json
```

如果本机还没有 Python，先走对应系统的 bootstrap 脚本。它们不需要预先有 Python：脚本会先安装或使用独立的 `uv` binary，再由 uv 安装 Python、创建 `.venv`、安装依赖。

Windows PowerShell：

```powershell
.\scripts\bootstrap_uv.ps1 -InstallUv
```

macOS/Linux：

```bash
INSTALL_UV=1 sh scripts/bootstrap_uv.sh
```

只检查当前环境：

```bash
python scripts/setup_environment.py --check-only
```

校验 Obsidian schema：

```bash
python scripts/schema_tool.py --command validate
```

从 arXiv HTML 生成结构化 reading pack：

```bash
python scripts/fetch_arxiv_html.py 1706.03762 --output .paper-obsidian/arxiv-html-test --limit 5
```

运行本地 smoke test：

```bash
python scripts/smoke_test_attention.py --output .paper-obsidian/smoke-test
```

smoke test 会下载 "Attention Is All You Need"，用 PyMuPDF 打开 PDF，渲染第一页证据图片，写入示例 metadata 和 report，构建 `obsidian_payload.json`，并校验 payload。

## Obsidian Vault

默认 vault 结构保持轻量：

- 笔记目录：`Papers/`
- 附件目录：`Papers/assets/`
- metadata 来源：每篇 Markdown 笔记里的 YAML frontmatter。

默认 frontmatter 字段：

- `title`
- `original_title`
- `authors`
- `publication_date`
- `year`
- `venue`
- `field`
- `type`
- `keywords`
- `reading_status`
- `read_date`
- `rating`
- `doi`
- `arxiv`
- `code`
- `report_language`
- `dedup_key`
- `dedup_strategy`
- `tags`

长篇贡献分析、技术核心、实验解释、局限性、复现记录和证据链放在 Markdown 正文里。

机器可读 schema 位于：

```text
config/obsidian_schema.yaml
```

生成 schema 摘要：

```bash
python scripts/schema_tool.py --command summary
```

生成 Markdown frontmatter 模板：

```bash
python scripts/schema_tool.py --command template
```

## 图片处理

- arXiv HTML hosted 图片在 HTTPS 可访问时可以直接嵌入。
- 本地证据截图在报告生成阶段放在 paper output folder。
- `scripts/publish_obsidian_payload.py` 会把本地 Markdown 图片复制到 vault 附件目录，并把链接改写成相对当前笔记的路径。
- 图片不便复制进 vault 时，可以用 `scripts/build_evidence_pack.py` 生成本地 evidence pack。

如果论文 license 或团队策略不允许公开分发图片，不建议把论文图表上传到公共图床。

## 常用调用方式

设置工作流：

```text
Use $paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <我的 Obsidian vault 绝对路径>

Please detect my runtime, prepare the local Python environment, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and verify that a payload can be dry-run published to the vault.
```

常见输入路由保持简单：

- 本地 PDF：走 PDF 解析和证据截图路径。
- arXiv 链接或 ID：优先尝试官方 arXiv HTML，包括已验证的 figure 图片 URL；HTML 不可用再回退 PDF。
- Publisher URL、DOI 或标题：先抓 metadata 和可访问的 full-text HTML；如果页面需要权限，请用户提供 PDF。
- 已有 report 或 payload：跳过阅读，只做 payload 校验和发布。

阅读并发布英文报告：

```text
Use $paper-to-obsidian-skill to read this paper in English and save it to my Obsidian vault:

Vault path: <我的 Obsidian vault 绝对路径>
Paper: https://arxiv.org/abs/1706.03762

Please resolve the paper identity, extract verified metadata, capture important evidence, generate an Obsidian-ready report with formulas, figures, tables, code and reproducibility notes, create or update the Markdown note, and verify the note after publishing.
```

阅读并发布中文报告：

```text
Use $paper-to-obsidian-skill to read this paper in Chinese and save it to my Obsidian vault:

Vault path: <我的 Obsidian vault 绝对路径>
Paper: <PDF path, DOI, arXiv URL, paper URL, or title>

Please keep the official English title in Original Title, write the report body in Chinese, preserve formulas in LaTeX, include key figures and tables, and verify the Markdown note after publishing.
```

发布已有报告：

```text
Use $paper-to-obsidian-skill to publish this existing report to my Obsidian vault:

Vault path: <我的 Obsidian vault 绝对路径>
Report path: <report.md>
Metadata path: <metadata.json>

Please build or validate obsidian_payload.json, deduplicate by DOI/arXiv/title, create or update the Markdown note, and verify the result.
```

## Payload 工作流

从 metadata 和 Markdown report 构建 Obsidian payload：

```bash
python scripts/build_obsidian_payload.py \
  --metadata metadata.json \
  --report report.md \
  --output obsidian_payload.json \
  --vault-path /path/to/obsidian-vault \
  --language English \
  --image-status local_only
```

校验报告质量：

```bash
python scripts/validate_report_quality.py report.md --payload obsidian_payload.json
```

校验 payload：

```bash
python scripts/validate_obsidian_payload.py obsidian_payload.json --require-vault
```

dry run 后发布：

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --dry-run
python scripts/publish_obsidian_payload.py obsidian_payload.json --if-exists update
```

把 Markdown 里的本地图片链接打包成自包含 HTML evidence pack：

```bash
python scripts/build_evidence_pack.py \
  --report report.md \
  --output evidence-pack.html \
  --title "Evidence Pack"
```

## 证据和报告策略

- 事实性表述需要能追溯到论文或官方来源。
- 重要公式保留 LaTeX。
- 关键数值对比整理成 Markdown 表格。
- `local_only` 图片发布前需要能从 payload 目录解析到本地源文件。
- 代码和复现笔记需要说明检查过什么、哪些仍未验证。
- 不确定推断需要明确标注。

## 本地配置状态

工作区相关的设置状态保存在仓库外：

```text
.paper-obsidian/config.json
```

常见字段：

- `runtime`
- `vault_path`
- `notes_dir`
- `attachments_dir`
- `schema_version`
- `default_report_language`

`.paper-obsidian/` 已被 Git 忽略，因为它可能包含本地 runtime 状态。

## Roadmap

- 从 `.txt`、`.md`、`.csv`、Zotero export 或现有 vault 笔记批量导入。
- 可选远程图片缓存或下载 helper。
- 更深入的 arXiv source asset extraction，在官方 HTML 渲染之外获取更高质量的图和表。
- Semantic Scholar 或 OpenAlex citation enrichment。
- 可选每日论文发现模式：arXiv 分类、关键词兴趣、评分和会议追踪。
- 团队阅读模式：assignee、priority、review status、weekly digest。
- 本地向量索引，支持对已读论文继续问答。

## License

MIT License。见 [LICENSE](LICENSE)。
