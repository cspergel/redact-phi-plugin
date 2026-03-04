"""Tests for spreadsheet handler."""
import csv
import os
import pytest
from pathlib import Path

from server.spreadsheet_handler import SpreadsheetHandler, SpreadsheetResult


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestSpreadsheetHandler:
    def setup_method(self):
        self.handler = SpreadsheetHandler(secret_key=b"test-secret-key-for-hmac-32bytes")

    def test_read_csv(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        assert isinstance(result, SpreadsheetResult)
        assert len(result.rows) == 3

    def test_phi_columns_detected(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        phi_cols = [c for c in result.column_classifications if result.column_classifications[c].is_phi]
        assert "Patient Name" in phi_cols
        assert "DOB" in phi_cols
        assert "MRN" in phi_cols

    def test_non_phi_columns_preserved(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        # CPT Code should be unchanged
        assert result.rows[0]["CPT Code"] == "99213"
        assert result.rows[0]["Charges"] == "150.00"
        assert result.rows[0]["Diagnosis Code"] == "M54.5"

    def test_phi_columns_tokenized(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        name_val = result.rows[0]["Patient Name"]
        # Should be a token like [NAM_xxxxxxxxxxxx]
        assert name_val.startswith("[")
        assert name_val.endswith("]")
        assert "John Smith" not in name_val

    def test_same_person_same_token(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        # Rows 0 and 2 are both John Smith
        assert result.rows[0]["Patient Name"] == result.rows[2]["Patient Name"]

    def test_different_people_different_tokens(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        assert result.rows[0]["Patient Name"] != result.rows[1]["Patient Name"]

    def test_token_map_populated(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        assert result.token_map is not None
        assert len(result.token_map.entries) > 0

    def test_doc_id_assigned(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        assert result.document_id is not None
        assert len(result.document_id) > 0

    def test_clean_text_representation(self):
        result = self.handler.process(str(FIXTURES_DIR / "sample_billing.csv"))
        text = result.as_text()
        assert "John Smith" not in text
        assert "99213" in text
        assert "M54.5" in text
