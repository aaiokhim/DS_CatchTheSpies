"""
D2. Одна бронь (PNR + рейс + дата) у разных людей.

python3 analysis/D2_shared_pnr.py
"""

import pandas as pd

from common import MERGED, RES, OUT, read_flights_all


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = read_flights_all(columns=["source_record_id", "pnr", "flight_number", "flight_date"]).dropna(subset=["pnr"])
    links = pd.read_parquet(RES / "record_links.parquet", columns=["source_record_id", "person_id"])
    per = pd.read_parquet(RES / "persons.parquet", columns=["person_id", "name_variants"])

    f = f.merge(links, on="source_record_id")
    f["booking"] = f["pnr"] + "|" + f["flight_number"] + "|" + f["flight_date"]
    bp = f[["booking", "person_id"]].drop_duplicates()
    n = bp.groupby("booking")["person_id"].transform("nunique")
    grp = bp[n > 1]
    print(f"броней с PNR: {bp['booking'].nunique()}; групповых (≥2 разных людей): {grp['booking'].nunique()}")

    pairs = grp.merge(grp, on="booking", suffixes=("_1", "_2"))
    pairs = pairs[pairs["person_id_1"] < pairs["person_id_2"]]
    pairs.groupby(["person_id_1", "person_id_2"]).agg(
        shared_bookings=("booking", "nunique"),
        bookings=("booking", lambda s: "; ".join(sorted(set(s))[:5]))).reset_index() \
        .to_csv(OUT / "D2_pairs.csv", index=False)

    partners = pd.concat([pairs.rename(columns={"person_id_1": "person_id", "person_id_2": "p"}),
                          pairs.rename(columns={"person_id_2": "person_id", "person_id_1": "p"})])
    g = grp.groupby("person_id")
    res = pd.DataFrame({
        "D2_flag": 1,
        "D2_count": g["booking"].nunique(),
        "D2_partners": partners.groupby("person_id")["p"].apply(lambda s: "; ".join(sorted(set(s))[:10])),
        "D2_pnrs": g["booking"].apply(lambda s: "; ".join(sorted(set(s))[:5])),
    }).reset_index().merge(per, on="person_id", how="left")
    res = res[["person_id", "name_variants", "D2_flag", "D2_count", "D2_partners", "D2_pnrs"]] \
        .sort_values("D2_count", ascending=False)
    res.to_csv(OUT / "D2_results.csv", index=False)
    print(f"D2 сработал у {len(res)} человек; из них с ≥2 групповыми бронями: {int((res.D2_count >= 2).sum())}"
          f"\n-> {OUT / 'D2_results.csv'}")


if __name__ == "__main__":
    main()
