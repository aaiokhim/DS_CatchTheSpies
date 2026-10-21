"""
Проверка перед git push: нет ли файлов больше 50 МБ среди тех, что попадут в репозиторий,
и есть ли README в каждой папке.

python3 scripts/check_repo.py
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 50 * 2**20

files = subprocess.run(["git", "ls-files", "--others", "--cached", "--exclude-standard"],
                       cwd=ROOT, capture_output=True, text=True).stdout.split()
big = [(f, (ROOT / f).stat().st_size) for f in files if (ROOT / f).exists() and (ROOT / f).stat().st_size > LIMIT]
for f, size in big:
    print(f"слишком большой: {f} ({size / 2**20:.0f} МБ)")

dirs = {str(Path(f).parent) for f in files} - {"."}
no_readme = sorted(d for d in dirs if not (ROOT / d / "README.md").exists())
for d in no_readme:
    print(f"нет README: {d}")

print("ok" if not big else "есть файлы больше 50 МБ, их нельзя пушить")
