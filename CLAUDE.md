# CLAUDE.md — local-ai-file-manager

## Local overrides
A `CLAUDE.local.md` file may exist alongside this file for private, machine-local settings (not committed to git). Always load it if present — it takes precedence over this file.

## Commit message policy
- Use the `type: short description` format
- Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`
- Body (optional) explains the *why*, not the *what*
- No co-author lines, no AI attribution

### Branching & merging
- Changes to `src/` and `main.py` go through **pull requests** — no direct pushes to `main`
- Documentation and config files (`CLAUDE.md`, `requirements.txt`, `.gitignore`, etc.) may be pushed directly to `main`
- PRs are merged using **squash merge**
- The squash commit uses the dominant type of the PR with a summary title
- The body lists the individual commits that made up the PR:

```
feat: confidence scoring and classification fixes

- feat: add confidence score and alternative category to classification
- feat: add confidence and alternative category columns to CSV output
- feat: show confidence and alternative category in CLI logs
- fix: strip markdown code block from LLM JSON response
- fix: remove undefined threshold rule from taxonomy
```

- Branch names should be short and descriptive (e.g. `threshold-experiment`, `pdf-support`)

### Pull request description format
PR title follows the same `type: short description` convention as commits.
PR body lists the individual commits that made up the branch:

```
feat: improve image and PDF classification accuracy

- refactor: split classifier into focused modules
- feat: add two-step document analysis for images
- feat: simplify taxonomy to single-level categories with descriptions
- refactor: remove subcategory from data model, CSV output and CLI logs
- fix: skip hidden files and directories in scanner
- feat: fallback to Do przejrzenia when confidence below 90%
```

## Language policy
- All documentation, comments, code identifiers, prompts, and any text not directly representing user data (e.g. file names, paths) must be written in **English**
- CSV column names and values that are not user-provided data (e.g. category names, action types) must also be in **English**
- User-facing CLI messages should be in English

## Language & stack
- Python
- Interface: terminal (CLI) — no UI in v0.1.0

## Architecture — roadmap
- **v0.1.0** — local app, everything runs on a single machine
- **future** — client-server architecture (split into server and client applications)

## What the app does (v0.2.0)
1. Takes a `path` as a CLI argument
2. Recursively scans the given path — all files (hidden files/dirs are skipped)
3. Writes a CSV file with all discovered files (status: `NEW`)
4. For each `NEW` file, an LLM agent autonomously selects tools to read and analyze the file
5. Agent returns: summary, category, suggested filename
6. CSV is updated per file (status: `DONE` or `FAILED`) — resumable on interrupt

## File analysis — LLM agent with tool calling
Analysis is performed by an **LLM agent running in LM Studio** using **function calling**:
- The agent has 4 tools: `get_file_info`, `read_text`, `read_pdf`, `read_image`
- The agent autonomously decides which tools to call based on the file type
- `read_pdf` detects whether a PDF is text-based or scanned (falls back to vision OCR)
- `read_image` sends images to the vision model for content description
- Model: **GLM-4.7-Flash** — OpenAI-compatible API, works offline, supports tool calling and vision
- Unsupported file formats result in status `FAILED` with error description

## CRITICAL — file operation safety rule

**The app in v0.1.0 does NOT perform any operations on files or directories.**

The only output of the app is a CSV file containing proposed changes.

Any future action modifying the filesystem (rename, move, delete, etc.) MUST:
1. Display the full list of planned changes to the user
2. Ask for confirmation: "Are you sure you want to perform these operations? (yes/no)"
3. Execute actions ONLY after explicit user confirmation

This rule is a core principle of the app and must not be skipped in any version.

## CSV output format
- `path` — original absolute path
- `name` — original filename
- `extension` — file extension
- `size_bytes` — file size in bytes
- `status` — processing status: `NEW` | `DONE` | `FAILED`
- `summary` — LLM-generated summary of file contents
- `category` — assigned category from taxonomy
- `suggested_name` — proposed descriptive filename
- `error` — error description (only for `FAILED` files)

## Project structure
```
local-ai-file-manager/
├── CLAUDE.md
├── CLAUDE.local.md           # private local settings (not committed)
├── README.md
├── requirements.txt          # openai, pypdf, python-docx, striprtf
├── .gitignore
├── main.py                   # CLI entry point
└── src/
    ├── __init__.py
    ├── models.py             # FileRecord dataclass (maps to CSV row)
    ├── llm_client.py         # LLM client wrapper with tool calling support
    ├── agent.py              # Agent: tool-calling loop per file
    ├── scanner.py             # directory scanner, writes initial CSV
    ├── csv_manager.py        # CSV read/write/update with status tracking
    ├── utils.py              # shared utilities (strip_markdown)
    ├── tools/
    │   ├── __init__.py       # tool registry (definitions + dispatch)
    │   ├── get_file_info.py  # file metadata (size, dates, MIME type)
    │   ├── read_text.py      # text extraction (txt, docx, md, html, rtf)
    │   ├── read_pdf.py       # PDF text extraction (text-based + scanned OCR)
    │   └── read_image.py     # image analysis via vision model
    └── prompts/
        ├── agent_system.md   # agent system prompt
        └── taxonomy.md       # single-level category taxonomy
```

## Running the app
```bash
pip install -r requirements.txt
python main.py /path/to/folder --output result.csv

# optional flags:
# --lm-url  http://localhost:1234/v1   (default LM Studio address)
# --model   glm-4.7-flash              (model name in LM Studio)
```

## Project status
- **v0.2.0 — in progress**
- Agent-based architecture with tool calling
- PDF text extraction + scanned PDF OCR via vision
- Text file extraction (txt, docx, md, html, rtf)
- Image analysis via vision model
- Resumable CSV pipeline (NEW/DONE/FAILED statuses)
- Single-level taxonomy in place (12 categories)
- GitHub: https://github.com/panhiszpandev/local-ai-file-manager (branch: main, SSH)

## TODO for next sessions
- [ ] Error handling for LM Studio connection issues (timeout, model unavailable)
- [ ] Possible: add `--dry-run` flag vs execution mode in the future
