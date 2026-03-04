---
name: phi-safe-analysis
description: Use when working with patient data, healthcare spreadsheets, clinical files, or any data that may contain Protected Health Information (PHI). Activates automatically when files contain patient names, DOBs, MRNs, or medical records.
---

# PHI-Safe Analysis

You are working in a HIPAA-aware environment with the Redact PHI plugin active.

## Rules

1. **NEVER read patient data files directly.** Always use `load_file_safe()` to open spreadsheets, CSVs, or data files that may contain PHI. This tool automatically detects and tokenizes PHI columns before you see the data.

2. **NEVER process pasted patient data raw.** When a user pastes or types text containing patient information (names, DOBs, MRNs, etc.), call `scrub_text()` on it first before doing any analysis.

3. **ALWAYS re-identify before presenting final output.** Before showing the user your final answer, analysis, summary, or report, call `reidentify()` to replace tokens with real values. The user needs to see real names and dates in their output.

4. **Treat tokens as opaque identifiers.** During your analysis, tokens like `[NAM_a1b2c3d4e5f6]` are just unique patient identifiers. You can group by them, count them, compare them — but never try to guess or reconstruct the original values.

5. **Same token = same entity.** If you see `[NAM_a1b2c3d4e5f6]` in multiple rows or files, it is the same patient. The token system ensures consistency across documents.

6. **Surface flagged matches.** If the system flags a potential patient match for confirmation, present it to the user and ask them to confirm or reject before proceeding with analysis that depends on it.

7. **Respect exemptions.** If the user asks to keep a PHI type visible (e.g., provider names for performance comparison), use `exempt_phi()`. Never exempt SSN.

## Workflow

```
1. User asks to analyze a file
2. You call load_file_safe(path) → get clean tokenized data
3. You analyze the clean data (tokens are opaque identifiers)
4. You call reidentify(your_output, doc_id) → get real values
5. You present the re-identified output to the user
```

## When User Pastes Data in Chat

```
1. User pastes text with patient info
2. You call scrub_text(user_text) → get clean version
3. You process the clean version
4. You call reidentify(your_answer, doc_id) → restore real values
5. You present re-identified answer
```

## Available Tools

- `load_file_safe(path)` — Load and de-identify a data file
- `scrub_text(text)` — De-identify pasted/typed text
- `reidentify(text, doc_id)` — Restore real values in your output
- `reidentify_file(content, output_path, doc_id)` — Re-identify and save to file
- `inspect(text)` — Debug: see what PHI was detected
- `session_status()` — Check session stats
- `exempt_phi(phi_type, reason)` — Keep a PHI type visible
- `remove_exemption(phi_type)` — Re-enable tokenization
- `confirm_match(token_a, token_b)` — Confirm patient identity match
- `reject_match(token_a, token_b)` — Reject patient identity match
