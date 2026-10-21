import sys
import csv
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())
try:
    sys.path.insert(0, str(ROOT))
    from paths import P4
except ImportError:
    P4 = ROOT / "participants" / "p4_pointz_skyteam"

OUT_DIR = P4 / "output"
INT_DIR = P4 / "intermediate"
INT_DIR.mkdir(parents=True, exist_ok=True)

def build_matches():
    pz_path = OUT_DIR / "pointz_flights.csv"
    st_path = OUT_DIR / "skyteam_exchange.csv"
    match_path = INT_DIR / "pointz_skyteam_matches.csv"

    pz_index = {}
    with open(pz_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["loyalty_id_normalized"], row["flight_date"], row["flight_number"])
            pz_index[key] = row

    matches_count = 0
    with open(st_path, "r", encoding="utf-8") as f_st, \
         open(match_path, "w", newline="", encoding="utf-8") as f_out:

        writer = csv.DictWriter(f_out, fieldnames=[
            "loyalty_id_normalized", "flight_date", "flight_number",
            "user_uid", "pointz_record_id", "skyteam_record_id",
            "origin_pointz", "origin_skyteam",
            "destination_pointz", "destination_skyteam",
            "fare_pointz", "fare_skyteam", "booking_class_skyteam",
            "route_matches", "fare_matches", "match_confidence"
        ])
        writer.writeheader()

        for row in csv.DictReader(f_st):
            key = (row["loyalty_id_normalized"], row["flight_date"], row["flight_number"])
            if key in pz_index:
                matches_count += 1
                pz_row = pz_index[key]
                r_match = (pz_row["origin_airport"] == row["origin_airport"]) and \
                          (pz_row["destination_airport"] == row["destination_airport"])
                f_match = (pz_row["fare_code"] == row["fare_code"])

                writer.writerow({
                    "loyalty_id_normalized": key[0],
                    "flight_date": key[1],
                    "flight_number": key[2],
                    "user_uid": pz_row["user_uid"],
                    "pointz_record_id": pz_row["source_record_id"],
                    "skyteam_record_id": row["source_record_id"],
                    "origin_pointz": pz_row["origin_airport_raw"],
                    "origin_skyteam": row["origin_airport_raw"],
                    "destination_pointz": pz_row["destination_airport_raw"],
                    "destination_skyteam": row["destination_airport_raw"],
                    "fare_pointz": pz_row["fare_code"],
                    "fare_skyteam": row["fare_code"],
                    "booking_class_skyteam": row["booking_class"],
                    "route_matches": r_match,
                    "fare_matches": f_match,
                    "match_confidence": "HIGH" if (r_match and f_match) else "MEDIUM"
                })

    print(f"[OK] pointz_skyteam_matches.csv: matches={matches_count}")

if __name__ == "__main__":
    build_matches()
