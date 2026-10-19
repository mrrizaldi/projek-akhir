#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

PT_KE_CM = 0.0351459
LEBAR_TEKS_CM = {"a4": 14.0, "a5": 9.8}
TABCOLSEP_BAWAAN_PT = 6.0
SEL_MAKS_KATA = 20
CAPTION_MAKS_KATA = 15
PARAGRAF_MAKS_KATA = 180
KALIMAT_MAKS_KATA = 35
ULANG_RASIO_MAKS = 0.5
ULANG_MIN_ANGKA = 5
SATUAN_MIN_SEL = 3
BERDASARKAN_MAKS_PER_BAB = 3
BAB_TANPA_TABEL = ("bab1.tex", "bab5.tex")
ISIAN_SAMAR = {"sama", "idem", "konfigurasi sama", "tidak diulang", "dst", "dst.", "ditto"}
SATUAN = r"(?:ms|\$\\mu\$s|µs|KB|MB|byte|detik|mV|mA|mW|Hz|\\%|sampel|entri)"
POLA_BLOK = re.compile(r"\\begin\{(table|longtable)\}(.*?)\\end\{\1\}", re.S)
POLA_ANGKA = re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w.])\d+,\d+|(?<![\w.,])\d{2,}(?![\d,])")
POLA_REF = r"\\(?:auto|page)?ref\{%s\}"
LINGKUNGAN_NONPROSA = ("table", "longtable", "figure", "equation", "align", "tabular", "tabularx", "center", "lstlisting", "verbatim")
RUMUS_DIBUANG = re.compile(r"\$[^$]*\$")


class Laporan:
    def __init__(self):
        self.temuan = []

    def catat(self, berkas, baris, kode, galat, pesan):
        self.temuan.append((str(berkas), baris, kode, galat, pesan))

    def jumlah_galat(self):
        return sum(1 for t in self.temuan if t[3])

    def jumlah_saran(self):
        return sum(1 for t in self.temuan if not t[3])

    def cetak(self, hanya_galat):
        for berkas, baris, kode, galat, pesan in self.temuan:
            if hanya_galat and not galat:
                continue
            tingkat = "galat" if galat else "saran"
            print(f"{berkas}:{baris}: [{kode} {tingkat}] {pesan}")


def tanpa_komentar(teks):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", b) for b in teks.split("\n"))


def nomor_baris(teks, posisi):
    return teks.count("\n", 0, posisi) + 1


def isi_kurung(teks, i):
    if i >= len(teks) or teks[i] != "{":
        return "", i
    dalam, j = 0, i
    while j < len(teks):
        if teks[j] == "{" and (j == 0 or teks[j - 1] != "\\"):
            dalam += 1
        elif teks[j] == "}" and teks[j - 1] != "\\":
            dalam -= 1
            if dalam == 0:
                return teks[i + 1:j], j + 1
        j += 1
    return teks[i + 1:], len(teks)


def ke_cm(ukuran, lebar_teks):
    ukuran = ukuran.strip()
    m = re.fullmatch(r"([\d.]*)\s*\\(?:linewidth|textwidth|columnwidth)", ukuran)
    if m:
        return (float(m.group(1)) if m.group(1) else 1.0) * lebar_teks
    m = re.fullmatch(r"([\d.]+)\s*(cm|mm|pt|in)", ukuran)
    if not m:
        return None
    nilai, satuan = float(m.group(1)), m.group(2)
    return {"cm": nilai, "mm": nilai / 10, "pt": nilai * PT_KE_CM, "in": nilai * 2.54}[satuan]


def baca_spesifikasi(spek, lebar_teks):
    lebar, kolom, garis, i = [], 0, 0, 0
    while i < len(spek):
        c = spek[i]
        if c in "><@!" and i + 1 < len(spek) and spek[i + 1] == "{":
            _, i = isi_kurung(spek, i + 1)
            continue
        if c == "|":
            garis += 1
        elif c in "pmbLR" and i + 1 < len(spek) and spek[i + 1] == "{":
            ukuran, i = isi_kurung(spek, i + 1)
            kolom += 1
            lebar.append(ke_cm(ukuran, lebar_teks))
            continue
        elif c in "lcrX":
            kolom += 1
            lebar.append(None)
        i += 1
    return lebar, kolom, garis


def cari_tabular(blok, lingkungan):
    if lingkungan == "longtable":
        lewati = re.match(r"\s*(\[[^\]]*\])?", blok).end()
        spek, akhir = isi_kurung(blok, lewati)
        return "longtable", None, spek, akhir
    m = re.search(r"\\begin\{(tabularx|tabular)\}", blok)
    if not m:
        return None, None, None, None
    i = m.end()
    lebar_x = None
    if m.group(1) == "tabularx":
        lebar_x, i = isi_kurung(blok, i)
    spek, akhir = isi_kurung(blok, i)
    return m.group(1), lebar_x, spek, akhir


def pecah_baris(isi):
    isi = re.sub(r"\\(caption|label)\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", isi)
    isi = re.sub(r"\\(rowcolor|cellcolor)(\[[^\]]*\])?\{[^}]*\}", " ", isi)
    isi = re.sub(r"\\(hline|endfirsthead|endhead|endfoot|endlastfoot|toprule|midrule|bottomrule|cline\{[^}]*\})", " ", isi)
    isi = re.sub(r"\\end\{(tabularx|tabular)\}.*", "", isi, flags=re.S)
    baris, lihat = [], set()
    for mentah in re.split(r"\\\\(?:\[[^\]]*\])?", isi):
        sel = [s.strip() for s in re.split(r"(?<!\\)&", mentah)]
        if not any(sel):
            continue
        kunci = "|".join(sel)
        if kunci in lihat:
            continue
        lihat.add(kunci)
        baris.append(sel)
    return baris


def buka_multicolumn(sel):
    m = re.match(r"\s*\\multicolumn\{(\d+)\}", sel)
    if not m:
        return 1, sel
    _, i = isi_kurung(sel, sel.find("{", m.end()))
    isi, _ = isi_kurung(sel, sel.find("{", i))
    return int(m.group(1)), isi


def teks_polos(sel):
    sel = re.sub(r"\\(?:ref|cite|label|autoref)\{[^}]*\}", "X", sel)
    sel = re.sub(r"\\[a-zA-Z]+\*?", " ", sel)
    return re.sub(r"[{}~]", " ", sel)


def jumlah_kata(teks):
    return len(re.findall(r"\S+", teks_polos(teks)))


def angka_dalam(teks):
    return set(POLA_ANGKA.findall(tanpa_komentar(teks)))


def nama_kolom(kepala, j):
    if j < len(kepala):
        return re.sub(r"\s+", " ", teks_polos(kepala[j])).strip() or f"kolom {j + 1}"
    return f"kolom {j + 1}"


def periksa_isi(lap, berkas, baris_awal, baris_tabel):
    if len(baris_tabel) < 2:
        return
    kepala, badan = baris_tabel[0], []
    for b in baris_tabel[1:]:
        rentang, isi = buka_multicolumn(b[0])
        if len(b) == 1 and rentang >= len(kepala):
            if jumlah_kata(isi) > SEL_MAKS_KATA:
                lap.catat(berkas, baris_awal, "T-CATATAN", False,
                          f"baris catatan selebar tabel ({jumlah_kata(isi)} kata), pindahkan ke Keterangan di bawah tabel")
            continue
        badan.append([buka_multicolumn(s)[1] for s in b])
    for j in range(len(kepala)):
        kolom = [b[j] for b in badan if j < len(b)]
        nama = nama_kolom(kepala, j)
        for b in badan:
            if j < len(b) and jumlah_kata(b[j]) > SEL_MAKS_KATA:
                awal = " ".join(teks_polos(b[0]).split()[:4])
                lap.catat(berkas, baris_awal, "T-SEL", False,
                          f"sel '{nama}' pada baris '{awal}' berisi {jumlah_kata(b[j])} kata (maks {SEL_MAKS_KATA}), pindahkan alasan ke paragraf atau Keterangan")
        bersatuan = [s for s in kolom if jumlah_kata(s) <= 4 and re.search(r"\d\s*~?\s*" + SATUAN + r"(?![a-zA-Z])", s)]
        if len(bersatuan) >= SATUAN_MIN_SEL and "(" not in kepala[j]:
            lap.catat(berkas, baris_awal, "T-SATUAN", False,
                      f"kolom '{nama}': satuan diulang di {len(bersatuan)} sel, tulis sekali di header, mis. '{nama} (ms)'")
        desimal = set()
        for s in kolom:
            m = re.fullmatch(r"[\s$+\-]*(?:\\mu)?\d[\d.]*,(\d+)\s*\$?", s)
            if m:
                desimal.add(len(m.group(1)))
        if len(desimal) > 1:
            lap.catat(berkas, baris_awal, "T-DESIMAL", False,
                      f"kolom '{nama}': jumlah desimal tidak seragam {sorted(desimal)}")
        for s in kolom:
            if teks_polos(s).strip().lower() in ISIAN_SAMAR:
                lap.catat(berkas, baris_awal, "T-ISIAN", False,
                          f"kolom '{nama}' berisi '{s.strip()}', pakai '--' lalu jelaskan di Keterangan")


def paragraf_sesudah(sumber_polos, posisi, label):
    sisa = sumber_polos[posisi:posisi + 8000]
    awal = posisi
    kandidat = []
    for m in re.finditer(r"(?:[^\n]+\n?)+", sisa):
        teks = m.group(0).strip()
        if not teks or teks.startswith(("\\end{", "\\begin{", "\\caption", "\\label", "\\centering")):
            continue
        if teks.startswith(("\\section", "\\subsection", "\\subsubsection", "\\chapter")):
            break
        kandidat.append((awal + m.start(), teks))
        if len(kandidat) == 3:
            break
    if not kandidat:
        return None, None
    if label:
        for pos, teks in kandidat:
            if re.search(POLA_REF % re.escape(label), teks):
                return pos, teks
    return kandidat[0]


def pembuka(teks):
    polos = re.sub(r"\\(?:ref|autoref)\{[^}]*\}", "N", teks)
    polos = re.sub(r"[~{}]", " ", re.sub(r"\\[a-zA-Z]+\*?", " ", polos))
    return " ".join(polos.split()[:3]).rstrip(",")


def periksa_tabel(lap, berkas, sumber, lebar_teks):
    polos = tanpa_komentar(sumber)
    penjelas = []
    for m in POLA_BLOK.finditer(polos):
        lingkungan, blok = m.group(1), m.group(2)
        baris_awal = nomor_baris(polos, m.start())
        if Path(berkas).name in BAB_TANPA_TABEL:
            lap.catat(berkas, baris_awal, "T-BAB", True, "Bab 1 dan Bab 5 tidak memuat tabel")
        if re.search(r"\\(hline|cline)|\\rowcolor", blok):
            lap.catat(berkas, baris_awal, "T-GRID", True, "gaya tiga garis: \\toprule, \\midrule, \\bottomrule, tanpa \\hline, \\cline, dan \\rowcolor")
        if not all(f"\\{garis}" in blok for garis in ("toprule", "midrule", "bottomrule")):
            lap.catat(berkas, baris_awal, "T-HEADER", True, "tabel tanpa pasangan lengkap \\toprule, \\midrule, \\bottomrule")
        if lingkungan == "table" and re.match(r"\s*\[H\]", blok):
            lap.catat(berkas, baris_awal, "T-FLOAT", False, "[H] mengunci posisi, pakai [!ht]")
        jenis, lebar_x, spek, akhir_spek = cari_tabular(blok, lingkungan)
        if spek and "|" in spek:
            lap.catat(berkas, baris_awal, "T-GRID", True, "garis vertikal | di spesifikasi kolom, gaya tiga garis tanpa garis vertikal")
        cap = re.search(r"\\caption\{", blok)
        if not cap:
            lap.catat(berkas, baris_awal, "T-CAPTION", True, "tabel tanpa \\caption")
        else:
            teks_cap, _ = isi_kurung(blok, cap.end() - 1)
            if lingkungan == "table" and jenis and blok.find("\\begin{" + jenis) < cap.start():
                lap.catat(berkas, baris_awal, "T-CAPTION", True, "caption tabel harus di ATAS tabel")
            if teks_cap.rstrip().endswith("."):
                lap.catat(berkas, baris_awal, "T-CAPTION", False, "caption berakhir titik, caption adalah frasa benda tanpa titik")
            if "(" in teks_polos(teks_cap):
                lap.catat(berkas, baris_awal, "T-CAPTION", False, "caption memuat keterangan dalam kurung, pindahkan ke baris Keterangan di bawah tabel")
            if jumlah_kata(teks_cap) > CAPTION_MAKS_KATA:
                lap.catat(berkas, baris_awal, "T-CAPTION", False, f"caption {jumlah_kata(teks_cap)} kata (maks {CAPTION_MAKS_KATA})")
        if spek is not None:
            lebar, kolom, garis = baca_spesifikasi(spek, lebar_teks)
            konteks = polos[max(0, m.start() - 600):m.start()] + blok
            sep = re.findall(r"\\setlength\{\\tabcolsep\}\{([\d.]+)pt\}", konteks)
            tabcolsep = float(sep[-1]) if sep else TABCOLSEP_BAWAAN_PT
            if jenis != "tabularx" and lebar and all(x is not None for x in lebar):
                total = sum(lebar) + kolom * 2 * tabcolsep * PT_KE_CM + garis * 0.4 * PT_KE_CM
                if total > lebar_teks + 0.05:
                    lap.catat(berkas, baris_awal, "T-LEBAR", True,
                              f"lebar tabel {total:.2f} cm melebihi lebar teks {lebar_teks:.2f} cm")
            isi = blok[akhir_spek:] if akhir_spek else blok
            periksa_isi(lap, berkas, baris_awal, pecah_baris(isi))
        lab = re.search(r"\\label\{([^}]*)\}", blok)
        label = lab.group(1) if lab else None
        if label:
            rujukan = [r.start() for r in re.finditer(POLA_REF % re.escape(label), polos)]
            if not rujukan:
                lap.catat(berkas, baris_awal, "T-RUJUK", True, f"{label} tidak pernah dirujuk di paragraf")
            elif min(rujukan) > m.start():
                lap.catat(berkas, baris_awal, "T-RUJUK", False, f"{label} baru dirujuk sesudah tabel, rujuk dulu di paragraf pengantar")
        pos, teks = paragraf_sesudah(polos, m.end(), label)
        if teks:
            penjelas.append((nomor_baris(polos, pos), teks, angka_dalam(blok), label))
    periksa_penjelas(lap, berkas, penjelas)


def periksa_penjelas(lap, berkas, penjelas):
    sebelumnya = None
    berdasarkan = 0
    berulang = []
    for baris, teks, angka_tabel, label in penjelas:
        buka = pembuka(teks)
        if buka.lower().startswith("berdasarkan tabel"):
            berdasarkan += 1
        if sebelumnya and buka.lower() == sebelumnya.lower():
            berulang.append(str(baris))
        sebelumnya = buka
        kata = jumlah_kata(teks)
        if kata > PARAGRAF_MAKS_KATA:
            lap.catat(berkas, baris, "N-PANJANG", False, f"paragraf penjelas {label} {kata} kata (maks {PARAGRAF_MAKS_KATA}), pecah per fungsi")
        diulang = angka_tabel & angka_dalam(teks)
        if len(angka_tabel) >= ULANG_MIN_ANGKA and len(diulang) / len(angka_tabel) > ULANG_RASIO_MAKS:
            lap.catat(berkas, baris, "N-ULANG", False,
                      f"paragraf penjelas {label} mengulang {len(diulang)} dari {len(angka_tabel)} angka tabel, tulis temuan dan maknanya")
    if berulang:
        lap.catat(berkas, int(berulang[0]), "N-PEMBUKA", False,
                  f"{len(berulang)} paragraf penjelas memakai pembuka yang sama dengan penjelas sebelumnya (baris {', '.join(berulang)})")
    if berdasarkan > BERDASARKAN_MAKS_PER_BAB:
        lap.catat(berkas, 1, "N-PEMBUKA", False,
                  f"'Berdasarkan Tabel' membuka {berdasarkan} paragraf (maks {BERDASARKAN_MAKS_PER_BAB} per bab), variasikan pembuka")


def prosa(sumber):
    polos = tanpa_komentar(sumber)
    for nama in LINGKUNGAN_NONPROSA:
        polos = re.sub(r"\\begin\{%s\*?\}.*?\\end\{%s\*?\}" % (nama, nama),
                       lambda m: "\n" * m.group(0).count("\n"), polos, flags=re.S)
    hasil, posisi = [], 0
    for blok in re.split(r"(\n\s*\n)", polos):
        teks = blok.strip()
        if teks and not teks.startswith(("\\section", "\\subsection", "\\subsubsection", "\\chapter", "\\label")):
            hasil.append((nomor_baris(polos, posisi + len(blok) - len(blok.lstrip())), teks))
        posisi += len(blok)
    return hasil


def periksa_prosa(lap, berkas, sumber):
    total_kata, sehingga, panjang, gaya = 0, 0, [], []
    for baris, teks in prosa(sumber):
        if "\\makebox" in teks or teks.startswith("\\noindent\\makebox"):
            continue
        tanpa_rumus = RUMUS_DIBUANG.sub("X", teks)
        total_kata += jumlah_kata(tanpa_rumus)
        sehingga += len(re.findall(r"\bsehingga\b", tanpa_rumus))
        if re.search(r";|—|---", tanpa_rumus):
            gaya.append(str(baris))
        for kalimat in re.split(r"(?<=[.?!])\s+(?=[A-Z0-9\\])", tanpa_rumus):
            n = jumlah_kata(kalimat)
            if n > KALIMAT_MAKS_KATA:
                panjang.append((n, baris, " ".join(teks_polos(kalimat).split()[:6])))
    if gaya:
        lap.catat(berkas, int(gaya[0]), "N-GAYA", False,
                  f"titik koma atau em dash di {len(gaya)} paragraf (laporan/CLAUDE.md), baris {', '.join(gaya)}")
    if panjang:
        contoh = "; ".join(f"baris {b} ({n} kata) '{a} ...'" for n, b, a in sorted(panjang, reverse=True)[:5])
        lap.catat(berkas, sorted(panjang, reverse=True)[0][1], "N-KALIMAT", False,
                  f"{len(panjang)} kalimat lebih dari {KALIMAT_MAKS_KATA} kata, terpanjang: {contoh}")
    if total_kata:
        per_seribu = sehingga * 1000 / total_kata
        if per_seribu > 5:
            lap.catat(berkas, 1, "N-SEHINGGA", False,
                      f"'sehingga' {sehingga} kali ({per_seribu:.1f} per 1.000 kata), variasikan atau pecah kalimat")


def uji_mandiri():
    contoh = "\n".join([
        "Hasilnya pada Tabel~\\ref{tab:a}.",
        "",
        "\\begin{table}[H]",
        "\\begin{tabular}{|p{9cm}|p{6cm}|}",
        "\\hline",
        "\\textbf{A} & \\textbf{B} \\\\",
        "\\hline",
        "x & 10 ms \\\\ y & 20 ms \\\\ z & 30 ms \\\\ w & Sama \\\\",
        "\\end{tabular}",
        "\\caption{Contoh (uji).}",
        "\\label{tab:a}",
        "\\end{table}",
        "",
        "Berdasarkan Tabel~\\ref{tab:a}, nilai 10 dan 20 dan 30; selesai.",
    ])
    lap = Laporan()
    periksa_tabel(lap, "uji.tex", contoh, LEBAR_TEKS_CM["a4"])
    periksa_prosa(lap, "uji.tex", contoh)
    kode = {t[2] for t in lap.temuan}
    harap = {"T-GRID", "T-HEADER", "T-FLOAT", "T-CAPTION", "T-LEBAR", "T-SATUAN", "T-ISIAN", "N-GAYA"}
    kurang = harap - kode
    if kurang:
        print(f"uji mandiri GAGAL, tidak terdeteksi: {sorted(kurang)}")
        return 1
    print(f"uji mandiri lulus ({len(lap.temuan)} temuan, {len(harap)} kode diharapkan terdeteksi)")
    return 0


def main():
    akar = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Pemeriksa tabel dan paragraf penjelas laporan PA")
    parser.add_argument("berkas", nargs="*", help="berkas .tex, bawaan laporan/buku-pa/bab/bab*.tex")
    parser.add_argument("--kertas", choices=sorted(LEBAR_TEKS_CM), default="a4")
    parser.add_argument("--hanya-galat", action="store_true")
    parser.add_argument("--ketat", action="store_true", help="saran juga membuat kode keluar 1")
    parser.add_argument("--tanpa-prosa", action="store_true", help="lewati pemeriksaan kalimat dan gaya paragraf")
    parser.add_argument("--uji", action="store_true")
    arg = parser.parse_args()
    if arg.uji:
        return uji_mandiri()
    daftar = [Path(b) for b in arg.berkas] or sorted((akar / "laporan/buku-pa/bab").glob("bab*.tex"))
    lap = Laporan()
    for berkas in daftar:
        sumber = berkas.read_text(encoding="utf-8")
        periksa_tabel(lap, berkas, sumber, LEBAR_TEKS_CM[arg.kertas])
        if not arg.tanpa_prosa:
            periksa_prosa(lap, berkas, sumber)
    lap.cetak(arg.hanya_galat)
    print(f"{len(daftar)} berkas, {lap.jumlah_galat()} galat, {lap.jumlah_saran()} saran")
    if lap.jumlah_galat() or (arg.ketat and lap.jumlah_saran()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
