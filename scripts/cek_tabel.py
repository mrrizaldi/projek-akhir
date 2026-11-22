#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

PT_TO_CM = 0.0351459
TEXT_WIDTH_CM = {"a4": 14.0, "a5": 9.8}
TABCOLSEP_DEFAULT_PT = 6.0
CELL_MAX_WORDS = 20
CAPTION_MAX_WORDS = 15
PARAGRAPH_MAX_WORDS = 180
SENTENCE_MAX_WORDS = 35
REPEAT_RATIO_MAX = 0.5
REPEAT_MIN_NUMBERS = 5
UNIT_MIN_CELLS = 3
BERDASARKAN_MAX_PER_CHAPTER = 3
CHAPTERS_WITHOUT_TABLES = ("bab1.tex", "bab5.tex")
FULL_GRID_TABLES = {"tab:perbandingan-penelitian"}
VAGUE_FILLERS = {"sama", "idem", "konfigurasi sama", "tidak diulang", "dst", "dst.", "ditto"}
UNITS_REGEX = r"(?:ms|\$\\mu\$s|µs|KB|MB|byte|detik|mV|mA|mW|Hz|\\%|sampel|entri)"
BLOCK_PATTERN = re.compile(r"\\begin\{(table|longtable)\}(.*?)\\end\{\1\}", re.S)
NUMBER_PATTERN = re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w.])\d+,\d+|(?<![\w.,])\d{2,}(?![\d,])")
REF_PATTERN = r"\\(?:auto|page)?ref\{%s\}"
NON_PROSE_ENVIRONMENTS = ("table", "longtable", "figure", "equation", "align", "tabular", "tabularx", "center", "lstlisting", "verbatim")
DISCARDED_MATH = re.compile(r"\$[^$]*\$")


class Report:
    def __init__(self):
        self.temuan = []

    def catat(self, berkas, baris, kode, fault, msg):
        self.temuan.append((str(berkas), baris, kode, fault, msg))

    def fault_count(self):
        return sum(1 for t in self.temuan if t[3])

    def suggestion_count(self):
        return sum(1 for t in self.temuan if not t[3])

    def emit(self, hanya_galat):
        for berkas, baris, kode, fault, msg in self.temuan:
            if hanya_galat and not fault:
                continue
            severity = "error" if fault else "suggestion"
            print(f"{berkas}:{baris}: [{kode} {severity}] {msg}")


def strip_comments(teks):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", b) for b in teks.split("\n"))


def line_number_of(teks, position):
    return teks.count("\n", 0, position) + 1


def braced_content(teks, i):
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


def to_cm(ukuran, text_width):
    ukuran = ukuran.strip()
    m = re.fullmatch(r"([\d.]*)\s*\\(?:linewidth|textwidth|columnwidth)", ukuran)
    if m:
        return (float(m.group(1)) if m.group(1) else 1.0) * text_width
    m = re.fullmatch(r"([\d.]+)\s*(cm|mm|pt|in)", ukuran)
    if not m:
        return None
    nilai, unit = float(m.group(1)), m.group(2)
    return {"cm": nilai, "mm": nilai / 10, "pt": nilai * PT_TO_CM, "in": nilai * 2.54}[unit]


def read_column_spec(column_spec, text_width):
    lebar, kolom, garis, i = [], 0, 0, 0
    while i < len(column_spec):
        c = column_spec[i]
        if c in "><@!" and i + 1 < len(column_spec) and column_spec[i + 1] == "{":
            _, i = braced_content(column_spec, i + 1)
            continue
        if c == "|":
            garis += 1
        elif c in "pmbLR" and i + 1 < len(column_spec) and column_spec[i + 1] == "{":
            ukuran, i = braced_content(column_spec, i + 1)
            kolom += 1
            lebar.append(to_cm(ukuran, text_width))
            continue
        elif c in "lcrX":
            kolom += 1
            lebar.append(None)
        i += 1
    return lebar, kolom, garis


def find_tabular(blok, environment):
    if environment == "longtable":
        lewati = re.match(r"\s*(\[[^\]]*\])?", blok).end()
        column_spec, akhir = braced_content(blok, lewati)
        return "longtable", None, column_spec, akhir
    m = re.search(r"\\begin\{(tabularx|tabular)\}", blok)
    if not m:
        return None, None, None, None
    i = m.end()
    x_width = None
    if m.group(1) == "tabularx":
        x_width, i = braced_content(blok, i)
    column_spec, akhir = braced_content(blok, i)
    return m.group(1), x_width, column_spec, akhir


def split_rows(isi):
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


def unwrap_multicolumn(sel):
    m = re.match(r"\s*\\multicolumn\{(\d+)\}", sel)
    if not m:
        return 1, sel
    _, i = braced_content(sel, sel.find("{", m.end()))
    isi, _ = braced_content(sel, sel.find("{", i))
    return int(m.group(1)), isi


def plain_text(sel):
    sel = re.sub(r"\\(?:ref|cite|label|autoref)\{[^}]*\}", "X", sel)
    sel = re.sub(r"\\[a-zA-Z]+\*?", " ", sel)
    return re.sub(r"[{}~]", " ", sel)


def word_count(teks):
    return len(re.findall(r"\S+", plain_text(teks)))


def numbers_in(teks):
    return set(NUMBER_PATTERN.findall(strip_comments(teks)))


def column_name(column_headers, j):
    if j < len(column_headers):
        return re.sub(r"\s+", " ", plain_text(column_headers[j])).strip() or f"column {j + 1}"
    return f"column {j + 1}"


def check_content(table_report, berkas, first_line, table_rows):
    if len(table_rows) < 2:
        return
    column_headers, badan = table_rows[0], []
    for b in table_rows[1:]:
        rentang, isi = unwrap_multicolumn(b[0])
        if len(b) == 1 and rentang >= len(column_headers):
            if word_count(isi) > CELL_MAX_WORDS:
                table_report.catat(berkas, first_line, "T-CATATAN", False,
                          f"table-wide note row ({word_count(isi)} words), move it to the Keterangan below the table")
            continue
        badan.append([unwrap_multicolumn(s)[1] for s in b])
    for j in range(len(column_headers)):
        kolom = [b[j] for b in badan if j < len(b)]
        nama = column_name(column_headers, j)
        for b in badan:
            if j < len(b) and word_count(b[j]) > CELL_MAX_WORDS:
                awal = " ".join(plain_text(b[0]).split()[:4])
                table_report.catat(berkas, first_line, "T-SEL", False,
                          f"cell '{nama}' in row '{awal}' has {word_count(b[j])} words (max {CELL_MAX_WORDS}), move the reasoning to the paragraph or Keterangan")
        with_units = [s for s in kolom if word_count(s) <= 4 and re.search(r"\d\s*~?\s*" + UNITS_REGEX + r"(?![a-zA-Z])", s)]
        if len(with_units) >= UNIT_MIN_CELLS and "(" not in column_headers[j]:
            table_report.catat(berkas, first_line, "T-SATUAN", False,
                      f"column '{nama}': unit repeated in {len(with_units)} cells, write it once in the header, e.g. '{nama} (ms)'")
        decimal_places = set()
        for s in kolom:
            m = re.fullmatch(r"[\s$+\-]*(?:\\mu)?\d[\d.]*,(\d+)\s*\$?", s)
            if m:
                decimal_places.add(len(m.group(1)))
        if len(decimal_places) > 1:
            table_report.catat(berkas, first_line, "T-DESIMAL", False,
                      f"column '{nama}': inconsistent decimal places {sorted(decimal_places)}")
        for s in kolom:
            if plain_text(s).strip().lower() in VAGUE_FILLERS:
                table_report.catat(berkas, first_line, "T-ISIAN", False,
                          f"column '{nama}' contains '{s.strip()}', use '--' and explain in Keterangan")


def paragraph_after(plain_source, position, label):
    sisa = plain_source[position:position + 8000]
    awal = position
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
            if re.search(REF_PATTERN % re.escape(label), teks):
                return pos, teks
    return kandidat[0]


def opening(teks):
    polos = re.sub(r"\\(?:ref|autoref)\{[^}]*\}", "N", teks)
    polos = re.sub(r"[~{}]", " ", re.sub(r"\\[a-zA-Z]+\*?", " ", polos))
    return " ".join(polos.split()[:3]).rstrip(",")


def check_tables(table_report, berkas, sumber, text_width):
    polos = strip_comments(sumber)
    explainers = []
    for m in BLOCK_PATTERN.finditer(polos):
        environment, blok = m.group(1), m.group(2)
        first_line = line_number_of(polos, m.start())
        if Path(berkas).name in CHAPTERS_WITHOUT_TABLES:
            table_report.catat(berkas, first_line, "T-BAB", True, "Chapters 1 and 5 contain no tables")
        grid_label_match = re.search(r"\\label\{([^}]*)\}", blok)
        full_grid = bool(grid_label_match) and grid_label_match.group(1) in FULL_GRID_TABLES
        if full_grid:
            if re.search(r"\\(toprule|midrule|bottomrule|rowcolor|cellcolor)", blok) or "\\hline" not in blok:
                table_report.catat(berkas, first_line, "T-GRID", True, "related-work table: plain full grid, \\hline and vertical rules, no booktabs and no color")
        elif re.search(r"\\(hline|cline)|\\rowcolor", blok):
            table_report.catat(berkas, first_line, "T-GRID", True, "three-line style: \\toprule, \\midrule, \\bottomrule, without \\hline, \\cline, and \\rowcolor")
        if not full_grid and not all(f"\\{garis}" in blok for garis in ("toprule", "midrule", "bottomrule")):
            table_report.catat(berkas, first_line, "T-HEADER", True, "table without the full \\toprule, \\midrule, \\bottomrule set")
        if environment == "table" and re.match(r"\s*\[H\]", blok):
            table_report.catat(berkas, first_line, "T-FLOAT", False, "[H] pins the position, use [!ht]")
        jenis, x_width, column_spec, column_spec_end = find_tabular(blok, environment)
        if column_spec and "|" in column_spec and not full_grid:
            table_report.catat(berkas, first_line, "T-GRID", True, "vertical rule | in the column spec, three-line style has no vertical rules")
        caption_match = re.search(r"\\caption\{", blok)
        if not caption_match:
            table_report.catat(berkas, first_line, "T-CAPTION", True, "table without \\caption")
        else:
            caption_text, _ = braced_content(blok, caption_match.end() - 1)
            if environment == "table" and jenis and blok.find("\\begin{" + jenis) < caption_match.start():
                table_report.catat(berkas, first_line, "T-CAPTION", True, "table caption must be ABOVE the table")
            if caption_text.rstrip().endswith("."):
                table_report.catat(berkas, first_line, "T-CAPTION", False, "caption ends with a period, a caption is a noun phrase without one")
            if "(" in plain_text(caption_text):
                table_report.catat(berkas, first_line, "T-CAPTION", False, "caption has a parenthetical note, move it to the Keterangan line below the table")
            if word_count(caption_text) > CAPTION_MAX_WORDS:
                table_report.catat(berkas, first_line, "T-CAPTION", False, f"caption {word_count(caption_text)} words (max {CAPTION_MAX_WORDS})")
        if column_spec is not None:
            lebar, kolom, garis = read_column_spec(column_spec, text_width)
            context = polos[max(0, m.start() - 600):m.start()] + blok
            sep = re.findall(r"\\setlength\{\\tabcolsep\}\{([\d.]+)pt\}", context)
            tabcolsep = float(sep[-1]) if sep else TABCOLSEP_DEFAULT_PT
            if jenis != "tabularx" and lebar and all(x is not None for x in lebar):
                total = sum(lebar) + kolom * 2 * tabcolsep * PT_TO_CM + garis * 0.4 * PT_TO_CM
                if total > text_width + 0.05:
                    table_report.catat(berkas, first_line, "T-LEBAR", True,
                              f"table width {total:.2f} cm exceeds text width {text_width:.2f} cm")
            isi = blok[column_spec_end:] if column_spec_end else blok
            check_content(table_report, berkas, first_line, split_rows(isi))
        label_match = re.search(r"\\label\{([^}]*)\}", blok)
        label = label_match.group(1) if label_match else None
        if label:
            references = [r.start() for r in re.finditer(REF_PATTERN % re.escape(label), polos)]
            if not references:
                table_report.catat(berkas, first_line, "T-RUJUK", True, f"{label} is never referenced in a paragraph")
            elif min(references) > m.start():
                table_report.catat(berkas, first_line, "T-RUJUK", False, f"{label} is first referenced after the table, reference it first in an introductory paragraph")
        pos, teks = paragraph_after(polos, m.end(), label)
        if teks:
            explainers.append((line_number_of(polos, pos), teks, numbers_in(blok), label))
    check_explainers(table_report, berkas, explainers)


def check_explainers(table_report, berkas, explainers):
    sebelumnya = None
    berdasarkan = 0
    repeated_openers = []
    for baris, teks, table_numbers, label in explainers:
        opener = opening(teks)
        if opener.lower().startswith("berdasarkan tabel"):
            berdasarkan += 1
        if sebelumnya and opener.lower() == sebelumnya.lower():
            repeated_openers.append(str(baris))
        sebelumnya = opener
        kata = word_count(teks)
        if kata > PARAGRAPH_MAX_WORDS:
            table_report.catat(berkas, baris, "N-PANJANG", False, f"explanatory paragraph {label} has {kata} words (max {PARAGRAPH_MAX_WORDS}), split it by function")
        diulang = table_numbers & numbers_in(teks)
        if len(table_numbers) >= REPEAT_MIN_NUMBERS and len(diulang) / len(table_numbers) > REPEAT_RATIO_MAX:
            table_report.catat(berkas, baris, "N-ULANG", False,
                      f"explanatory paragraph {label} repeats {len(diulang)} of {len(table_numbers)} table numbers, write the finding and its meaning")
    if repeated_openers:
        table_report.catat(berkas, int(repeated_openers[0]), "N-PEMBUKA", False,
                  f"{len(repeated_openers)} explanatory paragraphs open the same way as the previous one (lines {', '.join(repeated_openers)})")
    if berdasarkan > BERDASARKAN_MAX_PER_CHAPTER:
        table_report.catat(berkas, 1, "N-PEMBUKA", False,
                  f"'Berdasarkan Tabel' opens {berdasarkan} paragraphs (max {BERDASARKAN_MAX_PER_CHAPTER} per chapter), vary the openers")


def prose_blocks(sumber):
    polos = strip_comments(sumber)
    for nama in NON_PROSE_ENVIRONMENTS:
        polos = re.sub(r"\\begin\{%s\*?\}.*?\\end\{%s\*?\}" % (nama, nama),
                       lambda m: "\n" * m.group(0).count("\n"), polos, flags=re.S)
    hasil, position = [], 0
    for blok in re.split(r"(\n\s*\n)", polos):
        teks = blok.strip()
        if teks and not teks.startswith(("\\section", "\\subsection", "\\subsubsection", "\\chapter", "\\label")):
            hasil.append((line_number_of(polos, position + len(blok) - len(blok.lstrip())), teks))
        position += len(blok)
    return hasil


def check_prose(table_report, berkas, sumber):
    total_words, sehingga, panjang, gaya = 0, 0, [], []
    for baris, teks in prose_blocks(sumber):
        if "\\makebox" in teks or teks.startswith("\\noindent\\makebox"):
            continue
        without_math = DISCARDED_MATH.sub("X", teks)
        total_words += word_count(without_math)
        sehingga += len(re.findall(r"\bsehingga\b", without_math))
        if re.search(r";|—|---", without_math):
            gaya.append(str(baris))
        for sentence in re.split(r"(?<=[.?!])\s+(?=[A-Z0-9\\])", without_math):
            n = word_count(sentence)
            if n > SENTENCE_MAX_WORDS:
                panjang.append((n, baris, " ".join(plain_text(sentence).split()[:6])))
    if gaya:
        table_report.catat(berkas, int(gaya[0]), "N-GAYA", False,
                  f"semicolon or em dash in {len(gaya)} paragraphs (laporan/CLAUDE.md), lines {', '.join(gaya)}")
    if panjang:
        example = "; ".join(f"line {b} ({n} words) '{a} ...'" for n, b, a in sorted(panjang, reverse=True)[:5])
        table_report.catat(berkas, sorted(panjang, reverse=True)[0][1], "N-KALIMAT", False,
                  f"{len(panjang)} sentences over {SENTENCE_MAX_WORDS} words, longest: {example}")
    if total_words:
        per_thousand = sehingga * 1000 / total_words
        if per_thousand > 5:
            table_report.catat(berkas, 1, "N-SEHINGGA", False,
                      f"'sehingga' {sehingga} times ({per_thousand:.1f} per 1,000 words), vary or split the sentences")


PCB_REVISION_PATTERN = re.compile(r"\brev\s?[0-9]+\b|\brevisi\s+(?:pertama|kedua|ketiga)\b|\bPCB\s+revisi\b", re.I)
SUBSECTION_META_PATTERN = re.compile(r"(?:^|(?<=\. ))\s*(?:Subbab|Butir|Bagian) ini\b")
OBJECTIVE_LABEL_PATTERN = re.compile(r"\btujuan\s*([0-9]+|pertama|kedua|ketiga|keempat)\b", re.I)
BOARD_WORD_PATTERN = re.compile(r"\b[Pp]apan\b")
LIBRARY_WORD_PATTERN = re.compile(r"(?<!Kajian )(?<!KAJIAN )(?<!Daftar )(?<!DAFTAR )(?<!daftar )\b[Pp]ustaka\b")
POINTER_PATTERN = re.compile(r"(?:Sub)?[Bb]ab~?\\ref\{|\b(?:Sub)?[Bb]ab~?\s?[0-9]\b|(?:diuraikan|dibahas|dijelaskan) pada (?:sub-?bagian|butir [a-z]\b)")


def check_objective_labels(table_report, berkas, sumber):
    for nomor, baris in enumerate(strip_comments(sumber).split("\n"), 1):
        m = OBJECTIVE_LABEL_PATTERN.search(plain_text(baris))
        if m:
            table_report.catat(berkas, nomor, "N-TUJUAN", True,
                      f"numbered label '{m.group(0)}' in printed text, name the content of the objective (path, model, pipeline) like the AFIB book")
        m = PCB_REVISION_PATTERN.search(plain_text(baris))
        if m:
            table_report.catat(berkas, nomor, "N-REVISI", True,
                      f"internal revision label '{m.group(0)}' in printed text, write only the final design")
        m = LIBRARY_WORD_PATTERN.search(plain_text(baris)) or BOARD_WORD_PATTERN.search(plain_text(baris))
        if m:
            table_report.catat(berkas, nomor, "N-ISTILAH", True,
                      f"'{m.group(0)}' for an electronics/software term, write \\textit{{library}} atau \\textit{{board}} (laporan/CLAUDE.md, Istilah Asing)")
        m = POINTER_PATTERN.search(baris)
        if m:
            table_report.catat(berkas, nomor, "N-PENUNJUK", True,
                      f"pointer '{m.group(0)}' to another chapter, section, or item, state the content directly")
        m = SUBSECTION_META_PATTERN.search(plain_text(baris))
        if m:
            table_report.catat(berkas, nomor, "N-META", True,
                      f"opener '{m.group(0)} ...' in a section, go straight to the content; 'Bab ini ...' only in a chapter opener")


def check_chapter_opening(table_report, berkas, sumber):
    polos = strip_comments(sumber)
    bab = re.search(r"\\chapter\{", polos)
    if not bab:
        return
    sesudah = re.search(r"\\(?:section|subsection)\{", polos[bab.end():])
    between = polos[bab.end():bab.end() + sesudah.start()] if sesudah else polos[bab.end():]
    between = re.sub(r"^[^\n]*\}\s*", "", between, count=1)
    between = re.sub(r"\\label\{[^}]*\}", "", between)
    if between.strip():
        table_report.catat(berkas, line_number_of(polos, bab.start()), "N-PEMBUKA-BAB", True,
                  "opening paragraph before the first section, go straight to the first section like the proposal")


def run_table_self_test():
    example = "\n".join([
        "\\chapter{Uji}",
        "Bab ini memaparkan uji.",
        "\\section{Hasil}",
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
        "\\subsection{Jalur Preprocessing (Tujuan 1)}",
        "\\label{subsec:hasil-tujuan1}",
        "Subbab ini memaparkan hasil uji.",
        "Desain PCB rev1 disusun rekan.",
        "Pemetaan label diuraikan pada Subbab~\\ref{subsec:x}.",
        "Pustaka pyserial dipakai pada Kajian Pustaka.",
    ])
    table_report = Report()
    check_tables(table_report, "uji.tex", example, TEXT_WIDTH_CM["a4"])
    check_prose(table_report, "uji.tex", example)
    check_objective_labels(table_report, "uji.tex", example)
    check_chapter_opening(table_report, "uji.tex", example)
    kode = {t[2] for t in table_report.temuan}
    expected_codes = {"N-ISTILAH", "N-PEMBUKA-BAB", "N-PENUNJUK", "N-REVISI", "N-META", "N-TUJUAN", "T-GRID", "T-HEADER", "T-FLOAT", "T-CAPTION", "T-LEBAR", "T-SATUAN", "T-ISIAN", "N-GAYA"}
    grid = Report()
    check_tables(grid, "uji.tex", "Lihat Tabel~\\ref{tab:perbandingan-penelitian}.\n\\begin{longtable}{|c|c|}\n\\caption{Perbandingan Penelitian Terkait}\\label{tab:perbandingan-penelitian}\\\\\n\\toprule\na & b \\\\\n\\bottomrule\n\\end{longtable}\n", TEXT_WIDTH_CM["a4"])
    if "T-GRID" not in {t[2] for t in grid.temuan}:
        kode.discard("T-GRID")
    kurang = expected_codes - kode
    if kurang:
        print(f"self-test FAILED, not detected: {sorted(kurang)}")
        return 1
    print(f"self-test passed ({len(table_report.temuan)} findings, {len(expected_codes)} expected codes detected)")
    return 0


def main():
    base_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Checker for tables and explanatory paragraphs in the PA report")
    parser.add_argument("berkas", nargs="*", help=".tex files, default laporan/buku-pa/bab/bab*.tex")
    parser.add_argument("--kertas", choices=sorted(TEXT_WIDTH_CM), default="a4")
    parser.add_argument("--hanya-galat", action="store_true")
    parser.add_argument("--ketat", action="store_true", help="suggestions also make the exit code 1")
    parser.add_argument("--tanpa-prosa", action="store_true", help="skip the sentence and paragraph style checks")
    parser.add_argument("--uji", action="store_true")
    arg = parser.parse_args()
    if arg.uji:
        return run_table_self_test()
    daftar = [Path(b) for b in arg.berkas] or sorted((base_dir / "laporan/buku-pa/bab").glob("bab*.tex"))
    table_report = Report()
    for berkas in daftar:
        sumber = berkas.read_text(encoding="utf-8")
        check_tables(table_report, berkas, sumber, TEXT_WIDTH_CM[arg.kertas])
        check_objective_labels(table_report, berkas, sumber)
        check_chapter_opening(table_report, berkas, sumber)
        if not arg.tanpa_prosa:
            check_prose(table_report, berkas, sumber)
    table_report.emit(arg.hanya_galat)
    print(f"{len(daftar)} files, {table_report.fault_count()} errors, {table_report.suggestion_count()} suggestions")
    if table_report.fault_count() or (arg.ketat and table_report.suggestion_count()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
