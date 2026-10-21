"""
Общие функции для скриптов признаков: нормализация имён, двойники, группы person_id,
расчёт B1-B3, загрузка перелётов и запись результата в общем формате.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "paths.py").exists())))
from paths import (MERGED, PASSENGERS_ALL, RESOLVED as RES, ANALYSIS_OUT as OUT, ANALYSIS_REPORTS,
                   TIMETABLE, P1, read_flights_all)

CYR = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               ["A", "B", "V", "G", "D", "E", "E", "ZH", "Z", "I", "I", "K", "L", "M", "N", "O", "P",
                "R", "S", "T", "U", "F", "KH", "TS", "CH", "SH", "SHCH", "", "Y", "", "E", "IU", "IA"]))
PATRONYMIC = re.compile(r"(VICH|VNA|ICH|ICHNA)$")


def skeleton(name):
    if not isinstance(name, str) or not name.strip():
        return ""
    s = "".join(CYR.get(ch, ch) for ch in name.upper())
    s = re.sub(r"['’`.\-]", "", s)
    words = []
    for w in s.split():
        w = re.sub(r"(.)\1+", r"\1", w.replace("X", "KS").replace("TC", "TS").replace("Y", "I"))
        if len(w) > 1:
            words.append(w)
    if len(words) >= 3:
        words = [w for w in words if not PATRONYMIC.search(w)] or words
    return " ".join(sorted(set(words)))


def patronymic_letter(middle, full):
    for src in (middle, full):
        if not isinstance(src, str) or not src.strip():
            continue
        words = "".join(CYR.get(ch, ch) for ch in src.upper()).replace(".", " ").split()
        if src is middle and words:
            return words[0][0]
        for w in words:
            if PATRONYMIC.search(w):
                return w[0]
    return None


def name_any(P):
    parts = (P["first_name_raw"].fillna("") + " " + P["middle_name_raw"].fillna("") + " "
             + P["last_name_raw"].fillna("")).str.replace(r"\s+", " ", regex=True).str.strip()
    return P["full_name_raw"].fillna(parts.mask(parts == ""))


def doc_type(d):
    if not isinstance(d, str):
        return ""
    return {10: "internal", 9: "foreign"}.get(len(d), f"other{len(d)}")


def links():
    return pd.read_parquet(RES / "record_links.parquet", columns=["source_record_id", "person_id"])


def person_names():
    return pd.read_parquet(RES / "persons.parquet", columns=["person_id", "name_variants"])


def split_partners(verbose=True):
    path = OUT / "D1_same_person_candidates.csv"
    if not path.exists():
        print("!! нет analysis/output/D1_same_person_candidates.csv - «двойники» не учитываются "
              "(запусти analysis/D1_cotravelers.py)")
        return {}
    pr = pd.read_csv(path, dtype=str)[["person_id_1", "person_id_2"]]
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "birth_dates", "sex"]).set_index("person_id")

    def as_set(v):
        return {x.strip() for x in str(v).split(";") if x.strip()} if pd.notna(v) else set()

    bd = {k: as_set(v) for k, v in per["birth_dates"].dropna().items()}
    sx = {k: as_set(v) for k, v in per["sex"].dropna().items()}
    out, n_birth, n_sex = {}, 0, 0
    for a, b in zip(pr.person_id_1, pr.person_id_2):
        b1, b2 = bd.get(a, set()), bd.get(b, set())
        if b1 and b2 and not (b1 & b2):
            n_birth += 1
            continue
        s1, s2 = sx.get(a, set()), sx.get(b, set())
        if s1 and s2 and not (s1 & s2):
            n_sex += 1
            continue
        out.setdefault(a, set()).add(b)
        out.setdefault(b, set()).add(a)
    if verbose:
        print(f"«двойники»: пар-кандидатов {len(pr)}; исключено: разные даты рождения {n_birth}, "
              f"разный пол {n_sex}; используется {len(pr) - n_birth - n_sex}")
    return out


def save(df, code, cols_extra):
    OUT.mkdir(parents=True, exist_ok=True)
    df = df.merge(person_names(), on="person_id", how="left")
    cols = ["person_id", "name_variants", f"{code}_flag", f"{code}_count"] + cols_extra
    for c in cols:
        if c not in df:
            df[c] = pd.NA
    df = df[cols].sort_values(f"{code}_count", ascending=False)
    assert df["person_id"].is_unique, f"{code}: person_id повторяется"
    df.to_csv(OUT / f"{code}_results.csv", index=False)
    print(f"{code} сработал у {len(df)} человек -> {OUT / f'{code}_results.csv'}")
    return df


LOYALTY_SRC = {"pointz", "skyteam"}
BOOKING_SRC = {"sirena"}
BOARDING_SRC = {"boarding_data", "boarding_passes"}
FORUM_SRC = {"forum"}


def union_events():
    ev = pd.read_parquet(RES / "flight_events.parquet",
                         columns=["person_id", "flight_number", "flight_date", "sources"])
    s = ev["sources"].fillna("")
    for name, group in [("has_loyalty", LOYALTY_SRC), ("has_booking", BOOKING_SRC),
                        ("has_boarding", BOARDING_SRC), ("has_forum", FORUM_SRC)]:
        ev[name] = s.str.contains("|".join(sorted(group)), regex=True)
    ev = ev.drop(columns="sources")

    partners = split_partners()
    pairs = [(p, m) for p, ms in partners.items() for m in ms]
    members = pd.DataFrame(pairs, columns=["person_id", "member"])
    own = ev.rename(columns={"person_id": "member"}).assign(person_id=lambda d: d["member"], with_partner=False)
    if len(members):
        part = members.merge(ev.rename(columns={"person_id": "member"}), on="member").assign(with_partner=True)
        allev = pd.concat([own, part], ignore_index=True)
    else:
        allev = own
    flags = ["has_loyalty", "has_booking", "has_boarding", "has_forum"]
    u = (allev.groupby(["person_id", "flight_number", "flight_date"])[flags + ["with_partner"]]
              .max().reset_index())
    return u


def binom_sf(k, n, p):
    from math import comb
    if k <= 0:
        return 1.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    return min(1.0, sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def share_feature(u, code, base_mask, hit_mask, title, min_count=3, alpha=0.01):
    d = u.assign(base=base_mask, hit=base_mask & hit_mask)
    st = d.groupby("person_id").agg(base=("base", "sum"), count=("hit", "sum"),
                                    with_partner=("with_partner", "any")).reset_index()
    st = st[st["base"] > 0]
    p = st["count"].sum() / st["base"].sum()
    print(f"{code} - {title}: подходящих перелётов {int(st['base'].sum())}, из них с признаком "
          f"{int(st['count'].sum())}; общая доля {p:.3f}")
    cand = st[st["count"] >= min_count].copy()
    cache = {}
    cand["pvalue"] = [cache.setdefault((int(k), int(n)), binom_sf(int(k), int(n), p))
                      for k, n in zip(cand["count"], cand["base"])]
    alpha_corr = alpha / max(len(cand), 1)
    hit = cand[cand["pvalue"] < alpha_corr]
    res = pd.DataFrame({
        "person_id": hit["person_id"], f"{code}_flag": 1, f"{code}_count": hit["count"].astype(int),
        f"{code}_base": hit["base"].astype(int), f"{code}_share": (hit["count"] / hit["base"]).round(3),
        f"{code}_expected": (hit["base"] * p).round(1), f"{code}_pvalue": hit["pvalue"].map(lambda x: f"{x:.2e}"),
        f"{code}_global_rate": round(p, 4), f"{code}_with_partner": hit["with_partner"].astype(int),
    })
    print(f"   кандидатов (count ≥ {min_count}): {len(cand)}; значимо больше общей доли (p < {alpha}/{len(cand)} = {alpha_corr:.1e}, Бонферрони): {len(res)}")
    print(f"   без поправки (p < {alpha}) было бы {int((cand['pvalue'] < alpha).sum())} - примерно {alpha * len(cand):.0f} из них случайно")
    return res


_GROUPS = None


def analysis_groups():
    global _GROUPS
    if _GROUPS is not None:
        return _GROUPS
    partners = split_partners()
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, ms in partners.items():
        for b in ms:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    g = pd.DataFrame({"person_id": list(parent)})
    g["analysis_person_id"] = g["person_id"].map(find)
    print(f"групп из нескольких person_id: {g['analysis_person_id'].nunique()} "
          f"({len(g)} person_id)")
    _GROUPS = g
    return g


def load_analysis_flights(columns):
    cols = list(dict.fromkeys(["person_id"] + list(columns)))
    ev = pd.read_parquet(RES / "flight_events.parquet", columns=cols)
    g = analysis_groups()
    ev = ev.merge(g, on="person_id", how="left")
    ev["analysis_person_id"] = ev["analysis_person_id"].fillna(ev["person_id"])
    for c in ev.columns:
        if c.startswith(("airport_", "skyteam_", "route_", "has_")):
            ev[c] = ev[c].astype("boolean").fillna(False).astype(bool)
    return ev


def expand_groups(res, code):
    g = analysis_groups()
    members = g.groupby("analysis_person_id")["person_id"].agg(lambda s: "; ".join(sorted(s)))
    out = res.merge(g, on="analysis_person_id", how="left")
    out["person_id"] = out["person_id"].fillna(out["analysis_person_id"])
    out[f"{code}_group"] = out["analysis_person_id"].map(members).fillna("")
    return out.drop(columns="analysis_person_id")


def load_timetable(columns):
    cands = [TIMETABLE] + sorted(P1.rglob("timetable*unique*.csv"))
    for p in cands:
        if p.exists():
            return pd.read_csv(p, usecols=columns, dtype=str)
    return None
