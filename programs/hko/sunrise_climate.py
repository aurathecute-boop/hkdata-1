"""Hong Kong Observatory — sunrise/sunset and climate."""


def sunrise_sunset(year: int) -> list:
    """Daily sunrise, sunset, and sun-transit times for a year.

    Provides:
        - date, sunrise, sun transit, and sunset times per day of ``year``

    Coverage:
        - Geography: HK (Observatory reference point)
        - Time:      full year, daily

    Datasets:   hk-hko-rss-times-of-sunrise-suntransit-sunset
    Department: Hong Kong Observatory
    Endpoint:   https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=SRS&year={year}&rformat=json
    Format:     JSON

    Usage:
        >>> rows = sunrise_sunset(2026)       # list[dict], one per day

    Questions:
        - "what time is sunrise tomorrow?"
        - "sunset times in October"

    Quirks:
        - rformat=csv also available
    """
    import json
    import urllib.request

    url = ("https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
           f"?dataType=SRS&year={int(year)}&rformat=json")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # SRS returns {"data": [...]} with date/sunrise/sunset/sun transit.
    return data.get("data", data)


def daily_temperature() -> list:
    """Daily max / mean / min air temperature at HKO headquarters, 1884–present.

    Provides:
        - daily maximum, mean, and minimum temperature (deg C) at the Observatory
          headquarters, from 1884

    Coverage:
        - Geography: HKO headquarters (the canonical "Hong Kong" series)
        - Time:      historical series, daily, updated monthly (~1 month lag)

    Datasets:   hk-hko-rss-daily-temperature-info-hko
    Department: Hong Kong Observatory
    Endpoint:   https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=CLMTEMP&rformat=csv&station=HKO
    Format:     CSV

    Usage:
        >>> rows = daily_temperature()        # list[dict]
        >>> [r for r in rows if r.get("月") == "10"]

    Questions:
        - "what was the average temperature in October 2023?"
        - "HKO monthly temperature history"

    Quirks:
        - UTF-8 BOM on the first header cell — decode utf-8-sig
        - "***" placeholders mark missing/old rows
        - column names are Chinese (年/月/日/數值); the value column holds max,
          mean, or min depending on the selected series (HKO = mean by default)
    """
    import csv
    import io
    import urllib.request

    url = ("https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
           "?dataType=CLMTEMP&rformat=csv&station=HKO")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))
