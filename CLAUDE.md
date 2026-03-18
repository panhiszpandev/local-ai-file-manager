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

## What the app does (v0.1.0)
1. Takes a `path` as a CLI argument
2. Recursively scans the given path — all subdirectories (all levels deep) and all files (hidden files are skipped)
3. Reads file metadata
4. Classifies each file by type and category (single-level taxonomy, no subcategories)
5. Generates a CSV file with the result: old path, new path, old name, new name, target directory

## File classification — local LLM
Classification is performed by a **local LLM running in LM Studio** in up to two steps:
- **Step 1 (all files):** main classifier sends file metadata + image (if applicable) to the LLM, which returns `visual_content` description and a category
- **Step 2 (images only, when visual_content suggests a document):** a specialized document analyzer makes a second vision call with a focused prompt and document-type table to refine the category
- If confidence < 90%, the file is classified as `Do przejrzenia` regardless of the suggested category
- Model: **Qwen2.5 7B Vision** — OpenAI-compatible API, works offline, supports image analysis
- Unsupported file formats (e.g. HEIC) fall back to `Do przejrzenia`

## CRITICAL — file operation safety rule

**The app in v0.1.0 does NOT perform any operations on files or directories.**

The only output of the app is a CSV file containing proposed changes.

Any future action modifying the filesystem (rename, move, delete, etc.) MUST:
1. Display the full list of planned changes to the user
2. Ask for confirmation: "Are you sure you want to perform these operations? (yes/no)"
3. Execute actions ONLY after explicit user confirmation

This rule is a core principle of the app and must not be skipped in any version.

## CSV output format
- `old_path` — original full path
- `new_path` — proposed new full path
- `old_name` — original file/directory name
- `new_name` — proposed new name
- `visual_content` — LLM description of image content (images only)
- `file_type` — file type (extension)
- `category` — assigned category from taxonomy
- `confidence` — LLM confidence score (0.00–1.00)
- `alternative_category` — second best category if confidence < 0.9
- `action` — proposed action (rename / move / rename+move / none)
- `size_bytes` — file size in bytes
- `is_dir` — whether the entry is a directory

## Project structure
```
local-ai-file-manager/
├── CLAUDE.md
├── CLAUDE.local.md           # private local settings (not committed)
├── README.md
├── requirements.txt          # openai>=1.0.0
├── .gitignore
├── main.py                   # entry point, argparse CLI
└── src/
    ├── __init__.py
    ├── models.py             # dataclasses: FileInfo, ClassificationResult
    ├── scanner.py            # rglob, reads stat(), skips hidden files
    ├── classifier.py         # orchestrates classification pipeline
    ├── document_analyzer.py  # specialized second-step vision classifier for documents
    ├── image_utils.py        # image encoding, user message builder
    ├── utils.py              # shared utilities (strip_markdown)
    ├── csv_writer.py         # CSV output
    └── prompts/
        ├── system_prompt.md      # main LLM system prompt
        ├── taxonomy.md           # single-level category taxonomy
        └── document_analyzer.md  # document specialist prompt
```

## Running the app
```bash
pip install -r requirements.txt
python main.py /path/to/folder --output result.csv

# optional flags:
# --lm-url  http://localhost:1234/v1   (default LM Studio address)
# --model   qwen2.5-7b-instruct        (model name in LM Studio)
```

## Project status
- **v0.1.0 — in progress**
- Core pipeline working and tested on real data
- Two-step document classification implemented
- Single-level taxonomy in place (12 categories)
- GitHub: https://github.com/panhiszpandev/local-ai-file-manager (branch: main, SSH)

## TODO for next sessions
- [ ] PDF content extraction (e.g. `pypdf`) to improve classification of PDFs
- [ ] Error handling for LM Studio connection issues (timeout, model unavailable)
- [ ] Possible: add `--dry-run` flag vs execution mode in the future
