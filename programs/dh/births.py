"""Department of Health — birth statistics."""


def births() -> list:
    """Known live births by sex and crude birth rate, 1981–2024.

    Provides:
        - male and female known live births, and crude birth rate (per 1,000)

    Coverage:
        - Geography: HK-wide
        - Time:      historical series, annual (1981–2024)

    Datasets:   hk-dh-dh_ncddhss-ncdd-dataset-2
    Department: Department of Health
    Endpoint:   https://www.dh.gov.hk/datagovhk/ncdd/Number%20of%20Known%20Births%20for%20Different%20Sexes%20and%20Crude%20Birth%20Rate%201981-2024(en).csv
    Format:     CSV

    Usage:
        >>> rows = births()                   # list[dict]

    Questions:
        - "how many births were there last year?"
        - "birth rate trend in Hong Kong"

    Quirks:
        - "known births" = registered live births where sex is known
        - also a birth-weight distribution CSV in the same dataset
    """
    import csv
    import io
    import urllib.request

    url = ("https://www.dh.gov.hk/datagovhk/ncdd/"
           "Number%20of%20Known%20Births%20for%20Different%20Sexes%20and%20"
           "Crude%20Birth%20Rate%201981-2024(en).csv")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))
