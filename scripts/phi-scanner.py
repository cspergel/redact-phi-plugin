"""Safety hook: scan tool output for potential PHI leakage."""
import json
import re
import sys

# Quick PHI patterns (lightweight, no dependencies)
PHI_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b\d{2}/\d{2}/\d{4}\b", "Date (possible DOB)"),
    (r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", "Possible name"),
    (r"\bMR[- ]?\d{4,}\b", "MRN"),
    (r"\b\d{10}\b", "Possible NPI/phone"),
]

def scan_for_phi(text: str) -> list:
    """Scan text for potential PHI patterns."""
    findings = []
    for pattern, label in PHI_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            findings.append({"type": label, "count": len(matches)})
    return findings


def main():
    # Read tool output from stdin (provided by hook system)
    tool_output = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not tool_output:
        sys.exit(0)

    findings = scan_for_phi(tool_output)
    if findings:
        summary = ", ".join(f"{f['count']} {f['type']}" for f in findings)
        print(
            f"Warning: Potential PHI detected in raw tool output ({summary}). "
            f"Use load_file_safe() or scrub_text() to ensure proper de-identification.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
