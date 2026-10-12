"""Transport Department — KMB/LWB bus real-time data (raw endpoints)."""


def kmb_routes() -> list:
    """All KMB/LWB bus routes with named termini (raw route list).

    Provides:
        - route, bound (O=outbound/I=inbound), service_type, origin and
          destination names (en/tc/sc)

    Coverage:
        - Geography: all KMB/LWB routes
        - Time:      real-time reference data

    Datasets:   hk-td-tis_21-etakmb
    Department: Transport Department (data from KMB/LWB)
    Endpoint:   https://data.etabus.gov.hk/v1/transport/kmb/route/
    Format:     JSON

    Usage:
        >>> routes = kmb_routes()            # list[dict] (under ["data"])
        >>> [r for r in routes if "STAR FERRY" in (r.get("dest_en") or "")]

    Questions:
        - "which KMB routes go to Star Ferry?"
        - "list KMB routes"

    Quirks:
        - response wraps records under ["data"]
        - bound is O/I; the stop/eta endpoints use outbound/inbound instead
    """
    import json
    import urllib.request

    url = "https://data.etabus.gov.hk/v1/transport/kmb/route/"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def kmb_stop(stop_id: str) -> dict:
    """One KMB stop's name (en/tc/sc) and coordinates.

    Provides:
        - stop name (en/tc/sc), latitude, longitude

    Coverage:
        - Geography: all KMB/LWB stops
        - Time:      real-time reference data

    Datasets:   hk-td-tis_21-etakmb
    Department: Transport Department (data from KMB/LWB)
    Endpoint:   https://data.etabus.gov.hk/v1/transport/kmb/stop/{stop_id}
    Format:     JSON

    Usage:
        >>> stop = kmb_stop("18492910339410B1")

    Questions:
        - "what is the name of stop [id]?"

    Quirks:
        - stop IDs are alphanumeric (e.g. "18492910339410B1")
    """
    import json
    import urllib.request

    url = f"https://data.etabus.gov.hk/v1/transport/kmb/stop/{stop_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def kmb_eta(stop_id: str, route: str, service_type: int = 1) -> list:
    """Live KMB/LWB bus arrival times at a stop for a route.

    Provides:
        - live ETAs (ISO-8601 +08:00), remark (e.g. "Scheduled Bus"), and the
          feed's data_timestamp

    Coverage:
        - Geography: one stop × one route
        - Time:      real-time, updated continuously

    Datasets:   hk-td-tis_21-etakmb
    Department: Transport Department (data from KMB/LWB)
    Endpoint:   https://data.etabus.gov.hk/v1/transport/kmb/eta/{stop_id}/{route}/{service_type}
    Format:     JSON

    Usage:
        >>> etas = kmb_eta("18492910339410B1", "1")   # list of {eta, rmk_en, ...}

    Questions:
        - "when is the next KMB bus at stop X?"
        - "live bus arrival time"

    Quirks:
        - rmk_en "Scheduled Bus" = no live GPS; data_timestamp = feed generated
        - eta is ISO-8601 in +08:00 (HKT)
    """
    import json
    import urllib.request

    url = (f"https://data.etabus.gov.hk/v1/transport/kmb/eta/"
           f"{stop_id}/{route}/{int(service_type)}")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]
