"""LCSD free outdoor sports pitches/courts."""


def outdoor_badminton_courts() -> list:
    """Free outdoor badminton courts managed by LCSD.

    Provides:
        - district, venue name/address, number of courts, opening hours,
          ancillary (barrier-free) facilities, phone

    Coverage:
        - Geography: 14 venues across 8 districts (North, Tuen Mun, Yuen Long, …)
        - Time:      static inventory, updated as facilities change

    Datasets:   hk-lcsd-facility-facility-bmtc
    Department: Leisure and Cultural Services Department
    Endpoint:   https://www.lcsd.gov.hk/datagovhk/facility/facility-bmtc.json
    Format:     JSON

    Usage:
        >>> courts = outdoor_badminton_courts()  # list[dict]
        >>> [c for c in courts if c["District_cn"] == "北區"]

    Questions:
        - "where are the free outdoor badminton courts?"
        - "outdoor badminton courts near me"

    Quirks:
        - free outdoor pitches/courts only (not the indoor bookable sessions)
        - some venues share courts with volleyball
    """
    import json
    import urllib.request

    url = "https://www.lcsd.gov.hk/datagovhk/facility/facility-bmtc.json"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
