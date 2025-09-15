import tempfile
import unittest
from pathlib import Path

from connektome.data_manager import DataManager
from connektome.knowledge_base import KnowledgeBase, KnowledgeItem
from connektome.suggester import SuggestionEngine


def build_item(name: str, category: str, tags: list[str]) -> KnowledgeItem:
    return KnowledgeItem(
        name=name,
        category=category,
        cover_image="",
        wikipedia_url=f"https://example.com/{name}",
        description=f"Description for {name}",
        tags=tags,
        meanings=[f"Meaning for {name}"],
        readings=[],
    )


class SuggestionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage = Path(self.temp_dir.name) / "favorites.json"
        self.manager = DataManager(storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_suggestions_prioritise_shared_tags(self) -> None:
        item_a = build_item("Item A", "Book", ["fantasy", "adventure"])
        item_b = build_item("Item B", "Book", ["fantasy", "mythic"])
        item_c = build_item("Item C", "Film", ["science", "future"])

        kb = KnowledgeBase(items=[item_a, item_b, item_c])
        engine = SuggestionEngine(kb, self.manager)

        self.manager.add_or_update(self.manager.from_knowledge_item(item_a))

        suggestions = engine.suggest(limit=2)
        self.assertTrue(suggestions)
        self.assertEqual(suggestions[0]["name"], "Item B")
        self.assertTrue(
            any("Shared tags" in reason for reason in suggestions[0]["reasons"])
        )

    def test_suggestions_empty_profile_returns_curated_list(self) -> None:
        item_a = build_item("Item A", "Book", ["fantasy"])
        item_b = build_item("Item B", "Film", ["science"])
        kb = KnowledgeBase(items=[item_a, item_b])
        engine = SuggestionEngine(kb, self.manager)

        suggestions = engine.suggest(limit=2)
        self.assertEqual(len(suggestions), 2)
        self.assertEqual(suggestions[0]["score"], 0)
        self.assertIn("curated highlight", suggestions[0]["reasons"][0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

