"""LCSD leisure-facility inventories (static)."""


def fitness_rooms() -> list:
    """HK-wide fitness (gym) rooms in LCSD sports centres (static inventory).

    Provides:
        - venue name (en/tc), district, address, phone, room size
        - coordinates (degree-minute-second strings, not decimal degrees)
        - no real-time availability/occupancy (booking is via Leisure Link)

    Coverage:
        - Geography: all 18 districts
        - Time:      static inventory, updated as facilities change

    Datasets:   hk-lcsd-facility-facility-fit
    Department: Leisure and Cultural Services Department
    Endpoint:   http://www.lcsd.gov.hk/datagovhk/facility/facility-fitrm.json
    Format:     JSON

    Usage:
        >>> rooms = fitness_rooms()          # list[dict], ~87 rows
        >>> [r["Name_en"] for r in rooms if r["District_en"] == "Sham Shui Po"]

    Questions:
        - "is there a fitness room near Cheung Sha Wan?"
        - "which LCSD sports centres have a gym room?"

    Quirks:
        - Size_en contains HTML (121m<sup>2</sup>); use Size_cn or strip tags
        - Longitude/Latitude are DMS strings ("114-9-33"), not decimal degrees
        - District_en uses "&" (Central & Western) — normalise to "and" before joins
        - no venue is named "Cheung Sha Wan"; match Sham Shui Po by address
    """
    import json
    import urllib.request

    url = "http://www.lcsd.gov.hk/datagovhk/facility/facility-fitrm.json"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fitness_equipment() -> list:
    """Fitness equipment installed in LCSD fitness rooms (static inventory).

    Provides:
        - equipment name and count per fitness room, keyed by venue name (en/tc)

    Coverage:
        - Geography: all districts with a fitness room
        - Time:      static inventory

    Datasets:   hk-lcsd-facility-facility-fit
    Department: Leisure and Cultural Services Department
    Endpoint:   http://www.lcsd.gov.hk/datagovhk/facility/facility-fiteqmt.json
    Format:     JSON

    Usage:
        >>> rows = fitness_equipment()       # list[dict], ~1,925 rows
        >>> [r for r in rows if r["Name_en"] == "Po On Road Sports Centre"]

    Questions:
        - "what gym equipment is at Po On Road Sports Centre?"

    Quirks:
        - venue key is Name_en / Name_cn, matching fitness_rooms()
    """
    import json
    import urllib.request

    url = "http://www.lcsd.gov.hk/datagovhk/facility/facility-fiteqmt.json"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
