import sys
import yaml
import csv
import re
from pathlib import Path
from collections import Counter

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())
try:
    sys.path.insert(0, str(ROOT))
    from paths import RAW, P4
except ImportError:
    RAW = ROOT / "data" / "raw"
    P4 = ROOT / "participants" / "p4_pointz_skyteam"

try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

YAML_PATH = RAW / "SkyTeam-Exchange.yaml"
OUT_DIR = P4 / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "skyteam_exchange.csv"

NULL_MARKERS = {"", "n/a", "na", "null", "none", "not presented", "-"}
IATA_PAT = re.compile(r"^[A-Z]{3}$")

def clean_str(val):
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in NULL_MARKERS else s

def split_card_number(card_raw):
    raw = clean_str(card_raw)
    if not raw:
        return "", "", ""
    m = re.match(r"^([A-Za-z]{2,3})\s*[-#]?\s*(\d+)$", raw)
    if m:
        prog = m.group(1).upper()
        num = m.group(2)
        return f"{prog} {num}", prog, num
    return raw.upper(), "", raw

def is_valid_iata_raw(code_raw):
    return bool(IATA_PAT.match(clean_str(code_raw)))

def iter_yaml_date_chunks(filepath: Path):
    current_lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() in ("---", "..."):
                continue
            if line and not line[0].isspace() and ":" in line:
                if current_lines:
                    yield "".join(current_lines)
                    current_lines = []
            current_lines.append(line)
        if current_lines:
            yield "".join(current_lines)

def parse_skyteam_yaml(yaml_path: Path, out_csv: Path):
    fieldnames = [
        "source", "source_record_id",
        "flight_date_raw", "flight_date",
        "flight_number_raw", "flight_number",
        "origin_airport_raw", "origin_airport",
        "destination_airport_raw", "destination_airport",
        "is_suspicious_airport",
        "flight_status_raw", "flight_status",
        "loyalty_id_raw", "loyalty_id_normalized",
        "loyalty_program_code", "loyalty_number",
        "booking_class_raw", "booking_class",
        "fare_code_raw", "fare_code",
        "has_ff_cards"
    ]

    stats = Counter()

    with open(out_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for chunk_str in iter_yaml_date_chunks(yaml_path):
            data = yaml.load(chunk_str, Loader=Loader)
            if not isinstance(data, dict):
                continue

            for date_key, flights_dict in data.items():
                if not isinstance(flights_dict, dict):
                    continue
                date_raw = str(date_key)
                date_clean = clean_str(date_raw)

                for flight_key, flight_info in flights_dict.items():
                    if not isinstance(flight_info, dict):
                        continue
                    flight_raw = str(flight_key)
                    flight_clean = re.sub(r"\s+", "", clean_str(flight_raw).upper())

                    from_raw = str(flight_info.get("FROM", ""))
                    to_raw = str(flight_info.get("TO", ""))
                    status_raw = str(flight_info.get("STATUS", ""))
                    status_clean = clean_str(status_raw).upper()

                    dep_valid = is_valid_iata_raw(from_raw)
                    arr_valid = is_valid_iata_raw(to_raw)
                    suspicious = not (dep_valid and arr_valid)

                    ff_dict = flight_info.get("FF")
                    if isinstance(ff_dict, dict) and len(ff_dict) > 0:
                        for card_key, card_details in ff_dict.items():
                            stats["total_rows"] += 1
                            card_raw = str(card_key)
                            card_norm, prog_code, card_num = split_card_number(card_raw)
                            cls_raw = str(card_details.get("CLASS", "")) if isinstance(card_details, dict) else ""
                            fare_raw = str(card_details.get("FARE", "")) if isinstance(card_details, dict) else ""

                            writer.writerow({
                                "source": "SkyTeamExchange",
                                "source_record_id": f"st_{stats['total_rows']}",
                                "flight_date_raw": date_raw,
                                "flight_date": date_clean,
                                "flight_number_raw": flight_raw,
                                "flight_number": flight_clean,
                                "origin_airport_raw": from_raw,
                                "origin_airport": clean_str(from_raw).upper(),
                                "destination_airport_raw": to_raw,
                                "destination_airport": clean_str(to_raw).upper(),
                                "is_suspicious_airport": suspicious,
                                "flight_status_raw": status_raw,
                                "flight_status": status_clean,
                                "loyalty_id_raw": card_raw,
                                "loyalty_id_normalized": card_norm,
                                "loyalty_program_code": prog_code,
                                "loyalty_number": card_num,
                                "booking_class_raw": cls_raw,
                                "booking_class": clean_str(cls_raw).upper(),
                                "fare_code_raw": fare_raw,
                                "fare_code": clean_str(fare_raw).upper(),
                                "has_ff_cards": True
                            })

    print(f"[OK] SkyTeam YAML: total_rows={stats['total_rows']}")

if __name__ == "__main__":
    parse_skyteam_yaml(YAML_PATH, OUT_CSV)
