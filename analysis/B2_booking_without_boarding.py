"""
B2. Бронь в Sirena есть, а посадки нет.

python3 analysis/B2_booking_without_boarding.py [--min-count 3] [--alpha 0.01]
"""
import argparse

from common import save, share_feature, union_events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=3)
    ap.add_argument("--alpha", type=float, default=0.01)
    a = ap.parse_args()
    u = union_events()
    res = share_feature(u, "B2", u["has_booking"], ~u["has_boarding"],
                        "бронь Sirena без посадки", a.min_count, a.alpha)
    save(res, "B2", ["B2_base", "B2_share", "B2_expected", "B2_pvalue", "B2_global_rate", "B2_with_partner"])


if __name__ == "__main__":
    main()
