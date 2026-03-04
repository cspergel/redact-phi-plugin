"""Spreadsheet handler for reading and de-identifying tabular data."""
import csv
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from redactiphi.transform.tokenizer import HMACTokenizer
from redactiphi.transform.models import TokenMap, TokenEntry

from server.column_classifier import ColumnClassifier, ColumnClassification


@dataclass
class SpreadsheetResult:
    """Result of processing a spreadsheet."""
    document_id: str
    rows: List[Dict[str, str]]
    headers: List[str]
    column_classifications: Dict[str, ColumnClassification]
    token_map: TokenMap
    phi_columns_found: List[str]
    rows_processed: int

    def as_text(self) -> str:
        """Return a text representation of the de-identified data."""
        if not self.rows:
            return ""
        lines = []
        lines.append(" | ".join(self.headers))
        lines.append(" | ".join("---" for _ in self.headers))
        for row in self.rows:
            lines.append(" | ".join(row.get(h, "") for h in self.headers))
        return "\n".join(lines)


class SpreadsheetHandler:
    """Reads spreadsheets and de-identifies PHI columns."""

    def __init__(
        self,
        secret_key: bytes,
        scope_id: Optional[str] = None,
    ):
        self._tokenizer = HMACTokenizer(secret_key=secret_key)
        self._classifier = ColumnClassifier()
        self._scope_id = scope_id

    def process(
        self,
        file_path: str,
        document_id: Optional[str] = None,
    ) -> SpreadsheetResult:
        """Process a spreadsheet file and return de-identified data."""
        path = Path(file_path)
        doc_id = document_id or f"{path.stem}_{uuid.uuid4().hex[:8]}"

        if path.suffix.lower() in (".xlsx", ".xls"):
            headers, raw_rows = self._read_excel(path)
        elif path.suffix.lower() in (".csv", ".tsv"):
            headers, raw_rows = self._read_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        classifications = self._classifier.classify_headers(headers)
        phi_cols = [h for h, c in classifications.items() if c.is_phi]

        token_map = TokenMap(document_id=doc_id)
        clean_rows = []

        for row in raw_rows:
            clean_row = {}
            for header in headers:
                value = row.get(header, "")
                if header in phi_cols and value.strip():
                    phi_type = classifications[header].phi_type
                    token = self._tokenizer.tokenize(
                        value=value,
                        phi_type=phi_type,
                        subject_id=self._scope_id,
                    )
                    entry = TokenEntry(
                        token=token,
                        original=value,
                        phi_type=phi_type,
                        normalized=value.lower().strip(),
                    )
                    token_map.add(entry)
                    clean_row[header] = token
                else:
                    clean_row[header] = value
            clean_rows.append(clean_row)

        return SpreadsheetResult(
            document_id=doc_id,
            rows=clean_rows,
            headers=headers,
            column_classifications=classifications,
            token_map=token_map,
            phi_columns_found=phi_cols,
            rows_processed=len(clean_rows),
        )

    def _read_csv(self, path: Path) -> tuple[List[str], List[Dict[str, str]]]:
        """Read a CSV or TSV file."""
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames or []
            rows = list(reader)
        return headers, rows

    def _read_excel(self, path: Path) -> tuple[List[str], List[Dict[str, str]]]:
        """Read an Excel file."""
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(c) if c else f"col_{i}" for i, c in enumerate(next(rows_iter))]
        rows = []
        for row_values in rows_iter:
            row = {}
            for i, val in enumerate(row_values):
                if i < len(headers):
                    row[headers[i]] = str(val) if val is not None else ""
            rows.append(row)
        wb.close()
        return headers, rows
