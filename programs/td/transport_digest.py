"""Transport Department — monthly traffic and transport digest."""


def traffic_digest(table: str = "table11_eng") -> list:
    """Monthly Traffic & Transport Digest tables (CSV).

    Provides:
        - passenger journeys by operator (table11), vehicle registration
          (table21s), road accidents (table41a), tunnel flows (table51a),
          cross-boundary traffic (table61), etc.

    Coverage:
        - Geography: HK-wide
        - Time:      monthly, updated each month

    Datasets:   hk-td-tis_17-monthly-traffic-and-transport-digest-csv
    Department: Transport Department
    Endpoint:   https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/{table}.csv
    Format:     CSV

    Usage:
        >>> rows = traffic_digest("table11_eng")   # passenger journeys

    Questions:
        - "how many passenger journeys by MTR last month?"
        - "road traffic accidents trend"

    Quirks:
        - ~100 tables per language; pass the table name (e.g. table11_eng)
        - last revision date: DATA_LAST_REVISION_DATE_eng.csv
    """
    import csv
    import io
    import urllib.request

    url = f"https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/{table}.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))
