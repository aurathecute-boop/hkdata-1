"""Environmental Protection Department — river water quality."""


def river_water_quality() -> list:
    """Recent river water quality (DO and BOD5) at downstream stations.

    Provides:
        - dissolved oxygen (mg/L) and 5-day biochemical oxygen demand (mg/L)
          at downstream monitoring stations of major rivers, monthly

    Coverage:
        - Geography: major river systems across HK (Deep Bay, Victoria Harbour,
          Tolo Harbour water control zones, ...)
        - Time:      historical series, monthly (04/2024 → 03/2026)

    Datasets:   hk-epd-riverteam-river-water-quality-recent-data
    Department: Environmental Protection Department
    Endpoint:   https://cd.epic.epd.gov.hk/riverpsi/en/riverrecent/river-recent-en.csv
    Format:     CSV

    Usage:
        >>> rows = river_water_quality()      # list[dict]

    Questions:
        - "what is the water quality of the Shing Mun River?"
        - "river dissolved oxygen levels"

    Quirks:
        - key metrics: Dissolved Oxygen and 5-Day BOD, both mg/L
        - Chinese variants: /tc/.../river-recent-tc.csv, /sc/...
    """
    import csv
    import io
    import urllib.request

    url = "https://cd.epic.epd.gov.hk/riverpsi/en/riverrecent/river-recent-en.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))
