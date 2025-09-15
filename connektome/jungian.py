"""Jungian-inspired reflections for favourite items."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class ArchetypeProfile:
    name: str
    summary: str
    keywords: Sequence[str]
    categories: Sequence[str]
    shadow_aspect: str
    growth_question: str

    def keyword_set(self) -> set[str]:
        return {keyword.lower() for keyword in self.keywords}

    def category_set(self) -> set[str]:
        return {category.lower() for category in self.categories}


class JungianInterpreter:
    """Generate light-weight Jungian interpretations for stored favourites."""

    def __init__(self, archetypes: Iterable[ArchetypeProfile] | None = None) -> None:
        self._profiles: List[ArchetypeProfile] = list(archetypes) if archetypes else list(
            DEFAULT_ARCHETYPES
        )

    def interpret(self, item: Dict[str, object], limit: int = 3) -> Dict[str, object]:
        """Return archetypal insights for a stored favourite."""

        tags = {tag.lower() for tag in item.get("tags", [])}
        category = str(item.get("category", "")).lower()
        if not tags and not category:
            return {
                "item": item.get("name", "Unknown"),
                "archetypes": [],
                "reflection": "Insufficient metadata to generate an interpretation.",
            }

        scored: List[tuple[int, ArchetypeProfile, str]] = []
        for profile in self._profiles:
            score = 0
            matched_keywords = tags.intersection(profile.keyword_set())
            if matched_keywords:
                score += len(matched_keywords)
            if category in profile.category_set():
                score += 2
            if score:
                reason_parts: List[str] = []
                if matched_keywords:
                    reason_parts.append(
                        "keywords: " + ", ".join(sorted(matched_keywords))
                    )
                if category in profile.category_set():
                    reason_parts.append(f"category resonance with {category}")
                reason = "; ".join(reason_parts)
                scored.append((score, profile, reason))

        scored.sort(key=lambda value: (-value[0], value[1].name))
        top_matches = scored[:limit]

        insights: List[Dict[str, object]] = []
        for score, profile, reason in top_matches:
            insights.append(
                {
                    "name": profile.name,
                    "summary": profile.summary,
                    "shadow_aspect": profile.shadow_aspect,
                    "growth_question": profile.growth_question,
                    "score": score,
                    "reason": reason,
                }
            )

        reflection = self._compose_reflection(item, insights)
        return {"item": item.get("name", "Unknown"), "archetypes": insights, "reflection": reflection}

    def _compose_reflection(self, item: Dict[str, object], insights: List[Dict[str, object]]) -> str:
        if not insights:
            return (
                "Consider adding tags or a category so the app can map your"
                " favourite to Jungian archetypes."
            )

        headline = insights[0]
        item_name = item.get("name", "This favourite")
        lines = [
            f"{item_name} resonates strongly with the {headline['name']} archetype,"
            f" suggesting {headline['summary'].lower()}",
        ]
        if headline["shadow_aspect"]:
            lines.append(f"Its shadow asks you to watch for {headline['shadow_aspect'].lower()}.")
        if len(insights) > 1:
            secondary = ", ".join(entry["name"] for entry in insights[1:])
            lines.append(f"Secondary notes of {secondary} round out the picture.")

        prompt = insights[0].get("growth_question")
        if prompt:
            lines.append(f"Reflection prompt: {prompt}")
        return " ".join(lines)


DEFAULT_ARCHETYPES: List[ArchetypeProfile] = [
    ArchetypeProfile(
        name="The Hero",
        summary="a drive to overcome challenge through courage and disciplined action",
        keywords=["epic", "journey", "sacrifice", "courage", "resilience"],
        categories=["book", "film", "game"],
        shadow_aspect="burnout from constant striving or saviour complexes",
        growth_question="Where might you invite collaboration instead of carrying everything alone?",
    ),
    ArchetypeProfile(
        name="The Explorer",
        summary="a hunger for freedom, discovery and experiences beyond the familiar",
        keywords=["exploration", "freedom", "travel", "adventure", "curiosity"],
        categories=["game", "book", "film"],
        shadow_aspect="restlessness that prevents deep belonging",
        growth_question="How can you balance discovery with tending to the relationships that sustain you?",
    ),
    ArchetypeProfile(
        name="The Sage",
        summary="a commitment to understanding, contemplation and thoughtful guidance",
        keywords=["philosophy", "wisdom", "reflection", "science", "analysis"],
        categories=["book", "film", "artwork"],
        shadow_aspect="retreating into intellect to avoid feeling",
        growth_question="Where can your insight be paired with embodied experience?",
    ),
    ArchetypeProfile(
        name="The Creator",
        summary="the urge to bring novel beauty or meaning into the world",
        keywords=["art", "imagination", "expression", "aesthetic", "innovation"],
        categories=["artwork", "song", "book", "film"],
        shadow_aspect="perfectionism that blocks experimentation",
        growth_question="What would happen if you shared something unfinished but heartfelt?",
    ),
    ArchetypeProfile(
        name="The Lover",
        summary="a devotion to connection, sensuality and heartfelt bonds",
        keywords=["relationship", "emotion", "romance", "heart", "identity"],
        categories=["song", "film", "book"],
        shadow_aspect="losing self-definition when merging with others",
        growth_question="How do you honour your own needs while staying open-hearted?",
    ),
]

