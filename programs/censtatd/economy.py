"""Census and Statistics Department — economic indicators (CPI, GDP)."""


def cpi() -> list:
    """Consumer Price Index (CPI), seasonally adjusted, annual + monthly.

    Provides:
        - composite CPI and component indices, seasonally adjusted, by period

    Coverage:
        - Geography: HK-wide
        - Time:      historical series, monthly

    Datasets:   hk-censtatd-tablechart-510-60004
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=510-60004&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = cpi()                      # list[dict]

    Questions:
        - "what is the current inflation rate?"
        - "Hong Kong CPI by year"

    Quirks:
        - needs a browser-like User-Agent
        - sv/svDesc distinguish index vs year-on-year % change
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=510-60004&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]


def gdp() -> list:
    """Gross Domestic Product (GDP), current + chained dollars, quarterly/annual.

    Provides:
        - GDP at current prices, chained (2023) dollars, deflator, per-capita
          GDP, and seasonally-adjusted q/q % change, by period

    Coverage:
        - Geography: HK-wide
        - Time:      historical series, quarterly (freq Q) + annual (freq Y)

    Datasets:   hk-censtatd-tablechart-310-31001
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=310-31001&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = gdp()                      # list[dict]
        >>> [r for r in rows if r["sv"] == "CON"]

    Questions:
        - "what is Hong Kong's GDP growth?"
        - "Hong Kong GDP by quarter"

    Quirks:
        - needs a browser-like User-Agent
        - sv codes: CUR (current), CON (chained), DEF (deflator), CURPGDP/CONPGDP
          (per-capita), SA1 (seasonally-adjusted q/q %)
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=310-31001&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]
