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
TABLE_OPENER_MAX_PER_CHAPTER = 3
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

    def catat(self, berkas, line_number, kode, fault, msg):
        self.temuan.append((str(berkas), line_number, kode, fault, msg))

    def fault_count(self):
        return sum(1 for t in self.temuan if t[3])

    def suggestion_count(self):
        return sum(1 for t in self.temuan if not t[3])

    def emit(self, hanya_galat):
        for berkas, line_number, kode, fault, msg in self.temuan:
            if hanya_galat and not fault:
                continue
            severity = "error" if fault else "suggestion"
            print(f"{berkas}:{line_number}: [{kode} {severity}] {msg}")


def strip_comments(text):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", b) for b in text.split("\n"))


def line_number_of(text, position):
    return text.count("\n", 0, position) + 1


def braced_content(text, i):
    if i >= len(text) or text[i] != "{":
        return "", i
    depth, j = 0, i
    while j < len(text):
        if text[j] == "{" and (j == 0 or text[j - 1] != "\\"):
            depth += 1
        elif text[j] == "}" and text[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
        j += 1
    return text[i + 1:], len(text)


def to_cm(size, text_width):
    size = size.strip()
    m = re.fullmatch(r"([\d.]*)\s*\\(?:linewidth|textwidth|columnwidth)", size)
    if m:
        return (float(m.group(1)) if m.group(1) else 1.0) * text_width
    m = re.fullmatch(r"([\d.]+)\s*(cm|mm|pt|in)", size)
    if not m:
        return None
    nilai, unit = float(m.group(1)), m.group(2)
    return {"cm": nilai, "mm": nilai / 10, "pt": nilai * PT_TO_CM, "in": nilai * 2.54}[unit]


def read_column_spec(column_spec, text_width):
    widths, kolom, vertical_rules, i = [], 0, 0, 0
    while i < len(column_spec):
        c = column_spec[i]
        if c in "><@!" and i + 1 < len(column_spec) and column_spec[i + 1] == "{":
            _, i = braced_content(column_spec, i + 1)
            continue
        if c == "|":
            vertical_rules += 1
        elif c in "pmbLR" and i + 1 < len(column_spec) and column_spec[i + 1] == "{":
            size, i = braced_content(column_spec, i + 1)
            kolom += 1
            widths.append(to_cm(size, text_width))
            continue
        elif c in "lcrX":
            kolom += 1
            widths.append(None)
        i += 1
    return widths, kolom, vertical_rules


def find_tabular(latex_block, environment):
    if environment == "longtable":
        options_end = re.match(r"\s*(\[[^\]]*\])?", latex_block).end()
        column_spec, block_end = braced_content(latex_block, options_end)
        return "longtable", None, column_spec, block_end
    m = re.search(r"\\begin\{(tabularx|tabular)\}", latex_block)
    if not m:
        return None, None, None, None
    i = m.end()
    x_width = None
    if m.group(1) == "tabularx":
        x_width, i = braced_content(latex_block, i)
    column_spec, block_end = braced_content(latex_block, i)
    return m.group(1), x_width, column_spec, block_end


def split_rows(body):
    body = re.sub(r"\\(caption|label)\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", body)
    body = re.sub(r"\\(rowcolor|cellcolor)(\[[^\]]*\])?\{[^}]*\}", " ", body)
    body = re.sub(r"\\(hline|endfirsthead|endhead|endfoot|endlastfoot|toprule|midrule|bottomrule|cline\{[^}]*\})", " ", body)
    body = re.sub(r"\\end\{(tabularx|tabular)\}.*", "", body, flags=re.S)
    line_number, seen = [], set()
    for raw_row in re.split(r"\\\\(?:\[[^\]]*\])?", body):
        sel = [s.strip() for s in re.split(r"(?<!\\)&", raw_row)]
        if not any(sel):
            continue
        row_key = "|".join(sel)
        if row_key in seen:
            continue
        seen.add(row_key)
        line_number.append(sel)
    return line_number


def unwrap_multicolumn(sel):
    m = re.match(r"\s*\\multicolumn\{(\d+)\}", sel)
    if not m:
        return 1, sel
    _, i = braced_content(sel, sel.find("{", m.end()))
    body, _ = braced_content(sel, sel.find("{", i))
    return int(m.group(1)), body


def plain_text(sel):
    sel = re.sub(r"\\(?:ref|cite|label|autoref)\{[^}]*\}", "X", sel)
    sel = re.sub(r"\\[a-zA-Z]+\*?", " ", sel)
    return re.sub(r"[{}~]", " ", sel)


def word_count(text):
    return len(re.findall(r"\S+", plain_text(text)))


def numbers_in(text):
    return set(NUMBER_PATTERN.findall(strip_comments(text)))


def column_name(column_headers, j):
    if j < len(column_headers):
        return re.sub(r"\s+", " ", plain_text(column_headers[j])).strip() or f"column {j + 1}"
    return f"column {j + 1}"


def check_content(table_report, berkas, first_line, table_rows):
    if len(table_rows) < 2:
        return
    column_headers, body_rows = table_rows[0], []
    for b in table_rows[1:]:
        column_span, body = unwrap_multicolumn(b[0])
        if len(b) == 1 and column_span >= len(column_headers):
            if word_count(body) > CELL_MAX_WORDS:
                table_report.catat(berkas, first_line, "T-CATATAN", False,
                          f"table-wide note row ({word_count(body)} words), move it to the Keterangan below the table")
            continue
        body_rows.append([unwrap_multicolumn(s)[1] for s in b])
    for j in range(len(column_headers)):
        kolom = [b[j] for b in body_rows if j < len(b)]
        column_label = column_name(column_headers, j)
        for b in body_rows:
            if j < len(b) and word_count(b[j]) > CELL_MAX_WORDS:
                awal = " ".join(plain_text(b[0]).split()[:4])
                table_report.catat(berkas, first_line, "T-SEL", False,
                          f"cell '{column_label}' in row '{awal}' has {word_count(b[j])} words (max {CELL_MAX_WORDS}), move the reasoning to the paragraph or Keterangan")
        with_units = [s for s in kolom if word_count(s) <= 4 and re.search(r"\d\s*~?\s*" + UNITS_REGEX + r"(?![a-zA-Z])", s)]
        if len(with_units) >= UNIT_MIN_CELLS and "(" not in column_headers[j]:
            table_report.catat(berkas, first_line, "T-SATUAN", False,
                      f"column '{column_label}': unit repeated in {len(with_units)} cells, write it once in the header, e.g. '{column_label} (ms)'")
        decimal_places = set()
        for s in kolom:
            m = re.fullmatch(r"[\s$+\-]*(?:\\mu)?\d[\d.]*,(\d+)\s*\$?", s)
            if m:
                decimal_places.add(len(m.group(1)))
        if len(decimal_places) > 1:
            table_report.catat(berkas, first_line, "T-DESIMAL", False,
                      f"column '{column_label}': inconsistent decimal places {sorted(decimal_places)}")
        for s in kolom:
            if plain_text(s).strip().lower() in VAGUE_FILLERS:
                table_report.catat(berkas, first_line, "T-ISIAN", False,
                          f"column '{column_label}' contains '{s.strip()}', use '--' and explain in Keterangan")


def paragraph_after(plain_source, position, label):
    rest = plain_source[position:position + 8000]
    awal = position
    candidates = []
    for m in re.finditer(r"(?:[^\n]+\n?)+", rest):
        text = m.group(0).strip()
        if not text or text.startswith(("\\end{", "\\begin{", "\\caption", "\\label", "\\centering")):
            continue
        if text.startswith(("\\section", "\\subsection", "\\subsubsection", "\\chapter")):
            break
        candidates.append((awal + m.start(), text))
        if len(candidates) == 3:
            break
    if not candidates:
        return None, None
    if label:
        for pos, text in candidates:
            if re.search(REF_PATTERN % re.escape(label), text):
                return pos, text
    return candidates[0]


def opening(text):
    plain = re.sub(r"\\(?:ref|autoref)\{[^}]*\}", "N", text)
    plain = re.sub(r"[~{}]", " ", re.sub(r"\\[a-zA-Z]+\*?", " ", plain))
    return " ".join(plain.split()[:3]).rstrip(",")


def check_tables(table_report, berkas, source, text_width):
    plain = strip_comments(source)
    explainers = []
    for m in BLOCK_PATTERN.finditer(plain):
        environment, latex_block = m.group(1), m.group(2)
        first_line = line_number_of(plain, m.start())
        if Path(berkas).name in CHAPTERS_WITHOUT_TABLES:
            table_report.catat(berkas, first_line, "T-BAB", True, "Chapters 1 and 5 contain no tables")
        grid_label_match = re.search(r"\\label\{([^}]*)\}", latex_block)
        full_grid = bool(grid_label_match) and grid_label_match.group(1) in FULL_GRID_TABLES
        if full_grid:
            if re.search(r"\\(toprule|midrule|bottomrule|rowcolor|cellcolor)", latex_block) or "\\hline" not in latex_block:
                table_report.catat(berkas, first_line, "T-GRID", True, "related-work table: plain full grid, \\hline and vertical rules, no booktabs and no color")
        elif re.search(r"\\(hline|cline)|\\rowcolor", latex_block):
            table_report.catat(berkas, first_line, "T-GRID", True, "three-line style: \\toprule, \\midrule, \\bottomrule, without \\hline, \\cline, and \\rowcolor")
        if not full_grid and not all(f"\\{vertical_rules}" in latex_block for vertical_rules in ("toprule", "midrule", "bottomrule")):
            table_report.catat(berkas, first_line, "T-HEADER", True, "table without the full \\toprule, \\midrule, \\bottomrule set")
        if environment == "table" and re.match(r"\s*\[H\]", latex_block):
            table_report.catat(berkas, first_line, "T-FLOAT", False, "[H] pins the position, use [!ht]")
        tabular_kind, x_width, column_spec, column_spec_end = find_tabular(latex_block, environment)
        if column_spec and "|" in column_spec and not full_grid:
            table_report.catat(berkas, first_line, "T-GRID", True, "vertical rule | in the column spec, three-line style has no vertical rules")
        caption_match = re.search(r"\\caption\{", latex_block)
        if not caption_match:
            table_report.catat(berkas, first_line, "T-CAPTION", True, "table without \\caption")
        else:
            caption_text, _ = braced_content(latex_block, caption_match.end() - 1)
            if environment == "table" and tabular_kind and latex_block.find("\\begin{" + tabular_kind) < caption_match.start():
                table_report.catat(berkas, first_line, "T-CAPTION", True, "table caption must be ABOVE the table")
            if caption_text.rstrip().endswith("."):
                table_report.catat(berkas, first_line, "T-CAPTION", False, "caption ends with a period, a caption is a noun phrase without one")
            if "(" in plain_text(caption_text):
                table_report.catat(berkas, first_line, "T-CAPTION", False, "caption has a parenthetical note, move it to the Keterangan line below the table")
            if word_count(caption_text) > CAPTION_MAX_WORDS:
                table_report.catat(berkas, first_line, "T-CAPTION", False, f"caption {word_count(caption_text)} words (max {CAPTION_MAX_WORDS})")
        if column_spec is not None:
            widths, kolom, vertical_rules = read_column_spec(column_spec, text_width)
            context = plain[max(0, m.start() - 600):m.start()] + latex_block
            sep = re.findall(r"\\setlength\{\\tabcolsep\}\{([\d.]+)pt\}", context)
            tabcolsep = float(sep[-1]) if sep else TABCOLSEP_DEFAULT_PT
            if tabular_kind != "tabularx" and widths and all(x is not None for x in widths):
                total = sum(widths) + kolom * 2 * tabcolsep * PT_TO_CM + vertical_rules * 0.4 * PT_TO_CM
                if total > text_width + 0.05:
                    table_report.catat(berkas, first_line, "T-LEBAR", True,
                              f"table width {total:.2f} cm exceeds text width {text_width:.2f} cm")
            body = latex_block[column_spec_end:] if column_spec_end else latex_block
            check_content(table_report, berkas, first_line, split_rows(body))
        label_match = re.search(r"\\label\{([^}]*)\}", latex_block)
        label = label_match.group(1) if label_match else None
        if label:
            references = [r.start() for r in re.finditer(REF_PATTERN % re.escape(label), plain)]
            if not references:
                table_report.catat(berkas, first_line, "T-RUJUK", True, f"{label} is never referenced in a paragraph")
            elif min(references) > m.start():
                table_report.catat(berkas, first_line, "T-RUJUK", False, f"{label} is first referenced after the table, reference it first in an introductory paragraph")
        pos, text = paragraph_after(plain, m.end(), label)
        if text:
            explainers.append((line_number_of(plain, pos), text, numbers_in(latex_block), label))
    check_explainers(table_report, berkas, explainers)


def check_explainers(table_report, berkas, explainers):
    previous_opener = None
    berdasarkan = 0
    repeated_openers = []
    for line_number, text, table_numbers, label in explainers:
        opener = opening(text)
        if opener.lower().startswith("berdasarkan tabel"):
            berdasarkan += 1
        if previous_opener and opener.lower() == previous_opener.lower():
            repeated_openers.append(str(line_number))
        previous_opener = opener
        words = word_count(text)
        if words > PARAGRAPH_MAX_WORDS:
            table_report.catat(berkas, line_number, "N-PANJANG", False, f"explanatory paragraph {label} has {words} words (max {PARAGRAPH_MAX_WORDS}), split it by function")
        diulang = table_numbers & numbers_in(text)
        if len(table_numbers) >= REPEAT_MIN_NUMBERS and len(diulang) / len(table_numbers) > REPEAT_RATIO_MAX:
            table_report.catat(berkas, line_number, "N-ULANG", False,
                      f"explanatory paragraph {label} repeats {len(diulang)} of {len(table_numbers)} table numbers, write the finding and its meaning")
    if repeated_openers:
        table_report.catat(berkas, int(repeated_openers[0]), "N-PEMBUKA", False,
                  f"{len(repeated_openers)} explanatory paragraphs open the same way as the previous one (lines {', '.join(repeated_openers)})")
    if berdasarkan > TABLE_OPENER_MAX_PER_CHAPTER:
        table_report.catat(berkas, 1, "N-PEMBUKA", False,
                  f"'Berdasarkan Tabel' opens {berdasarkan} paragraphs (max {TABLE_OPENER_MAX_PER_CHAPTER} per chapter), vary the openers")


def prose_blocks(source):
    plain = strip_comments(source)
    for column_label in NON_PROSE_ENVIRONMENTS:
        plain = re.sub(r"\\begin\{%s\*?\}.*?\\end\{%s\*?\}" % (column_label, column_label),
                       lambda m: "\n" * m.group(0).count("\n"), plain, flags=re.S)
    hasil, position = [], 0
    for latex_block in re.split(r"(\n\s*\n)", plain):
        text = latex_block.strip()
        if text and not text.startswith(("\\section", "\\subsection", "\\subsubsection", "\\chapter", "\\label")):
            hasil.append((line_number_of(plain, position + len(latex_block) - len(latex_block.lstrip())), text))
        position += len(latex_block)
    return hasil


def check_prose(table_report, berkas, source):
    total_words, sehingga, long_sentences, style_lines = 0, 0, [], []
    for line_number, text in prose_blocks(source):
        if "\\makebox" in text or text.startswith("\\noindent\\makebox"):
            continue
        without_math = DISCARDED_MATH.sub("X", text)
        total_words += word_count(without_math)
        sehingga += len(re.findall(r"\bsehingga\b", without_math))
        if re.search(r";|—|---", without_math):
            style_lines.append(str(line_number))
        for sentence in re.split(r"(?<=[.?!])\s+(?=[A-Z0-9\\])", without_math):
            n = word_count(sentence)
            if n > SENTENCE_MAX_WORDS:
                long_sentences.append((n, line_number, " ".join(plain_text(sentence).split()[:6])))
    if style_lines:
        table_report.catat(berkas, int(style_lines[0]), "N-GAYA", False,
                  f"semicolon or em dash in {len(style_lines)} paragraphs (laporan/CLAUDE.md), lines {', '.join(style_lines)}")
    if long_sentences:
        example = "; ".join(f"line {b} ({n} words) '{a} ...'" for n, b, a in sorted(long_sentences, reverse=True)[:5])
        table_report.catat(berkas, sorted(long_sentences, reverse=True)[0][1], "N-KALIMAT", False,
                  f"{len(long_sentences)} sentences over {SENTENCE_MAX_WORDS} words, longest: {example}")
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


def check_objective_labels(table_report, berkas, source):
    for line_no, line_number in enumerate(strip_comments(source).split("\n"), 1):
        m = OBJECTIVE_LABEL_PATTERN.search(plain_text(line_number))
        if m:
            table_report.catat(berkas, line_no, "N-TUJUAN", True,
                      f"numbered label '{m.group(0)}' in printed text, name the content of the objective (path, model, pipeline) like the AFIB book")
        m = PCB_REVISION_PATTERN.search(plain_text(line_number))
        if m:
            table_report.catat(berkas, line_no, "N-REVISI", True,
                      f"internal revision label '{m.group(0)}' in printed text, write only the final design")
        m = LIBRARY_WORD_PATTERN.search(plain_text(line_number)) or BOARD_WORD_PATTERN.search(plain_text(line_number))
        if m:
            table_report.catat(berkas, line_no, "N-ISTILAH", True,
                      f"'{m.group(0)}' for an electronics/software term, write \\textit{{library}} atau \\textit{{board}} (laporan/CLAUDE.md, Istilah Asing)")
        m = POINTER_PATTERN.search(line_number)
        if m:
            table_report.catat(berkas, line_no, "N-PENUNJUK", True,
                      f"pointer '{m.group(0)}' to another chapter, section, or item, state the content directly")
        m = SUBSECTION_META_PATTERN.search(plain_text(line_number))
        if m:
            table_report.catat(berkas, line_no, "N-META", True,
                      f"opener '{m.group(0)} ...' in a section, go straight to the content; 'Bab ini ...' only in a chapter opener")


def check_chapter_opening(table_report, berkas, source):
    plain = strip_comments(source)
    bab = re.search(r"\\chapter\{", plain)
    if not bab:
        return
    next_section = re.search(r"\\(?:section|subsection)\{", plain[bab.end():])
    between = plain[bab.end():bab.end() + next_section.start()] if next_section else plain[bab.end():]
    between = re.sub(r"^[^\n]*\}\s*", "", between, count=1)
    between = re.sub(r"\\label\{[^}]*\}", "", between)
    if between.strip():
        table_report.catat(berkas, line_number_of(plain, bab.start()), "N-PEMBUKA-BAB", True,
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
    undetected = expected_codes - kode
    if undetected:
        print(f"self-test FAILED, not detected: {sorted(undetected)}")
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
        source = berkas.read_text(encoding="utf-8")
        check_tables(table_report, berkas, source, TEXT_WIDTH_CM[arg.kertas])
        check_objective_labels(table_report, berkas, source)
        check_chapter_opening(table_report, berkas, source)
        if not arg.tanpa_prosa:
            check_prose(table_report, berkas, source)
    table_report.emit(arg.hanya_galat)
    print(f"{len(daftar)} files, {table_report.fault_count()} errors, {table_report.suggestion_count()} suggestions")
    if table_report.fault_count() or (arg.ketat and table_report.suggestion_count()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
