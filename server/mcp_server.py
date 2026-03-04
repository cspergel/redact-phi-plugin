"""MCP server for Redact PHI Cowork plugin."""
import json
import os
import re
import secrets
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

from redactiphi.service import RedactiPHIService
from redactiphi.transform.models import TokenMap, TokenEntry

from server.policy import cowork_analytics_policy
from server.session_store import SessionStore
from server.spreadsheet_handler import SpreadsheetHandler
from server.identity_resolver import IdentityResolver
from server.exemption_manager import ExemptionManager


class RedactPHIServer:
    """Core server logic wrapping Redact iPHI for Cowork."""

    def __init__(
        self,
        secret_key: Optional[bytes] = None,
        persist_dir: Optional[str] = None,
    ):
        self._secret_key = secret_key or secrets.token_bytes(32)
        self._policy = cowork_analytics_policy()
        self._service = RedactiPHIService(
            secret_key=self._secret_key,
            policy=self._policy,
            use_storage=False,
            use_transformer=False,
        )
        self._session = SessionStore(persist_dir=persist_dir)
        self._spreadsheet = SpreadsheetHandler(
            secret_key=self._secret_key,
            scope_id=self._session.session_id,
        )
        self._resolver = IdentityResolver()
        self._exemptions = ExemptionManager()
        self._last_doc_id: Optional[str] = None

    def load_file_safe(self, path: str) -> str:
        """Read a file, de-identify PHI, return clean data."""
        result = self._spreadsheet.process(path)
        self._last_doc_id = result.document_id

        # Store token map in session
        token_map_data = {
            "document_id": result.document_id,
            "entries": {
                entry.token: {
                    "token": entry.token,
                    "original": entry.original,
                    "phi_type": entry.phi_type,
                    "normalized": entry.normalized,
                }
                for entry in result.token_map.entries.values()
            },
        }
        self._session.store_token_map(result.document_id, token_map_data)

        # Register identities for cross-document linking
        mrn_col = None
        name_col = None
        dob_col = None
        for header, cls in result.column_classifications.items():
            if cls.is_phi and cls.phi_type == "MRN":
                mrn_col = header
            elif cls.is_phi and cls.phi_type == "PATIENT_NAME":
                name_col = header
            elif cls.is_phi and cls.phi_type == "DOB":
                dob_col = header

        if mrn_col:
            for row in result.rows:
                mrn_token = row.get(mrn_col, "")
                name_token = row.get(name_col, "") if name_col else None
                # Look up originals from token map
                mrn_orig = result.token_map.get_original(mrn_token)
                name_orig = result.token_map.get_original(name_token) if name_token else None
                dob_orig = None
                if dob_col:
                    dob_token = row.get(dob_col, "")
                    dob_orig = result.token_map.get_original(dob_token)
                if mrn_orig and name_orig:
                    self._resolver.register(
                        mrn=mrn_orig,
                        name=name_orig,
                        dob=dob_orig,
                        name_token=name_token,
                    )

        text_output = result.as_text()
        phi_summary = f"\n\n[doc_id: {result.document_id}]\n"
        phi_summary += f"[PHI columns tokenized: {', '.join(result.phi_columns_found)}]\n"
        phi_summary += f"[Rows: {result.rows_processed}, Tokens: {len(result.token_map.entries)}]"

        return text_output + phi_summary

    def scrub_text(self, text: str, doc_id: Optional[str] = None) -> str:
        """De-identify free text."""
        did = doc_id or f"text_{secrets.token_hex(4)}"
        result = self._service.deidentify(text, document_id=did)

        token_map_data = {
            "document_id": did,
            "entries": {
                entry.token: {
                    "token": entry.token,
                    "original": entry.original,
                    "phi_type": entry.phi_type,
                    "normalized": entry.normalized,
                }
                for entry in result.token_map.entries.values()
            },
        }
        self._session.store_token_map(did, token_map_data)
        self._last_doc_id = did
        return result.deid_text

    def reidentify(self, text: str, doc_id: str) -> str:
        """Re-identify tokens in text."""
        token_map_data = self._session.get_token_map(doc_id)
        if not token_map_data:
            # Try unified lookup across all docs
            pattern = r"\[([A-Z]{3})_([a-f0-9]{12})\]"
            def replace_token(match):
                token = match.group(0)
                original = self._session.lookup_token(token)
                return original if original else token
            return re.sub(pattern, replace_token, text)

        # Reconstruct a TokenMap from the session store data
        token_map = TokenMap(document_id=doc_id)
        for token, entry_data in token_map_data.get("entries", {}).items():
            token_map.add(TokenEntry(
                token=entry_data["token"],
                original=entry_data["original"],
                phi_type=entry_data["phi_type"],
                normalized=entry_data["normalized"],
            ))

        return self._service.reidentify(text, doc_id, token_map=token_map)

    def inspect(self, text: str) -> str:
        """Show detected PHI without transforming."""
        result = self._service.deidentify(text, store_tokens=False, log_audit=False)
        findings = []
        for f in result.findings:
            findings.append(f"  - {f.phi_type}: \"{f.text}\" (confidence: {f.confidence:.2f})")
        if findings:
            return "PHI detected:\n" + "\n".join(findings)
        return "No PHI detected."

    def session_status(self) -> str:
        """Return session statistics."""
        stats = self._session.stats()
        exemptions = self._exemptions.list_exemptions()
        pending = self._resolver.pending_confirmations()

        lines = [
            f"Redact PHI Plugin: Active",
            f"Session ID: {stats['session_id']}",
            f"Documents loaded: {stats['documents_loaded']}",
            f"Total tokens: {stats['total_tokens']}",
        ]
        if exemptions:
            lines.append(f"Active exemptions: {', '.join(f'{k} ({v})' for k, v in exemptions.items())}")
        if pending:
            lines.append(f"Flagged matches: {len(pending)} pending confirmation")

        return "\n".join(lines)

    def exempt_phi(self, phi_type: str, reason: str = "") -> str:
        """Exempt a PHI type from tokenization."""
        try:
            self._exemptions.exempt(phi_type, reason)
            return f"Exempted {phi_type} from tokenization. Reason: {reason}"
        except ValueError as e:
            return str(e)

    def remove_exemption(self, phi_type: str) -> str:
        """Remove a PHI type exemption."""
        self._exemptions.remove_exemption(phi_type)
        return f"Removed exemption for {phi_type}. It will be tokenized again."

    def confirm_match(self, token_a: str, token_b: str) -> str:
        """Confirm an identity match."""
        pending = self._resolver.pending_confirmations()
        for match in pending:
            self._resolver.confirm_match(match.match_id)
            return f"Match confirmed. Identities merged."
        return "No pending match found."

    def reject_match(self, token_a: str, token_b: str) -> str:
        """Reject an identity match."""
        pending = self._resolver.pending_confirmations()
        for match in pending:
            self._resolver.reject_match(match.match_id)
            return f"Match rejected. Identities kept separate."
        return "No pending match found."


# --- FastMCP wiring ---

mcp = FastMCP("redact-phi")

_server: Optional[RedactPHIServer] = None


def _get_server() -> RedactPHIServer:
    global _server
    if _server is None:
        persist_dir = os.environ.get(
            "REDACT_PHI_DATA_DIR",
            os.path.expanduser("~/.redact-phi/sessions"),
        )
        _server = RedactPHIServer(persist_dir=persist_dir)
    return _server


@mcp.tool()
def load_file_safe(path: str) -> str:
    """Load a spreadsheet or data file, automatically detect and tokenize PHI columns, and return clean de-identified data.

    Supports: .xlsx, .xls, .csv, .tsv

    Args:
        path: Absolute path to the file to load
    """
    return _get_server().load_file_safe(path)


@mcp.tool()
def scrub_text(text: str, doc_id: str = "") -> str:
    """De-identify free text by detecting and tokenizing PHI (names, dates, MRNs, etc).

    Use this when the user pastes or types patient data directly in conversation.

    Args:
        text: The text containing potential PHI to scrub
        doc_id: Optional document ID for tracking (auto-generated if empty)
    """
    return _get_server().scrub_text(text, doc_id=doc_id or None)


@mcp.tool()
def reidentify(text: str, doc_id: str) -> str:
    """Replace tokens with original PHI values in text for the user's final output.

    Always call this before presenting final results to the user.

    Args:
        text: Text containing tokens like [NAM_abc123def456] to replace
        doc_id: Document ID from the original load_file_safe or scrub_text call
    """
    return _get_server().reidentify(text, doc_id)


@mcp.tool()
def reidentify_file(content: str, output_path: str, doc_id: str) -> str:
    """Re-identify tokens in content and write the result to a file.

    Args:
        content: Text content with tokens to re-identify
        output_path: Path to write the re-identified output
        doc_id: Document ID for token map lookup
    """
    server = _get_server()
    result = server.reidentify(content, doc_id)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
    return f"Re-identified output written to {output_path}"


@mcp.tool()
def inspect(text: str) -> str:
    """Show what PHI is detected in text without transforming it. Useful for debugging.

    Args:
        text: Text to scan for PHI
    """
    return _get_server().inspect(text)


@mcp.tool()
def session_status() -> str:
    """Show current session statistics: documents loaded, tokens active, exemptions, and pending matches."""
    return _get_server().session_status()


@mcp.tool()
def exempt_phi(phi_type: str, reason: str = "") -> str:
    """Exempt a PHI type from tokenization so it remains visible to Claude.

    Cannot exempt: SSN, IP_ADDRESS, DEVICE_ID, VEHICLE_ID

    Args:
        phi_type: The PHI type to exempt (e.g., PROVIDER_NAME, FACILITY)
        reason: Why this exemption is needed (logged for audit)
    """
    return _get_server().exempt_phi(phi_type, reason)


@mcp.tool()
def remove_exemption(phi_type: str) -> str:
    """Re-enable tokenization for a previously exempted PHI type.

    Args:
        phi_type: The PHI type to re-enable tokenization for
    """
    return _get_server().remove_exemption(phi_type)


@mcp.tool()
def confirm_match(token_a: str, token_b: str) -> str:
    """Confirm that two tokens refer to the same patient (merge identities).

    Args:
        token_a: First patient token
        token_b: Second patient token
    """
    return _get_server().confirm_match(token_a, token_b)


@mcp.tool()
def reject_match(token_a: str, token_b: str) -> str:
    """Reject a proposed patient match (keep identities separate).

    Args:
        token_a: First patient token
        token_b: Second patient token
    """
    return _get_server().reject_match(token_a, token_b)


if __name__ == "__main__":
    mcp.run(transport="stdio")
