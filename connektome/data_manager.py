"""Persistence helpers for saving favourite items."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .knowledge_base import KnowledgeItem


class DataManager:
    """Handles storing and retrieving favourite items from disk."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write_data([])

    def _read_data(self) -> List[Dict[str, object]]:
        with self.storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_data(self, data: List[Dict[str, object]]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)

    def list_favourites(self, category: Optional[str] = None) -> List[Dict[str, object]]:
        favourites = self._read_data()
        if category:
            category_lower = category.strip().lower()
            favourites = [
                item
                for item in favourites
                if str(item.get("category", "")).lower() == category_lower
            ]
        return favourites

    def get_favourite(self, name: str) -> Optional[Dict[str, object]]:
        name_lower = name.strip().lower()
        for item in self._read_data():
            if str(item.get("name", "")).lower() == name_lower:
                return item
        return None

    def add_or_update(self, item: Dict[str, object]) -> Dict[str, object]:
        """Add a new favourite or update an existing one."""

        favourites = self._read_data()
        name_lower = str(item.get("name", "")).strip().lower()
        updated = False
        for index, existing in enumerate(favourites):
            if str(existing.get("name", "")).strip().lower() == name_lower:
                favourites[index] = item
                updated = True
                break

        if not updated:
            favourites.append(item)

        self._write_data(favourites)
        return item

    def remove(self, name: str) -> bool:
        name_lower = name.strip().lower()
        favourites = self._read_data()
        filtered = [item for item in favourites if str(item.get("name", "")).lower() != name_lower]
        removed = len(filtered) != len(favourites)
        if removed:
            self._write_data(filtered)
        return removed

    def from_knowledge_item(
        self,
        item: KnowledgeItem,
        notes: Optional[str] = None,
        categories_override: Optional[str] = None,
    ) -> Dict[str, object]:
        """Convert a :class:`KnowledgeItem` into a persisted dictionary."""

        payload: Dict[str, object] = {
            "name": item.name,
            "category": categories_override or item.category,
            "cover_image": item.cover_image,
            "wikipedia_url": item.wikipedia_url,
            "description": item.description,
            "tags": item.tags,
            "meanings": item.meanings,
            "readings": item.readings,
        }
        if notes:
            payload["notes"] = notes
        return payload

    def import_many(self, items: Iterable[Dict[str, object]]) -> None:
        favourites = self._read_data()
        favourites.extend(items)
        self._write_data(favourites)

