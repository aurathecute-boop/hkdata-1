"""Hong Kong Observatory — current weather and forecasts."""


def current_weather() -> dict:
    """Current weather report: temperature, humidity, rainfall by station.

    Provides:
        - current temperature, humidity, rainfall at HKO stations
        - weather icons and text descriptions

    Coverage:
        - Geography: HK-wide (multiple stations)
        - Time:      real-time, updated every ~10 minutes

    Datasets:   hk-hko-weather-current (rhrread)
    Department: Hong Kong Observatory
    Endpoint:   https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en
    Format:     JSON

    Usage:
        >>> w = current_weather()
        >>> w["temperature"]["data"]

    Questions:
        - "what is the temperature now in Hong Kong?"
        - "current humidity and rainfall"

    Quirks:
        - temperature/rainfall/humidity are nested under {"data": [...]}
        - Chinese: lang=tc (Traditional) / sc (Simplified)
    """
    import json
    import urllib.request

    url = ("https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
           "?dataType=rhrread&lang=en")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def nine_day_forecast() -> dict:
    """9-day weather forecast from the Hong Kong Observatory.

    Provides:
        - forecast min/max temperature, humidity, weather text per day

    Coverage:
        - Geography: HK-wide
        - Time:      forecast, 9 days ahead

    Datasets:   hk-hko-weather-forecast (fnd)
    Department: Hong Kong Observatory
    Endpoint:   https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en
    Format:     JSON

    Usage:
        >>> f = nine_day_forecast()
        >>> f["weatherForecast"]

    Questions:
        - "what is the weather forecast for next week?"
        - "9-day weather forecast"

    Quirks:
        - forecast rows under weatherForecast[]
    """
    import json
    import urllib.request

    url = ("https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
           "?dataType=fnd&lang=en")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def weather_warnings() -> dict:
    """Current weather warnings summary (tropical cyclone, rainstorm, etc.).

    Provides:
        - active weather warnings and their codes/descriptions

    Coverage:
        - Geography: HK-wide
        - Time:      real-time

    Datasets:   hk-hko-weather-warning (warnsum)
    Department: Hong Kong Observatory
    Endpoint:   https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=warnsum&lang=en
    Format:     JSON

    Usage:
        >>> w = weather_warnings()
        >>> w["details"]

    Questions:
        - "is there a typhoon signal now?"
        - "current weather warnings"

    Quirks:
        - warning details under "details"
    """
    import json
    import urllib.request

    url = ("https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
           "?dataType=warnsum&lang=en")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
