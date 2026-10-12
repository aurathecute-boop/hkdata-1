"""Census and Statistics Department — education tables."""


def schools_by_type_region() -> list:
    """Number of day schools by type/sector and region, annual.

    Provides:
        - school counts by type (kindergarten / primary / secondary), sector,
          and region (HK Island / Kowloon / NT), annual from 2013

    Coverage:
        - Geography: HK Island, Kowloon, New Territories, total
        - Time:      historical series, annual

    Datasets:   hk-censtatd-tablechart-925-92023
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=925-92023&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = schools_by_type_region()   # list[dict]
        >>> [r for r in rows if r["period"] == "2024"]

    Questions:
        - "how many primary schools are in Hong Kong?"
        - "number of schools by type and region"

    Quirks:
        - needs a browser-like User-Agent
        - field TYPE_INS_SCHOOL / TYPE_INS_SCHOOLDesc = school type code/name
        - DC / DCDesc = region (HK/KLN/NT or empty for total)
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=925-92023&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]
