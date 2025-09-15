# Connektome

The Connektome CLI is a small personal knowledge keeper for your favourite
books, films, artworks, games and songs.  It stores your selections by category,
pre-fills rich metadata from an offline knowledge base, and offers reflective
tools inspired by Jungian psychology.

## Features

- **Save favourites with metadata** – add an item by name and the app will pull
  a cover image, Wikipedia link, description, tags, meanings and suggested
  readings from the curated knowledge base.
- **Search for inspiration** – query the built-in catalogue to discover new
  pieces aligned with your interests.
- **Personalised suggestions** – receive recommendations based on the tags and
  categories you already love.
- **Jungian interpretations** – explore archetypal insights that explain why a
  favourite resonates with you.
- **Symbolism and further reading** – review stored meanings and receive deeper
  reading recommendations for each entry.

All functionality works offline using the bundled metadata, making the app easy
to experiment with locally.

## Getting started

1. Ensure you have Python 3.10+ installed.
2. (Optional) Create and activate a virtual environment.
3. Run commands using the module entry point:

```bash
python -m connektome.app --help
```

Your saved favourites are stored in `data/favorites.json`.  You can specify an
alternative path with the `--storage` option on any command.

## Common commands

Add an item (auto-populating metadata when available):

```bash
python -m connektome.app add "The Lord of the Rings"
```

List everything you have saved:

```bash
python -m connektome.app list
```

Search the knowledge base:

```bash
python -m connektome.app search "space"
```

Request recommendations:

```bash
python -m connektome.app suggest --limit 5
```

Generate a Jungian interpretation:

```bash
python -m connektome.app interpret "Spirited Away"
```

Inspect meanings and suggested reading:

```bash
python -m connektome.app meaning "Meditations"
python -m connektome.app readings "Meditations"
```

Remove an entry if you change your mind:

```bash
python -m connektome.app remove "The Art of War"
```

## Running tests

The project ships with a lightweight unit test suite.  Execute it with:

```bash
python -m unittest discover
```

