"""
C6. После долгой паузы резкий всплеск перелётов.

python3 analysis/C6_bursty_activity.py [--gap 90] [--window 14] [--min-flights 4]
"""
import argparse

import numpy as np
import pandas as pd

from common import expand_groups, load_analysis_flights, save


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=int, default=90)
    ap.add_argument("--window", type=int, default=14)
    ap.add_argument("--min-flights", type=int, default=4)
    a = ap.parse_args()
    f = load_analysis_flights(["flight_number", "flight_date"])
    f["flight_date"] = pd.to_datetime(f["flight_date"], errors="coerce")
    f = (f.dropna(subset=["flight_date"])
          .drop_duplicates(["analysis_person_id", "flight_number", "flight_date"])
          .sort_values(["analysis_person_id", "flight_date"]))
    f["gap_days"] = f.groupby("analysis_person_id")["flight_date"].diff().dt.days
    starts = f[f["gap_days"] > a.gap]
    dates = {pid: g["flight_date"].to_numpy() for pid, g in
             f[f["analysis_person_id"].isin(starts["analysis_person_id"])].groupby("analysis_person_id")}
    rows, sizes = [], []
    for pid, st in starts.groupby("analysis_person_id"):
        d = dates[pid]
        bursts, bs = [], []
        for r in st.itertuples():
            end = r.flight_date + pd.Timedelta(days=a.window)
            k = int(np.searchsorted(d, end.to_datetime64(), "right") -
                    np.searchsorted(d, r.flight_date.to_datetime64(), "left"))
            sizes.append(k)
            if k >= a.min_flights:
                bs.append(k)
                bursts.append(f"пауза {int(r.gap_days)} дн.; с {r.flight_date.date()} - {k} рейсов за {a.window} дн.")
        if bursts:
            rows.append((pid, 1, len(bursts), max(bs), " | ".join(bursts[:5])))
    print(f"пауз > {a.gap} дн.: {len(sizes)}; рейсов за {a.window} дн. после паузы: "
          f"медиана {np.median(sizes) if sizes else 0:g}, максимум {max(sizes) if sizes else 0}")
    res = pd.DataFrame(rows, columns=["analysis_person_id", "C6_flag", "C6_count", "C6_max_burst_flights",
                                      "C6_examples"])
    save(expand_groups(res, "C6"), "C6", ["C6_max_burst_flights", "C6_examples", "C6_group"])


if __name__ == "__main__":
    main()
