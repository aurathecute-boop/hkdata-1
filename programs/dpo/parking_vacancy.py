"""Digital Policy Office — live car-park vacancy (one-stop API)."""


def car_park_vacancy(extent: str, data: str = "info", lang: str = "en_US") -> dict:
    """Live off-street car-park info/vacancy inside a bounding box.

    Provides:
        - per car park: name, address, district, lat/long, opening status,
          height limits, contact, website (data="info")
        - live vacancy per vehicle type with last-update time (data="vacancy")

    Coverage:
        - Geography: 556 participating car parks territory-wide, by bounding box
        - Time:      real-time, refreshed per car park (~1–5 min)

    Datasets:   hk-dpo-datagovhk1-carpark-info-vacancy
    Department: Digital Policy Office (aggregates Transport Dept + DEVB)
    Endpoint:   https://api.data.gov.hk/v1/carpark-info-vacancy
    Format:     JSON

    Usage:
        >>> info = car_park_vacancy("114.14,22.32,114.18,22.35", data="info")
        >>> vac  = car_park_vacancy("114.14,22.32,114.18,22.35", data="vacancy")
        >>> info["results"]   # join with vac on park_Id

    Questions:
        - "is there parking near Mong Kok?"
        - "car park vacancy around [POI]"

    Quirks:
        - extent = "left_lon,bottom_lat,right_lon,top_lat" (bounding box)
        - vacancy_type: A=count, B=binary, C=0 (closed); vacancy -1 = no data
        - opening_status CLOSED may still report a vacancy figure — show both
        - response is {"results": [...]} (data.gov.hk v1 convention)
    """
    import json
    import urllib.parse
    import urllib.request

    params = {"data": data, "lang": lang, "extent": extent}
    url = ("https://api.data.gov.hk/v1/carpark-info-vacancy?"
           + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
