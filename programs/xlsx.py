"""XLSX / XLS workbooks from data.gov.hk — read them without hand-rolling zip+XML.

1,397 of the ~3,822 catalog datasets publish a spreadsheet instead of JSON/CSV
(the C&SD census tables, CEDD expenditure, 28Hse, ...). The engine's ``test``
command can only report them as a binary resource, so these two functions are
the way in.
"""


def xlsx_rows(url, sheet=0, header=0) -> list:
    """Rows of one worksheet, as JSON-ready dicts.

    Provides:
        - one dict per data row, keys = the header row's cell values
        - the whole sheet (no pagination) — government workbooks are small
        - numeric cells as numbers, empty cells as ``None`` (never ``NaN``)

    Coverage:
        - Geography: whatever the workbook covers (usually HK-wide)
        - Time:      whatever edition the URL points at (the file is static)

    Datasets:   any — 1400+ catalog datasets ship XLSX/XLS, e.g.
                hk-cedd-csu-cedd-asd-2526 (CEDD departmental expenditure)
    Department: cross-department (XLSX is the default export for C&SD, CEDD,
                Census tables, 28Hse property data, ...)
    Endpoint:   the resource URL itself, e.g.
                https://www.cedd.gov.hk/datagovhk/CEDD_Dept_Expenditure_2025-26%20(Eng).xlsx
    Format:     XLSX / XLSM / XLS

    Usage:
        >>> rows = xlsx_rows("https://www.cedd.gov.hk/datagovhk/CEDD_Dept_Expenditure_2025-26%20(Eng).xlsx")
        >>> rows[0]
        {'Code': '...', 'Item': '...', ...}
        >>> xlsx_rows(url, sheet="Table 1", header=3)   # skip title rows

    Questions:
        - "read this XLSX dataset" / "open the spreadsheet resource"
        - "what is in the census Excel table?"
        - "departmental expenditure spreadsheet rows"

    Quirks:
        - most government workbooks put 2–5 title/notes rows above the header;
          inspect with ``xlsx_preview`` then pass ``header=<n>``
        - ``sheet`` accepts an index or a sheet name
        - reads the bytes through pandas + openpyxl (no temp file, no unzip)
        - some publishers use legacy ``.xls``; pandas needs ``xlrd`` for those,
          so prefer the ``.xlsx`` resource when a dataset offers both
    """
    import io

    import pandas as pd
    import requests

    resp = requests.get(url, headers={"User-Agent": "curl/8.0"}, timeout=60)
    resp.raise_for_status()
    frame = pd.read_excel(io.BytesIO(resp.content), sheet_name=sheet,
                          header=header, engine="openpyxl")
    frame.columns = [str(col).strip() for col in frame.columns]
    frame = frame.where(pd.notna(frame), None)
    return frame.to_dict(orient="records")


def xlsx_preview(url, rows=8) -> dict:
    """Sheet names + the first rows of a workbook, before you pick a header row.

    Provides:
        - ``sheets``: every worksheet name in the workbook
        - ``shape``: (rows, columns) of the first sheet, read with no header
        - ``rows``: the first ``rows`` grid rows, raw (lists), ``None`` for blanks

    Coverage:
        - Geography: n/a (structure of one workbook)
        - Time:      the edition at that URL

    Datasets:   any — the 1400+ XLSX/XLS resources in the catalog
    Department: cross-department
    Endpoint:   the resource URL itself
    Format:     XLSX / XLSM / XLS

    Usage:
        >>> info = xlsx_preview(url)
        >>> info["sheets"]              # ['Table 1', 'Notes']
        >>> info["rows"][:3]            # title rows, then the header row

    Questions:
        - "what sheets does this Excel file have?"
        - "where is the header row in this spreadsheet?"
        - "preview the xlsx before parsing"

    Quirks:
        - reads every sheet to list names, but only previews the first one
        - use the header row index it reveals with ``xlsx_rows(url, header=n)``
    """
    import io

    import pandas as pd
    import requests

    resp = requests.get(url, headers={"User-Agent": "curl/8.0"}, timeout=60)
    resp.raise_for_status()
    book = pd.read_excel(io.BytesIO(resp.content), sheet_name=None,
                         header=None, engine="openpyxl")
    first = next(iter(book.values()), None)
    head = []
    if first is not None:
        for grid_row in first.head(rows).itertuples(index=False):
            head.append([None if pd.isna(cell) else cell for cell in grid_row])
    return {
        "sheets": list(book),
        "shape": list(first.shape) if first is not None else [0, 0],
        "rows": head,
    }
