"""Census and Statistics Department — crime (persons arrested)."""


def persons_arrested() -> list:
    """Persons arrested for crime by offence type, age group and sex, annual.

    Provides:
        - number of persons arrested, broken down by offence type, age group,
          and sex, annual

    Coverage:
        - Geography: HK-wide (territory-wide only)
        - Time:      historical series, annual

    Datasets:   hk-censtatd-tablechart-940-92031
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=940-92031&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = persons_arrested()         # list[dict]

    Questions:
        - "how many people were arrested for theft last year?"
        - "crime arrests by age group"

    Quirks:
        - needs a browser-like User-Agent
        - no district-level breakdown exists on data.gov.hk
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=940-92031&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]
