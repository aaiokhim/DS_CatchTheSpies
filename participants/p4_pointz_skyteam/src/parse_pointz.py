import sys
import xml.etree.ElementTree as ET
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

XML_PATH = RAW / "PointzAggregator-AirlinesData.xml"
OUT_DIR = P4 / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NULL_MARKERS = {"", "n/a", "na", "null", "none", "not presented", "-"}
IATA_PAT = re.compile(r"^[A-Z]{3}$")

def clean_str(val):
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in NULL_MARKERS else s

def normalize_name(val):
    s = clean_str(val).upper()
    return re.sub(r"\s+", " ", s)

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

def parse_pointz_xml(xml_path: Path):
    users_path = OUT_DIR / "pointz_users.csv"
    cards_path = OUT_DIR / "pointz_cards.csv"
    flights_path = OUT_DIR / "pointz_flights.csv"

    with open(users_path, "w", newline="", encoding="utf-8") as users_f, \
         open(cards_path, "w", newline="", encoding="utf-8") as cards_f, \
         open(flights_path, "w", newline="", encoding="utf-8") as flights_f:

        users_writer = csv.DictWriter(users_f, fieldnames=[
            "source", "source_record_id", "user_uid",
            "first_name_raw", "last_name_raw", "full_name_raw",
            "first_name_normalized", "last_name_normalized", "full_name_normalized",
            "cards_count", "flights_count"
        ])
        cards_writer = csv.DictWriter(cards_f, fieldnames=[
            "source", "source_record_id", "user_uid", "user_source_record_id",
            "card_type_raw", "loyalty_id_raw", "loyalty_id_normalized",
            "loyalty_program_code", "loyalty_number",
            "bonus_program_raw", "activities_count"
        ])
        flights_writer = csv.DictWriter(flights_f, fieldnames=[
            "source", "source_record_id", "user_uid", "user_source_record_id", "card_source_record_id",
            "loyalty_id_raw", "loyalty_id_normalized",
            "loyalty_program_code", "loyalty_number",
            "activity_type_raw", "flight_number_raw", "flight_number",
            "flight_date_raw", "flight_date",
            "origin_airport_raw", "origin_airport",
            "destination_airport_raw", "destination_airport",
            "is_suspicious_airport",
            "fare_code_raw", "fare_code"
        ])

        users_writer.writeheader()
        cards_writer.writeheader()
        flights_writer.writeheader()

        stats = Counter()
        context = ET.iterparse(xml_path, events=("end",))
        for event, elem in context:
            if elem.tag == "user":
                stats["users"] += 1
                user_rec_id = f"pz_user_{stats['users']}"
                uid = clean_str(elem.attrib.get("uid"))

                name_elem = elem.find("name")
                first_raw = name_elem.attrib.get("first", "") if name_elem is not None else ""
                last_raw = name_elem.attrib.get("last", "") if name_elem is not None else ""
                full_raw = f"{first_raw} {last_raw}".strip()

                first_norm = normalize_name(first_raw)
                last_norm = normalize_name(last_raw)
                full_norm = normalize_name(full_raw)

                cards_elem = elem.find("cards")
                cards_type = cards_elem.attrib.get("type", "") if cards_elem is not None else ""
                card_list = cards_elem.findall("card") if cards_elem is not None else []

                user_flights_total = 0

                for card_elem in card_list:
                    stats["cards"] += 1
                    card_rec_id = f"pz_card_{stats['cards']}"
                    card_raw = card_elem.attrib.get("number", "")
                    card_norm, prog_code, card_num = split_card_number(card_raw)

                    bp_elem = card_elem.find("bonusprogramm")
                    bp_raw = clean_str(bp_elem.text) if bp_elem is not None else ""

                    acts_elem = card_elem.find("activities")
                    act_list = acts_elem.findall("activity") if acts_elem is not None else []
                    user_flights_total += len(act_list)

                    cards_writer.writerow({
                        "source": "PointzAggregator",
                        "source_record_id": card_rec_id,
                        "user_uid": uid,
                        "user_source_record_id": user_rec_id,
                        "card_type_raw": cards_type,
                        "loyalty_id_raw": card_raw,
                        "loyalty_id_normalized": card_norm,
                        "loyalty_program_code": prog_code,
                        "loyalty_number": card_num,
                        "bonus_program_raw": bp_raw,
                        "activities_count": len(act_list)
                    })

                    for act_elem in act_list:
                        stats["flights"] += 1
                        act_type = act_elem.attrib.get("type", "")
                        code_raw = act_elem.findtext("Code", default="")
                        date_raw = act_elem.findtext("Date", default="")
                        dep_raw = act_elem.findtext("Departure", default="")
                        arr_raw = act_elem.findtext("Arrival", default="")
                        fare_raw = act_elem.findtext("Fare", default="")

                        dep_valid = is_valid_iata_raw(dep_raw)
                        arr_valid = is_valid_iata_raw(arr_raw)
                        suspicious = not (dep_valid and arr_valid)

                        flights_writer.writerow({
                            "source": "PointzAggregator",
                            "source_record_id": f"pz_act_{stats['flights']}",
                            "user_uid": uid,
                            "user_source_record_id": user_rec_id,
                            "card_source_record_id": card_rec_id,
                            "loyalty_id_raw": card_raw,
                            "loyalty_id_normalized": card_norm,
                            "loyalty_program_code": prog_code,
                            "loyalty_number": card_num,
                            "activity_type_raw": act_type,
                            "flight_number_raw": code_raw,
                            "flight_number": re.sub(r"\s+", "", clean_str(code_raw).upper()),
                            "flight_date_raw": date_raw,
                            "flight_date": clean_str(date_raw),
                            "origin_airport_raw": dep_raw,
                            "origin_airport": clean_str(dep_raw).upper(),
                            "destination_airport_raw": arr_raw,
                            "destination_airport": clean_str(arr_raw).upper(),
                            "is_suspicious_airport": suspicious,
                            "fare_code_raw": fare_raw,
                            "fare_code": clean_str(fare_raw).upper()
                        })

                users_writer.writerow({
                    "source": "PointzAggregator",
                    "source_record_id": user_rec_id,
                    "user_uid": uid,
                    "first_name_raw": first_raw,
                    "last_name_raw": last_raw,
                    "full_name_raw": full_raw,
                    "first_name_normalized": first_norm,
                    "last_name_normalized": last_norm,
                    "full_name_normalized": full_norm,
                    "cards_count": len(card_list),
                    "flights_count": user_flights_total
                })

                elem.clear()

    print(f"[OK] Pointz XML: users={stats['users']}, cards={stats['cards']}, flights={stats['flights']}")

if __name__ == "__main__":
    parse_pointz_xml(XML_PATH)
