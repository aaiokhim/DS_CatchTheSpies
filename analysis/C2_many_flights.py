"""
C2. Аномально много перелётов (порог Q3 + 3*IQR).

python3 analysis/C2_many_flights.py
"""
import math

from common import expand_groups, load_analysis_flights, save


def main():
    f = load_analysis_flights(["flight_number", "flight_date"]).dropna(subset=["flight_date"])
    f = f.drop_duplicates(["analysis_person_id", "flight_number", "flight_date"])
    n = f.groupby("analysis_person_id").size()
    ref = n[n > 1]
    q1, q3 = ref.quantile(0.25), ref.quantile(0.75)
    thr = math.ceil(q3 + 3 * (q3 - q1))
    print(f"людей с > 1 перелётом: {len(ref)}; Q1 {q1:g}, Q3 {q3:g}; порог > {thr}")
    res = n[n > thr].rename("C2_count").reset_index()
    res["C2_flag"] = 1
    res["C2_threshold"] = thr
    save(expand_groups(res, "C2"), "C2", ["C2_threshold", "C2_group"])


if __name__ == "__main__":
    main()
