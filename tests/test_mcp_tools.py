"""Tests for MCP tool functions."""
import os
import pytest
from pathlib import Path

from server.mcp_server import (
    RedactPHIServer,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestRedactPHIServer:
    def setup_method(self):
        self.server = RedactPHIServer(
            secret_key=b"test-secret-key-for-hmac-32bytes"
        )

    def test_load_file_safe_csv(self):
        result = self.server.load_file_safe(str(FIXTURES_DIR / "sample_billing.csv"))
        assert "John Smith" not in result
        assert "99213" in result
        assert "M54.5" in result

    def test_load_file_safe_returns_doc_id(self):
        result = self.server.load_file_safe(str(FIXTURES_DIR / "sample_billing.csv"))
        assert "[doc_id:" in result

    def test_scrub_text(self):
        result = self.server.scrub_text("Patient John Smith has MRN MR-12345")
        assert "John Smith" not in result

    def test_reidentify(self):
        # First load a file to populate token maps
        load_result = self.server.load_file_safe(str(FIXTURES_DIR / "sample_billing.csv"))
        # Extract doc_id from result
        doc_id = self.server._last_doc_id
        # Get a tokenized name from the result
        # Now reidentify
        reid_result = self.server.reidentify(load_result, doc_id)
        assert "John Smith" in reid_result

    def test_session_status(self):
        self.server.load_file_safe(str(FIXTURES_DIR / "sample_billing.csv"))
        status = self.server.session_status()
        assert "Documents loaded" in status
        assert "Total tokens" in status

    def test_inspect(self):
        result = self.server.inspect("Patient John Smith, DOB 01/15/1980")
        assert "PATIENT_NAME" in result or "John Smith" in result

    def test_exempt_phi(self):
        result = self.server.exempt_phi("PROVIDER_NAME", "testing")
        assert "PROVIDER_NAME" in result

    def test_exempt_phi_ssn_blocked(self):
        result = self.server.exempt_phi("SSN", "testing")
        assert "cannot" in result.lower()

    def test_remove_exemption(self):
        self.server.exempt_phi("PROVIDER_NAME", "testing")
        result = self.server.remove_exemption("PROVIDER_NAME")
        assert "removed" in result.lower() or "PROVIDER_NAME" in result
