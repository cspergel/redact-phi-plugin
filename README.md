# Redact PHI — Claude Cowork Plugin

Seamlessly scrub ePHI from spreadsheets and conversations in Claude Cowork with round-trip re-identification.

## Quick Start

1. Install the plugin:
   ```bash
   claude plugin install redact-phi
   ```

2. Drop a spreadsheet with patient data into your Cowork folder

3. Ask Claude to analyze it — PHI is automatically scrubbed before Claude sees it and re-identified in final outputs

## Features

- Automatic PHI detection in spreadsheet columns (names, DOB, MRN, etc.)
- HMAC-based tokenization (deterministic, joinable across documents)
- MRN-based cross-document patient linking
- Selective PHI exemptions (keep provider names visible for analysis)
- Confidence-based match flagging for uncertain identity merges
- Local audit trail with every operation logged
- Supports: .xlsx, .xls, .csv, .tsv

## Commands

- `/redact-status` — Show plugin status, active tokens, and exemptions

## Development Setup

```bash
# Clone this repo
git clone https://github.com/cspergel/redact-phi-plugin.git
cd redact-phi-plugin

# Install dependencies (pulls redactiphi from GitHub)
pip install -e ".[dev]"

# Or if developing alongside the redact repo locally:
pip install -e /path/to/redact
pip install -e ".[local,dev]"

# Run tests
pytest tests/ -v
```

## Requirements

- Claude Cowork (macOS or Windows)
- Python 3.10+
- uv package manager
