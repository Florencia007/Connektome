"""Local knowledge base for the Connektome favourites app."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class KnowledgeItem:
    """Represents a single cultural artefact in the knowledge base."""

    name: str
    category: str
    cover_image: str
    wikipedia_url: str
    description: str
    tags: List[str]
    meanings: List[str]
    readings: List[Dict[str, str]]

    def normalised_name(self) -> str:
        return self.name.strip().lower()


class KnowledgeBase:
    """Stores curated cultural artefacts with lightweight metadata.

    The class provides small, dependency free search utilities that stand in for
    more sophisticated third-party APIs.  The bundled data is intentionally rich
    enough to let the rest of the application run offline while still
    demonstrating the experience of working against a cultural graph.
    """

    def __init__(self, items: Optional[Iterable[KnowledgeItem]] = None) -> None:
        self._items: List[KnowledgeItem] = list(items) if items else list(DEFAULT_ITEMS)

    def all_items(self) -> List[KnowledgeItem]:
        return list(self._items)

    def find_by_name(self, name: str) -> Optional[KnowledgeItem]:
        needle = name.strip().lower()
        for item in self._items:
            if item.normalised_name() == needle:
                return item
        return None

    def search(self, keyword: str, limit: int = 5) -> List[KnowledgeItem]:
        keyword_lower = keyword.strip().lower()
        if not keyword_lower:
            return []

        scored: List[tuple[int, KnowledgeItem]] = []
        for item in self._items:
            score = 0
            if keyword_lower in item.normalised_name():
                score += 4
            if keyword_lower in item.description.lower():
                score += 2
            if any(keyword_lower in tag for tag in item.tags):
                score += 1
            if score:
                scored.append((score, item))

        scored.sort(key=lambda value: (-value[0], value[1].name))
        return [item for _, item in scored[:limit]]

    def related_by_tags(self, tags: Iterable[str], limit: int = 5) -> List[KnowledgeItem]:
        tag_set = {tag.lower() for tag in tags}
        if not tag_set:
            return []

        scored: List[tuple[int, KnowledgeItem]] = []
        for item in self._items:
            overlap = sum(1 for tag in item.tags if tag.lower() in tag_set)
            if overlap:
                scored.append((overlap, item))

        scored.sort(key=lambda value: (-value[0], value[1].name))
        return [item for _, item in scored[:limit]]


DEFAULT_ITEMS: List[KnowledgeItem] = [
    KnowledgeItem(
        name="The Lord of the Rings",
        category="Book",
        cover_image="https://upload.wikimedia.org/wikipedia/en/8/8e/The_Lord_of_the_Rings_cover.gif",
        wikipedia_url="https://en.wikipedia.org/wiki/The_Lord_of_the_Rings",
        description=(
            "J.R.R. Tolkien's epic high fantasy saga chronicling the quest to"
            " destroy the One Ring and the fellowship forged along the way."
        ),
        tags=["fantasy", "epic", "hero's journey", "friendship"],
        meanings=[
            "An exploration of courage and fellowship in the face of overwhelming"
            " darkness.",
            "Invites reflection on the cyclical battle between power and humility.",
        ],
        readings=[
            {
                "title": "On Fairy-Stories",
                "author": "J.R.R. Tolkien",
                "url": "https://en.wikipedia.org/wiki/On_Fairy-Stories",
            },
            {
                "title": "The Road to Middle-earth",
                "author": "Tom Shippey",
                "url": "https://en.wikipedia.org/wiki/Tom_Shippey",
            },
        ],
    ),
    KnowledgeItem(
        name="Spirited Away",
        category="Film",
        cover_image="https://upload.wikimedia.org/wikipedia/en/d/db/Spirited_Away_Japanese_poster.png",
        wikipedia_url="https://en.wikipedia.org/wiki/Spirited_Away",
        description=(
            "Hayao Miyazaki's coming-of-age tale where a young girl navigates a"
            " spirit world filled with gods, witches and unusual creatures."
        ),
        tags=["animation", "coming of age", "spiritual", "transformation"],
        meanings=[
            "Illustrates the shedding of childhood naivety through acts of"
            " empathy.",
            "Highlights the power of remembering one's name as a symbol of"
            " identity.",
        ],
        readings=[
            {
                "title": "Starting Point: 1979-1996",
                "author": "Hayao Miyazaki",
                "url": "https://en.wikipedia.org/wiki/Starting_Point:_1979%E2%80%931996",
            },
            {
                "title": "Anime: A History",
                "author": "Jonathan Clements",
                "url": "https://en.wikipedia.org/wiki/Jonathan_Clements_(author)",
            },
        ],
    ),
    KnowledgeItem(
        name="The Starry Night",
        category="Artwork",
        cover_image="https://upload.wikimedia.org/wikipedia/commons/e/ea/The_Starry_Night.JPG",
        wikipedia_url="https://en.wikipedia.org/wiki/The_Starry_Night",
        description=(
            "Vincent van Gogh's swirling depiction of a night sky over Saint-Rémy"
            " which blends turbulence with serenity."
        ),
        tags=["post-impressionism", "night", "emotion", "landscape"],
        meanings=[
            "Captures the tension between the inner emotional world and external"
            " calm.",
            "Invites meditation on the sublime vastness of the cosmos.",
        ],
        readings=[
            {
                "title": "Dear Theo",
                "author": "Vincent van Gogh",
                "url": "https://en.wikipedia.org/wiki/Dear_Theo",
            },
            {
                "title": "Van Gogh: The Life",
                "author": "Steven Naifeh and Gregory White Smith",
                "url": "https://en.wikipedia.org/wiki/Vincent_van_Gogh",
            },
        ],
    ),
    KnowledgeItem(
        name="Bohemian Rhapsody",
        category="Song",
        cover_image="https://upload.wikimedia.org/wikipedia/en/9/9f/Bohemian_Rhapsody.png",
        wikipedia_url="https://en.wikipedia.org/wiki/Bohemian_Rhapsody",
        description=(
            "Queen's operatic rock suite blending ballad, opera and hard rock"
            " movements into an emotional confession."
        ),
        tags=["rock", "opera", "identity", "anthem"],
        meanings=[
            "Expresses the turmoil of confronting one's shadow self.",
            "Demonstrates the liberation found in radical self-expression.",
        ],
        readings=[
            {
                "title": "Mercury: An Intimate Biography of Freddie Mercury",
                "author": "Lesley-Ann Jones",
                "url": "https://en.wikipedia.org/wiki/Freddie_Mercury",
            }
        ],
    ),
    KnowledgeItem(
        name="Meditations",
        category="Book",
        cover_image="https://upload.wikimedia.org/wikipedia/commons/2/2e/Meditations_Marcus_Aurelius_1811.jpg",
        wikipedia_url="https://en.wikipedia.org/wiki/Meditations",
        description=(
            "Marcus Aurelius' personal writings on Stoic philosophy and the"
            " cultivation of virtue amidst leadership."
        ),
        tags=["philosophy", "stoicism", "reflection", "leadership"],
        meanings=[
            "Encourages steadfastness and equanimity through mindful practice.",
            "Frames adversity as an opportunity for inner alignment.",
        ],
        readings=[
            {
                "title": "How to Think Like a Roman Emperor",
                "author": "Donald Robertson",
                "url": "https://en.wikipedia.org/wiki/Donald_Robertson_(writer)",
            },
            {
                "title": "The Inner Citadel",
                "author": "Pierre Hadot",
                "url": "https://en.wikipedia.org/wiki/Pierre_Hadot",
            },
        ],
    ),
    KnowledgeItem(
        name="The Legend of Zelda: Breath of the Wild",
        category="Game",
        cover_image="https://upload.wikimedia.org/wikipedia/en/0/0b/The_Legend_of_Zelda_Breath_of_the_Wild.jpg",
        wikipedia_url="https://en.wikipedia.org/wiki/The_Legend_of_Zelda:_Breath_of_the_Wild",
        description=(
            "Nintendo's open-world adventure where Link awakens to explore Hyrule"
            " with unprecedented freedom."
        ),
        tags=["adventure", "exploration", "freedom", "mythic"],
        meanings=[
            "Celebrates curiosity and playful experimentation.",
            "Positions the player as a restorer of balance between technology and"
            " nature.",
        ],
        readings=[
            {
                "title": "The Hyrule Historia",
                "author": "Nintendo",
                "url": "https://en.wikipedia.org/wiki/Hyrule_Historia",
            },
            {
                "title": "The Triforce of Wisdom",
                "author": "Kyle Hilliard",
                "url": "https://en.wikipedia.org/wiki/The_Legend_of_Zelda",
            },
        ],
    ),
    KnowledgeItem(
        name="Blade Runner 2049",
        category="Film",
        cover_image="https://upload.wikimedia.org/wikipedia/en/2/27/Blade_Runner_2049_logo.png",
        wikipedia_url="https://en.wikipedia.org/wiki/Blade_Runner_2049",
        description=(
            "Denis Villeneuve's neo-noir science fiction film exploring identity,"
            " memory and the soul of artificial beings."
        ),
        tags=["science fiction", "identity", "noir", "memory"],
        meanings=[
            "Questions what makes an identity real when memories can be engineered.",
            "Highlights the longing for meaning in post-human futures.",
        ],
        readings=[
            {
                "title": "Do Androids Dream of Electric Sheep?",
                "author": "Philip K. Dick",
                "url": "https://en.wikipedia.org/wiki/Do_Androids_Dream_of_Electric_Sheep%3F",
            },
            {
                "title": "Future Noir: The Making of Blade Runner",
                "author": "Paul M. Sammon",
                "url": "https://en.wikipedia.org/wiki/Paul_M._Sammon",
            },
        ],
    ),
    KnowledgeItem(
        name="The Great Wave off Kanagawa",
        category="Artwork",
        cover_image="https://upload.wikimedia.org/wikipedia/commons/0/0a/Great_Wave_off_Kanagawa2.jpg",
        wikipedia_url="https://en.wikipedia.org/wiki/The_Great_Wave_off_Kanagawa",
        description=(
            "Katsushika Hokusai's ukiyo-e print capturing a towering wave poised"
            " above boats near Mount Fuji."
        ),
        tags=["ukiyo-e", "nature", "impermanence", "resilience"],
        meanings=[
            "Symbolises the sublime power of nature and human adaptability.",
            "Evokes the rhythms of impermanence central to Japanese aesthetics.",
        ],
        readings=[
            {
                "title": "Hokusai",
                "author": "Matthi Forrer",
                "url": "https://en.wikipedia.org/wiki/Hokusai",
            }
        ],
    ),
    KnowledgeItem(
        name="Interstellar",
        category="Film",
        cover_image="https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg",
        wikipedia_url="https://en.wikipedia.org/wiki/Interstellar_(film)",
        description=(
            "Christopher Nolan's cosmic odyssey that entwines astrophysics with"
            " a father's love and humanity's survival."
        ),
        tags=["space", "sacrifice", "family", "science fiction"],
        meanings=[
            "Frames love as a force capable of transcending time and space.",
            "Encourages awe toward the mysteries of the universe.",
        ],
        readings=[
            {
                "title": "The Science of Interstellar",
                "author": "Kip Thorne",
                "url": "https://en.wikipedia.org/wiki/Kip_Thorne",
            },
            {
                "title": "Black Hole Blues",
                "author": "Janna Levin",
                "url": "https://en.wikipedia.org/wiki/Janna_Levin",
            },
        ],
    ),
    KnowledgeItem(
        name="The Little Prince",
        category="Book",
        cover_image="https://upload.wikimedia.org/wikipedia/en/0/05/Littleprince.JPG",
        wikipedia_url="https://en.wikipedia.org/wiki/The_Little_Prince",
        description=(
            "Antoine de Saint-Exupéry's poetic novella reflecting on innocence,"
            " loss and the value of seeing with the heart."
        ),
        tags=["childhood", "wisdom", "imagination", "philosophy"],
        meanings=[
            "Invites adults to reconcile logic with imagination.",
            "Teaches that relationships cultivate responsibility and wonder.",
        ],
        readings=[
            {
                "title": "Wind, Sand and Stars",
                "author": "Antoine de Saint-Exupéry",
                "url": "https://en.wikipedia.org/wiki/Wind,_Sand_and_Stars",
            }
        ],
    ),
    KnowledgeItem(
        name="The Art of War",
        category="Book",
        cover_image="https://upload.wikimedia.org/wikipedia/commons/2/2c/Art_of_War_%28Chinese_Edition%29.jpg",
        wikipedia_url="https://en.wikipedia.org/wiki/The_Art_of_War",
        description=(
            "Sun Tzu's ancient treatise on strategy, balance and the psychology of"
            " conflict."
        ),
        tags=["strategy", "balance", "leadership", "tactics"],
        meanings=[
            "Demonstrates how adaptability and awareness overcome brute force.",
            "Warns that true victory preserves harmony rather than domination.",
        ],
        readings=[
            {
                "title": "The Book of Five Rings",
                "author": "Miyamoto Musashi",
                "url": "https://en.wikipedia.org/wiki/The_Book_of_Five_Rings",
            }
        ],
    ),
]

