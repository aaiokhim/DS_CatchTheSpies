"""
C3. Повторяющиеся короткие поездки за границу: вылет из России и возврат за 0-2 дня.

Страна аэропорта берётся из расписания участника 1.

python3 analysis/C3_short_international_trips.py [--max-days 2] [--min-trips 2]
"""
import argparse

import pandas as pd

from common import expand_groups, load_analysis_flights, load_timetable, save

RUSSIA = "Russian Federation"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=2)
    ap.add_argument("--min-trips", type=int, default=2)
    a = ap.parse_args()
    tt = load_timetable(["origin_airport", "origin_country", "destination_airport", "destination_country"])
    if tt is None:
        raise SystemExit("!! нет participants/p1_timetable/output/timetable_unique.csv (расписание участника 1) - C3 не посчитан")
    ac = pd.concat([tt[["origin_airport", "origin_country"]].set_axis(["a", "c"], axis=1),
                    tt[["destination_airport", "destination_country"]].set_axis(["a", "c"], axis=1)]).dropna()
    country = ac.groupby("a")["c"].agg(lambda x: x.value_counts().index[0]).to_dict()

    f = load_analysis_flights(["flight_event_id", "flight_number", "flight_date", "origin_airport",
                               "destination_airport", "origin_airport_source", "destination_airport_source",
                               "airport_still_broken", "skyteam_route_disagrees", "n_sources"])
    f["flight_date"] = pd.to_datetime(f["flight_date"], errors="coerce")
    f = f[f["flight_date"].notna() & f["origin_airport"].notna() & f["destination_airport"].notna()
          & ~f["airport_still_broken"] & ~f["skyteam_route_disagrees"]
          & f["origin_airport_source"].ne("skyteam") & f["destination_airport_source"].ne("skyteam")]
    f = (f.sort_values("n_sources", ascending=False)
          .drop_duplicates(["analysis_person_id", "flight_number", "flight_date"]))
    f = f.assign(oc=f["origin_airport"].map(country), dc=f["destination_airport"].map(country)).dropna(subset=["oc", "dc"])
    f["out"] = f["oc"].eq(RUSSIA) & f["dc"].ne(RUSSIA)
    f["back"] = f["oc"].ne(RUSSIA) & f["dc"].eq(RUSSIA)
    print(f"перелётов со страной: {len(f)}; вылетов из России: {int(f['out'].sum())}; "
          f"возвращений: {int(f['back'].sum())}")
    both = f.groupby("analysis_person_id")[["out", "back"]].any()
    f = f[f["analysis_person_id"].isin(both[both["out"] & both["back"]].index)].sort_values(
        ["analysis_person_id", "flight_date"])

    rows = []
    for pid, grp in f.groupby("analysis_person_id"):
        outbound, trips = None, []
        for r in grp.itertuples():
            if r.out:
                outbound = r
            elif r.back and outbound is not None:
                days = (r.flight_date - outbound.flight_date).days
                if 0 <= days <= a.max_days:
                    trips.append(f"{outbound.flight_number} {outbound.flight_date.date()} "
                                 f"{outbound.origin_airport}-{outbound.destination_airport} -> "
                                 f"{r.flight_number} {r.flight_date.date()} {r.origin_airport}-"
                                 f"{r.destination_airport} ({days} дн.)")
                outbound = None
        if len(trips) >= a.min_trips:
            rows.append((pid, 1, len(trips), " | ".join(trips[:5])))
    res = pd.DataFrame(rows, columns=["analysis_person_id", "C3_flag", "C3_count", "C3_examples"])
    save(expand_groups(res, "C3"), "C3", ["C3_examples", "C3_group"])


if __name__ == "__main__":
    main()
