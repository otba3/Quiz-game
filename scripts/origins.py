"""Country -> continent rules for the Origin category.

The API has no continent field, only "culture" text such as
"Japan, Edo period (1615-1868)", so we keep our own table.
Shared by verify_origins.py and the export script.
"""

# Every country used in our questions (answers AND options), plus names the
# museum uses in "culture" text. Add a line when a new country appears.
COUNTRY_TO_CONTINENT = {
    # Asia
    "China": "Asia", "India": "Asia", "Indonesia": "Asia", "Iran": "Asia",
    "Japan": "Asia", "Korea": "Asia", "Philippines": "Asia", "Turkey": "Asia",
    "Uzbekistan": "Asia",
    # Europe
    "England": "Europe", "France": "Europe", "Germany": "Europe", "Greece": "Europe",
    "Italy": "Europe", "Netherlands": "Europe", "Spain": "Europe", "Switzerland": "Europe",
    # Africa
    "Algeria": "Africa", "Congo": "Africa", "Côte d'Ivoire": "Africa", "Egypt": "Africa",
    "Ghana": "Africa", "Liberia": "Africa", "Morocco": "Africa", "Nigeria": "Africa",
    "Sudan": "Africa", "Tunisia": "Africa", "Uganda": "Africa",
    # North America ("America" is how the museum often writes the United States)
    "America": "North America", "United States": "North America", "Mexico": "North America",
    "Guatemala": "North America", "Costa Rica": "North America", "Cuba": "North America",
}


def countries_in(culture):
    """All known countries mentioned in a culture text, e.g. 'North Italy, Brescia' -> ['Italy']."""
    return [country for country in COUNTRY_TO_CONTINENT if country.lower() in culture.lower()]


def continents_in(culture):
    """The continents of those countries, without repeats, e.g. ['Europe']."""
    return sorted({COUNTRY_TO_CONTINENT[country] for country in countries_in(culture)})
