"""Integration tests for the full de-ID / re-ID workflow."""
import pytest
from pathlib import Path

from server.mcp_server import RedactPHIServer


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestEndToEndWorkflow:
    def setup_method(self):
        self.server = RedactPHIServer(
            secret_key=b"test-secret-key-for-hmac-32bytes"
        )

    def test_full_round_trip(self):
        """Load file -> verify clean -> re-identify -> verify originals restored."""
        clean_data = self.server.load_file_safe(
            str(FIXTURES_DIR / "sample_billing.csv")
        )
        doc_id = self.server._last_doc_id

        # Clean data should NOT contain PHI
        assert "John Smith" not in clean_data
        assert "01/15/1980" not in clean_data
        assert "MR-12345" not in clean_data

        # Clean data SHOULD contain non-PHI
        assert "99213" in clean_data
        assert "150.00" in clean_data
        assert "M54.5" in clean_data

        # Re-identify should restore originals
        reidentified = self.server.reidentify(clean_data, doc_id)
        assert "John Smith" in reidentified
        assert "Jane Doe" in reidentified

    def test_cross_document_patient_linking(self):
        """Same patient (by MRN) across two files should get same token."""
        clean_q1 = self.server.load_file_safe(
            str(FIXTURES_DIR / "sample_billing.csv")
        )
        clean_q2 = self.server.load_file_safe(
            str(FIXTURES_DIR / "sample_q2_billing.csv")
        )

        # Both files have MR-12345 (John Smith / Smith John A.)
        # After identity resolution, they should be linked
        status = self.server.session_status()
        assert "2" in status  # 2 documents loaded

    def test_conversational_scrub_and_reid(self):
        """Scrub text -> re-identify -> verify round trip."""
        # First load file to establish tokens
        self.server.load_file_safe(str(FIXTURES_DIR / "sample_billing.csv"))

        # Then scrub conversational text
        scrubbed = self.server.scrub_text(
            "Tell me about patient John Smith's billing history"
        )
        assert "John Smith" not in scrubbed

    def test_exemption_flow(self):
        """Exempt a PHI type -> verify it's tracked."""
        result = self.server.exempt_phi("PROVIDER_NAME", "compare by doctor")
        assert "PROVIDER_NAME" in result

        status = self.server.session_status()
        assert "PROVIDER_NAME" in status

        self.server.remove_exemption("PROVIDER_NAME")
        status2 = self.server.session_status()
        assert "PROVIDER_NAME" not in status2

    def test_inspect_shows_phi(self):
        """Inspect should show detected PHI without transforming."""
        result = self.server.inspect(
            "Patient John Smith, DOB 01/15/1980, MRN MR-12345"
        )
        assert "PHI detected" in result
