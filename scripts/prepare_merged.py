"""
Кладёт готовые общие таблицы в integration/merged/: копирует passengers_all.parquet и режет
flights_all.parquet на файлы по источникам (GitHub не принимает файлы больше 100 МБ).

python3 scripts/prepare_merged.py --src ~/DS/merged
"""
import argparse
import shutil
import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import FLIGHT_PARTS, FLIGHTS_ALL, MERGED, PASSENGERS_ALL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="папка со старыми passengers_all.parquet и flights_all.parquet")
    src = Path(ap.parse_args().src).expanduser()

    MERGED.mkdir(parents=True, exist_ok=True)
    shutil.copy(src / "passengers_all.parquet", PASSENGERS_ALL)
    print(f"passengers_all.parquet: {pq.ParquetFile(PASSENGERS_ALL).metadata.num_rows} строк")

    FLIGHTS_ALL.mkdir(parents=True, exist_ok=True)
    for p in FLIGHTS_ALL.glob("*.parquet"):
        p.unlink()
    part_of = {p.split("_", 1)[1]: p for p in FLIGHT_PARTS}
    f = pq.ParquetFile(src / "flights_all.parquet")
    writers, counts = {}, {}
    for batch in f.iter_batches(batch_size=200_000):
        sources = batch.column("source").to_pylist()
        start = 0
        for i in range(1, len(sources) + 1):
            if i == len(sources) or sources[i] != sources[start]:
                s = sources[start]
                if s not in writers:
                    writers[s] = pq.ParquetWriter(FLIGHTS_ALL / f"{part_of[s]}.parquet", f.schema_arrow)
                writers[s].write_batch(batch.slice(start, i - start))
                counts[s] = counts.get(s, 0) + i - start
                start = i
    for w in writers.values():
        w.close()

    total = f.metadata.num_rows
    for s, n in counts.items():
        size = (FLIGHTS_ALL / f"{part_of[s]}.parquet").stat().st_size / 2**20
        print(f"flights_all/{part_of[s]}.parquet: {n} строк, {size:.0f} МБ")
    assert sum(counts.values()) == total, "число строк не совпало"
    print(f"flights_all: {total} строк, совпадает с исходным файлом")


if __name__ == "__main__":
    main()
