"""Digital Policy Office — public holidays (1823)."""


def public_holidays() -> list:
    """Hong Kong public holidays (dates + names), 2024–2026.

    Provides:
        - holiday date (YYYYMMDD) and name

    Coverage:
        - Geography: HK-wide
        - Time:      static yearly files covering 2024, 2025, 2026

    Datasets:   hk-dpo-statistic-cal
    Department: Digital Policy Office (1823 Contact Centre)
    Endpoint:   https://www.1823.gov.hk/common/ical/en.json
    Format:     JSON (iCalendar)

    Usage:
        >>> holidays = public_holidays()      # list[{"date","name"}]
        >>> [h for h in holidays if h["date"].startswith("2026")]

    Questions:
        - "when is the next public holiday?"
        - "list Hong Kong public holidays this year"

    Quirks:
        - iCalendar JSON; events under vcalendar[0].vevent
        - date is YYYYMMDD (dtstart[0]); name is summary
        - Chinese: /tc.json or /sc.json
    """
    import json
    import urllib.request

    url = "https://www.1823.gov.hk/common/ical/en.json"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8-sig"))
    events = data["vcalendar"][0]["vevent"]
    return [{"date": e["dtstart"][0], "name": e["summary"]} for e in events]
