"""Century rules for the Year category, shared by verify_years.py and the export.

Strict rule: the 19th century is 1801-1900.
Museum "1400s" (stored as 1400-1499) counts as the 15th century (1401-1500).
"""


def century_of(year):
    """1876 -> 19, 1900 -> 19, 1901 -> 20 (strict rule)."""
    return (year - 1) // 100 + 1


def century_label(number):
    """19 -> '19th century'. 11th-13th are special: 'th', not 'st/nd/rd'."""
    if number % 100 in (11, 12, 13):
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix} century"


def artwork_centuries(artwork):
    """Return (earliest, latest) century labels for an API artwork record."""
    start_year = artwork["creation_date_earliest"]
    # The museum stores "1400s" as 1400-1499. That label means the 15th century
    # (1401-1500), so a round start year counts as the first year of the next one.
    if start_year % 100 == 0:
        start_year += 1
    earliest = century_label(century_of(start_year))
    latest = century_label(century_of(artwork["creation_date_latest"]))
    return earliest, latest
