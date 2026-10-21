"""
B4. Один номер билета у разных людей (не считая двойников).

python3 analysis/B4_shared_ticket.py
"""
import pandas as pd

from common import MERGED, links, save, split_partners, read_flights_all


def main():
    F = read_flights_all(columns=["source_record_id", "e_ticket"]).dropna()
    F = F.merge(links(), on="source_record_id")[["e_ticket", "person_id"]].drop_duplicates()
    n = F.groupby("e_ticket")["person_id"].transform("nunique")
    cand = F[n > 1]
    partners = split_partners()
    rows = []
    for t, g in cand.groupby("e_ticket"):
        pids = set(g["person_id"])
        first = next(iter(pids))
        if pids <= {first} | partners.get(first, set()):
            continue
        for pid in pids:
            rows.append((pid, t, "; ".join(sorted(pids - {pid}))))
    print(f"билетов: {F['e_ticket'].nunique()}; у разных person_id: {cand['e_ticket'].nunique()}; "
          f"после исключения «двойников»: {len({r[1] for r in rows})}")
    d = pd.DataFrame(rows, columns=["person_id", "ticket", "others"])
    g = d.groupby("person_id")
    res = pd.DataFrame({"B4_flag": 1, "B4_count": g["ticket"].nunique(),
                        "B4_tickets": g["ticket"].agg(lambda s: "; ".join(sorted(set(s))[:10])),
                        "B4_other_person_ids": g["others"].agg(lambda s: "; ".join(sorted(set(s))))}
                       ).reset_index() if len(d) else pd.DataFrame(columns=["person_id", "B4_flag", "B4_count"])
    save(res, "B4", ["B4_tickets", "B4_other_person_ids"])


if __name__ == "__main__":
    main()
