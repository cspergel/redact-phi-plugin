"""Tests for exemption manager."""
import pytest

from server.exemption_manager import ExemptionManager


class TestExemptionManager:
    def setup_method(self):
        self.manager = ExemptionManager()

    def test_no_exemptions_by_default(self):
        assert self.manager.is_exempt("PATIENT_NAME") is False

    def test_add_exemption(self):
        self.manager.exempt("PROVIDER_NAME", reason="compare by doctor")
        assert self.manager.is_exempt("PROVIDER_NAME") is True

    def test_remove_exemption(self):
        self.manager.exempt("PROVIDER_NAME", reason="test")
        self.manager.remove_exemption("PROVIDER_NAME")
        assert self.manager.is_exempt("PROVIDER_NAME") is False

    def test_ssn_cannot_be_exempted(self):
        with pytest.raises(ValueError, match="cannot be exempted"):
            self.manager.exempt("SSN", reason="test")

    def test_ip_address_cannot_be_exempted(self):
        with pytest.raises(ValueError, match="cannot be exempted"):
            self.manager.exempt("IP_ADDRESS", reason="test")

    def test_list_exemptions(self):
        self.manager.exempt("PROVIDER_NAME", reason="reason1")
        self.manager.exempt("FACILITY", reason="reason2")
        exemptions = self.manager.list_exemptions()
        assert len(exemptions) == 2
        assert exemptions["PROVIDER_NAME"] == "reason1"
        assert exemptions["FACILITY"] == "reason2"

    def test_audit_log(self):
        self.manager.exempt("PROVIDER_NAME", reason="test")
        self.manager.remove_exemption("PROVIDER_NAME")
        log = self.manager.audit_log()
        assert len(log) == 2
        assert log[0]["action"] == "exempt"
        assert log[1]["action"] == "remove"
