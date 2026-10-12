"""Census and Statistics Department — tourism arrivals."""


def visitor_arrivals() -> list:
    """Monthly visitor arrivals to Hong Kong by nationality/region.

    Provides:
        - visitor arrivals by region of residence (Mainland, Americas, Europe,
          Africa, etc.), monthly from 2004

    Coverage:
        - Geography: by source region (not HK district)
        - Time:      historical series, monthly (YYYYMM)

    Datasets:   hk-censtatd-tablechart-650-80001
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=650-80001&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = visitor_arrivals()         # list[dict]
        >>> [r for r in rows if r["REGION"] == "CN"]

    Questions:
        - "how many Mainland visitors came last month?"
        - "visitor arrivals by region"

    Quirks:
        - needs a browser-like User-Agent
        - REGION uses short codes (CN=Mainland, AM, EU, ...); REGIONDesc has names
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=650-80001&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]
