"""Tests for session store."""
import json
import os
import pytest
from pathlib import Path

from server.session_store import SessionStore


class TestSessionStore:
    def test_create_session(self):
        store = SessionStore()
        assert store.session_id is not None
        assert len(store.session_id) > 0

    def test_store_and_retrieve_token_map(self):
        store = SessionStore()
        token_map_data = {
            "document_id": "doc-1",
            "entries": {
                "[NAM_abc123def456]": {
                    "token": "[NAM_abc123def456]",
                    "original": "John Smith",
                    "phi_type": "PATIENT_NAME",
                    "normalized": "john smith",
                }
            },
        }
        store.store_token_map("doc-1", token_map_data)
        retrieved = store.get_token_map("doc-1")
        assert retrieved == token_map_data

    def test_get_missing_token_map_returns_none(self):
        store = SessionStore()
        assert store.get_token_map("nonexistent") is None

    def test_unified_token_lookup(self):
        store = SessionStore()
        store.store_token_map("doc-1", {
            "document_id": "doc-1",
            "entries": {
                "[NAM_abc123def456]": {
                    "token": "[NAM_abc123def456]",
                    "original": "John Smith",
                    "phi_type": "PATIENT_NAME",
                    "normalized": "john smith",
                }
            },
        })
        store.store_token_map("doc-2", {
            "document_id": "doc-2",
            "entries": {
                "[DOB_789012345678]": {
                    "token": "[DOB_789012345678]",
                    "original": "01/15/1980",
                    "phi_type": "DOB",
                    "normalized": "01/15/1980",
                }
            },
        })
        # Unified lookup finds tokens across all docs
        assert store.lookup_token("[NAM_abc123def456]") == "John Smith"
        assert store.lookup_token("[DOB_789012345678]") == "01/15/1980"
        assert store.lookup_token("[NAM_000000000000]") is None

    def test_list_documents(self):
        store = SessionStore()
        store.store_token_map("doc-1", {"document_id": "doc-1", "entries": {}})
        store.store_token_map("doc-2", {"document_id": "doc-2", "entries": {}})
        assert set(store.list_documents()) == {"doc-1", "doc-2"}

    def test_stats(self):
        store = SessionStore()
        store.store_token_map("doc-1", {
            "document_id": "doc-1",
            "entries": {
                "[NAM_abc123def456]": {
                    "token": "[NAM_abc123def456]",
                    "original": "John Smith",
                    "phi_type": "PATIENT_NAME",
                    "normalized": "john smith",
                }
            },
        })
        stats = store.stats()
        assert stats["documents_loaded"] == 1
        assert stats["total_tokens"] == 1

    def test_persist_and_load(self, tmp_path):
        store = SessionStore(persist_dir=str(tmp_path))
        store.store_token_map("doc-1", {
            "document_id": "doc-1",
            "entries": {
                "[NAM_abc123def456]": {
                    "token": "[NAM_abc123def456]",
                    "original": "John Smith",
                    "phi_type": "PATIENT_NAME",
                    "normalized": "john smith",
                }
            },
        })
        store.save()

        # Load into new store
        store2 = SessionStore(
            persist_dir=str(tmp_path),
            session_id=store.session_id,
        )
        store2.load()
        assert store2.lookup_token("[NAM_abc123def456]") == "John Smith"
