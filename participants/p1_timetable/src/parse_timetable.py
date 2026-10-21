import csv
import sys
import re
import time
from pathlib import Path
import pymupdf as fitz

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable


# ================= НАСТРОЙКИ ПУТЕЙ =================
try:
    repo_root = next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())
    sys.path.insert(0, str(repo_root))
    from paths import RAW, P1

    PDF_PATH = RAW / "Skyteam_Timetable.pdf"
    OUT_DIR = P1 / "output"
    INTERMEDIATE_DIR = P1 / "intermediate"
except StopIteration:
    BASE_DIR = Path(__file__).resolve().parent.parent
    PDF_PATH = BASE_DIR / "Skyteam_Timetable.pdf"
    OUT_DIR = BASE_DIR / "output"
    INTERMEDIATE_DIR = BASE_DIR / "intermediate"


OUT_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FULL_CSV = INTERMEDIATE_DIR / "timetable_clean.csv"
OUTPUT_UNIQUE_CSV = OUT_DIR / "timetable_unique.csv"
ERRORS_CSV = INTERMEDIATE_DIR / "timetable_parse_errors.csv"


# ================= РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ =================
# 1a. Шапка в одной строке: "FROM: Aalborg, Denmark AAL" или "Aalborg, Denmark AAL FROM:"
RE_HEADER_FULL = re.compile(
    r"^(?:(FROM|TO):\s*(.+?)\s+([A-Z]{3})|(.+?)\s+([A-Z]{3})\s+(FROM|TO):)$"
)

# 1b. Строка локации отдельно от FROM:/TO: -> "Aalborg, Denmark AAL"
RE_LOCATION_ONLY = re.compile(
    r"^([A-Za-z][A-Za-z\s\.,\-\(\)/'’]+?)\s+([A-Z]{3})$"
)

# 2. Основная строка расписания
RE_FLIGHT = re.compile(
    r"^(\d{2}\s+[A-Za-z]{3})\s*-\s*(\d{2}\s+[A-Za-z]{3})\s+"
    r"([1-7\s]+?)\s+"
    r"(\d{2}:\d{2})\s+"
    r"(\d{2}:\d{2}(?:\s*(?:\+-|[+-])\d)?)\s+"
    r"([A-Z0-9]{2,3}\d{1,4})(\*?)\s+"
    r"([A-Z0-9]{2,4})\s+"
    r"(\d+H\d+M)$"
)

# 3. Строка Operated by
RE_OPERATED = re.compile(r"^Operated by:\s*(.+)$", re.IGNORECASE)

IGNORE_PREFIXES = (
    "Validity",
    "Days",
    "Dep",
    "Arr",
    "Flight",
    "Aircraft",
    "Travel",
    "Time",
    "Consult your travel agent",
    "SKYTEAM",
)

TRUNCATED_COUNTRIES = {
    "United States of": "United States of America",
    "United States": "United States of America",
    "United": "United States of America",
    "Russian": "Russian Federation",
    "Czech": "Czech Republic",
    "Dominican": "Dominican Republic",
    "United Arab": "United Arab Emirates",
    "Papua New": "Papua New Guinea",
    "Central African": "Central African Republic",
    "Democratic": "Democratic Republic of the Congo",
    "Congo (Democratic": "Congo (Democratic Republic)",
    "Korea (Republic": "Korea (Republic of)",
}


def parse_city_country(location_str: str):
    if "," in location_str:
        parts = location_str.rsplit(",", 1)
        city = parts[0].strip()
        country = parts[1].strip()
        # Если в PDF название страны обрезалось из-за длинного названия города
        if country in TRUNCATED_COUNTRIES:
            if country == "United" and not re.search(r"\b[A-Z]{2}$", city):
                # Если у города нет 2-буквенного кода штата США (напр. MN, NY), возможно это UK/UAE
                pass
            else:
                country = TRUNCATED_COUNTRIES[country]
        return city, country
    return location_str.strip(), ""


def extract_column_lines(page: fitz.Page, mid_x: float):
    words = page.get_text("words")
    left_words = [w for w in words if w[0] < mid_x]
    right_words = [w for w in words if w[0] >= mid_x]

    def group_words_into_lines(word_list, y_tolerance=3.5):
        if not word_list:
            return []
        word_list.sort(key=lambda w: (w[3], w[0]))
        lines = []
        current_line = [word_list[0]]
        current_y1 = word_list[0][3]

        for w in word_list[1:]:
            if abs(w[3] - current_y1) <= y_tolerance:
                current_line.append(w)
            else:
                current_line.sort(key=lambda item: item[0])
                lines.append(" ".join(item[4] for item in current_line))
                current_line = [w]
                current_y1 = w[3]

        if current_line:
            current_line.sort(key=lambda item: item[0])
            lines.append(" ".join(item[4] for item in current_line))

        return lines

    return group_words_into_lines(left_words), group_words_into_lines(right_words)


def update_route_state(state: dict, direction: str, loc_text: str, iata_code: str):
    city, country = parse_city_country(loc_text)
    if direction == "FROM":
        state["origin_airport"] = iata_code
        state["origin_city"] = city
        state["origin_country"] = country
    elif direction == "TO":
        state["dest_airport"] = iata_code
        state["dest_city"] = city
        state["dest_country"] = country


def flush_pending_row(state: dict, full_writer, unique_writer, global_seen_keys: set):
    row = state["pending_row"]
    if row is None:
        return 0

    full_writer.writerow(row)

    dedup_key = (
        row["flight_number_raw"],
        row["operated_by_raw"],
        row["origin_airport"],
        row["destination_airport"],
        row["valid_from"],
        row["valid_to"],
        row["days_normalized"],
        row["departure_time"],
        row["arrival_time"],
        row["arrival_next_day"],
        row["aircraft_code"],
    )

    added_unique = 0
    if dedup_key not in global_seen_keys:
        global_seen_keys.add(dedup_key)
        unique_writer.writerow(row)
        added_unique = 1

    state["pending_row"] = None
    return added_unique


def parse_pdf_timetable(pdf_path: Path, full_csv: Path, unique_csv: Path, errors_csv: Path):
    start_time = time.time()
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[*] Открыт файл: {pdf_path.name} | Всего страниц: {total_pages}")

    fieldnames = [
        "source_record_id",
        "flight_number",
        "flight_number_raw",
        "carrier_code",
        "is_codeshare",
        "operated_by_raw",
        "origin_airport",
        "origin_city",
        "origin_country",
        "destination_airport",
        "destination_city",
        "destination_country",
        "valid_from",
        "valid_to",
        "validity_raw",
        "days_raw",
        "days_normalized",
        "departure_time",
        "arrival_time",
        "arrival_next_day",
        "aircraft_code",
        "travel_time",
        "source_page",
        "source_column",
        "source",
    ]

    error_fieldnames = ["source_page", "source_column", "reason", "raw_line"]

    col_state = {
        "L": {
            "origin_airport": "", "origin_city": "", "origin_country": "",
            "dest_airport": "", "dest_city": "", "dest_country": "",
            "pending_row": None,
        },
        "R": {
            "origin_airport": "", "origin_city": "", "origin_country": "",
            "dest_airport": "", "dest_city": "", "dest_country": "",
            "pending_row": None,
        },
    }

    global_seen_keys = set()
    record_id = 0
    unique_count = 0
    errors_count = 0
    consult_agent_count = 0

    with (
        open(full_csv, mode="w", newline="", encoding="utf-8") as f_full,
        open(unique_csv, mode="w", newline="", encoding="utf-8") as f_uniq,
        open(errors_csv, mode="w", newline="", encoding="utf-8") as f_err,
    ):
        full_writer = csv.DictWriter(f_full, fieldnames=fieldnames)
        full_writer.writeheader()

        unique_writer = csv.DictWriter(f_uniq, fieldnames=fieldnames)
        unique_writer.writeheader()

        err_writer = csv.DictWriter(f_err, fieldnames=error_fieldnames)
        err_writer.writeheader()

        for page_idx in tqdm(range(4, total_pages), desc="Парсинг PDF", unit="стр"):
            page_num = page_idx + 1
            page = doc[page_idx]
            mid_x = page.rect.width / 2.0

            left_lines, right_lines = extract_column_lines(page, mid_x)

            for col_label, lines in (("L", left_lines), ("R", right_lines)):
                state = col_state[col_label]
                pending_loc = None
                pending_dir = None

                for raw_line in lines:
                    line = raw_line.strip()
                    if not line:
                        continue

                    if "Consult your travel agent" in line:
                        unique_count += flush_pending_row(
                            state, full_writer, unique_writer, global_seen_keys
                        )
                        consult_agent_count += 1
                        continue

                    if line.startswith(IGNORE_PREFIXES):
                        continue

                    m_op = RE_OPERATED.match(line)
                    if m_op:
                        if state["pending_row"] is not None:
                            state["pending_row"]["operated_by_raw"] = m_op.group(1).strip()
                            unique_count += flush_pending_row(
                                state, full_writer, unique_writer, global_seen_keys
                            )
                        continue

                    m_hdr = RE_HEADER_FULL.match(line)
                    if m_hdr:
                        unique_count += flush_pending_row(
                            state, full_writer, unique_writer, global_seen_keys
                        )
                        g1, g2, g3, g4, g5, g6 = m_hdr.groups()
                        if g1:
                            direction, loc_text, iata_code = g1, g2, g3
                        else:
                            loc_text, iata_code, direction = g4, g5, g6

                        update_route_state(state, direction, loc_text, iata_code)
                        pending_loc = None
                        pending_dir = None
                        continue

                    if line in ("FROM:", "TO:"):
                        unique_count += flush_pending_row(
                            state, full_writer, unique_writer, global_seen_keys
                        )
                        direction = line[:-1]
                        if pending_loc is not None:
                            update_route_state(state, direction, pending_loc[0], pending_loc[1])
                            pending_loc = None
                        else:
                            pending_dir = direction
                        continue

                    m_fl = RE_FLIGHT.match(line)
                    if m_fl:
                        unique_count += flush_pending_row(
                            state, full_writer, unique_writer, global_seen_keys
                        )

                        (
                            v_from,
                            v_to,
                            days_str,
                            dep_time,
                            arr_time_raw,
                            flight_num,
                            star,
                            aircraft,
                            travel_time,
                        ) = m_fl.groups()

                        arr_time_clean = arr_time_raw.strip()
                        next_day_shift = ""
                        if "+" in arr_time_clean or "-" in arr_time_clean:
                            arr_parts = re.split(r"(?=[+-])", arr_time_clean, maxsplit=1)
                            arr_time_clean = arr_parts[0].strip()
                            next_day_shift = arr_parts[1].strip()

                        carrier_match = re.match(r"^([A-Z0-9]{2})", flight_num)
                        carrier = carrier_match.group(1) if carrier_match else flight_num[:2]

                        record_id += 1
                        state["pending_row"] = {
                            "source_record_id": record_id,
                            "flight_number": flight_num,
                            "flight_number_raw": f"{flight_num}{star}",
                            "carrier_code": carrier,
                            "is_codeshare": bool(star == "*"),
                            "operated_by_raw": "",
                            "origin_airport": state["origin_airport"],
                            "origin_city": state["origin_city"],
                            "origin_country": state["origin_country"],
                            "destination_airport": state["dest_airport"],
                            "destination_city": state["dest_city"],
                            "destination_country": state["dest_country"],
                            "valid_from": v_from,
                            "valid_to": v_to,
                            "validity_raw": f"{v_from} - {v_to}",
                            "days_raw": days_str,
                            "days_normalized": days_str.replace(" ", ""),
                            "departure_time": dep_time,
                            "arrival_time": arr_time_clean,
                            "arrival_next_day": next_day_shift,
                            "aircraft_code": aircraft,
                            "travel_time": travel_time,
                            "source_page": page_num,
                            "source_column": col_label,
                            "source": "Skyteam_Timetable",
                        }
                        continue

                    m_loc = RE_LOCATION_ONLY.match(line)
                    if m_loc:
                        unique_count += flush_pending_row(
                            state, full_writer, unique_writer, global_seen_keys
                        )
                        loc_text, iata_code = m_loc.groups()
                        if pending_dir is not None:
                            update_route_state(state, pending_dir, loc_text, iata_code)
                            pending_dir = None
                        else:
                            pending_loc = (loc_text, iata_code)
                        continue

                    errors_count += 1
                    err_writer.writerow({
                        "source_page": page_num,
                        "source_column": col_label,
                        "reason": "Unrecognized line pattern",
                        "raw_line": line,
                    })

        for col_label in ("L", "R"):
            unique_count += flush_pending_row(
                col_state[col_label], full_writer, unique_writer, global_seen_keys
            )

    doc.close()
    elapsed = time.time() - start_time
    print("\n================ ГОТОВО ================")
    print(f"Время выполнения:         {elapsed:.1f} сек.")
    print(f"Всего извлечено строк:    {record_id} -> {full_csv.name}")
    print(f"Уникальных строк рейсов:  {unique_count} -> {unique_csv.name}")
    print(f"Маршрутов без рейсов:     {consult_agent_count}")
    print(f"Нераспознанных строк:     {errors_count} (см. {errors_csv.name})")


if __name__ == "__main__":
    if not PDF_PATH.exists():
        print(f"[!] Файл {PDF_PATH} не найден!")
    else:
        parse_pdf_timetable(PDF_PATH, OUTPUT_FULL_CSV, OUTPUT_UNIQUE_CSV, ERRORS_CSV)