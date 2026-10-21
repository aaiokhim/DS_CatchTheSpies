"""
B1. Посадка на рейс SU есть, а брони в Sirena нет.

Человек сравнивается с общей долей по базе (биномиальный тест, поправка Бонферрони).

python3 analysis/B1_boarding_without_booking.py [--min-count 3] [--alpha 0.01]
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
    res = share_feature(u, "B1", su & u["has_boarding"], ~u["has_booking"],
                        "посадка без брони Sirena (рейсы SU)", a.min_count, a.alpha)
    save(res, "B1", ["B1_base", "B1_share", "B1_expected", "B1_pvalue", "B1_global_rate", "B1_with_partner"])


if __name__ == "__main__":
    main()
