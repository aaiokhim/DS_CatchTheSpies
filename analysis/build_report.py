"""
Общий отчёт по всем посчитанным признакам: analysis/reports/REPORT.md и рейтинг людей
analysis/output/report_ranking.csv.

python3 analysis/build_report.py
"""
import re
from datetime import datetime

import pandas as pd

from common import OUT, ANALYSIS_REPORTS

HERE = ANALYSIS_REPORTS
REPORT = HERE / "REPORT.md"

TITLES = {
    "A1": "Один документ у разных людей", "A2": "Несколько документов у одного человека",
    "A3": "Тот же рейс и дата, другой документ", "A4": "Одна карта у разных людей",
    "A5": "Один Pointz user_uid у разных людей", "A6": "Анонимный профиль форума раскрыт",
    "A7": "Несовпадение пола",
    "B1": "Посадка без брони", "B2": "Бронь без посадки", "B3": "Перелёт только в loyalty-источниках",
    "B4": "Один билет у разных людей", "B5": "Много перелётов без даты рождения",
    "C1": "Невозможный маршрут", "C2": "Аномально много перелётов", "C3": "Короткие международные поездки",
    "C4": "Окольные маршруты", "C5": "Редкие направления", "C6": "Рваная активность",
    "D1": "Постоянные попутчики", "D2": "Общий PNR у разных людей",
    "E1": "Много loyalty-карт / программ", "E2": "Перекос источников",
}
CATEGORY_TITLES = {"A": "Личность и идентификаторы", "B": "Бронирование / посадка / мили",
                   "C": "Время и география", "D": "Совместные поездки и бронирования",
                   "E": "Loyalty-программы и профиль источников"}
STRENGTH = {"A1": "сильный", "A2": "сильный", "A3": "сильный", "A4": "сильный", "A5": "средний",
            "A6": "слабый", "A7": "средний", "B1": "средний", "B2": "слабый", "B3": "средний",
            "B4": "сильный", "B5": "слабый", "C1": "сильный", "C2": "слабый", "C3": "средний",
            "C4": "слабый", "C5": "слабый", "C6": "слабый", "D1": "средний", "D2": "слабый",
            "E1": "слабый", "E2": "слабый"}
STRONG = {k for k, v in STRENGTH.items() if v == "сильный"}

KNOWN = [
    ("GORDEI GLEBOV", r"GORDEI.*GLEBOV|GLEBOV.*GORDEI|ГЛЕБОВ ГОРДЕЙ", "A1"),
    ("RAMIL BUROV", r"RAMIL.*BUROV|BUROV.*RAMIL|БУРОВ РАМИЛ", "A1"),
    ("AMALIIA KUDRIAVTSEVA", r"AMALI.*KUDR|KUDR.*AMALI|КУДРЯВЦЕВА АМАЛИ", "A2"),
    ("ROMAN MASLENNIKOV", r"ROMAN.*MASLENNIKOV|MASLENNIKOV.*ROMAN|МАСЛЕННИКОВ РОМАН", "A4"),
    ("OLESYA GOLOVINA", r"OLES.*GOLOVINA|GOLOVINA.*OLES|ГОЛОВИНА ОЛЕС", "A4"),
    ("YULIYA KORSHUNOVA", r"YULI.*KORSHUNOVA|KORSHUNOVA.*YULI|IULI.*KORSHUNOVA|КОРШУНОВА ЮЛИ", "A5"),
    ("STANISLAV KONDRATOV", r"STANISLAV.*KONDRATOV|KONDRATOV.*STANISLAV|КОНДРАТОВ СТАНИСЛАВ", "A5"),
]


def md_table(df, max_rows=None, max_len=80):
    if df is None or len(df) == 0:
        return "_нет данных_"
    if max_rows:
        df = df.head(max_rows)
    def cell(v):
        s = "" if pd.isna(v) else str(v)
        s = s.replace("|", "/").replace("\n", " ")
        return s if len(s) <= max_len else s[:max_len - 1] + "…"
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(cell(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep] + rows)


def first_name(v):
    return v.split("; ")[0] if isinstance(v, str) else ""


def load_features():
    feats = {}
    for f in sorted(OUT.glob("*_results.csv")):
        m = re.fullmatch(r"([A-E]\d+)_results\.csv", f.name)
        if m:
            feats[m.group(1)] = pd.read_csv(f, dtype={"person_id": str})
    return feats


def load_categories():
    cats = {}
    for f in sorted(OUT.glob("category_*_results.csv")):
        cats[f.stem.split("_")[1]] = pd.read_csv(f, dtype={"person_id": str})
    return cats


def main():
    feats, cats = load_features(), load_categories()
    if not feats:
        raise SystemExit("в analysis/output/ нет файлов <код>_results.csv - сначала запусти признаки")
    L = [f"# Результаты поиска подозрительного поведения",
         "", f"_Отчёт собран автоматически скриптом `analysis/build_report.py` "
             f"{datetime.now():%Y-%m-%d %H:%M} из файлов `analysis/output/`._", "",
         "Методика признаков: `docs/SPY_FEATURES.md`.", ""]

    L += ["## 1. Сводка по признакам", "",
          "| Код | Признак | Сила | Людей | Случаев (сумма count) |", "|---|---|---|---|---|"]
    for code in sorted(feats, key=lambda c: (c[0], int(c[1:]))):
        d = feats[code]
        cnt = d.get(f"{code}_count")
        total = int(cnt.sum()) if cnt is not None and len(d) else 0
        L.append(f"| {code} | {TITLES.get(code, '')} | {STRENGTH.get(code, '')} | {len(d)} | {total} |")
    missing = [c for c in TITLES if c not in feats]
    if missing:
        L += ["", f"Ещё не посчитаны: {', '.join(missing)}."]

    a3 = feats.get("A3")
    weak_a3 = set()
    if a3 is not None and "A3_kind" in a3:
        weak_a3 = set(a3.loc[a3["A3_kind"] == "namesakes", "person_id"])

    L += ["", "## 2. Категории", "",
          "Топ внутри категории: все люди с сильным признаком (не меньше 10 строк); сортировка - по числу "
          "сильных признаков, затем средних, затем по числу разных признаков; люди с именем выше безымянных "
          "записей. Так слабые массовые признаки (A6, E1) не вытесняют сильные.", ""]
    for cat, d in cats.items():
        fc = f"{cat}_flags_count"
        L += [f"### {cat} - {CATEGORY_TITLES.get(cat, '')}", "",
              f"Людей хотя бы с одним признаком: {len(d)}", ""]
        if fc in d:
            vc = d[fc].value_counts().sort_index()
            L += [md_table(pd.DataFrame({"разных признаков": vc.index, "людей": vc.values})), ""]
        trig = d[f"{cat}_triggered_features"].fillna("").str.split("; ")
        d = d.assign(
            сильных=[sum(STRENGTH.get(f) == "сильный" and not (f == "A3" and pid in weak_a3) for f in fs)
                     for fs, pid in zip(trig, d["person_id"])],
            средних=[sum(STRENGTH.get(f) == "средний" for f in fs) for fs in trig])
        d = d.assign(_named=d["name_variants"].notna())
        n_top = max(10, int((d["сильных"] > 0).sum()))
        top = d.sort_values(["сильных", "средних", fc, "_named", f"{cat}_total_occurrences"],
                            ascending=False).head(n_top)
        top = top.assign(имя=top["name_variants"].map(first_name))
        L += [f"Топ-{n_top} (все люди с сильным признаком, но не меньше 10):", "",
              md_table(top[["person_id", "имя", "сильных", "средних", fc, f"{cat}_total_occurrences",
                            f"{cat}_triggered_features"]]), ""]

    L += ["## 3. Признаки подробно", ""]
    for code in sorted(feats, key=lambda c: (c[0], int(c[1:]))):
        d = feats[code]
        L += [f"### {code} - {TITLES.get(code, '')} ({STRENGTH.get(code, '')})", "",
              f"Людей: {len(d)}", ""]
        thr = [c for c in d.columns if c.endswith(("_threshold", "_low_threshold", "_high_threshold", "_median",
                                                   "_global_rate"))]
        if thr and len(d):
            L += ["Пороги: " + "; ".join(f"`{c}` = {d[c].iloc[0]}" for c in thr), ""]
        for col in [f"{code}_kind", f"{code}_direction", f"{code}_reason", f"{code}_same_type", f"{code}_found_by"]:
            if col in d and len(d):
                vc = d[col].value_counts()
                L += [f"`{col}`: " + "; ".join(f"{k} - {v}" for k, v in vc.items()), ""]
        if len(d):
            ex = d.assign(имя=d["name_variants"].map(first_name))
            detail = [c for c in d.columns if c.startswith(f"{code}_") and c not in
                      (f"{code}_flag",) and not c.endswith(("_threshold", "_median", "_global_rate"))][:5]
            L += ["Примеры:", "", md_table(ex[["person_id", "имя"] + detail], max_rows=5), ""]

    allp = None
    for code, d in feats.items():
        part = d[["person_id", "name_variants"]].assign(feature=code)
        allp = part if allp is None else pd.concat([allp, part])
    allp["strong"] = allp["feature"].isin(STRONG) & ~((allp["feature"] == "A3") & allp["person_id"].isin(weak_a3))
    allp["category"] = allp["feature"].str[0]
    g = allp.groupby("person_id")
    rank = pd.DataFrame({
        "имя": g["name_variants"].first().map(first_name),
        "категорий": g["category"].nunique(),
        "признаков": g["feature"].nunique(),
        "сильных": g["strong"].sum().astype(int),
        "признаки": g["feature"].agg(lambda s: "; ".join(sorted(set(s), key=lambda c: (c[0], int(c[1:]))))),
    }).reset_index()
    rank = rank.sort_values(["сильных", "категорий", "признаков"], ascending=False)

    L += ["## 4. Общий рейтинг", "",
          f"Людей хотя бы с одним признаком: {len(rank)}; хотя бы с одним сильным: "
          f"{int((rank['сильных'] > 0).sum())}.", "",
          "Сортировка: число сильных признаков → число категорий → число признаков. "
          "Сильные: " + ", ".join(sorted(STRONG)) + " (A3 - только `same_person_possible`).", "",
          "| категорий | людей |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in rank["категорий"].value_counts().sort_index(ascending=False).items()]
    L += ["", "Топ-30:", "", md_table(rank.head(30)), ""]
    rank.to_csv(OUT / "report_ranking.csv", index=False)
    L += ["Полный рейтинг: `analysis/output/report_ranking.csv`.", ""]

    L += ["## 5. Проверка на известных случаях", "",
          "Люди с уже найденными аномалиями должны получить ожидаемые признаки. "
          "«не найден» - у человека нет ни одного сработавшего признака.", "",
          "| Кто | Ожидается | person_id | Сработавшие признаки | Итог |", "|---|---|---|---|---|"]
    for who, pat, exp in KNOWN:
        hit = rank[rank["person_id"].isin(
            allp.loc[allp["name_variants"].fillna("").str.upper().str.contains(pat, regex=True), "person_id"])]
        if len(hit):
            feats_found = "; ".join(sorted(set("; ".join(hit["признаки"]).split("; "))))
            ok = "OK" if exp in feats_found.split("; ") else "НЕТ ожидаемого признака"
            L.append(f"| {who} | {exp} | {', '.join(hit['person_id'])} | {feats_found} | {ok} |")
        else:
            L.append(f"| {who} | {exp} | - | - | не найден |")

    L += ["", "## 6. Служебные проверки", ""]
    chk = OUT / "D1_same_person_check.csv"
    if chk.exists():
        c = pd.read_csv(chk, dtype=str)
        vc = c["category"].value_counts()
        L += ["Пары «одно имя + ≥3 общих перелёта» (`D1_same_person_check.csv`):", "",
              md_table(pd.DataFrame({"категория": vc.index, "пар": vc.values})), ""]
    tp = OUT / "D1_two_passports_pairs.csv"
    if tp.exists():
        t = pd.read_csv(tp, dtype=str)
        vc = t["verdict"].value_counts()
        L += ["Два паспорта (`D1_two_passports_pairs.csv`): " +
              "; ".join(f"{k} - {v}" for k, v in vc.items()), ""]
    pairs = OUT / "D1_pairs.csv"
    if pairs.exists():
        p = pd.read_csv(pairs, dtype=str)
        p["shared_flights"] = p["shared_flights"].astype(int)
        L += [f"Попутчики (`D1_pairs.csv`): пар {len(p)}; максимум общих перелётов у пары - "
              f"{p['shared_flights'].max() if len(p) else 0}.", ""]

    HERE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"признаков: {len(feats)} ({', '.join(sorted(feats))}); категорий: {len(cats)} ({', '.join(cats)})")
    print(f"людей хотя бы с одним признаком: {len(rank)}; с сильным: {int((rank['сильных'] > 0).sum())}")
    print(f"-> {REPORT}\n-> {OUT / 'report_ranking.csv'}")


if __name__ == "__main__":
    main()
