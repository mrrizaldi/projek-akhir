#!/usr/bin/env python3
import argparse
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

LINGKUNGAN_NONPROSA = ("table", "table*", "longtable", "tabular", "tabularx", "figure", "figure*", "equation", "equation*", "align", "align*", "lstlisting", "verbatim")
KATA_PER_SATUAN_KEPADATAN = 100
AMBANG_KONEKTOR_PER_100_KATA = 3.0
AMBANG_HAL_INI_PER_SUBBAB = 3
AMBANG_KONEKTOR_SAMA_PER_SUBBAB = 2
AMBANG_KALIMAT_PANJANG = 35
AMBANG_RANTAI_YANG = 3
AMBANG_YAITU_PER_PARAGRAF = 2
JENDELA_RANTAI_YANG = 15
CUPLIKAN_MAKS = 70
GALAT = "galat"
TINJAU = "tinjau"

POLA = [
    ("S-ZAMAN", GALAT, r"(?i)\bdi (era|zaman|tengah) (digital|modern|globalisasi|serba|teknologi|pesatnya|derasnya|revolusi)|\bseiring (dengan )?(perkembangan|kemajuan|berjalannya) (zaman|teknologi|waktu)|\bdewasa ini\b|\bdalam dunia \w+ yang (terus|semakin) berkembang", "pembuka zaman tanpa informasi"),
    ("S-PENEGAS", GALAT, r"(?i)\bt(idak|ak) (dapat|bisa) dipungkiri\b|\bseperti yang (kita )?(ketahui|diketahui)( bersama)?\b|\bsudah menjadi rahasia umum\b|\bsebagaimana kita ketahui\b", "penegas pengganti bukti"),
    ("S-META", GALAT, r"(?i)\b(perlu|penting untuk) (diketahui|dicatat|dipahami|diingat|diperhatikan)( bahwa)?\b|\bpatut (dicatat|diperhatikan)\b|\bmari kita\b|\bperhatikan bahwa\b|\byang menarik(nya)? adalah\b", "kalimat meta atau nada ceramah"),
    ("S-GELEMBUNG", GALAT, r"(?i)\bmemegang peranan (yang )?(sangat )?(penting|krusial|vital|sentral|strategis)|\bberperan (sangat )?(vital|krusial)\b|\bmenjadi (kunci utama|faktor kunci)\b|\btak lepas dari\b|\bsolusi (yang )?(inovatif|revolusioner|tepat guna|terbaik|jitu)\b|\bsangat (efektif dan efisien|luar biasa)\b", "klaim digelembungkan"),
    ("S-SIGNIFIKAN", TINJAU, r"(?i)\bsignifikan\b", "signifikan tanpa uji statistik? sebut angka dan ambangnya"),
    ("S-MUTLAK", TINJAU, r"(?i)\b(pasti|selalu|tidak pernah|menjamin|dijamin|sempurna|tanpa cacat|tidak diragukan lagi)\b", "kata mutlak, cek cakupan datanya"),
    ("S-PAYUNG", GALAT, r"(?i)\bberbagai (aspek|faktor|bidang|kalangan|dimensi)\b|\bfaktor-faktor tertentu\b|\bperan strategis\b", "kata payung kosong, sebut variabelnya"),
    ("S-ATRIBUSI", TINJAU, r"(?i)\b(banyak|sejumlah|berbagai) (penelitian|studi|peneliti|ahli|literatur)\b|\bpara ahli\b", "atribusi kabur, perlu \\cite di kalimat yang sama"),
    ("S-PENUTUP", GALAT, r"(?i)\bdengan demikian,? dapat disimpulkan( bahwa)?\b|(?:^|(?<=[.!?])\s)(?-i:Secara keseluruhan),|\bdemikianlah\b|\bsebagai (kesimpulan|penutup)\b|\bmenjanjikan\b|\bsemoga\b", "penutup ritual"),
    ("S-RESIDU", GALAT, r"(?i)\b(tentu|baik),? berikut\b|\bjangan ragu untuk\b|contentReference|oaicite|turn0search|\[cite:\s*\d+\]|【|】", "residu chatbot"),
    ("S-PLEONASME", GALAT, r"(?i)\badalah merupakan\b|\b(agar supaya|demi untuk|sejak dari)\b|\bberbagai macam\b|\bdisebabkan karena\b|\bdalam rangka untuk\b|\bberdasarkan (pada|kepada)\b", "pleonasme"),
    ("S-KONTRAS", TINJAU, r"(?i)\b(bukan|tidak) (hanya|sekadar|cuma)\b[^.]{1,80}?\b(tetapi|namun|melainkan)\b|\blebih dari sekadar\b|\bbukan lagi\b[^.]{1,40}?\bmelainkan\b", "kontras formulaik tidak hanya ... tetapi juga"),
    ("S-SANGKAL", GALAT, r"(?i)\bbukan berarti\b", "penyangkalan antisipatif"),
    ("S-SUBJEK", GALAT, r"(?:^|(?<=[.!?])\s)(?:Dari|Dalam|Pada|Bagi|Menurut|Berdasarkan)\s(?:(?!\b(?:penulis|peneliti)\b)[^.?!,;:]){1,60}?\s(?:menunjukkan|membahas|memperlihatkan|menjelaskan|mengatakan|menyatakan|menggambarkan|menyajikan|menyimpulkan|membuktikan)\b", "subjek hilang karena kata depan"),
    ("S-KONJ-GANDA", GALAT, r"(?i)\b(meskipun|walaupun|walau|biarpun|kendatipun)\b[^.]{1,120}?,\s*(tetapi|namun)\b|(?:^|(?<=[.!?])\s)(Karena|Sebab|Oleh karena|Berdasarkan|Mengingat)\b[^.]{1,120}?,\s*maka\b", "konjungsi berpasangan"),
    ("S-PEMBUKA-KONJ", GALAT, r"(?:^|(?<=[.!?])\s)(Sehingga|Sedangkan)\b", "Sehingga/Sedangkan sebagai pembuka kalimat"),
    ("S-KOMA-SEHINGGA", GALAT, r",\s+sehingga\b", "koma sebelum sehingga"),
    ("S-KOPULA", TINJAU, r"(?i)\b(berperan|bertindak|hadir|berdiri) sebagai\b|\bmenjadi wadah bagi\b|\botak (dari|sistem)\b|\bjantung dari\b", "kopula dihindari, pakai adalah"),
    ("S-NOMINAL", TINJAU, r"(?i)\b(melakukan|mengalami|memberikan|mengadakan|melaksanakan)\s+(pe\w{3,}an|ke\w{3,}an)\b|\bmemberikan (pengaruh|kontribusi) terhadap\b", "nominalisasi dengan verba ringan"),
    ("S-EKOR", TINJAU, r"(?i),\s*(yang )?(menunjukkan|mencerminkan|menegaskan|menandakan|menggarisbawahi|menyoroti|menjadikannya)\b", "klausa ekor penafsiran, cek fakta atau penilaian"),
    ("S-MODAL", GALAT, r"(?i)\b(mungkin|dapat|bisa|cenderung|berpotensi|kemungkinan|diduga)\s+(mungkin|dapat|bisa|cenderung|berpotensi|kemungkinan)\b", "modalitas bertumpuk"),
    ("S-MEMBUKTIKAN", TINJAU, r"(?i)\bmembuktikan\b", "membuktikan, cek kekuatan klaim"),
    ("S-DOKUMEN", GALAT, r"(?i)\b(bab|subbab|bagian|tulisan) ini (akan )?(membahas|memaparkan|menguraikan|menjelaskan|bertujuan)\b|\bpada (bab|subbab|bagian) ini akan\b", "kalimat tentang dokumen"),
    ("S-TANTANGAN", TINJAU, r"(?i)\bmeskipun (memiliki|terdapat) (beberapa |berbagai )?(keterbatasan|kekurangan|tantangan)\b|\bperlu (dilakukan )?penelitian lebih lanjut\b", "keterbatasan atau saran generik"),
    ("S-SENADA", GALAT, r"(?i)\b(senada|sejalan) dengan (itu|hal tersebut)\b", "penghubung tinjauan pustaka per sumber"),
    ("S-SPASIAL", GALAT, r"(?i)\b(tabel|gambar|grafik|diagram|persamaan)\s+(berikut( ini)?|di (atas|bawah)( ini)?)\b", "rujukan spasial semu, pakai nomor"),
    ("S-RETORIS", GALAT, r"\?", "pertanyaan retoris di paragraf"),
    ("S-PERSONA", GALAT, r"(?i)\b(kami|kita|saya|anda|kamu|aku)\b", "kata ganti orang pertama atau kedua"),
    ("S-PROMOSI", GALAT, r"(?i)\b(kini|telah) hadir\b|\bdirancang khusus\b|\bhasil (yang )?(maksimal|optimal)\b|\b(revolusioner|terobosan baru|game changer)\b", "nada promosi"),
    ("S-KOLOKIAL", GALAT, r"(?i)\b(bikin|banget|nggak|ngga|gak|kayak|gampang|ribet|gimana|aja)\b", "kolokial"),
    ("S-EMOSI", GALAT, r"(?i)\b(mencengangkan|mengejutkan|luar biasa|sayangnya|menakjubkan|sangat menarik|memuaskan)\b", "kata emosional"),
    ("S-BIROKRAT", TINJAU, r"(?:^|(?<=[.!?])\s)Adapun\b|(?i:\bdalam rangka\b|\bguna (mengetahui|meningkatkan)\b)", "register birokratis"),
    ("S-DIMANA", GALAT, r"(?i)\bdimana\b|(?<=\w),?\s+di mana\s+(?!pun\b|saja\b)(?=[a-z])", "di mana sebagai penghubung"),
    ("S-YANG-MANA", GALAT, r"(?i)\byang mana\b", "yang mana sebagai penghubung"),
    ("S-KALKE", GALAT, r"(?i)\bmemainkan perana?n?\b|\bmengambil tempat\b|\badalah penting untuk\b|\bdalam (kasus|konteks) ini\b|\bberbicara (tentang|soal)\b", "frasa kalke"),
    ("S-DANGLING", TINJAU, r"(?:^|(?<=[.!?])\s)(Menggunakan|Memanfaatkan|Dengan menggunakan|Mempertimbangkan)\s[^,]{3,60},", "klausa partisip di depan, cek subjek induk"),
    ("S-KARENA-ITU", TINJAU, r"(?<!Oleh )(?<!oleh )(?<![.!?] )(?<!^)\bkarena itu\b", "karena itu disisipkan di tengah klausa"),
    ("S-JADI", TINJAU, r"(?:^|(?<=[.!?])\s)Jadi\b", "Jadi sebagai pembuka kalimat"),
    ("S-CELAH", TINJAU, r"(?i)\bbelum (ada|pernah ada) (penelitian|studi)\b", "klaim celah, perlu dasar literatur"),
]

KONEKTOR = re.compile(r"(?:^|(?<=[.!?])\s)(Selain itu|Tidak hanya itu|Terlebih lagi|Lebih lanjut|Namun demikian|Oleh karena itu|Oleh sebab itu|Dengan demikian|Di sisi lain|Sementara itu|Selanjutnya|Dengan kata lain|Konsekuensinya)\b")
HAL_INI = re.compile(r"(?i)\bhal (ini|tersebut)\b")
YAITU = re.compile(r"(?i)\byaitu\b")
POLA_ANGKA = re.compile(r"\d+(?:[.,{}]+\d+)*")
POLA_KUNCI = re.compile(r"\\(cite|ref|autoref|pageref|label|eqref)\{([^}]*)\}")
POLA_SUBBAB = re.compile(r"^\s*\\(chapter|section|subsection)\*?\{")


def buang_komentar(baris):
    return re.sub(r"(?<!\\)%.*", "", baris)


def ratakan(teks):
    teks = POLA_KUNCI.sub(lambda m: " [RUJ] " if m.group(1) != "label" else " ", teks)
    teks = re.sub(r"\$[^$]*\$", " RUMUS ", teks)
    teks = re.sub(r"\\(textit|textbf|emph|textsc|texttt|mbox)\{([^}]*)\}", r"\2", teks)
    teks = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", teks)
    teks = teks.replace("~", " ").replace("\\%", "%")
    teks = re.sub(r"[{}]", "", teks)
    return re.sub(r"\s+", " ", teks).strip()


def paragraf(teks_berkas):
    hasil, kumpul, mulai, dalam_nonprosa, subbab = [], [], 0, 0, 0
    for nomor, baris in enumerate(teks_berkas.splitlines(), start=1):
        bersih = buang_komentar(baris)
        for nama in re.findall(r"\\begin\{([^}]+)\}", bersih):
            if nama in LINGKUNGAN_NONPROSA:
                dalam_nonprosa += 1
        akhir_nonprosa = sum(1 for nama in re.findall(r"\\end\{([^}]+)\}", bersih) if nama in LINGKUNGAN_NONPROSA)
        kosong = not bersih.strip()
        if POLA_SUBBAB.match(bersih):
            subbab += 1
        if dalam_nonprosa or kosong or POLA_SUBBAB.match(bersih) or bersih.lstrip().startswith(("\\begin", "\\end", "\\item")):
            if kumpul:
                hasil.append((mulai, subbab, ratakan(" ".join(kumpul))))
                kumpul = []
            if bersih.lstrip().startswith("\\item") and not dalam_nonprosa:
                hasil.append((nomor, subbab, ratakan(bersih)))
        else:
            if not kumpul:
                mulai = nomor
            kumpul.append(bersih)
        dalam_nonprosa = max(0, dalam_nonprosa - akhir_nonprosa)
    if kumpul:
        hasil.append((mulai, subbab, ratakan(" ".join(kumpul))))
    return [(n, s, t) for n, s, t in hasil if len(t.split()) > 2]


def kalimat(teks):
    return [k for k in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\[])", teks) if k]


def periksa(berkas):
    temuan = []
    paras = paragraf(Path(berkas).read_text(encoding="utf-8"))
    total_kata = 0
    konektor_total = 0
    per_subbab_hal_ini = Counter()
    per_subbab_konektor = Counter()
    panjang = []
    for nomor, subbab, teks in paras:
        kata = teks.split()
        total_kata += len(kata)
        for kode, tingkat, pola, pesan in POLA:
            for m in re.finditer(pola, teks):
                awal = max(0, m.start() - CUPLIKAN_MAKS // 2)
                temuan.append((nomor, kode, tingkat, pesan, teks[awal:awal + CUPLIKAN_MAKS]))
        for k in KONEKTOR.findall(teks):
            konektor_total += 1
            per_subbab_konektor[(subbab, k)] += 1
        per_subbab_hal_ini[subbab] += len(HAL_INI.findall(teks))
        jumlah_yaitu = len(YAITU.findall(teks))
        if jumlah_yaitu >= AMBANG_YAITU_PER_PARAGRAF:
            temuan.append((nomor, "S-YAITU-PADAT", TINJAU, f"'yaitu' {jumlah_yaitu} kali dalam satu paragraf", teks[:CUPLIKAN_MAKS]))
        for k in kalimat(teks):
            n = len(k.split())
            panjang.append(n)
            if n > AMBANG_KALIMAT_PANJANG:
                temuan.append((nomor, "S-PANJANG", TINJAU, f"kalimat {n} kata", k[:CUPLIKAN_MAKS]))
            jendela = k.split()
            for i in range(len(jendela)):
                potong = jendela[i:i + JENDELA_RANTAI_YANG]
                if sum(1 for w in potong if w == "yang") >= AMBANG_RANTAI_YANG and not any(w.endswith(",") for w in potong):
                    temuan.append((nomor, "S-RANTAI-YANG", TINJAU, "rantai yang", " ".join(potong)[:CUPLIKAN_MAKS]))
                    break
    for subbab, jumlah in per_subbab_hal_ini.items():
        if jumlah >= AMBANG_HAL_INI_PER_SUBBAB:
            temuan.append((0, "S-HAL-INI", TINJAU, f"'hal ini/tersebut' {jumlah} kali di subbab ke-{subbab}", ""))
    for (subbab, k), jumlah in per_subbab_konektor.items():
        if jumlah > AMBANG_KONEKTOR_SAMA_PER_SUBBAB:
            temuan.append((0, "S-KONEKTOR-ULANG", TINJAU, f"'{k}' {jumlah} kali di subbab ke-{subbab}", ""))
    kepadatan = konektor_total * KATA_PER_SATUAN_KEPADATAN / total_kata if total_kata else 0.0
    metrik = {
        "kata": total_kata,
        "kalimat": len(panjang),
        "rerata_kalimat": statistics.mean(panjang) if panjang else 0.0,
        "simpangan_kalimat": statistics.pstdev(panjang) if panjang else 0.0,
        "konektor_per_100": kepadatan,
    }
    if kepadatan > AMBANG_KONEKTOR_PER_100_KATA:
        temuan.append((0, "S-KONEKTOR-PADAT", TINJAU, f"konektor {kepadatan:.1f} per 100 kata", ""))
    return temuan, metrik


def invarian(teks):
    tanpa_komentar = "\n".join(buang_komentar(b) for b in teks.splitlines())
    prosa = POLA_KUNCI.sub(" ", tanpa_komentar)
    angka = Counter(re.sub(r"[{}]", "", a) for a in POLA_ANGKA.findall(prosa))
    kunci = Counter(f"{m.group(1)}:{k.strip()}" for m in POLA_KUNCI.finditer(tanpa_komentar) for k in m.group(2).split(","))
    komentar = [b.strip() for b in teks.splitlines() if b.lstrip().startswith("%")]
    return angka, kunci, komentar


def banding(lama, baru):
    a_lama, k_lama, c_lama = invarian(Path(lama).read_text(encoding="utf-8"))
    a_baru, k_baru, c_baru = invarian(Path(baru).read_text(encoding="utf-8"))
    masalah = []
    for nama, x, y in (("angka", a_lama, a_baru), ("rujukan", k_lama, k_baru)):
        hilang, tambah = x - y, y - x
        if hilang:
            masalah.append(f"{nama} hilang: {dict(hilang)}")
        if tambah:
            masalah.append(f"{nama} bertambah: {dict(tambah)}")
    if c_lama != c_baru:
        masalah.append(f"baris komentar % berubah ({len(c_lama)} -> {len(c_baru)})")
    return masalah


def uji():
    contoh = "Di era digital ini, sistem ini tidak hanya cepat tetapi juga murah. Hal ini bukan berarti selesai, dimana data dikirim.\n\nBerdasarkan Tabel~\\ref{tab:a} menunjukkan latensi 1,2 detik.\n"
    jalur = Path("/tmp/cek_slop_uji.tex")
    jalur.write_text(contoh, encoding="utf-8")
    temuan, metrik = periksa(jalur)
    kode = {t[1] for t in temuan}
    for wajib in ("S-ZAMAN", "S-KONTRAS", "S-SANGKAL", "S-DIMANA", "S-SUBJEK"):
        assert wajib in kode, (wajib, kode)
    assert metrik["kata"] > 0
    baru = Path("/tmp/cek_slop_uji_baru.tex")
    baru.write_text(contoh.replace("1,2", "1,3"), encoding="utf-8")
    assert any("angka" in m for m in banding(jalur, baru))
    baru.write_text(contoh.replace("Di era digital ini, s", "S"), encoding="utf-8")
    assert banding(jalur, baru) == []
    jalur.unlink()
    baru.unlink()
    print("uji lulus")


def main():
    parser = argparse.ArgumentParser(description="Pemeriksa pola tulisan AI di paragraf laporan PA (skill tulis-tanpa-slop).")
    parser.add_argument("berkas", nargs="*", help="berkas .tex yang diperiksa")
    parser.add_argument("--banding", nargs=2, metavar=("LAMA", "BARU"), help="pastikan angka, \\cite/\\ref/\\label, dan komentar %% tidak berubah")
    parser.add_argument("--uji", action="store_true", help="uji mandiri pemeriksa")
    parser.add_argument("--ringkas", action="store_true", help="hanya metrik dan jumlah temuan per kode")
    args = parser.parse_args()
    if args.uji:
        uji()
        return
    if args.banding:
        lama, baru = args.banding
        masalah = banding(lama, baru)
        for m in masalah:
            print(f"{baru}: {m}")
        print("invarian aman" if not masalah else f"{len(masalah)} masalah invarian")
        sys.exit(1 if masalah else 0)
    jumlah_galat = 0
    for berkas in args.berkas:
        temuan, metrik = periksa(berkas)
        galat = [t for t in temuan if t[2] == GALAT]
        jumlah_galat += len(galat)
        print(f"== {berkas}: {metrik['kata']} kata, {metrik['kalimat']} kalimat, rerata {metrik['rerata_kalimat']:.1f} (sb {metrik['simpangan_kalimat']:.1f}), konektor {metrik['konektor_per_100']:.2f}/100 kata, {len(galat)} galat, {len(temuan) - len(galat)} tinjau")
        if args.ringkas:
            for kode, n in sorted(Counter(t[1] for t in temuan).items()):
                print(f"   {kode}: {n}")
            continue
        for nomor, kode, tingkat, pesan, cuplikan in sorted(temuan):
            print(f"{berkas}:{nomor}: {kode} [{tingkat}] {pesan}: {cuplikan}")
    sys.exit(1 if jumlah_galat else 0)


if __name__ == "__main__":
    main()
