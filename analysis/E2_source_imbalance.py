"""
E2. Перекос между перелётами, которые видны только в милях, и перелётами только в бронях и посадках.

python3 analysis/E2_source_imbalance.py [--min-flights 5] [--min-side 3]
"""
import argparse

import pandas as pd

from common import RES, OUT

from common import split_partners


LOYALTY = {"pointz", "skyteam"}
TRAVEL = {"sirena", "boarding_data", "boarding_passes"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-flights", type=int, default=5)
    ap.add_argument("--min-diff", type=float, default=0.5)
    ap.add_argument("--min-side", type=int, default=3)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    ev = pd.read_parquet(RES / "flight_events.parquet", columns=["person_id", "sources"])
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "name_variants"])

    src = ev["sources"].str.split("; ")
    ev["L"] = src.map(lambda s: bool(LOYALTY & set(s)))
    ev["T"] = src.map(lambda s: bool(TRAVEL & set(s)))
    ev = ev[ev["L"] | ev["T"]]

    ev = ev.assign(loyalty_only=ev["L"] & ~ev["T"], travel_only=ev["T"] & ~ev["L"], both=ev["L"] & ev["T"])
    st = ev.groupby("person_id")[["loyalty_only", "travel_only", "both"]].sum().astype(int)
    st["n"] = st.sum(axis=1)
    st = st[st["n"] >= a.min_flights]
    st["imbalance"] = (st["loyalty_only"] - st["travel_only"]) / st["n"]

    q1, med, q3 = st["imbalance"].quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    if iqr > 0:
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    else:
        lo, hi = med - a.min_diff, med + a.min_diff
    print(f"людей с ≥{a.min_flights} перелётами: {len(st)}")
    print(st["imbalance"].describe().to_string())
    print(f"пороги: imbalance ≤ {lo:.3f} или ≥ {hi:.3f} (медиана {med:.3f}); "
          f"на перевешивающей стороне ≥ {a.min_side} перелётов")
    if hi > 1 or lo < -1:
        print("   (порог за пределами [-1, 1] недостижим - выбросы возможны только с одной стороны)")

    st["split_partner"] = ""
    cand = OUT / "D1_same_person_candidates.csv"
    if cand.exists():
        pr = pd.DataFrame([(a, b) for a, ms in split_partners().items() for b in ms],
                          columns=["person_id_1", "person_id_2"])
        partner = pr.groupby("person_id_1")["person_id_2"].agg("; ".join)
        st["split_partner"] = st.index.map(partner).fillna("")
        full = pd.read_parquet(RES / "flight_events.parquet", columns=["person_id", "flight_number", "flight_date", "sources"])
        grp = pr.rename(columns={"person_id_1": "person_id", "person_id_2": "partner"})
        groups = pd.concat([pd.DataFrame({"person_id": st.index, "member": st.index}),
                            grp[grp["person_id"].isin(st.index)].rename(columns={"partner": "member"})])
        u = groups.merge(full, left_on="member", right_on="person_id", suffixes=("", "_m"))
        u = u.groupby(["person_id", "flight_number", "flight_date"])["sources"].agg("; ".join).reset_index()
        us = u["sources"].str.split("; ")
        uL, uT = us.map(lambda s: bool(LOYALTY & set(s))), us.map(lambda s: bool(TRAVEL & set(s)))
        u = u.assign(lo=uL & ~uT, to=uT & ~uL)[uL | uT]
        uu = u.groupby("person_id")[["lo", "to"]].sum()
        uu["n"] = u.groupby("person_id").size()
        st["union_imbalance"] = ((uu["lo"] - uu["to"]) / uu["n"]).reindex(st.index)
    else:
        print("!! нет D1_same_person_candidates.csv - разрез склейки не учитывается (запусти D1 раньше)")
        st["union_imbalance"] = st["imbalance"]

    side = st["travel_only"].where(st["imbalance"] < med, st["loyalty_only"])
    extreme = ((st["imbalance"] <= lo) | (st["imbalance"] >= hi)) & (side >= a.min_side)
    extreme_union = (st["union_imbalance"] <= lo) | (st["union_imbalance"] >= hi)
    explained = extreme & (st["split_partner"] != "") & ~extreme_union
    print(f"перекос у {int(extreme.sum())}; из них объясняется разрезом склейки (у «двойника» "
          f"недостающие перелёты): {int(explained.sum())} - не считаются")
    hit = st[extreme & ~explained].copy()
    hit["E2_direction"] = hit["imbalance"].map(lambda x: "loyalty_heavy" if x > med else "travel_heavy")
    hit["E2_count"] = hit["travel_only"].where(hit["E2_direction"] == "travel_heavy", hit["loyalty_only"])
    res = pd.DataFrame({
        "person_id": hit.index, "E2_flag": 1, "E2_count": hit["E2_count"].values,
        "E2_direction": hit["E2_direction"].values, "E2_imbalance": hit["imbalance"].round(3).values,
        "E2_n_flights": hit["n"].values, "E2_loyalty_only": hit["loyalty_only"].values,
        "E2_travel_only": hit["travel_only"].values, "E2_both": hit["both"].values,
        "E2_low_threshold": round(lo, 3), "E2_high_threshold": round(hi, 3), "E2_median": round(med, 3),
        "E2_split_partner": hit["split_partner"].values,
        "E2_union_imbalance": hit["union_imbalance"].round(3).values,
    }).merge(per, on="person_id", how="left")
    cols = ["person_id", "name_variants"] + [c for c in res.columns if c.startswith("E2_")]
    res = res[cols].sort_values("E2_imbalance", key=abs, ascending=False)
    res.to_csv(OUT / "E2_results.csv", index=False)
    print(f"E2 сработал у {len(res)} человек "
          f"({(res.E2_direction == 'loyalty_heavy').sum()} loyalty_heavy, "
          f"{(res.E2_direction == 'travel_heavy').sum()} travel_heavy) -> {OUT / 'E2_results.csv'}")


if __name__ == "__main__":
    main()
