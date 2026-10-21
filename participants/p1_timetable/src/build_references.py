import re
import sys
import pandas as pd
from pathlib import Path


try:
    repo_root = next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())
    sys.path.insert(0, str(repo_root))
    from paths import P1

    BASE_P1 = P1
except StopIteration:
    BASE_P1 = Path(__file__).resolve().parent.parent

OUT_DIR = BASE_P1 / "output"
INTERMEDIATE_DIR = BASE_P1 / "intermediate"
REPORTS_DIR = BASE_P1 / "reports"

OUT_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = OUT_DIR / "timetable_unique.csv"
AIRPORTS_OUT = OUT_DIR / "airports_reference.csv"
ROUTES_OUT = OUT_DIR / "routes_reference.csv"
ISSUES_OUT = INTERMEDIATE_DIR / "airport_metadata_issues.csv"
QA_OUT = REPORTS_DIR / "timetable_reference_qa.md"


SUSPICIOUS_COUNTRY_PATTERNS = {
    "": "empty_country (truncated in PDF due to long city name)",
    "Republic of": "comma_split_or_truncated (e.g. 'Korea, Republic of')",
    "United": "truncated_country (e.g. 'Tanzania, United Republic of' or 'United Kingdom')",
    "United Republic": "truncated_country ('Tanzania, United Republic of')",
    "United Republic of": "comma_split ('Tanzania, United Republic of')",
    "Spain and Canary": "truncated_country ('Spain and Canary Islands')",
    "Islamic": "truncated_country ('Iran, Islamic Republic of')",
    "Islamic Republic": "truncated_country ('Iran, Islamic Republic of')",
    "Islamic Republic of": "comma_split ('Iran, Islamic Republic of')",
    "Democratic": "truncated_country ('Congo, Democratic Republic of')",
    "Democratic Republic": "truncated_country ('Congo, Democratic Republic of')",
    "Federated": "truncated_country ('Micronesia, Federated States of')",
    "Bolivarian": "truncated_country ('Venezuela, Bolivarian Republic of')",
    "Plurinational": "truncated_country ('Bolivia, Plurinational State of')",
    "Lao People's": "truncated_country ('Lao People's Democratic Republic')",
    "Syrian Arab": "truncated_country ('Syrian Arab Republic')",
    "Brunei": "truncated_country ('Brunei Darussalam')",
    "The Former": "truncated_country ('Macedonia, The Former Yugoslav Republic of')",
}

SUGGESTED_FIXES = {
    "Republic of": "Korea, Republic of",
    "Spain and Canary": "Spain and Canary Islands",
}


def detect_metadata_issue(row: pd.Series):
    city = str(row["city"]).strip()
    country = str(row["country"]).strip()
    reasons = []

    if not country:
        reasons.append("empty_country")

    if "," in city:
        reasons.append("comma_in_city_field")

    if country in SUSPICIOUS_COUNTRY_PATTERNS and country != "":
        reasons.append(SUSPICIOUS_COUNTRY_PATTERNS[country])
    elif re.search(r"\b(and|of|the|de|da|del|United|Republic)$", country, re.IGNORECASE):
        if country not in (
            "United States of America",
            "Czech Republic",
            "Dominican Republic",
            "Central African Republic",
        ):
            reasons.append("truncated_country_ending")

    has_issue = len(reasons) > 0
    reason_str = "; ".join(reasons)

    suggested_city = city
    suggested_country = country
    if "," in city:
        c_parts = [p.strip() for p in city.split(",", 1)]
        suggested_city = c_parts[0]
        if country:
            suggested_country = f"{c_parts[1]}, {country}"
        else:
            suggested_country = c_parts[1]

    if suggested_country == "Tanzania, United":
        suggested_country = "Tanzania, United Republic of"
    elif suggested_country in SUGGESTED_FIXES:
        suggested_country = SUGGESTED_FIXES[suggested_country]

    return pd.Series(
        [has_issue, reason_str, suggested_city, suggested_country],
        index=[
            "metadata_quality_issue",
            "issue_reason",
            "city_suggested",
            "country_suggested",
        ],
    )


def build_references():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Не найден входной файл: {INPUT_CSV.resolve()}. "
            f"Убедись, что timetable_unique.csv лежит в папке проекта."
        )

    print(f"[*] Чтение входного файла: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, dtype=str, keep_default_na=False)
    total_input_rows = len(df)
    print(f"[*] Загружено строк из timetable_unique.csv: {total_input_rows}")

    df["is_codeshare_bool"] = df["is_codeshare"].str.strip().str.lower() == "true"

    origins = df[["origin_airport", "origin_city", "origin_country"]].rename(
        columns={
            "origin_airport": "airport_code",
            "origin_city": "city",
            "origin_country": "country",
        }
    )
    destinations = df[
        ["destination_airport", "destination_city", "destination_country"]
    ].rename(
        columns={
            "destination_airport": "airport_code",
            "destination_city": "city",
            "destination_country": "country",
        }
    )

    all_airports = pd.concat([origins, destinations], ignore_index=True)
    all_airports["airport_code"] = all_airports["airport_code"].str.strip()
    all_airports["city"] = all_airports["city"].str.strip()
    all_airports["country"] = all_airports["country"].str.strip()

    airports_ref = (
        all_airports.groupby(["airport_code", "city", "country"], as_index=False)
        .size()
        .rename(columns={"size": "n_occurrences"})
    )

    code_variants_count = airports_ref.groupby("airport_code")["city"].transform("count")
    airports_ref["has_conflict"] = code_variants_count > 1
    airports_ref["source"] = "Skyteam_Timetable"

    qa_cols = airports_ref.apply(detect_metadata_issue, axis=1)
    airports_ref = pd.concat([airports_ref, qa_cols], axis=1)

    airports_cols = [
        "airport_code",
        "city",
        "country",
        "source",
        "n_occurrences",
        "has_conflict",
        "metadata_quality_issue",
        "issue_reason",
    ]
    airports_ref = airports_ref.sort_values(
        by=["airport_code", "n_occurrences"], ascending=[True, False]
    )

    airports_ref[airports_cols].to_csv(AIRPORTS_OUT, index=False, encoding="utf-8")
    print(f"[+] Сохранён {AIRPORTS_OUT} ({len(airports_ref)} строк)")

    issues_df = airports_ref[
        airports_ref["metadata_quality_issue"] | airports_ref["has_conflict"]
    ][
        [
            "airport_code",
            "city",
            "country",
            "n_occurrences",
            "has_conflict",
            "metadata_quality_issue",
            "issue_reason",
            "city_suggested",
            "country_suggested",
            "source",
        ]
    ]
    issues_df.to_csv(ISSUES_OUT, index=False, encoding="utf-8")
    print(f"[+] Сохранён {ISSUES_OUT} ({len(issues_df)} проблемных аэропортов)")

    route_group_cols = [
        "flight_number",
        "carrier_code",
        "origin_airport",
        "destination_airport",
        "is_codeshare",
        "operated_by_raw",
    ]

    routes_ref = (
        df.groupby(route_group_cols, as_index=False)
        .size()
        .rename(columns={"size": "schedule_rows_count"})
    )
    routes_ref["source"] = "Skyteam_Timetable"

    routes_cols = [
        "flight_number",
        "carrier_code",
        "origin_airport",
        "destination_airport",
        "is_codeshare",
        "operated_by_raw",
        "source",
        "schedule_rows_count",
    ]
    routes_ref = routes_ref[routes_cols].sort_values(
        by=["flight_number", "origin_airport", "destination_airport"]
    )
    routes_ref.to_csv(ROUTES_OUT, index=False, encoding="utf-8")
    print(f"[+] Сохранён {ROUTES_OUT} ({len(routes_ref)} строк)")

    n_unique_airports = airports_ref["airport_code"].nunique()
    n_unique_flights = df["flight_number"].nunique()

    flight_od_pairs = df[
        ["flight_number", "origin_airport", "destination_airport"]
    ].drop_duplicates()
    n_unique_flight_od = len(flight_od_pairs)

    conflict_airports_df = airports_ref[airports_ref["has_conflict"]]
    n_conflict_airport_codes = conflict_airports_df["airport_code"].nunique()

    metadata_issues_only = airports_ref[airports_ref["metadata_quality_issue"]]
    n_metadata_issues = len(metadata_issues_only)

    routes_per_flight = flight_od_pairs.groupby("flight_number").size()
    multi_route_flights = routes_per_flight[routes_per_flight > 1]
    n_multi_route_flights = len(multi_route_flights)

    n_codeshare_routes_ref = len(
        routes_ref[routes_ref["is_codeshare"].str.lower() == "true"]
    )
    n_codeshare_flight_od = len(
        df[df["is_codeshare_bool"]][
            ["flight_number", "origin_airport", "destination_airport"]
        ].drop_duplicates()
    )

    total_schedule_rows_check = routes_ref["schedule_rows_count"].sum()
    total_airport_mentions_check = airports_ref["n_occurrences"].sum()

    qa_lines = [
        "# QA Report: Timetable Reference Tables (Участник 1)",
        "",
        "## 1. Входные и выходные файлы",
        f"- **Входной файл:** `{INPUT_CSV.name}` (`{total_input_rows}` строк)",
        f"- **Справочник аэропортов:** `integration/{AIRPORTS_OUT.name}` (`{len(airports_ref)}` строк, добавлен флаг `metadata_quality_issue` и `issue_reason`)",
        f"- **Список проблемных метаданных аэропортов:** `integration/{ISSUES_OUT.name}` (`{len(issues_df)}` строк)",
        f"- **Справочник маршрутов:** `integration/{ROUTES_OUT.name}` (`{len(routes_ref)}` строк)",
        "- **Период действия расписания:** `01.11.2018 – 31.01.2019` (справочный источник).",
        "",
        "## 2. Контрольные показатели (по ТЗ + QA-патч по `country`)",
        f"- **Количество уникальных аэропортов (`airport_code`):** `{n_unique_airports}`",
        f"- **Количество уникальных номеров рейсов (`flight_number`):** `{n_unique_flights}`",
        f"- **Количество уникальных комбинаций `flight_number + origin_airport + destination_airport`:** `{n_unique_flight_od}`",
        f"- **Количество `airport_code` с конфликтом `city/country` (`has_conflict = True`):** `{n_conflict_airport_codes}`",
        f"- **Количество `airport_code` с артефактами парсинга/обрезки `country` в PDF (`metadata_quality_issue = True`):** `{n_metadata_issues}`",
        f"- **Количество `flight_number` с более чем одним маршрутом (`origin -> destination`):** `{n_multi_route_flights}`",
        f"- **Количество codeshare-маршрутов (`is_codeshare = True`):** `{n_codeshare_routes_ref}` в `routes_reference.csv` (`{n_codeshare_flight_od}` уникальных троек `flight + origin + dest`)",
        "",
        "## 3. Проверка целостности данных (Sanity Checks)",
        f"- **Сумма `schedule_rows_count` в `routes_reference.csv`:** `{total_schedule_rows_check}` (совпадает с `timetable_unique.csv`: `{total_schedule_rows_check == total_input_rows}`)",
        f"- **Сумма `n_occurrences` в `airports_reference.csv`:** `{total_airport_mentions_check}` (ровно `2 * {total_input_rows} = {2 * total_input_rows}`, потерь нет: `{total_airport_mentions_check == 2 * total_input_rows}`)",
        "",
        "## 4. Детализация проблемных/обрезанных `country` (`metadata_quality_issue = True`)",
        "В исходном PDF длинные названия городов/стран обрезались правым полем колонки перед IATA-кодом (например, `CPC`), либо содержали вторую запятую в названии страны (`Cheongju, Korea, Republic of`, `Dar Es Salaam, Tanzania, United Republic of`). Исходные значения в `airports_reference.csv` сохранены без изменений, все кейсы помечены флагом `metadata_quality_issue = True` и вынесены в `integration/airport_metadata_issues.csv`:",
        "",
        "| airport_code | city (raw) | country (raw) | n_occurrences | issue_reason | city_suggested | country_suggested |",
        "| :--- | :--- | :--- | :---: | :--- | :--- | :--- |",
    ]

    for _, r in issues_df.iterrows():
        qa_lines.append(
            f"| `{r['airport_code']}` | {r['city']} | `{r['country']}` | {r['n_occurrences']} | {r['issue_reason']} | {r['city_suggested']} | {r['country_suggested']} |"
        )

    qa_lines.append("")
    qa_lines.append("## 5. Детализация конфликтов `has_conflict = True`")
    if n_conflict_airport_codes == 0:
        qa_lines.append(
            "Конфликтов, где один и тот же `airport_code` записан в PDF по-разному в разных шапках, нет (`0`). Все проблемы `country` связаны с единообразным усечением длинных строк в шапке PDF и перечислены в Разделе 4."
        )
    else:
        for _, r in conflict_airports_df.iterrows():
            qa_lines.append(
                f"- `{r['airport_code']}`: {r['city']} / {r['country']} ({r['n_occurrences']})"
            )

    QA_OUT.write_text("\n".join(qa_lines) + "\n", encoding="utf-8")
    print(f"[+] Обновлён QA-отчёт: {QA_OUT}")

    print("\n================ КРАТКАЯ СВОДКА QA ================")
    print(f"Уникальных аэропортов:                        {n_unique_airports}")
    print(f"Аэропортов с конфликтом (has_conflict):       {n_conflict_airport_codes}")
    print(f"Аэропортов с проблемой country (metadata):    {n_metadata_issues}")
    print(f"Уникальных flight_number:                     {n_unique_flights}")
    print(f"Уникальных (flight + origin + destination):   {n_unique_flight_od}")
    print(f"Рейсов с >1 маршрутом:                        {n_multi_route_flights}")
    print(f"Codeshare-маршрутов:                          {n_codeshare_routes_ref}")


if __name__ == "__main__":
    build_references()