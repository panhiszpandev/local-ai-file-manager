# local-ai-file-manager

A local CLI tool that scans a directory, classifies files using a local vision LLM, and generates a CSV with proposed file reorganization — without touching any files.

## How it works

1. Recursively scans a given directory (hidden files are skipped)
2. For each file, sends metadata (and image content if applicable) to a local LLM
3. LLM classifies the file into one of 12 categories
4. For images that appear to contain documents, a specialized second vision call refines the category
5. If confidence < 90%, the file is assigned to `Do przejrzenia` (review queue)
6. Outputs a CSV with proposed changes — no files are ever modified

## Requirements

- Python 3.9+
- [LM Studio](https://lmstudio.ai/) running locally with **Qwen2.5 7B Vision** (or compatible vision model)

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
| `--lm-url` | `http://localhost:1234/v1` | LM Studio API base URL |
| `--model` | `qwen2.5-7b-instruct` | Model name as shown in LM Studio |

## Output CSV columns

| Column | Description |
|---|---|
| `old_path` | Original full path |
| `new_path` | Proposed new full path |
| `old_name` | Original filename |
| `new_name` | Proposed new filename |
| `visual_content` | LLM description of image content (images only) |
| `file_type` | File extension |
| `category` | Assigned category |
| `confidence` | LLM confidence score (0.00–1.00) |
| `alternative_category` | Runner-up category when confidence < 0.9 |
| `action` | Proposed action: `rename`, `move`, `rename+move`, or `none` |
| `size_bytes` | File size in bytes |
| `is_dir` | Whether the entry is a directory |

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
    ├── models.py             # FileInfo, ClassificationResult dataclasses
    ├── scanner.py            # recursive file scanner
    ├── classifier.py         # main classification pipeline
    ├── document_analyzer.py  # specialized document vision classifier
    ├── image_utils.py        # image encoding utilities
    ├── utils.py              # shared utilities
    ├── csv_writer.py         # CSV output
    └── prompts/
        ├── system_prompt.md      # main LLM system prompt
        ├── taxonomy.md           # category taxonomy
        └── document_analyzer.md  # document specialist prompt
```
