# Runtime And Vault Access

Use this reference during setup when deciding how the skill should write to Obsidian from a specific agent runtime.

## Default Pattern

Obsidian vaults are normal local directories containing Markdown notes and attachments. The default publishing path needs filesystem access only:

- Read and write Markdown files under the selected vault.
- Create the configured notes directory when missing.
- Create the configured attachments directory when missing.
- Copy local evidence images into the vault.
- Verify note and attachment paths after writing.

No Obsidian MCP server, connector, desktop app, or API token is required for the default workflow.

## Optional App-Level Integrations

Only use an Obsidian MCP server, Local REST API plugin, or app automation when the user explicitly asks to control Obsidian itself, trigger Obsidian commands, inspect plugin-rendered output, or interact with the currently open vault through the app UI.

When an optional integration is used:

1. Keep the file-based payload and frontmatter schema unchanged.
2. Treat connector access as user-scoped and operate only inside the requested vault.
3. Do not require app-level integration for normal note creation.

## Capability Checklist

Before setup or publishing, verify:

- The vault path exists and is a directory.
- The configured `notes_dir` and `attachments_dir` are vault-relative paths without `..`.
- The runtime can write a test file or run a dry-run publish.
- Python dependencies are available for paper reading.

If filesystem write access is unavailable, complete local report generation outside the vault and tell the user which path could not be written.

## Safety Boundary

- Never write outside the resolved vault path.
- Do not delete existing user notes.
- On duplicates, update only the matched paper note unless the user asks otherwise.
- Keep API keys and private credentials out of generated notes, payloads, and frontmatter.
