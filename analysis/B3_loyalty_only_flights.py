"""
B3. Рейс SU виден только в Pointz или SkyTeam, без брони и посадки.

python3 analysis/B3_loyalty_only_flights.py [--min-count 3] [--alpha 0.01]
"""
import argparse

from common import save, share_feature, union_events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=3)
    ap.add_argument("--alpha", type=float, default=0.01)
    a = ap.parse_args()
    u = union_events()
    su = u["flight_number"].str.startswith("SU")
    res = share_feature(u, "B3", su & u["has_loyalty"], ~u["has_booking"] & ~u["has_boarding"],
                        "рейсы SU только в loyalty-источниках", a.min_count, a.alpha)
    save(res, "B3", ["B3_base", "B3_share", "B3_expected", "B3_pvalue", "B3_global_rate", "B3_with_partner"])


if __name__ == "__main__":
    main()
