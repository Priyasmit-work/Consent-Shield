from __future__ import annotations

from typing import Optional

from app.schemas.preferences import CategoryPreferences, Preferences, default_preferences


class PreferencesRepository:
    """
    Backed by the `privacy_preferences` table (Section 11 of the API
    contract) when Supabase is configured; otherwise an in-memory dict
    keyed by user_id, scoped exactly the same way RLS would scope rows
    (one row per user).
    """

    TABLE = "privacy_preferences"

    def __init__(self, supabase_client) -> None:
        self._client = supabase_client
        self._memory: dict[str, Preferences] = {}

    def get(self, user_id: str) -> Preferences:
        if self._client is not None:
            resp = (
                self._client.table(self.TABLE)
                .select("*")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            row = resp.data if resp else None
            if row:
                return self._row_to_model(row)
            prefs = default_preferences()
            self._upsert_row(user_id, prefs)
            return prefs

        if user_id not in self._memory:
            self._memory[user_id] = default_preferences()
        return self._memory[user_id]

    def put(self, user_id: str, prefs: Preferences) -> Preferences:
        if self._client is not None:
            self._upsert_row(user_id, prefs)
            return prefs

        self._memory[user_id] = prefs
        return prefs

    def _upsert_row(self, user_id: str, prefs: Preferences) -> None:
        row = {
            "user_id": user_id,
            "mode": prefs.mode.value,
            "categories": prefs.categories.as_dict(),
            "auto_apply": prefs.auto_apply,
            "require_confirmation_for_unknown": prefs.require_confirmation_for_unknown,
            "allow_network_observation": prefs.allow_network_observation,
            "save_scan_history": prefs.save_scan_history,
            "updated_at": prefs.updated_at.isoformat(),
        }
        self._client.table(self.TABLE).upsert(row).execute()

    @staticmethod
    def _row_to_model(row: dict) -> Preferences:
        return Preferences(
            mode=row["mode"],
            categories=CategoryPreferences(**row["categories"]),
            auto_apply=row["auto_apply"],
            require_confirmation_for_unknown=row["require_confirmation_for_unknown"],
            allow_network_observation=row["allow_network_observation"],
            save_scan_history=row["save_scan_history"],
            updated_at=row["updated_at"],
        )
