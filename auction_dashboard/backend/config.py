"""
Your personal search profile.
Edit this file to update your criteria — the weekly scraper uses it to filter listings.
"""

SEARCH_PROFILE = {
    "max_price_eur": 300_000,
    "preferred_price_eur": 150_000,   # cash purchase ceiling

    # Target regions — edit or add more specific municipalities
    "regions": {
        "sicily": {
            "country": "IT",
            "keywords": ["noto", "siracusa", "ragusa", "modica", "scicli", "avola",
                         "palazzolo acreide", "ispica", "rosolini", "pachino"],
        },
        "south_france": {
            "country": "FR",
            "keywords": ["languedoc", "herault", "gard", "aude", "pyrénées",
                         "provence", "var", "vaucluse", "bouches-du-rhone",
                         "occitanie", "montpellier", "nîmes", "perpignan"],
        },
        "lisbon": {
            "country": "PT",
            "keywords": ["lisboa", "sintra", "cascais", "setúbal", "setubal",
                         "almada", "palmela", "sesimbra", "mafra", "torres vedras"],
        },
        "madrid": {
            "country": "ES",
            "keywords": ["toledo", "guadalajara", "segovia", "ávila", "avila",
                         "cuenca", "comunidad de madrid", "sierra de guadarrama",
                         "alcalá", "aranjuez", "chinchón"],
        },
    },

    # Property type keywords (searched in title + description)
    "property_type_keywords": [
        # Italian
        "masseria", "palazzo", "casale", "villa storica", "convento", "monastero",
        "torre", "castello", "rudere",
        # French
        "château", "chateau", "manoir", "mas", "bastide", "prieuré",
        "abbaye", "moulin", "corps de ferme",
        # Portuguese
        "quinta", "solar", "palácio", "palacio", "convento", "herdade",
        # Spanish
        "cortijo", "finca", "palacio", "casa señorial", "hacienda",
        "molino", "ermita", "monasterio",
        # Generic
        "historical", "historic", "heritage", "period", "ruins", "ruin",
        "to restore", "to renovate", "refurbish", "restore",
    ],

    "min_area_m2": 150,   # minimum property size

    # Email alert settings
    "alert_email": "",    # fill in your email address
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
}

# Scraper sources to enable (set False to skip one temporarily)
SOURCES = {
    "spain_boe": True,
    "italy_astalegale": True,
    "france_licitor": True,
    "portugal_eleiloes": True,
}
