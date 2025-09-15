"""Personalised suggestion engine for the favourites app."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Dict, List

from .data_manager import DataManager
from .knowledge_base import KnowledgeBase, KnowledgeItem


class SuggestionEngine:
    """Generate recommendations based on stored favourites."""

    def __init__(self, knowledge_base: KnowledgeBase, data_manager: DataManager) -> None:
        self.knowledge_base = knowledge_base
        self.data_manager = data_manager

    def profile(self) -> Dict[str, Counter]:
        favourites = self.data_manager.list_favourites()
        tag_counter: Counter[str] = Counter()
        category_counter: Counter[str] = Counter()
        for favourite in favourites:
            category = str(favourite.get("category", "")).strip().lower()
            if category:
                category_counter[category] += 1
            for tag in favourite.get("tags", []):
                tag_lower = str(tag).strip().lower()
                if tag_lower:
                    tag_counter[tag_lower] += 1
        return {"tags": tag_counter, "categories": category_counter}

    def suggest(self, limit: int = 5) -> List[Dict[str, object]]:
        favourites = self.data_manager.list_favourites()
        if not favourites:
            return [
                self._format_default_suggestion(item)
                for item in self.knowledge_base.all_items()[:limit]
            ]

        profile = self.profile()
        tag_counter = profile["tags"]
        category_counter = profile["categories"]
        favourite_names = {str(item.get("name", "")).strip().lower() for item in favourites}

        scored: List[tuple[float, KnowledgeItem, List[str]]] = []
        for candidate in self.knowledge_base.all_items():
            if candidate.normalised_name() in favourite_names:
                continue

            score = 0.0
            reasons: List[str] = []

            overlapping_tags = [
                tag for tag in candidate.tags if tag_counter.get(tag.lower())
            ]
            if overlapping_tags:
                tag_score = sum(tag_counter[tag.lower()] for tag in overlapping_tags)
                score += tag_score
                reasons.append(
                    "Shared tags: "
                    + ", ".join(sorted(overlapping_tags, key=lambda tag: -tag_counter[tag.lower()]))
                )

            category_key = candidate.category.lower()
            if category_counter.get(category_key):
                cat_score = category_counter[category_key] * 2
                score += cat_score
                reasons.append(
                    f"Matches your frequent category '{candidate.category}'"
                )

            if not score:
                continue

            scored.append((score, candidate, reasons))

        scored.sort(key=lambda value: (-value[0], value[1].name))
        return [self._format_scored_suggestion(score, item, reasons) for score, item, reasons in scored[:limit]]

    def _format_scored_suggestion(
        self, score: float, item: KnowledgeItem, reasons: List[str]
    ) -> Dict[str, object]:
        payload = asdict(item)
        payload.update({"score": round(score, 2), "reasons": reasons})
        return payload

    def _format_default_suggestion(self, item: KnowledgeItem) -> Dict[str, object]:
        payload = asdict(item)
        payload.update(
            {
                "score": 0,
                "reasons": [
                    "No favourites stored yet – here's a curated highlight from the knowledge base."
                ],
            }
        )
        return payload

