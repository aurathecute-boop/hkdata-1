"""Housing Authority public rental housing eligibility limits."""


def prh_income_asset_limits() -> list:
    """PRH application income and asset limits by household size.

    Provides:
        - monthly income limit and asset limit per household size/type

    Coverage:
        - Geography: HK-wide eligibility criteria
        - Time:      annual, updated when the Housing Authority reviews limits

    Datasets:   hk-housing-aas-prhicaslmt
    Department: Hong Kong Housing Authority
    Endpoint:   https://data.housingauthority.gov.hk/dataset/prhicaslmt/prh_income_asset_limit_en.json
    Format:     JSON

    Usage:
        >>> limits = prh_income_asset_limits()    # list[dict], 29 household types
        >>> limits[0]
        {'type': ..., 'family_household_size': ..., 'income_limit_per_mth': ...,
         'net_asset_limit': ..., 'effective_from': ...}

    Questions:
        - "what is the PRH income limit for a 4-person household?"
        - "public housing asset limit this year"

    Quirks:
        - covers both income and asset limits, broken down by household size
        - Traditional Chinese: .../prh_income_asset_limit_tc.json
    """
    import json
    import urllib.request

    url = ("https://data.housingauthority.gov.hk/dataset/prhicaslmt/"
           "prh_income_asset_limit_en.json")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["records"]
