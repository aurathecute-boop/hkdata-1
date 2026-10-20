"""Hospital Authority — Accident & Emergency (A&E) waiting time."""


def ae_waiting_time(hospitals=None, with_district=True) -> list:
    """Current A&E waiting time for every Hospital Authority hospital.

    Provides (per hospital):
        - triage wait bands as published by HA: T1 (critical), T2 (emergency),
          T3 (urgent) median + 95th percentile, T4/T5 (semi-urgent +
          non-urgent) median + 95th percentile
        - the raw text exactly as HA publishes it (e.g. "少於 15 分鐘")
        - parsed minutes for the numeric bands (t3_median_min, t3_p95_min,
          t45_median_min, t45_p95_min) — None when HA publishes no number
        - "manage_t1" / "manage_t2" flags (Y / N / N/A)
        - HA hospital cluster, street address, coordinates, and the
          18-district name (resolved from the address)
        - "update_time": the feed's own as-at timestamp (HKT)

    Coverage:
        - Geography: HK-wide — the 18 hospitals with an A&E department
        - Time:      real-time, refreshed every 15 minutes

    Datasets:   hospital-hadata-ae-waiting-time, hospital-hadata-health-care-facilities
    Department: Hospital Authority
    Endpoint:   https://www.ha.org.hk/opendata/aed/aedwtdata2-en.json
                https://www.ha.org.hk/opendata/aed/aedwtdata2-tc.json
                https://www.ha.org.hk/opendata/facility-hosp.json
    Format:     JSON

    Usage:
        >>> rows = ae_waiting_time()
        >>> rows[0]["hospital"], rows[0]["district"], rows[0]["t3_median"]
        ('伊利沙伯醫院', '油尖旺區', '12 分鐘')
        >>> rows = ae_waiting_time(hospitals=["伊利沙伯醫院"], with_district=False)

    Questions:
        - "current A&E waiting time at public hospitals in Hong Kong"
        - "how long do I wait in A&E in Kwun Tong right now"
        - "A&E waiting time for the four Kowloon districts with emergency departments"
        - "急症室輪候時間" / "急症室排隊" / "急症室等幾耐"
        - "which hospital has the longest A&E wait for urgent cases"

    Quirks:
        - T1/T2 are published as text ("0 分鐘", "少於 15 分鐘", or
          "多名病人正在搶救中" when resuscitation is in progress) — there is no
          numeric field for them
        - T3 waits are in MINUTES; T4/T5 waits are in HOURS rounded up to the
          next 0.5 hour — t45_median_min converts them to minutes
        - "0 分鐘" for T1/T2 means no queue at that moment, not a zero wait
        - manage_t1 / manage_t2 = "是" means HA is managing that patient's
          case (e.g. via a fast-track / bypass), "不適用" when N/A
        - district comes from the Lands Department ALS lookup of the hospital
          name, snapped to the HA facility coordinates; it is None when the
          lookup fails
        - the 18 rows are the HA hospitals with an A&E department; hospitals
          such as 葵涌急症科醫院 and 聖德肋撒醫院 are not in this feed
    """
    import math
    import urllib.parse

    import requests

    def get_json(url, headers=None):
        merged = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                "10_15_7)"}
        merged.update(headers or {})
        resp = requests.get(url, headers=merged, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def to_minutes(text):
        if not text:
            return None
        t = text.replace(" ", "")
        if "分鐘" in t:
            try:
                return int(float(t.replace("分鐘", "").replace("少於", "")))
            except ValueError:
                return None
        if "小時" in t:
            try:
                return int(round(float(t.replace("小時", "")) * 60))
            except ValueError:
                return None
        return None

    def geocode_district(name, lat, lon):
        url = ("https://www.als.gov.hk/lookup?q="
               + urllib.parse.quote(name))
        try:
            data = get_json(url, {"Accept": "application/json",
                                  "User-Agent": "Mozilla/5.0"})
        except Exception:
            return None
        best = None
        for item in data.get("SuggestedAddress") or []:
            addr = item.get("Address", {}).get("PremisesAddress", {})
            chi = addr.get("ChiPremisesAddress", {})
            eng = addr.get("EngPremisesAddress", {})
            district = ((chi.get("ChiDistrict") or {}).get("DcDistrict")
                        or (eng.get("EngDistrict") or {}).get("DcDistrict"))
            geo = addr.get("GeospatialInformation", {})
            try:
                dlat = float(geo.get("Latitude"))
                dlon = float(geo.get("Longitude"))
            except (TypeError, ValueError):
                continue
            if lat is None:
                return district
            dist = math.hypot((dlat - lat) * 111.0,
                              (dlon - lon) * 102.0)
            if dist <= 1.5 and (best is None or dist < best[0]):
                best = (dist, district)
        return best[1] if best else None

    wait_en = get_json("https://www.ha.org.hk/opendata/aed/aedwtdata2-en.json")
    wait_tc = get_json("https://www.ha.org.hk/opendata/aed/aedwtdata2-tc.json")
    facilities = get_json(
        "https://www.ha.org.hk/opendata/facility-hosp.json")

    wait_en_rows = wait_en.get("waitTime", [])
    fac_by_tc = {r["institution_tc"]: r for r in facilities}
    update_time = wait_tc.get("updateTime") or wait_en.get("updateTime")

    rows = []
    for idx, rec in enumerate(wait_tc.get("waitTime", [])):
        name_tc = rec["hospName"]
        en = wait_en_rows[idx] if idx < len(wait_en_rows) else {}
        name_en = en.get("hospName")
        if hospitals and name_tc not in hospitals and name_en not in hospitals:
            continue
        fac = fac_by_tc.get(name_tc, {})
        lat, lon = fac.get("latitude"), fac.get("longitude")
        row = {
            "hospital": name_tc,
            "hospital_en": name_en,
            "cluster": fac.get("cluster_tc"),
            "address": fac.get("address_tc"),
            "lat": lat,
            "lon": lon,
            "t1": rec.get("t1wt"),
            "t2": rec.get("t2wt"),
            "t3_median": rec.get("t3p50"),
            "t3_p95": rec.get("t3p95"),
            "t45_median": rec.get("t45p50"),
            "t45_p95": rec.get("t45p95"),
            "t3_median_min": to_minutes(rec.get("t3p50")),
            "t3_p95_min": to_minutes(rec.get("t3p95")),
            "t45_median_min": to_minutes(rec.get("t45p50")),
            "t45_p95_min": to_minutes(rec.get("t45p95")),
            "manage_t1": rec.get("manageT1case"),
            "manage_t2": rec.get("manageT2case"),
            "update_time": update_time,
        }
        if with_district:
            row["district"] = geocode_district(name_tc, lat, lon)
        rows.append(row)
    return rows


def ha_hospitals(ae_only=False) -> list:
    """Hospital Authority hospitals and institutions with cluster and address.

    Provides:
        - institution name (en/tc), HA hospital cluster, street address,
          latitude/longitude, and whether the hospital runs an A&E department
        - 44 institutions in total; 18 of them run an A&E department

    Coverage:
        - Geography: HK-wide
        - Time:      static institution list (updated periodically by HA)

    Datasets:   hospital-hadata-health-care-facilities
    Department: Hospital Authority
    Endpoint:   https://www.ha.org.hk/opendata/facility-hosp.json
    Format:     JSON

    Usage:
        >>> rows = ha_hospitals(ae_only=True)
        >>> rows[0]["institution_tc"], rows[0]["cluster_tc"]
        ('伊利沙伯醫院', '九龍中醫院聯網')

    Questions:
        - "which hospitals have an A&E department?"
        - "which HA cluster does [hospital] belong to"
        - "hospital address and coordinates in Hong Kong"
        - "醫院聯網 急症科醫院 名單"

    Quirks:
        - "葵涌急症科醫院" and other standalone A&E units are not separate
          rows; 葵涌醫院 itself carries with_AE_service = 否
        - the file mixes Hong Kong and New Territories clusters — use
          "address_tc" (not the cluster) to decide the 18-district
    """
    import json
    import urllib.request

    url = "https://www.ha.org.hk/opendata/facility-hosp.json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = json.loads(resp.read().decode("utf-8"))
    if ae_only:
        rows = [r for r in rows if r.get("with_AE_service_tc") == "是"]
    return rows
