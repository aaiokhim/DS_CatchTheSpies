import sys
from pathlib import Path
import csv
import re

sys.path.insert(
    0,
    str(
        next(
            p for p in Path(__file__).resolve().parents
            if (p / "paths.py").exists()
        )
    )
)

from paths import RAW, P3

input_file = RAW / "Sirena-export-fixed.tab"

output_file = P3 / "output" / "sirena.csv"

errors_file = P3 / "intermediate" / "sirena_errors.csv"



def clean(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def parse_flight_and_sh(value):

    value = clean(value)

    if value is None:
        return None, None

    match = re.fullmatch(
        r"([A-Z0-9]{2}\d{1,4})([A-Z]{2,3})?",
        value
    )

    if match:
        return (
            match.group(1),
            match.group(2)
        )

    return value, None

def parse_additional_info(value):

    value = clean(value)

    if value is None:
        return None, None, None, None

    loyalty_program_code = None
    loyalty_number = None

    match = re.search(
        r"FF#\s*([A-Z0-9]{2})\s+(\d+)",
        value
    )

    if match:
        loyalty_program_code = match.group(1)
        loyalty_number = match.group(2)

        additional_code_raw = value[:match.start()].strip()

        if additional_code_raw == "":
            additional_code_raw = None

    else:
        additional_code_raw = value

    return (
        value,
        additional_code_raw,
        loyalty_program_code,
        loyalty_number
    )


def parse_line(line):

    passenger_name = clean(line[0:60])

    birth_date = clean(line[60:72])

    depart_date = clean(line[72:84])
    depart_time = clean(line[84:96])

    arrival_date = clean(line[96:108])
    arrival_time = clean(line[108:120])

    flight_sh_raw = clean(line[120:132])

    flight_number, sh_raw = parse_flight_and_sh(
        flight_sh_raw
    )

    origin_airport = clean(line[132:138])
    destination_airport = clean(line[138:144])

    pnr = clean(line[144:150])

    e_ticket = clean(line[150:168])

    travel_doc = clean(line[168:180])

    seat = clean(line[180:186])

    meal = clean(line[186:192])

    travel_class = clean(line[192:198])

    fare = clean(line[198:204])

    baggage = clean(line[204:216])

    pax_additional_info_raw = clean(
        line[216:276]
    )

    (
        pax_additional_info_raw,
        additional_code_raw,
        loyalty_program_code,
        loyalty_number
    ) = parse_additional_info(
        pax_additional_info_raw
    )

    agent_info = clean(line[276:336])

    return {
        "passenger_name_raw":
            passenger_name,

        "birth_date":
            birth_date,

        "depart_date":
            depart_date,

        "depart_time":
            depart_time,

        "arrival_date":
            arrival_date,

        "arrival_time":
            arrival_time,

        "flight_number":
            flight_number,

        "sh_raw":
            sh_raw,

        "origin_airport":
            origin_airport,

        "destination_airport":
            destination_airport,

        "pnr":
            pnr,

        "e_ticket":
            e_ticket,

        "travel_doc":
            travel_doc,

        "seat":
            seat,

        "meal":
            meal,

        "travel_class":
            travel_class,

        "fare":
            fare,

        "baggage":
            baggage,

        "pax_additional_info_raw":
            pax_additional_info_raw,

        "additional_code_raw":
            additional_code_raw,

        "loyalty_program_code":
            loyalty_program_code,

        "loyalty_number":
            loyalty_number,

        "agent_info":
            agent_info,

        "source_file":
            input_file.name,
    }


fieldnames = [
    "passenger_name_raw",

    "birth_date",

    "depart_date",
    "depart_time",

    "arrival_date",
    "arrival_time",

    "flight_number",
    "sh_raw",

    "origin_airport",
    "destination_airport",

    "pnr",
    "e_ticket",

    "travel_doc",

    "seat",
    "meal",

    "travel_class",
    "fare",
    "baggage",

    "pax_additional_info_raw",
    "additional_code_raw",

    "loyalty_program_code",
    "loyalty_number",

    "agent_info",

    "source_file",
]



total_lines = 0
parsed_lines = 0
invalid_length = 0
parse_errors = 0

loyalty_count = 0
missing_birth_date = 0


with open(
    input_file,
    "r",
    encoding="utf-8-sig"
) as source, open(
    output_file,
    "w",
    newline="",
    encoding="utf-8-sig"
) as result, open(
    errors_file,
    "w",
    newline="",
    encoding="utf-8-sig"
) as error_result:

    writer = csv.DictWriter(
        result,
        fieldnames=fieldnames
    )

    writer.writeheader()

    error_writer = csv.DictWriter(
        error_result,
        fieldnames=[
            "line_number",
            "error_type",
            "line_length",
            "message",
            "raw_line",
        ]
    )

    error_writer.writeheader()

    header = source.readline().rstrip("\r\n")

    print(
        "Длина заголовка:",
        len(header)
    )

    for line_number, line in enumerate(
        source,
        start=2
    ):

        line = line.rstrip("\r\n")

        if line.strip() == "":
            continue

        total_lines += 1

        if len(line) != 336:

            invalid_length += 1

            error_writer.writerow({
                "line_number":
                    line_number,

                "error_type":
                    "invalid_length",

                "line_length":
                    len(line),

                "message":
                    "Ожидалась строка длиной 336 символов",

                "raw_line":
                    line,
            })

            continue

        try:
            row = parse_line(line)

            writer.writerow(row)

            parsed_lines += 1

            if row["loyalty_number"] is not None:
                loyalty_count += 1

            if row["birth_date"] == "N/A":
                missing_birth_date += 1

        except Exception as e:

            parse_errors += 1

            error_writer.writerow({
                "line_number":
                    line_number,

                "error_type":
                    "parse_error",

                "line_length":
                    len(line),

                "message":
                    str(e),

                "raw_line":
                    line,
            })

print(
    f"Готово: {parsed_lines}/{total_lines} строк спрсено, "
    f"{invalid_length} строк с неправильной длиной, "
    f"{parse_errors} ошибок."
)

print(
    f"Записей с loyalty ID: {loyalty_count}, "
    f"без даты рождения: {missing_birth_date}."
)