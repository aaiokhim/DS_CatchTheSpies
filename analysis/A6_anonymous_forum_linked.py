"""
A6. Профиль форума без имени, который склейка связала с человеком, чьё имя известно из других источников.

python3 analysis/A6_anonymous_forum_linked.py
"""
import pandas as pd

from common import MERGED, RES, links, name_any, save, PASSENGERS_ALL


def main():
    P = pd.read_parquet(PASSENGERS_ALL,
                        columns=["source_record_id", "source", "full_name_raw", "first_name_raw",
                                 "middle_name_raw", "last_name_raw"])
    P["name"] = name_any(P)
    P = P.merge(links(), on="source_record_id")
    anon = P[(P["source"] == "forum") & P["name"].isna()]
    named = P[P["name"].notna()]
    named_src = named.groupby("person_id")["source"].agg(lambda s: "; ".join(sorted(set(s))))
    hit = anon[anon["person_id"].isin(named_src.index)]
    print(f"анонимных профилей форума: {len(anon)}; связаны с именем из других источников: {len(hit)}")

    g = hit.groupby("person_id")
    res = pd.DataFrame({
        "A6_flag": 1,
        "A6_count": g.size(),
        "A6_forum_profiles": g["source_record_id"].agg(lambda s: "; ".join(sorted(s))),
    }).reset_index()
    res["A6_named_sources"] = res["person_id"].map(named_src)
    save(res, "A6", ["A6_forum_profiles", "A6_named_sources"])


if __name__ == "__main__":
    main()
