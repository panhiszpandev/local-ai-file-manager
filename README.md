# local-ai-file-manager

A local CLI tool that scans a directory, analyzes files using a local LLM agent with tool calling, and generates a CSV with summaries, categories, and suggested filenames — without touching any files.

## How it works

1. Recursively scans a given directory (hidden files/dirs are skipped)
2. Writes a CSV with all discovered files (status: `NEW`)
3. For each file, an LLM agent autonomously selects tools to read and analyze the content
4. Agent returns a summary, category, and suggested filename
5. CSV is updated per file (`DONE` or `FAILED`) — resumable on interrupt

## Requirements

- Python 3.9+
- [LM Studio](https://lmstudio.ai/) running locally with **GLM-4.7-Flash** (or compatible model with tool calling and vision support)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py /path/to/folder --output result.csv
```

**Optional flags:**

| Flag | Default | Description |
|---|---|---|
| `--output`, `-o` | `result.csv` | Output CSV file path |
| `--lm-url` | `http://127.0.0.1:1234/v1` | LM Studio API base URL |
| `--model` | `glm-4.7-flash` | Model name as shown in LM Studio |

Defaults can be overridden with environment variables `LLM_BASE_URL` and `LLM_MODEL` (or a `.env` file).

## Agent tools

The agent has 4 tools it can call autonomously based on file type:

| Tool | Purpose |
|---|---|
| `get_file_info` | File metadata (size, dates, MIME type) |
| `read_text` | Text extraction (txt, md, csv, html, docx, rtf) |
| `read_pdf` | PDF text extraction (text-based + scanned OCR via vision) |
| `read_image` | Image analysis via vision model |

## Output CSV columns

| Column | Description |
|---|---|
| `path` | Original absolute path |
| `name` | Original filename |
| `extension` | File extension |
| `size_bytes` | File size in bytes |
| `status` | Processing status: `NEW`, `DONE`, or `FAILED` |
| `summary` | LLM-generated summary of file contents |
| `category` | Assigned category from taxonomy |
| `suggested_name` | Proposed descriptive filename |
| `error` | Error description (only for `FAILED` files) |

## Categories

| Category | Contains |
|---|---|
| **Kariera** | CV, job applications, employment contracts, certificates |
| **Finanse** | Invoices, bank statements, payslips, tax documents |
| **Zdrowie** | Medical results, prescriptions, health insurance |
| **Admin** | Utility bills, government letters, property documents, insurance |
| **Podróże** | Flight tickets, boarding passes, hotel reservations |
| **Zakupy** | Purchase confirmations, warranties, product manuals |
| **Edukacja** | Course materials, notes, textbooks, research papers |
| **Technologia** | Source code, scripts, technical documentation |
| **Zdjęcia** | Photos of people, places, events, scenery |
| **Multimedia** | Movies, music, games, entertainment |
| **Osobiste** | ID documents, personal notes, private correspondence |
| **Do przejrzenia** | Unclassified, uncertain, or low-confidence files |

## Safety

**The app never modifies, moves, or deletes any files.** The only output is a CSV file with proposals. Any future execution mode will require explicit user confirmation before performing any filesystem operations.

## Project structure

```
local-ai-file-manager/
├── main.py                   # CLI entry point
└── src/
    ├── models.py             # FileRecord dataclass (maps to CSV row)
    ├── llm_client.py         # LLM client wrapper with tool calling support
    ├── agent.py              # Agent: tool-calling loop per file
    ├── scanner.py            # directory scanner, writes initial CSV
    ├── csv_manager.py        # CSV read/write/update with status tracking
    ├── utils.py              # shared utilities
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
