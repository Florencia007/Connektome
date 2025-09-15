import tempfile
import unittest
from pathlib import Path

from connektome.data_manager import DataManager


SAMPLE_ITEM = {
    "name": "Sample",
    "category": "Book",
    "cover_image": "http://example.com/cover.jpg",
    "wikipedia_url": "https://en.wikipedia.org/wiki/Sample",
    "description": "A sample item for testing.",
    "tags": ["test", "sample"],
    "meanings": ["Meaning"],
    "readings": [
        {"title": "Sample Reading", "author": "Tester", "url": "http://example.com"}
    ],
}


class DataManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "favorites.json"
        self.manager = DataManager(self.storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_and_get_favourite(self) -> None:
        entry = dict(SAMPLE_ITEM)
        self.manager.add_or_update(entry)

        retrieved = self.manager.get_favourite("Sample")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Sample")
        self.assertEqual(retrieved["category"], "Book")

    def test_update_replaces_existing(self) -> None:
        entry = dict(SAMPLE_ITEM)
        self.manager.add_or_update(entry)

        entry_updated = dict(entry)
        entry_updated["description"] = "Updated description"
        self.manager.add_or_update(entry_updated)

        retrieved = self.manager.get_favourite("Sample")
        self.assertEqual(retrieved["description"], "Updated description")
        self.assertEqual(len(self.manager.list_favourites()), 1)

    def test_remove_deletes_entry(self) -> None:
        entry = dict(SAMPLE_ITEM)
        self.manager.add_or_update(entry)

        self.assertTrue(self.manager.remove("Sample"))
        self.assertIsNone(self.manager.get_favourite("Sample"))
        self.assertFalse(self.manager.remove("Sample"))


if __name__ == "__main__":  # pragma: no cover - for direct execution during debugging
    unittest.main()

