"""LCSD real-time sports-court session availability (SmartPLAY)."""


def badminton_sessions() -> list:
    """Real-time badminton court session availability across LCSD sports centres.

    Provides:
        - district + venue name/address (en/tc), phone, coordinates
        - per session: date, start/end time, facility type, booking status

    Coverage:
        - Geography: 105 venues, all 18 districts
        - Time:      real-time, refreshed every 5 minutes

    Datasets:   hk-lcsd-facility-facility-bmtcvenue
    Department: Leisure and Cultural Services Department
    Endpoint:   https://data.smartplay.lcsd.gov.hk/rest/cms/api/v1/publ/contents/open-data/badminton/file
    Format:     JSON

    Usage:
        >>> sessions = badminton_sessions()       # list[dict], ~13k rows
        >>> [s for s in sessions if "港灣道" in s["Venue_Name_TC"]]

    Questions:
        - "are there badminton court sessions available tonight?"
        - "badminton availability at Harbour Road Sports Centre"

    Quirks:
        - includes both available and booked slots (see Session_Status)
        - indoor courts only (not free outdoor courts)
        - urban (市區) courts are air-conditioned; court fees apply
    """
    import json
    import urllib.request

    url = ("https://data.smartplay.lcsd.gov.hk/rest/cms/api/v1/publ/"
           "contents/open-data/badminton/file")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
