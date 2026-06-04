# Paper To Obsidian Skill

`paper-to-obsidian-skill` 是一个面向 Codex、Claude、WorkBuddy 和兼容 CLI runtime 的论文阅读与 Obsidian 发布 skill。它会把论文整理成 Obsidian vault 里的 Markdown 笔记：YAML frontmatter 保存索引字段，正文承载深度阅读报告、公式、图表、实验结果、代码检查、局限性和复现笔记。

默认工作流不需要 Obsidian MCP、connector 或 API token。Obsidian vault 本质是本地文件夹，所以这个 skill 直接写 Markdown 文件和附件。

## 功能

- 支持本地 PDF、arXiv URL、DOI、论文网页或标题。
- 抽取经过来源校验的 metadata 和证据。
- arXiv HTML 可用时，优先用它解析章节、公式、表格和图像 URL。
- 从 metadata 和 Markdown report 构建 `obsidian_payload.json`。
- 在 Obsidian vault 中创建或更新一篇论文笔记。
- 将本地证据图片复制到 vault 附件目录。
- 按 DOI、arXiv ID 或规范化标题去重。

## 仓库结构

```text
paper-to-obsidian-skill/
  .claude-plugin/marketplace.json
  SKILL.md
  agents/openai.yaml
  config/obsidian_schema.yaml
  plugins/paper-to-obsidian/
  references/
  scripts/
  tools/
```

根目录 skill 是源文件。Claude plugin 副本用下面的命令同步：

```bash
python tools/sync_plugin.py
```

## 安装到 Codex

把仓库复制到 Codex skills 目录：

```powershell
Copy-Item -Recurse . $env:USERPROFILE\.codex\skills\paper-to-obsidian-skill
```

然后使用：

```text
Use $paper-to-obsidian-skill to read this paper in English and save it to my Obsidian vault:

Vault path: D:\path\to\vault
Paper: https://arxiv.org/abs/1706.03762
```

## 本地环境

准备并检查 Python 环境：

```bash
python scripts/setup_environment.py --use-uv --install --json-report .paper-obsidian/environment-check.json
```

运行 smoke test：

```bash
python scripts/smoke_test_attention.py --output .paper-obsidian/smoke-test
```

## 发布流程

构建 payload：

```bash
python scripts/build_obsidian_payload.py --metadata metadata.json --report report.md --output obsidian_payload.json --vault-path D:\path\to\vault
```

校验报告质量：

```bash
python scripts/validate_report_quality.py report.md --payload obsidian_payload.json
```

校验：

```bash
python scripts/validate_obsidian_payload.py obsidian_payload.json --require-vault
```

dry run 后发布：

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --dry-run
python scripts/publish_obsidian_payload.py obsidian_payload.json --if-exists update
```

## 默认 vault 结构

- 笔记目录：`Papers/`
- 附件目录：`Papers/assets/`
- schema：`config/obsidian_schema.yaml`
- 本地状态：`.paper-obsidian/config.json`

frontmatter 保持轻量。贡献分析、方法细节、实验解释、局限性、证据说明和复现记录放在 Markdown 正文里。
