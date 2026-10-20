"""Template for a program function — copy this skeleton into a new file.

A program is a **single runnable function** whose docstring is both the retrieval
surface (what gets embedded) and the reading surface (what an agent reads to call
it). The docstring must lead with *what the data provides*, not what the function
is called.

Contract
--------
- One function = one capability. Group related functions in one file under the
  right ``programs/<org>/`` subpackage.
- Functions return JSON-serializable data (dict / list / scalar). **Never print**
  inside a library function.
- Imports go *inside* the function, and helpers/constants in this file are
  inlined by ``reindex`` — so never import another ``programs/`` module.
- Use the mainstream library, not a hand-rolled parser: ``requests`` for HTTP,
  ``pandas`` for CSV/XLSX/joins, ``lxml.html`` for scraped tables,
  ``feedparser`` for RSS. The source runs in the skill venv (Python 3.11+).
- The docstring uses the section fields below. ``Provides`` / ``Coverage`` /
  ``Questions`` are the most important — ``Questions`` is the retrieval aid that
  lets a reworded query still hit this function.

Fields
------
:Provides:    what fields/tables the data returns (units, example values)
:Coverage:    geography + temporality (real-time / historical / static)
:Datasets:    data.gov.hk dataset ID(s) — or ``none`` when the data comes
              from a department's own web app instead of an open dataset
              (then say so: "none — scraped from <dept> web app")
:Department:  source department/org
:Endpoint:    endpoint URL(s)
:Format:      JSON / XML / CSV / RSS / HTML (scraped)
:Usage:       a doctest-style example of calling it and the shape of the result
:Questions:   natural-language questions this answers
:Quirks:      encoding / auth / direction / join-key gotchas

Example (copied verbatim, then edited)::

    def fitness_rooms() -> list:
        \"\"\"HK-wide fitness (gym) rooms and their real-time status.

        Provides:
            - room name (en/tc), district, address, phone
            - real-time status: open / temporarily closed, with reason

        Coverage:
            - Geography: HK-wide, by district
            - Time:      real-time feed, refreshed sub-daily

        Datasets:   hk-lcsd-facility-facility-fit
        Department: Leisure and Cultural Services Department
        Endpoint:   https://www.lcsd.gov.hk/datagovhk/facility/facility-fitrm.json
        Format:     JSON

        Usage:
            >>> rooms = fitness_rooms()
            >>> rooms[0]
            {'name': '...', 'district': '...', 'status': 'open'}

        Questions:
            - "is there a fitness room near Cheung Sha Wan?"
            - "gym room availability by district"

        Quirks:
            - status field is 'status'; closed rooms carry a 'reason'
        \"\"\"
        import json
        import urllib.request

        url = "https://www.lcsd.gov.hk/datagovhk/facility/facility-fitrm.json"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
"""
