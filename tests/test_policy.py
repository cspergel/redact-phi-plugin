"""Tests for COWORK_ANALYTICS transform policy."""
import pytest
from redactiphi.transform.pipeline import TransformType

from server.policy import cowork_analytics_policy


class TestCoworkAnalyticsPolicy:
    def test_policy_name(self):
        policy = cowork_analytics_policy()
        assert policy.name == "cowork_analytics"

    def test_patient_name_tokenized(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("PATIENT_NAME") == TransformType.TOKENIZE

    def test_dob_tokenized_not_shifted(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("DOB") == TransformType.TOKENIZE

    def test_date_tokenized_not_shifted(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("DATE") == TransformType.TOKENIZE

    def test_mrn_tokenized(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("MRN") == TransformType.TOKENIZE

    def test_ssn_redacted(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("SSN") == TransformType.REDACT

    def test_phone_redacted(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("PHONE") == TransformType.REDACT

    def test_email_redacted(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("EMAIL") == TransformType.REDACT

    def test_provider_name_tokenized(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("PROVIDER_NAME") == TransformType.TOKENIZE

    def test_facility_tokenized(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("FACILITY") == TransformType.TOKENIZE

    def test_age_tokenized(self):
        policy = cowork_analytics_policy()
        assert policy.get_transform("AGE") == TransformType.TOKENIZE_AGE
