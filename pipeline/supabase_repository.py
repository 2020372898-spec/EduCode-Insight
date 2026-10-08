"""Persistent Supabase repository for EduCodeInsight assignment results.

The repository deliberately contains no Streamlit UI logic.  A Supabase client can
be injected for testing; otherwise the project's ``get_supabase_client`` helper is
used lazily.
"""
from __future__ import annotations

from typing import Any, Optional


class SupabaseRepository:
    """Persist practical metadata and student result JSON in Supabase."""

    def __init__(self, client=None):
        if client is None:
            # Lazy import keeps the rest of the pipeline importable even when the
            # optional Supabase dependency has not yet been installed.
            from .supabase_client import get_supabase_client
            client = get_supabase_client()
        self.client = client

    def _find_practical(self, user_id: str, slug: str) -> Optional[dict[str, Any]]:
        response = (
            self.client.table("practicals")
            .select("id,user_id,name,slug,created_at,metadata")
            .eq("user_id", str(user_id))
            .eq("slug", str(slug))
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def save_practical(self, user_id: str, name: str, slug: str, metadata: Optional[dict] = None) -> str:
        """Create or update one practical and return its UUID."""
        existing = self._find_practical(user_id, slug)
        payload = {
            "user_id": str(user_id),
            "name": str(name),
            "slug": str(slug),
            "metadata": metadata or {},
        }
        if existing:
            response = (
                self.client.table("practicals")
                .update(payload)
                .eq("id", existing["id"])
                .execute()
            )
            rows = response.data or []
            return str((rows[0] if rows else existing)["id"])

        response = self.client.table("practicals").insert(payload).execute()
        rows = response.data or []
        if not rows:
            raise RuntimeError("Supabase did not return the newly created practical.")
        return str(rows[0]["id"])

    def save_student_result(self, practical_id: str, student_id: str, result_data: dict) -> None:
        """Create or update a student's result within a practical."""
        lookup = (
            self.client.table("student_results")
            .select("id")
            .eq("practical_id", str(practical_id))
            .eq("student_id", str(student_id))
            .limit(1)
            .execute()
        )
        rows = lookup.data or []
        payload = {
            "practical_id": str(practical_id),
            "student_id": str(student_id),
            "result_data": result_data,
        }
        if rows:
            (
                self.client.table("student_results")
                .update(payload)
                .eq("id", rows[0]["id"])
                .execute()
            )
        else:
            self.client.table("student_results").insert(payload).execute()

    def save_student_results(self, practical_id: str, results: list[dict]) -> None:
        """Synchronise a complete set of student result dictionaries efficiently."""
        if not results:
            return
        existing_response = (
            self.client.table("student_results")
            .select("id,student_id")
            .eq("practical_id", str(practical_id))
            .execute()
        )
        existing = {str(row.get("student_id")): row.get("id") for row in (existing_response.data or [])}

        inserts = []
        updates = []
        for result in results:
            student_id = str(result.get("student_id", "UnknownStudent"))
            payload = {
                "practical_id": str(practical_id),
                "student_id": student_id,
                "result_data": result,
            }
            if student_id in existing:
                updates.append((existing[student_id], payload))
            else:
                inserts.append(payload)

        if inserts:
            self.client.table("student_results").insert(inserts).execute()
        for row_id, payload in updates:
            self.client.table("student_results").update(payload).eq("id", row_id).execute()

    def list_practicals(self, user_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("practicals")
            .select("id,user_id,name,slug,created_at,metadata")
            .eq("user_id", str(user_id))
            .order("name")
            .execute()
        )
        return list(response.data or [])

    def load_practical(self, user_id: str, slug: str) -> tuple[list[dict], dict]:
        practical = self._find_practical(user_id, slug)
        if not practical:
            return [], {}

        response = (
            self.client.table("student_results")
            .select("student_id,result_data")
            .eq("practical_id", practical["id"])
            .order("student_id")
            .execute()
        )
        results = []
        for row in response.data or []:
            result = dict(row.get("result_data") or {})
            result.pop("_cache_key", None)
            result.pop("_audit_key", None)
            results.append(result)

        metadata = dict(practical.get("metadata") or {})
        metadata.setdefault("assignment_name", practical.get("name", slug))
        metadata.setdefault("assignment_slug", practical.get("slug", slug))
        return results, metadata

    def delete_practical(self, user_id: str, slug: str) -> bool:
        practical = self._find_practical(user_id, slug)
        if not practical:
            return False
        practical_id = practical["id"]
        self.client.table("student_results").delete().eq("practical_id", practical_id).execute()
        self.client.table("practicals").delete().eq("id", practical_id).execute()
        return True


__all__ = ["SupabaseRepository"]
