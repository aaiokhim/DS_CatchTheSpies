"""
C1. Невозможная последовательность перелётов: следующий вылет раньше прилёта с предыдущего.

Время прилёта из данных, если его нет - из расписания участника 1.

python3 analysis/C1_impossible_route.py
"""
import pandas as pd

from common import expand_groups, load_analysis_flights, load_timetable, save


def main():
    cols = ["flight_event_id", "flight_number", "flight_date", "departure_time", "arrival_date",
            "arrival_time", "origin_airport", "destination_airport", "origin_city", "destination_city",
            "origin_airport_source", "destination_airport_source", "airport_still_broken",
            "skyteam_route_disagrees", "n_sources"]
    f = load_analysis_flights(cols)
    f = f[f["flight_date"].notna() & f["departure_time"].notna() & f["origin_airport"].notna()
          & f["destination_airport"].notna() & ~f["airport_still_broken"] & ~f["skyteam_route_disagrees"]
          & f["origin_airport_source"].ne("skyteam") & f["destination_airport_source"].ne("skyteam")].copy()
    f["departure"] = pd.to_datetime(f["flight_date"] + " " + f["departure_time"], errors="coerce")
    f = f.dropna(subset=["departure"])
    f = (f.sort_values(["n_sources", "flight_event_id"], ascending=[False, True])
          .drop_duplicates(["analysis_person_id", "flight_number", "flight_date"]))

    f["arrival"] = pd.to_datetime(f["arrival_date"] + " " + f["arrival_time"], errors="coerce")
    own = f["arrival"].notna().sum()
    tt = load_timetable(["flight_number", "origin_airport", "origin_city", "destination_airport",
                         "destination_city", "departure_time", "arrival_time", "arrival_next_day"])
    city = {}
    if tt is not None:
        clock = tt["arrival_time"].str.extract(r"(\d+):(\d+)").astype(float)
        nd = tt["arrival_next_day"].str.extract(r"(-?\d+)")[0].astype(float).fillna(0)
        tt["arr_min"] = clock[0] * 60 + clock[1] + nd * 1440
        sched = tt.groupby(["flight_number", "origin_airport", "destination_airport", "departure_time"],
                           as_index=False)["arr_min"].median()
        f = f.merge(sched, on=["flight_number", "origin_airport", "destination_airport", "departure_time"],
                    how="left")
        from_tt = f["arrival"].isna() & f["arr_min"].notna()
        f.loc[from_tt, "arrival"] = f.loc[from_tt, "departure"].dt.normalize() + \
            pd.to_timedelta(f.loc[from_tt, "arr_min"], unit="m")
        ac = pd.concat([tt[["origin_airport", "origin_city"]].set_axis(["a", "c"], axis=1),
                        tt[["destination_airport", "destination_city"]].set_axis(["a", "c"], axis=1)]).dropna()
        city = ac.groupby("a")["c"].agg(lambda x: x.value_counts().index[0]).str.upper().to_dict()
    else:
        print("!! нет расписания участника 1 - время прилёта только из своих данных")
    print(f"перелётов: {len(f)}; время прилёта известно: {int(f['arrival'].notna().sum())} "
          f"(из своих данных {own})")

    def city_of(ap, c):
        return ap.map(city).fillna(c.str.upper()).fillna(ap)
    f["o_city"] = city_of(f["origin_airport"], f["origin_city"])
    f["d_city"] = city_of(f["destination_airport"], f["destination_city"])

    f = f.sort_values(["analysis_person_id", "departure"])
    g = f.groupby("analysis_person_id")
    for c in ["flight_number", "departure", "origin_airport", "destination_airport", "d_city", "arrival"]:
        f["prev_" + c] = g[c].shift()
    f["gap_hours"] = (f["departure"] - f["prev_arrival"]).dt.total_seconds() / 3600
    same_city = f["prev_d_city"].eq(f["o_city"])
    bad = f["prev_arrival"].notna() & (
        (same_city & f["gap_hours"].lt(0))
        | (~same_city & f["departure"].dt.normalize().lt(f["prev_arrival"].dt.normalize())))
    cases = f[bad].copy()
    print(f"проверено переходов: {int(f['prev_arrival'].notna().sum())}; невозможных: {len(cases)}")
    cases["example"] = [
        f"{r.prev_flight_number} {r.prev_origin_airport}-{r.prev_destination_airport} {r.prev_departure} -> "
        f"{r.flight_number} {r.origin_airport}-{r.destination_airport} {r.departure} (запас {r.gap_hours:.1f} ч.)"
        for r in cases.itertuples()]
    res = cases.groupby("analysis_person_id").agg(
        C1_count=("example", "size"), C1_examples=("example", lambda x: " | ".join(x.head(5)))).reset_index()
    res["C1_flag"] = 1
    save(expand_groups(res, "C1"), "C1", ["C1_examples", "C1_group"])


if __name__ == "__main__":
    main()
