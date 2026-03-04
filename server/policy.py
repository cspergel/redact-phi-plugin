"""COWORK_ANALYTICS transform policy for Cowork plugin."""
from redactiphi.transform.pipeline import TransformPolicy, TransformType


def cowork_analytics_policy() -> TransformPolicy:
    """Create the COWORK_ANALYTICS policy.

    Tokenizes all PHI types including dates (no date shifting).
    Dates are tokenized so analytics can use real date relationships
    after re-identification. SSN, phone, and email are fully redacted.
    """
    return TransformPolicy(
        name="cowork_analytics",
        description="Analytics policy for Cowork: tokenize everything including dates",
        transforms={
            "PATIENT_NAME": TransformType.TOKENIZE,
            "PROVIDER_NAME": TransformType.TOKENIZE,
            "FAMILY_MEMBER_NAME": TransformType.TOKENIZE,
            "PERSON_NAME": TransformType.TOKENIZE,
            "DOB": TransformType.TOKENIZE,
            "DATE": TransformType.TOKENIZE,
            "AGE": TransformType.TOKENIZE_AGE,
            "MRN": TransformType.TOKENIZE,
            "SSN": TransformType.REDACT,
            "MEDICARE_ID": TransformType.TOKENIZE,
            "INSURANCE_ID": TransformType.TOKENIZE,
            "ACCOUNT_NUMBER": TransformType.TOKENIZE,
            "PHONE": TransformType.REDACT,
            "FAX": TransformType.REDACT,
            "EMAIL": TransformType.REDACT,
            "FACILITY": TransformType.TOKENIZE,
            "LOCATION": TransformType.TOKENIZE,
            "IP_ADDRESS": TransformType.REDACT,
            "URL": TransformType.REDACT,
            "DEVICE_ID": TransformType.REDACT,
            "VEHICLE_ID": TransformType.REDACT,
            "NPI": TransformType.TOKENIZE,
            "DEA_NUMBER": TransformType.TOKENIZE,
            "LICENSE_NUMBER": TransformType.TOKENIZE,
        },
    )
