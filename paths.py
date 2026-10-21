"""Пути проекта. Все скрипты берут папки отсюда, чтобы структуру можно было менять в одном месте."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent

RAW = ROOT / "data" / "raw"

PARTICIPANTS = ROOT / "participants"
P1 = PARTICIPANTS / "p1_timetable"
P2 = PARTICIPANTS / "p2_forum_boarding"
P3 = PARTICIPANTS / "p3_sirena_boarding_passes"
P4 = PARTICIPANTS / "p4_pointz_skyteam"
PARTICIPANT_OUTPUTS = [P1 / "output", P3 / "output", P4 / "output"]

P2_PROCESSED = P2 / "output" / "processed"
P2_CSV = P2_PROCESSED / "csv"
P2_ANOMALIES = P2 / "intermediate" / "anomalies"
P2_HANDOFF = P2 / "intermediate" / "integration_handoff"
P2_SAMPLES = P2 / "samples"
P2_REPORTS = P2 / "reports"

TIMETABLE = P1 / "output" / "timetable_unique.csv"

MERGED = ROOT / "integration" / "merged"
PASSENGERS_ALL = MERGED / "passengers_all.parquet"
FLIGHTS_ALL = MERGED / "flights_all"
RESOLVED = ROOT / "integration" / "resolved"
INT_SAMPLES = ROOT / "integration" / "samples"
INT_REPORTS = ROOT / "integration" / "reports"

ANALYSIS_OUT = ROOT / "analysis" / "output"
ANALYSIS_REPORTS = ROOT / "analysis" / "reports"

FLIGHT_PARTS = ["1_forum", "2_boarding_data", "3_sirena", "4_boarding_passes", "5_pointz", "6_skyteam"]


def read_flights_all(columns=None):
    parts = [FLIGHTS_ALL / f"{p}.parquet" for p in FLIGHT_PARTS if (FLIGHTS_ALL / f"{p}.parquet").exists()]
    if not parts:
        raise FileNotFoundError(f"нет частей flights_all в {FLIGHTS_ALL}")
    return pd.concat([pd.read_parquet(p, columns=columns) for p in parts], ignore_index=True)
