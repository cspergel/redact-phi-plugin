"""Identity resolver for cross-document patient linking."""
import uuid
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from typing import Dict, List, Optional, Set


class MatchConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PatientIdentity:
    """A resolved patient identity."""
    mrn: str
    names_seen: Set[str] = field(default_factory=set)
    dob: Optional[str] = None
    canonical_name_token: Optional[str] = None

    def add_name(self, name: str) -> None:
        self.names_seen.add(name)


@dataclass
class MatchResult:
    """Result of resolving a patient identity."""
    match_id: str
    identity: PatientIdentity
    confidence: MatchConfidence
    needs_confirmation: bool
    matched_name: str
    existing_names: Set[str]


class IdentityResolver:
    """Resolves patient identities across documents using MRN."""

    NAME_SIMILARITY_THRESHOLD = 0.4

    def __init__(self):
        self._identities: Dict[str, PatientIdentity] = {}  # MRN -> identity
        self._dob_index: Dict[str, List[str]] = {}  # DOB -> list of MRNs
        self._pending: Dict[str, MatchResult] = {}  # match_id -> result

    def register(
        self,
        mrn: str,
        name: str,
        dob: Optional[str] = None,
        name_token: Optional[str] = None,
    ) -> PatientIdentity:
        """Register or update a patient identity."""
        if mrn in self._identities:
            identity = self._identities[mrn]
            identity.add_name(name)
            if dob and not identity.dob:
                identity.dob = dob
            if name_token and not identity.canonical_name_token:
                identity.canonical_name_token = name_token
        else:
            identity = PatientIdentity(
                mrn=mrn,
                names_seen={name},
                dob=dob,
                canonical_name_token=name_token,
            )
            self._identities[mrn] = identity
            if dob:
                self._dob_index.setdefault(dob, []).append(mrn)

        return identity

    def resolve(
        self,
        mrn: Optional[str] = None,
        name: Optional[str] = None,
        dob: Optional[str] = None,
    ) -> Optional[MatchResult]:
        """Try to resolve a patient to an existing identity."""
        if mrn and mrn in self._identities:
            identity = self._identities[mrn]
            name_similar = self._is_name_similar(name, identity.names_seen) if name else True

            if name_similar:
                if name:
                    identity.add_name(name)
                return MatchResult(
                    match_id=uuid.uuid4().hex[:12],
                    identity=identity,
                    confidence=MatchConfidence.HIGH,
                    needs_confirmation=False,
                    matched_name=name or "",
                    existing_names=set(identity.names_seen),
                )
            else:
                result = MatchResult(
                    match_id=uuid.uuid4().hex[:12],
                    identity=identity,
                    confidence=MatchConfidence.MEDIUM,
                    needs_confirmation=True,
                    matched_name=name or "",
                    existing_names=set(identity.names_seen),
                )
                self._pending[result.match_id] = result
                return result

        if not mrn and dob and name:
            candidates = self._dob_index.get(dob, [])
            for candidate_mrn in candidates:
                identity = self._identities[candidate_mrn]
                if self._is_name_similar(name, identity.names_seen):
                    result = MatchResult(
                        match_id=uuid.uuid4().hex[:12],
                        identity=identity,
                        confidence=MatchConfidence.MEDIUM,
                        needs_confirmation=True,
                        matched_name=name,
                        existing_names=set(identity.names_seen),
                    )
                    self._pending[result.match_id] = result
                    return result

        return None

    def get_canonical_name_token(self, mrn: str) -> Optional[str]:
        """Get the canonical name token for a patient."""
        identity = self._identities.get(mrn)
        return identity.canonical_name_token if identity else None

    def pending_confirmations(self) -> List[MatchResult]:
        """Return all pending match confirmations."""
        return list(self._pending.values())

    def confirm_match(self, match_id: str) -> None:
        """Confirm a pending match."""
        result = self._pending.pop(match_id, None)
        if result and result.matched_name:
            result.identity.add_name(result.matched_name)

    def reject_match(self, match_id: str) -> None:
        """Reject a pending match."""
        self._pending.pop(match_id, None)

    def _is_name_similar(self, name: Optional[str], known_names: Set[str]) -> bool:
        """Check if a name is similar to any known names."""
        if not name:
            return False
        name_lower = name.lower().strip()
        for known in known_names:
            known_lower = known.lower().strip()
            if name_lower == known_lower:
                return True
            ratio = SequenceMatcher(None, name_lower, known_lower).ratio()
            if ratio >= self.NAME_SIMILARITY_THRESHOLD:
                return True
        return False
