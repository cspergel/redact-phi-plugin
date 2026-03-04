"""Exemption manager for selective PHI type exemptions."""
from datetime import datetime, timezone
from typing import Any, Dict, List


# PHI types that can NEVER be exempted
NEVER_EXEMPT = frozenset({"SSN", "IP_ADDRESS", "DEVICE_ID", "VEHICLE_ID"})


class ExemptionManager:
    """Manages selective PHI type exemptions for a session."""

    def __init__(self):
        self._exemptions: Dict[str, str] = {}  # phi_type -> reason
        self._audit: List[Dict[str, Any]] = []

    def exempt(self, phi_type: str, reason: str = "") -> None:
        """Exempt a PHI type from tokenization."""
        if phi_type in NEVER_EXEMPT:
            raise ValueError(f"{phi_type} cannot be exempted")
        self._exemptions[phi_type] = reason
        self._audit.append({
            "action": "exempt",
            "phi_type": phi_type,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def remove_exemption(self, phi_type: str) -> None:
        """Remove an exemption."""
        self._exemptions.pop(phi_type, None)
        self._audit.append({
            "action": "remove",
            "phi_type": phi_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def is_exempt(self, phi_type: str) -> bool:
        """Check if a PHI type is currently exempt."""
        return phi_type in self._exemptions

    def list_exemptions(self) -> Dict[str, str]:
        """Return all active exemptions."""
        return dict(self._exemptions)

    def audit_log(self) -> List[Dict[str, Any]]:
        """Return the exemption audit log."""
        return list(self._audit)
