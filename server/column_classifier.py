"""Column classifier for detecting PHI columns in spreadsheets."""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ColumnClassification:
    """Result of classifying a column header."""
    header: str
    is_phi: bool
    phi_type: Optional[str] = None
    confidence: float = 1.0


# Pattern tuples: (compiled_regex, phi_type)
_PHI_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Names
    (re.compile(r"\b(patient\s*name|member\s*name|pt\s*name|subscriber\s*name)\b", re.I), "PATIENT_NAME"),
    (re.compile(r"^name$", re.I), "PATIENT_NAME"),
    (re.compile(r"\b(first\s*name|last\s*name|middle\s*name|full\s*name)\b", re.I), "PATIENT_NAME"),
    (re.compile(r"\b(rendering\s*provider|attending\s*physician|physician\s*name|provider\s*name|doctor\s*name|referring\s*provider|ordering\s*provider|surgeon|attending)\b", re.I), "PROVIDER_NAME"),
    # DOB
    (re.compile(r"\b(dob|date\s*of\s*birth|birth\s*date|birthday)\b", re.I), "DOB"),
    # Dates
    (re.compile(r"\b(admission\s*date|admit\s*date|discharge\s*date|service\s*date|date\s*of\s*service|dos|encounter\s*date|visit\s*date|procedure\s*date|surgery\s*date)\b", re.I), "DATE"),
    # MRN
    (re.compile(r"\b(mrn|medical\s*record\s*(number|num|no|#)?|chart\s*(number|num|no|#)?|patient\s*id)\b", re.I), "MRN"),
    # SSN
    (re.compile(r"\b(ssn|social\s*security|ss#|ss\s*#)\b", re.I), "SSN"),
    # Contact
    (re.compile(r"\b(phone|telephone|cell|mobile|fax)\s*(number|num|no|#)?\b", re.I), "PHONE"),
    (re.compile(r"\b(email|e-mail|email\s*address)\b", re.I), "EMAIL"),
    # Address
    (re.compile(r"\b(address|street|city|state|zip|zip\s*code|postal)\b", re.I), "STREET_ADDRESS"),
    # Facility
    (re.compile(r"\b(facility|facility\s*name|hospital|clinic|location\s*name|site\s*name)\b", re.I), "FACILITY"),
    # IDs
    (re.compile(r"\b(npi|national\s*provider)\b", re.I), "NPI"),
    (re.compile(r"\b(dea|dea\s*number)\b", re.I), "DEA_NUMBER"),
    (re.compile(r"\b(insurance\s*id|member\s*id|policy\s*number|payer\s*id|group\s*number)\b", re.I), "INSURANCE_ID"),
    (re.compile(r"\b(medicare\s*id|medicaid\s*id|mbi)\b", re.I), "MEDICARE_ID"),
    (re.compile(r"\b(account\s*(number|num|no|#)?|acct)\b", re.I), "ACCOUNT_NUMBER"),
    # Age
    (re.compile(r"^age$", re.I), "AGE"),
]

_NON_PHI_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(cpt|cpt\s*code|procedure\s*code|hcpcs)\b", re.I),
    re.compile(r"\b(icd|icd[\s-]*10|icd[\s-]*9|diagnosis\s*code|dx|dx\s*code)\b", re.I),
    re.compile(r"\b(drg|drg\s*code|ms[\s-]*drg|apr[\s-]*drg)\b", re.I),
    re.compile(r"\b(charge|charges|amount|total|cost|fee|payment|balance|copay|coinsurance|deductible|allowed|billed|paid)\b", re.I),
    re.compile(r"\b(units?|quantity|qty|count)\b", re.I),
    re.compile(r"\b(modifier|mod)\b", re.I),
    re.compile(r"\b(place\s*of\s*service|pos|type\s*of\s*service|tos)\b", re.I),
    re.compile(r"\b(revenue\s*code|rev\s*code)\b", re.I),
    re.compile(r"\b(status|flag|indicator|type|category|class|group)\b", re.I),
    re.compile(r"\b(description|desc|notes?|comment|reason)\b", re.I),
    re.compile(r"\b(department|dept|specialty|service\s*line)\b", re.I),
    re.compile(r"\b(payer|payer\s*name|insurance\s*name|plan\s*name)\b", re.I),
]


class ColumnClassifier:
    """Classifies spreadsheet column headers as PHI or non-PHI."""

    def classify(self, header: str) -> ColumnClassification:
        """Classify a single column header."""
        header_stripped = header.strip()

        # Check non-PHI patterns first (more specific)
        for pattern in _NON_PHI_PATTERNS:
            if pattern.search(header_stripped):
                return ColumnClassification(
                    header=header_stripped, is_phi=False
                )

        # Check PHI patterns
        for pattern, phi_type in _PHI_PATTERNS:
            if pattern.search(header_stripped):
                return ColumnClassification(
                    header=header_stripped, is_phi=True, phi_type=phi_type
                )

        # Default: not PHI
        return ColumnClassification(header=header_stripped, is_phi=False)

    def classify_headers(
        self, headers: List[str]
    ) -> Dict[str, ColumnClassification]:
        """Classify a batch of column headers."""
        return {h: self.classify(h) for h in headers}
