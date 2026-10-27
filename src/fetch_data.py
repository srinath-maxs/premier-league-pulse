"""Step 1: download the raw data into data/raw/.

Run:  python src/fetch_data.py
Already-downloaded files are skipped. Add --force to download everything again.
"""
import sys
import urllib.request

from config import RAW, RESULTS_URL, SEASON_CODES, TM_BASE, TM_FILES, TM_GAMES_URL


def download(url: str, dest, force: bool = False) -> None:
    if dest.exists() and not force:
        print(f"  already have {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {dest.name} ...", flush=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)


def main(force: bool = False) -> None:
    print("Match results (one file per season):")
    for code in SEASON_CODES:
        download(RESULTS_URL.format(code=code), RAW / "results" / f"season-{code}.csv", force)

    print("Transfermarkt squad data (large files, can take a few minutes):")
    for name, path in TM_FILES.items():
        download(TM_BASE + path, RAW / "transfermarkt" / f"{name}.csv", force)

    print("Transfermarkt match records (managers for every game):")
    gz = RAW / "transfermarkt" / "games.csv.gz"
    out = RAW / "transfermarkt" / "games.csv"
    if not out.exists() or force:
        download(TM_GAMES_URL, gz, force)
        import gzip, shutil
        with gzip.open(gz, "rb") as f_in, open(out, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    else:
        print("  already have games.csv")

    print("Done.")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
