import unittest

from connektome.jungian import JungianInterpreter


class JungianInterpreterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.interpreter = JungianInterpreter()

    def test_interpretation_matches_archetype(self) -> None:
        item = {
            "name": "Heroic Tale",
            "category": "Book",
            "tags": ["epic", "courage", "journey"],
        }

        insight = self.interpreter.interpret(item)
        self.assertTrue(insight["archetypes"])
        top = insight["archetypes"][0]
        self.assertEqual(top["name"], "The Hero")
        self.assertIn("keywords", top["reason"])

    def test_interpretation_handles_missing_metadata(self) -> None:
        item = {"name": "Mystery"}

        insight = self.interpreter.interpret(item)
        self.assertEqual(insight["archetypes"], [])
        self.assertIn("Insufficient metadata", insight["reflection"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

