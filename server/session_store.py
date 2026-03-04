"""Session store for token maps across documents."""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionStore:
    """Manages token maps across multiple documents within a session.

    Provides unified token lookup across all loaded documents and
    optional persistence to disk.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.persist_dir = persist_dir
        self._token_maps: Dict[str, Dict[str, Any]] = {}
        self._created_at = datetime.now(timezone.utc).isoformat()

    def store_token_map(self, doc_id: str, token_map_data: Dict[str, Any]) -> None:
        """Store a token map for a document."""
        self._token_maps[doc_id] = token_map_data

    def get_token_map(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a token map by document ID."""
        return self._token_maps.get(doc_id)

    def lookup_token(self, token: str) -> Optional[str]:
        """Look up the original value for a token across all documents."""
        for token_map_data in self._token_maps.values():
            entries = token_map_data.get("entries", {})
            if token in entries:
                return entries[token].get("original")
        return None

    def list_documents(self) -> List[str]:
        """List all document IDs in this session."""
        return list(self._token_maps.keys())

    def stats(self) -> Dict[str, Any]:
        """Return session statistics."""
        total_tokens = sum(
            len(tm.get("entries", {})) for tm in self._token_maps.values()
        )
        return {
            "session_id": self.session_id,
            "documents_loaded": len(self._token_maps),
            "total_tokens": total_tokens,
            "created_at": self._created_at,
        }

    def save(self) -> None:
        """Persist session to disk."""
        if not self.persist_dir:
            return
        session_dir = Path(self.persist_dir) / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "created_at": self._created_at,
            "token_maps": self._token_maps,
        }
        path = session_dir / "session.json"
        path.write_text(json.dumps(data, indent=2))

    def load(self) -> None:
        """Load session from disk."""
        if not self.persist_dir:
            return
        path = Path(self.persist_dir) / self.session_id / "session.json"
        if not path.exists():
            return
        data = json.loads(path.read_text())
        self._created_at = data.get("created_at", self._created_at)
        self._token_maps = data.get("token_maps", {})
