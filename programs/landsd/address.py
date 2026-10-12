"""Lands Department — Address Lookup Service (ALS)."""


def address_lookup(query: str) -> dict:
    """Address search + geocoding via the Address Lookup Service.

    Provides:
        - matched addresses: Chinese/English address, building name, street,
          district, and geographic coordinates

    Coverage:
        - Geography: HK-wide address database
        - Time:      real-time lookup

    Datasets:   hk-dpo-als_01-als
    Department: Lands Department
    Endpoint:   https://www.als.gov.hk/lookup?q={query}
    Format:     JSON

    Usage:
        >>> r = address_lookup("時代廣場")    # dict of matches
        >>> r = address_lookup("Times Square")

    Questions:
        - "what are the coordinates of [address]?"
        - "geocode an address"

    Quirks:
        - requires Accept: application/json header
        - old als.ogcio.gov.hk is deprecated — use als.gov.hk
    """
    import json
    import urllib.parse
    import urllib.request

    url = "https://www.als.gov.hk/lookup?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
