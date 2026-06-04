# Schema Customization

Use `config/obsidian_schema.yaml` to customize the Obsidian frontmatter schema. The YAML is the source of truth for setup, payload validation, note rendering, and user-facing schema documentation.

## Basic Workflow

1. Copy `config/obsidian_schema.yaml` if you want a project-specific schema.
2. Edit property names, frontmatter names, types, options, defaults, or optional extensions.
3. Validate:

```bash
python scripts/schema_tool.py --schema config/obsidian_schema.yaml --command validate
```

4. Render a template:

```bash
python scripts/schema_tool.py --schema config/obsidian_schema.yaml --command frontmatter-template
```

## Supported Property Fields

Each property object supports:

```yaml
- name: "Rating"
  frontmatter: "rating"
  type: "SELECT"
  required: false
  default: ""
  purpose: "Reader rating."
  options:
    - { name: "5 stars" }
```

## Supported Types

The schema tool accepts:

```text
TEXT, LIST, DATE, URL, SELECT, NUMBER, BOOLEAN
```

Every property should have a unique `frontmatter` field. The schema must define a `title` frontmatter field.

## Select And List Options

For `SELECT`, validation fails unless the value is listed in `options`. For `LIST`, validation allows values beyond the configured options so controlled categories can evolve.

Store open-ended paper topic phrases in `keywords` as a list.

## Design Guidance

- Keep the default frontmatter lean. Add long analysis to the note body.
- Prefer fields that support filtering, sorting, search, status, review, and retrieval.
- Put scoring/team/discovery fields under `optional_extensions` until the user asks for those workflows.
- Keep `doi`, `arxiv`, `original_title`, and `dedup_key` stable because deduplication depends on them.
