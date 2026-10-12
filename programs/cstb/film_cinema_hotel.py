"""Culture, Sports and Tourism Bureau — cinemas and film."""


def cinemas() -> list:
    """Hong Kong cinema inventory: name, address, screens, seats, coordinates.

    Provides:
        - cinema name (en/tc/sc), address, screen count, seat count, website,
          contact, WGS84 + HK1980 coordinates, last-update date

    Coverage:
        - Geography: HK-wide (~60 cinemas)
        - Time:      static inventory, updated quarterly

    Datasets:   hk-cstb-cstb_ccida-hkcinemas
    Department: Culture, Sports and Tourism Bureau (Create Hong Kong)
    Endpoint:   https://www.ccidahk.gov.hk/data/hkcinemas.csv
    Format:     CSV

    Usage:
        >>> rows = cinemas()                  # list[dict]
        >>> [c for c in rows if "Mong" in (c.get("Name_EN") or "")]

    Questions:
        - "what cinemas are in Mong Kok?"
        - "largest cinema by seats"

    Quirks:
        - UTF-8 with BOM — decode utf-8-sig
    """
    import csv
    import io
    import urllib.request

    url = "https://www.ccidahk.gov.hk/data/hkcinemas.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def film_boxoffice() -> list:
    """Hong Kong box office revenue for Film Development Fund projects.

    Provides:
        - film title (en/tc/sc), funding scheme, HK box office (HK$),
          last-update date

    Coverage:
        - Geography: HK-wide (FDF-funded films only)
        - Time:      updated quarterly

    Datasets:   hk-cstb-cstb_ccida-hkboxoffice-for-fdf-projects
    Department: Culture, Sports and Tourism Bureau (Create Hong Kong)
    Endpoint:   https://www.ccidahk.gov.hk/data/hkboxoffice_FDF_projects.csv
    Format:     CSV

    Usage:
        >>> rows = film_boxoffice()           # list[dict]

    Questions:
        - "what is the box office of FDF-funded films?"
        - "top grossing government-funded film"

    Quirks:
        - only FDF-funded films, not the whole HK box office
        - cross-reference film_fund_projects() for funding amount vs box office
    """
    import csv
    import io
    import urllib.request

    url = "https://www.ccidahk.gov.hk/data/hkboxoffice_FDF_projects.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def film_fund_projects() -> list:
    """Film Development Fund approved projects (funding amount, since 2009).

    Provides:
        - film title (en/tc/sc), applicant company, approval date, funded amount

    Coverage:
        - Geography: HK-wide
        - Time:      quarterly, historical back to June 2009

    Datasets:   hk-cstb-cstb_ccida-approved-projects-funded-under-fdf
    Department: Culture, Sports and Tourism Bureau (Create Hong Kong)
    Endpoint:   https://www.ccidahk.gov.hk/data/FDF_approved_projects_FPF_FPG.csv
    Format:     CSV

    Usage:
        >>> rows = film_fund_projects()       # list[dict]

    Questions:
        - "how much did the Film Development Fund approve?"
        - "FDF approved projects list"

    Quirks:
        - FPF/FPG standard grant ~$9,000,000 per film
        - other schemes: FDF_approved_projects_Others.csv
    """
    import csv
    import io
    import urllib.request

    url = "https://www.ccidahk.gov.hk/data/FDF_approved_projects_FPF_FPG.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def hotel_occupancy() -> list:
    """Hotel room occupancy rate (%), monthly + annual, past 5 years.

    Provides:
        - monthly and annual hotel room occupancy rate (%) by hotel class

    Coverage:
        - Geography: HK-wide
        - Time:      historical series, monthly (past 5 years)

    Datasets:   hk-cstb-cstb_tc-tc-hotel-room-occupancy-rate
    Department: Culture, Sports and Tourism Bureau (data from HK Tourism Board)
    Endpoint:   https://www.tourism.gov.hk/datagovhk/hotelroomoccupancy/hotel_room_occupancy_rate_monthly_en.csv
    Format:     CSV

    Usage:
        >>> rows = hotel_occupancy()          # list[dict]

    Questions:
        - "what was the hotel occupancy rate last month?"
        - "hotel occupancy trend"

    Quirks:
        - hosted on tourism.gov.hk (metadata on data.gov.hk)
        - annual variant: hotel_room_occupancy_rate_yearly_en.csv
    """
    import csv
    import io
    import urllib.request

    url = ("https://www.tourism.gov.hk/datagovhk/hotelroomoccupancy/"
           "hotel_room_occupancy_rate_monthly_en.csv")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))
