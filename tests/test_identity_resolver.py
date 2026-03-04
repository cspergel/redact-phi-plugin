"""Tests for identity resolver."""
import pytest

from server.identity_resolver import (
    IdentityResolver,
    PatientIdentity,
    MatchResult,
    MatchConfidence,
)


class TestIdentityResolver:
    def setup_method(self):
        self.resolver = IdentityResolver()

    def test_register_new_patient(self):
        identity = self.resolver.register(
            mrn="MR-12345", name="John Smith", dob="01/15/1980"
        )
        assert identity.mrn == "MR-12345"
        assert "John Smith" in identity.names_seen

    def test_same_mrn_returns_same_identity(self):
        id1 = self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        id2 = self.resolver.register(mrn="MR-12345", name="Smith, John A.", dob="01/15/1980")
        assert id1.mrn == id2.mrn
        assert "John Smith" in id2.names_seen
        assert "Smith, John A." in id2.names_seen

    def test_different_mrn_different_identity(self):
        id1 = self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        id2 = self.resolver.register(mrn="MR-67890", name="Jane Doe", dob="03/22/1975")
        assert id1.mrn != id2.mrn

    def test_resolve_by_mrn(self):
        self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        match = self.resolver.resolve(mrn="MR-12345", name="J. Smith")
        assert match.confidence == MatchConfidence.HIGH
        assert match.identity.mrn == "MR-12345"
        assert match.needs_confirmation is False

    def test_resolve_mrn_with_very_different_name_flags(self):
        self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        match = self.resolver.resolve(mrn="MR-12345", name="Totally Different Person")
        assert match.confidence == MatchConfidence.MEDIUM
        assert match.needs_confirmation is True

    def test_resolve_unknown_mrn_returns_none(self):
        match = self.resolver.resolve(mrn="MR-99999", name="Nobody")
        assert match is None

    def test_resolve_dob_and_similar_name_no_mrn(self):
        self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        match = self.resolver.resolve(mrn=None, name="John Smith", dob="01/15/1980")
        assert match is not None
        assert match.confidence == MatchConfidence.MEDIUM
        assert match.needs_confirmation is True

    def test_get_canonical_token_for_name(self):
        self.resolver.register(
            mrn="MR-12345", name="John Smith", dob="01/15/1980",
            name_token="[NAM_abc123def456]"
        )
        self.resolver.register(
            mrn="MR-12345", name="Smith, John A.", dob="01/15/1980",
        )
        token = self.resolver.get_canonical_name_token("MR-12345")
        assert token == "[NAM_abc123def456]"

    def test_pending_confirmations(self):
        self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        self.resolver.resolve(mrn="MR-12345", name="Totally Different Person")
        pending = self.resolver.pending_confirmations()
        assert len(pending) == 1

    def test_confirm_match(self):
        self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        match = self.resolver.resolve(mrn="MR-12345", name="Totally Different Person")
        self.resolver.confirm_match(match.match_id)
        assert len(self.resolver.pending_confirmations()) == 0

    def test_reject_match(self):
        self.resolver.register(mrn="MR-12345", name="John Smith", dob="01/15/1980")
        match = self.resolver.resolve(mrn="MR-12345", name="Totally Different Person")
        self.resolver.reject_match(match.match_id)
        assert len(self.resolver.pending_confirmations()) == 0
