"""
C5. Перелёты в редкие аэропорты (нижние 5% по частоте).

python3 analysis/C5_rare_destinations.py [--percentile 0.05] [--min-flights 2]
"""
import argparse
import math

from common import expand_groups, load_analysis_flights, save


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--percentile", type=float, default=0.05)
    ap.add_argument("--min-flights", type=int, default=2)
    a = ap.parse_args()
    f = load_analysis_flights(["flight_number", "flight_date", "destination_airport",
                               "destination_airport_source", "airport_still_broken",
                               "skyteam_route_disagrees", "n_sources"])
    f = f[f["flight_date"].notna() & f["destination_airport"].notna() & ~f["airport_still_broken"]
          & ~f["skyteam_route_disagrees"] & f["destination_airport_source"].ne("skyteam")]
    f = (f.sort_values("n_sources", ascending=False)
          .drop_duplicates(["analysis_person_id", "flight_number", "flight_date"]))
    cnt = f["destination_airport"].value_counts()
    limit = math.ceil(cnt.quantile(a.percentile, interpolation="higher"))
    rare = cnt[cnt <= limit]
    print(f"аэропортов назначения: {len(cnt)}; редкие (≤ {limit} перелётов): {len(rare)}")
    r = f[f["destination_airport"].isin(rare.index)].copy()
    r["detail"] = r["destination_airport"].map(lambda x: f"{x} (всего {rare[x]})")
    st = r.groupby("analysis_person_id").agg(
        C5_count=("destination_airport", "size"),
        C5_airports=("detail", lambda x: "; ".join(sorted(set(x))))).reset_index()
    res = st[st["C5_count"] >= a.min_flights].copy()
    res["C5_flag"] = 1
    res["C5_threshold"] = limit
    save(expand_groups(res, "C5"), "C5", ["C5_threshold", "C5_airports", "C5_group"])


if __name__ == "__main__":
    main()
