import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIBS = sorted((ROOT / "laporan").glob("*/referensi.bib"))
OUT = ROOT / "laporan" / "pustaka"
UA = "Mozilla/5.0 (X11; Linux x86_64) unduh_pustaka/1.0"
DOI_TAMBAHAN = {
    "verma_2024": "10.1016/j.heliyon.2024.e40266",
    "xiang_2026": "10.1016/j.engappai.2025.113603",
    "khan_2025": "10.1016/j.compbiomed.2025.111345",
    "fahoum_2026": "10.1016/j.bspc.2026.110345",
    "kumaran_2026": "10.1016/j.knosys.2026.116176",
    "elhadad_2025": "10.1016/j.cmpb.2024.108268",
}
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}?email=unpaywall@impactstory.org"


def entri_bib():
    seen = {}
    for bib in BIBS:
        for m in re.finditer(r"@\w+\{(\w+),(.*?)\n\}", bib.read_text(), re.S):
            key, body = m.group(1), m.group(2)
            doi = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
            url = re.search(r"(?:url|howpublished)\s*=\s*\{.*?(https?://[^}\s]+)", body)
            seen.setdefault(key, (doi.group(1).strip() if doi else DOI_TAMBAHAN.get(key), url.group(1) if url else None))
    return seen


def ambil(url):
    r = subprocess.run(["curl", "-sSL", "--max-time", "90", "-A", UA, url], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode().strip())
    return r.stdout


def url_pdf(doi):
    j = json.loads(ambil(UNPAYWALL.format(doi=doi)))
    loc = j.get("best_oa_location") or {}
    cands = [loc.get("url_for_pdf")] + [l.get("url_for_pdf") for l in j.get("oa_locations", [])]
    return [c for c in cands if c], j.get("is_oa")


def unduh(key, cands):
    for u in cands:
        try:
            data = ambil(u)
        except Exception as e:
            print(f"  gagal {u}: {e}")
            continue
        if data[:4] == b"%PDF":
            (OUT / f"{key}.pdf").write_bytes(data)
            return u
        print(f"  bukan PDF: {u}")
    return None


def main():
    OUT.mkdir(exist_ok=True)
    gagal = []
    for key, (doi, url) in entri_bib().items():
        if (OUT / f"{key}.pdf").exists():
            print(f"[ada]    {key}")
            continue
        cands, is_oa = [], None
        if doi:
            try:
                cands, is_oa = url_pdf(doi)
            except Exception as e:
                print(f"  unpaywall {doi}: {e}")
        if url and url.lower().endswith(".pdf"):
            cands.append(url)
        src = unduh(key, cands) if cands else None
        if src:
            print(f"[unduh]  {key}  <- {src}")
        else:
            gagal.append((key, doi, url, is_oa))
            print(f"[gagal]  {key}  doi={doi} oa={is_oa}")
    print(f"\nterunduh: {len(list(OUT.glob('*.pdf')))}  gagal: {len(gagal)}")
    for g in gagal:
        print("  ", *g)
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
