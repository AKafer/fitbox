#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for c in df.columns:
        k = str(c).strip().lower().replace(" ", "").replace("_", "")
        if k in ("timems", "time", "t", "ms"):
            rename_map[c] = "timeMs"
        elif k in ("maxaccel", "accel", "a", "maxa"):
            rename_map[c] = "maxAccel"
    return df.rename(columns=rename_map) if rename_map else df


def to_hits(df: pd.DataFrame) -> List[Dict]:
    if not {"timeMs", "maxAccel"}.issubset(df.columns):
        raise ValueError(
            f"Нет нужных колонок. Есть: {list(df.columns)}; нужны: ['timeMs','maxAccel']"
        )
    df = df[["timeMs", "maxAccel"]].copy()
    df["timeMs"] = pd.to_numeric(df["timeMs"], errors="coerce").astype("Int64")
    df["maxAccel"] = pd.to_numeric(df["maxAccel"], errors="coerce")
    df = df.dropna(subset=["timeMs", "maxAccel"])
    df["timeMs"] = df["timeMs"].astype(int)
    df["maxAccel"] = df["maxAccel"].astype(float)
    return [{"timeMs": int(t), "maxAccel": float(a)} for t, a in df.to_records(index=False)]


def main():
    ap = argparse.ArgumentParser(description="Extract hits from Excel sheet to JSON.")
    ap.add_argument("-f", "--file", required=True, help="Путь к .xlsx")
    ap.add_argument("-s", "--sheet", required=True, help="Имя листа (например, BAG02)")
    args = ap.parse_args()

    try:
        df = pd.read_excel(args.file, sheet_name=args.sheet)
        df = normalize_cols(df)
        hits = to_hits(df)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    payload = {"hits": hits}
    output_json = json.dumps(payload, ensure_ascii=False, indent=2)

    print(output_json)
    try:
        try:
            script_dir = Path(__file__).resolve().parent
        except NameError:
            script_dir = Path.cwd()  # на всякий случай (если __file__ недоступен)
        out_path = script_dir / "res.txt"
        out_path.write_text(output_json + "\n", encoding="utf-8")
    except Exception as e:
        print(f"Не удалось записать res.txt: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
