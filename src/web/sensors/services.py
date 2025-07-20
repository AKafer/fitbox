import io

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from database.models import Sprints


def build_sprint_hits_excel(slot_id: int, sprint_id: int, sprints: list[Sprints]) -> bytes:
    wb = Workbook()
    summary_ws = wb.active
    summary_ws.title = "summary"

    devices_hits = {}
    for sp in sprints:
        device = sp.sensor_id or "UNKNOWN"
        hits = []
        if isinstance(sp.data, dict):
            raw_hits = sp.data.get('hits', [])
            if isinstance(raw_hits, list):
                hits = raw_hits
        devices_hits[device] = hits

    summary_ws.append(["Slot ID", slot_id])
    summary_ws.append(["Sprint ID", sprint_id])
    summary_ws.append([])
    summary_ws.append(["Device", "Hits Count"])
    total_all = 0
    for device, hits in devices_hits.items():
        summary_ws.append([device, len(hits)])
        total_all += len(hits)
    summary_ws.append([])
    summary_ws.append(["TOTAL", total_all])

    _auto_width(summary_ws)

    for device, hits in devices_hits.items():
        sheet_name = device[:31]
        ws = wb.create_sheet(title=sheet_name)

        all_keys = set()
        for h in hits:
            if isinstance(h, dict):
                all_keys.update(h.keys())

        if not all_keys:
            columns = ["raw"]
        else:
            preferred = ["timeMs", "maxAccel"]
            rest = sorted(k for k in all_keys if k not in preferred)
            columns = [k for k in preferred if k in all_keys] + rest

        ws.append(["#", *columns])

        for idx, h in enumerate(hits, start=1):
            if isinstance(h, dict):
                row = [h.get(k) for k in columns]
            else:
                row = [str(h)]
            ws.append([idx, *row])

        _auto_width(ws)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _auto_width(ws):
    for col in ws.columns:
        max_len = 0
        letter = get_column_letter(col[0].column)
        for cell in col:
            v = cell.value
            if v is None:
                continue
            ln = len(str(v))
            if ln > max_len:
                max_len = ln
        ws.column_dimensions[letter].width = min(max_len + 2, 60)
