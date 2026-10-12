"""Government Property Agency car-park inventory."""


def government_car_parks() -> list:
    """Government car parks open for public use, with spaces and EV chargers.

    Provides:
        - car park name, district, address, vehicle type, size
        - height restriction, opening hours, EV charger count, parking fees

    Coverage:
        - Geography: HK-wide (GPA-managed car parks)
        - Time:      static inventory, updated as changes occur

    Datasets:   hk-gpa-msd-gpa-psi-t-cp
    Department: Government Property Agency
    Endpoint:   https://www.gpa.gov.hk/doc/psi/ds/psi-t-cp_ENG.json
    Format:     JSON

    Usage:
        >>> parks = government_car_parks()        # list[dict]
        >>> [p for p in parks if p.get("District") == "Sham Shui Po"]

    Questions:
        - "is there a government car park near Mong Kok?"
        - "which car parks have EV chargers?"

    Quirks:
        - JSON may carry a UTF-8 BOM and raw control characters; parse with
          utf-8-sig + strict=False
        - some car parks are night-time only on weekdays, 24h on weekends
        - CSV variant: psi-t-cp_ENG.csv; TC/SC via _TC / _SC
    """
    import json
    import urllib.request

    url = "https://www.gpa.gov.hk/doc/psi/ds/psi-t-cp_ENG.json"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")  # BOM-safe
        return json.loads(text, strict=False)   # tolerates control chars
