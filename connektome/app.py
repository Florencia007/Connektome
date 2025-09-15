"""Command line interface for the Connektome favourites experience."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from textwrap import fill
from typing import List, Optional

from .data_manager import DataManager
from .jungian import JungianInterpreter
from .knowledge_base import KnowledgeBase, KnowledgeItem
from .suggester import SuggestionEngine

DEFAULT_STORAGE = Path(__file__).resolve().parent.parent / "data" / "favorites.json"


@dataclass
class AppContext:
    knowledge_base: KnowledgeBase
    data_manager: DataManager
    suggestion_engine: SuggestionEngine
    jungian: JungianInterpreter


def build_context(storage: Path) -> AppContext:
    knowledge_base = KnowledgeBase()
    data_manager = DataManager(storage)
    suggestion_engine = SuggestionEngine(knowledge_base, data_manager)
    jungian = JungianInterpreter()
    return AppContext(knowledge_base, data_manager, suggestion_engine, jungian)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Save your favourite cultural artefacts and explore curated insights.",
    )
    parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_STORAGE,
        help="Path to the favourites storage file (defaults to data/favorites.json).",
    )

    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a favourite item, auto-populating metadata.")
    add_parser.add_argument("name", help="Name of the item to save.")
    add_parser.add_argument(
        "--category",
        help="Override the category if it differs from the knowledge base entry.",
    )
    add_parser.add_argument("--notes", help="Personal notes to attach to the entry.")
    add_parser.add_argument("--description", help="Fallback description when no metadata is found.")
    add_parser.add_argument("--wikipedia", help="Fallback Wikipedia link when not in the knowledge base.")
    add_parser.add_argument("--cover-image", dest="cover_image", help="Fallback cover image URL.")
    add_parser.set_defaults(func=handle_add)

    list_parser = subparsers.add_parser("list", help="Show stored favourites, optionally by category.")
    list_parser.add_argument("--category", help="Filter favourites by category.")
    list_parser.set_defaults(func=handle_list)

    search_parser = subparsers.add_parser(
        "search",
        help="Search the built-in knowledge base for inspiration.",
    )
    search_parser.add_argument("keyword", help="Keyword to search for in names, descriptions and tags.")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to show.")
    search_parser.set_defaults(func=handle_search)

    suggest_parser = subparsers.add_parser(
        "suggest", help="Recommend new items based on your stored favourites."
    )
    suggest_parser.add_argument("--limit", type=int, default=5, help="Maximum number of suggestions to show.")
    suggest_parser.set_defaults(func=handle_suggest)

    interpret_parser = subparsers.add_parser(
        "interpret", help="Generate a Jungian reflection for a stored favourite."
    )
    interpret_parser.add_argument("name", help="Name of the stored favourite to interpret.")
    interpret_parser.set_defaults(func=handle_interpret)

    meaning_parser = subparsers.add_parser(
        "meaning", help="Show symbolic meanings attached to a favourite."
    )
    meaning_parser.add_argument("name", help="Name of the favourite to explain.")
    meaning_parser.set_defaults(func=handle_meaning)

    reading_parser = subparsers.add_parser(
        "readings", help="Recommend further reading related to a favourite."
    )
    reading_parser.add_argument("name", help="Name of the favourite to base recommendations on.")
    reading_parser.set_defaults(func=handle_readings)

    remove_parser = subparsers.add_parser("remove", help="Remove a stored favourite.")
    remove_parser.add_argument("name", help="Name of the favourite to remove.")
    remove_parser.set_defaults(func=handle_remove)

    return parser


def handle_add(args: argparse.Namespace, context: AppContext) -> int:
    kb_item = context.knowledge_base.find_by_name(args.name)
    if not kb_item:
        search_matches = context.knowledge_base.search(args.name)
        if search_matches:
            kb_item = search_matches[0]

    if kb_item:
        payload = context.data_manager.from_knowledge_item(
            kb_item, notes=args.notes, categories_override=args.category
        )
        context.data_manager.add_or_update(payload)
        print(f"Saved '{kb_item.name}' with curated metadata.")
        return 0

    category = args.category or "Uncategorised"
    payload = {
        "name": args.name,
        "category": category,
        "cover_image": args.cover_image or "",
        "wikipedia_url": args.wikipedia
        or f"https://en.wikipedia.org/wiki/{args.name.strip().replace(' ', '_')}",
        "description": args.description or "A personal favourite awaiting a richer description.",
        "tags": [],
        "meanings": ["Consider researching this item to enrich its symbolism."],
        "readings": [],
    }
    if args.notes:
        payload["notes"] = args.notes
    context.data_manager.add_or_update(payload)
    print(
        "Item saved with your custom metadata. Use the 'search' command to see if"
        " the knowledge base has similar entries you can import later."
    )
    return 0


def handle_list(args: argparse.Namespace, context: AppContext) -> int:
    favourites = context.data_manager.list_favourites(args.category)
    if not favourites:
        if args.category:
            print(f"No favourites stored in category '{args.category}'.")
        else:
            print("You have not saved any favourites yet. Use the 'add' command to begin.")
        return 0

    for favourite in favourites:
        print_item_summary(favourite)
        print("-" * 80)
    return 0


def handle_search(args: argparse.Namespace, context: AppContext) -> int:
    matches = context.knowledge_base.search(args.keyword, limit=args.limit)
    if not matches:
        print("No entries matched your search.")
        return 0

    for match in matches:
        print_knowledge_item(match)
        print("-" * 80)
    return 0


def handle_suggest(args: argparse.Namespace, context: AppContext) -> int:
    suggestions = context.suggestion_engine.suggest(limit=args.limit)
    if not suggestions:
        print("Store a few favourites first so we can learn what you love.")
        return 0

    for suggestion in suggestions:
        print_suggestion(suggestion)
        print("-" * 80)
    return 0


def handle_interpret(args: argparse.Namespace, context: AppContext) -> int:
    favourite = context.data_manager.get_favourite(args.name)
    if not favourite:
        kb_item = context.knowledge_base.find_by_name(args.name)
        if kb_item:
            favourite = context.data_manager.from_knowledge_item(kb_item)

    if not favourite:
        print(
            "Favourite not found. Add it first with the 'add' command or check spelling."
        )
        return 1

    insight = context.jungian.interpret(favourite)
    print(f"Jungian reflection for {insight['item']}:")
    for archetype in insight["archetypes"]:
        print(f" • {archetype['name']} (score {archetype['score']})")
        print(wrap_text(f"Reason: {archetype['reason']}", indent=6))
        print(wrap_text(f"Shadow: {archetype['shadow_aspect']}", indent=6))
        print(wrap_text(f"Reflection: {archetype['growth_question']}", indent=6))
    print(wrap_text(insight["reflection"], indent=4))
    return 0


def handle_meaning(args: argparse.Namespace, context: AppContext) -> int:
    favourite = context.data_manager.get_favourite(args.name)
    if not favourite:
        kb_item = context.knowledge_base.find_by_name(args.name)
        if kb_item:
            favourite = context.data_manager.from_knowledge_item(kb_item)

    if not favourite:
        print("Meaning unavailable – save the favourite first so we can attach symbolism.")
        return 1

    print(f"Symbolic meanings for {favourite['name']}:")
    meanings = favourite.get("meanings", [])
    if not meanings:
        print(" • No meanings recorded yet. Add notes or enrich this entry manually.")
        return 0

    for meaning in meanings:
        print(wrap_text(f" • {meaning}", indent=2))
    return 0


def handle_readings(args: argparse.Namespace, context: AppContext) -> int:
    favourite = context.data_manager.get_favourite(args.name)
    if not favourite:
        kb_item = context.knowledge_base.find_by_name(args.name)
        if kb_item:
            favourite = context.data_manager.from_knowledge_item(kb_item)

    if not favourite:
        print("No reading suggestions found. Save the item or check the spelling.")
        return 1

    readings = favourite.get("readings", [])
    if not readings:
        print("No readings are attached to this item yet.")
        return 0

    print(f"Further reading inspired by {favourite['name']}:")
    for reading in readings:
        title = reading.get("title")
        author = reading.get("author")
        url = reading.get("url")
        descriptor = f"{title} by {author}" if author else title
        if url:
            descriptor += f" — {url}"
        print(wrap_text(f" • {descriptor}", indent=2))
    return 0


def handle_remove(args: argparse.Namespace, context: AppContext) -> int:
    removed = context.data_manager.remove(args.name)
    if removed:
        print(f"Removed '{args.name}' from your favourites.")
        return 0
    print("Item not found; nothing was removed.")
    return 1


def print_item_summary(favourite: dict) -> None:
    print(f"{favourite['name']} — {favourite.get('category', 'Uncategorised')}")
    print(wrap_text(favourite.get("description", ""), indent=2))
    if favourite.get("wikipedia_url"):
        print(f"  Wikipedia: {favourite['wikipedia_url']}")
    if favourite.get("cover_image"):
        print(f"  Cover: {favourite['cover_image']}")
    if favourite.get("tags"):
        print(f"  Tags: {', '.join(favourite['tags'])}")
    if favourite.get("notes"):
        print(wrap_text(f"Notes: {favourite['notes']}", indent=2))


def print_knowledge_item(item: KnowledgeItem) -> None:
    print(f"{item.name} — {item.category}")
    print(wrap_text(item.description, indent=2))
    print(f"  Wikipedia: {item.wikipedia_url}")
    if item.cover_image:
        print(f"  Cover: {item.cover_image}")
    if item.tags:
        print(f"  Tags: {', '.join(item.tags)}")


def print_suggestion(suggestion: dict) -> None:
    print(f"{suggestion['name']} — score {suggestion['score']}")
    print(wrap_text(suggestion.get("description", ""), indent=2))
    if suggestion.get("wikipedia_url"):
        print(f"  Wikipedia: {suggestion['wikipedia_url']}")
    if suggestion.get("cover_image"):
        print(f"  Cover: {suggestion['cover_image']}")
    if suggestion.get("tags"):
        print(f"  Tags: {', '.join(suggestion['tags'])}")
    if suggestion.get("reasons"):
        for reason in suggestion["reasons"]:
            print(wrap_text(f"Reason: {reason}", indent=2))


def wrap_text(text: Optional[str], indent: int = 0, width: int = 88) -> str:
    if not text:
        return ""
    prefix = " " * indent
    return fill(text, width=width, initial_indent=prefix, subsequent_indent=prefix)


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    context = build_context(args.storage)
    return args.func(args, context)


if __name__ == "__main__":
    raise SystemExit(main())

