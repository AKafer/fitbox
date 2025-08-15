import io

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from constants import KOEF_POWER, TEMPO_BORDER_PERCENT, DEGREE_POWER
from database.models import Sprints


def build_sprint_hits_excel(
    slot_id: int, sprint_id: int, sprints: list[Sprints]
) -> bytes:
    wb = Workbook()
    summary_ws = wb.active
    summary_ws.title = 'summary'

    devices_hits = {}
    for sp in sprints:
        device = sp.sensor_id or 'UNKNOWN'
        hits = []
        if isinstance(sp.data, dict):
            raw_hits = sp.data.get('hits', [])
            if isinstance(raw_hits, list):
                hits = raw_hits
        devices_hits[device] = hits

    summary_ws.append(['Slot ID', slot_id])
    summary_ws.append(['Sprint ID', sprint_id])
    summary_ws.append([])
    summary_ws.append(['Device', 'Hits Count'])
    total_all = 0
    for device, hits in devices_hits.items():
        summary_ws.append([device, len(hits)])
        total_all += len(hits)
    summary_ws.append([])
    summary_ws.append(['TOTAL', total_all])

    _auto_width(summary_ws)

    for device, hits in devices_hits.items():
        sheet_name = device[:31]
        ws = wb.create_sheet(title=sheet_name)

        all_keys = set()
        for h in hits:
            if isinstance(h, dict):
                all_keys.update(h.keys())

        if not all_keys:
            columns = ['raw']
        else:
            preferred = ['timeMs', 'maxAccel']
            rest = sorted(k for k in all_keys if k not in preferred)
            columns = [k for k in preferred if k in all_keys] + rest

        ws.append(['#', *columns])

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


def is_synced_hit(time_ms: int, blink_interval: float) -> bool:
    if time_ms is None or blink_interval <= 0:
        return False
    k = round(time_ms / blink_interval)
    nearest = k * blink_interval
    return abs(time_ms - nearest) <= blink_interval * TEMPO_BORDER_PERCENT


def calculate_sprint_metrics(
    hits: list, blink_interval: float, hit_count: int
) -> dict:
    if not hits or hit_count == 0:
        return {}
    max_punch = max(float(hit.get('maxAccel', 0)) for hit in hits)
    sum_punches = sum(float(hit.get('maxAccel', 0)) for hit in hits)
    average_punch = sum_punches / hit_count if hit_count > 0 else 0
    power = (average_punch / max_punch) * KOEF_POWER if max_punch > 0 else 0
    synced_hits = 0
    for hit in hits:
        time_ms = hit.get('timeMs')
        if time_ms is not None:
            if is_synced_hit(int(time_ms), blink_interval):
                synced_hits += 1
    tempo = synced_hits / hit_count * 100 if blink_interval > 0 else 0
    energy = tempo * (power / KOEF_POWER) ** DEGREE_POWER
    return {'tempo': tempo, 'power': power, 'energy': energy}
