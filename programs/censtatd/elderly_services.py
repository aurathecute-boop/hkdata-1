"""Census and Statistics Department — elderly service statistics."""


def elderly_service_recipients() -> list:
    """Elderly service recipients across community support / care / residential.

    Provides:
        - number of elderly service recipients by service type
          (NEC, DECC, SCE, DE/DCU, home care, residential homes), annual + monthly

    Coverage:
        - Geography: HK-wide
        - Time:      historical series, annual + monthly

    Datasets:   hk-censtatd-tablechart-935-88005
    Department: Census and Statistics Department
    Endpoint:   https://www.censtatd.gov.hk/api/get.php?id=935-88005&lang=en&full_series=1
    Format:     JSON

    Usage:
        >>> rows = elderly_service_recipients() # list[dict]

    Questions:
        - "how many people use elderly home care services?"

    Quirks:
        - needs a browser-like User-Agent
        - these are RECIPIENT counts, not centre counts (see programs/swd/elderly_centres.py)
        - related tables: 935-88006 (community care), 935-88004 (residential)
    """
    import json
    import urllib.request

    url = ("https://www.censtatd.gov.hk/api/get.php"
           "?id=935-88005&lang=en&full_series=1")
    req = urllib.request.Request(
        url, headers={"User-Agent":
                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["dataSet"]
