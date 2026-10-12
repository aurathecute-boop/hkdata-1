"""Census and Statistics Department — population."""


def population() -> list:
    """Mid-year Hong Kong population by sex, annual series.

    Provides:
        - mid-year population by sex (male / female / both), annual from 1961

    Coverage:
        - Geography: HK-wide
        - Time:      historical series, annual

    Datasets:   hk-censtatd-tablechart-110-02001
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=110-02001&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = population()               # list[dict]
        >>> [r for r in rows if r["sv"] == "POP_TOTAL"]

    Questions:
        - "how many people live in Hong Kong?"
        - "Hong Kong population by year and sex"

    Quirks:
        - needs a browser-like User-Agent (bare urllib gets 403)
        - record fields: sv/svDesc (variable), period (year), figure
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=110-02001&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]
