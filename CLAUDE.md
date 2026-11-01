# CLAUDE.md — Proyek Akhir (monorepo PA)

Panduan untuk Claude Code saat bekerja di repo ini. Baca dulu sebelum aksi.
Aturan khusus subdir: `model/CLAUDE.md` (jalur TinyML, decision point, jebakan)
dan `laporan/CLAUDE.md` (gaya tulis laporan).

## Apa ini

Monorepo Proyek Akhir: **monitoring detak jantung kontinu, klasifikasi
aritmia di edge** (ESP32-S3 + TinyML INT8). Komponen per subdir — lihat
`README.md` untuk tabel & alur artefak.

**Dokumen kerja yang sedang berjalan** lintas komponen ada di `docs/`
(indeks `docs/README.md`); `docs/arsip/` hanya riwayat.

**Pekerjaan terbuka** (bertanggal, jangan sampai lupa): daftar tunggal di
[`model/CLAUDE.md` §Pekerjaan terbuka](model/CLAUDE.md#pekerjaan-terbuka) —
konsumsi daya, **WiFi board sengaja OFF (darurat sejak 14 Okt 2026, kembalikan
ke ON setelah konverter baterai disetel 5 V)**, lalu rencana rekaman mentah
langsung ke server lewat WiFi, serta PCB rev2. Data resmi sinyal tubuh = sesi
22 Okt 2026 siang (`model/data/recordings/README.md`); data sebelum 13 Okt 2026
= uji coba (arsip). Angka laporan yang menunggu data: `grep -rn
PLACEHOLDER-DATA laporan/buku-pa` (tinggal daya).

## Aturan keras (STRICT, ditetapkan user 13 Okt 2026)

Berlaku untuk semua kode di repo. Tidak ada pengecualian tanpa izin user.

### Verifikasi pekerjaan sendiri
A. **Jalankan sendiri sebelum bilang selesai.** Build, flash, jalankan di board
   (board tercolok = Claude yang menjalankan), tekan/suntik tombolnya, baca log
   serial, jalankan skrip. User bukan verifikator.
B. **Setiap commit membawa bukti:** keluaran test yang lulus, potongan log serial,
   keluaran skrip, atau tangkapan layar/foto. Bukti ditulis di pesan commit atau
   laporan akhir. Tanpa bukti, tidak di-commit.
C. **Kalau tidak bisa diverifikasi, berhenti dan katakan.** Sebutkan persis apa
   yang belum terbukti (mis. tampilan layar, bunyi buzzer, angka daya dengan
   baterai) dan cara user mengeceknya. Tebakan yang tampak selesai adalah hal
   terburuk yang bisa diserahkan.

### Kenali kode dulu
1. **Baca peta fitur sebelum menyentuh modul.** Peta yang sudah tertulis:
   `README.md` (komponen), `firmware/README.md` (modul, tombol, menu, perintah
   serial), `model/docs/README.md` (pipeline model), `model/CLAUDE.md`
   (decision point). Jangan menebak struktur yang sudah didokumentasikan.
2. **Buka berkas sebelum mengeditnya.** Jangan pernah menulis kode dari ingatan
   tentang isi berkas.
3. **Satu fitur per commit.** Fitur tidak meng-include fitur lain; kode bersama
   lewat lapisan bersama. Firmware: lapisan bersama = `perangkat`, `konfig`,
   `ecg_*`, `ina219`; perangkai = `main.cpp` dan `menu.cpp`; fitur lain tidak
   saling meng-include.

### Aturan keras, ditegakkan pemeriksa
4. **Tanpa `useEffect`** (berlaku bila ada kode React/frontend): turunkan
   nilainya atau tangani di event.
5. **TANPA KOMENTAR KODE.** C/C++, Python (termasuk docstring), shell, dan
   `platformio.ini`. Kalau kode butuh komentar, ganti namanya atau pecah sampai
   tidak butuh. Penjelasan, rasional, jebakan, dan cara pakai ditulis di
   DOKUMEN tersendiri (`firmware/README.md`, walkthrough, `model/docs/`), bukan
   di kode. Berkas GENERATED juga tanpa komentar (generatornya tidak menulis
   komentar). Pengecualian fungsional saja: deskripsi target `##` di Makefile
   (dipakai `make help`) dan teks bantuan CLI yang dicetak program.
6. **Aturan hidup di CI.** Pemeriksa: `python3 scripts/cek_komentar.py` dan
   `.github/workflows/cek.yml`. Aturan yang tidak bisa diperiksa mesin diubah
   jadi pemeriksaan, atau dihapus dari berkas ini.

### Tutup lingkarannya
7. **Setiap kegagalan yang ditangkap user menjadi skill hari itu juga**
   (`.claude/skills/<nama>/SKILL.md`). Kegagalan yang sama tidak boleh terulang.
8. **Setiap skill punya eval** yang dinilai model berbeda, target 10/10,
   **maksimal 3 putaran**. Belum 10/10 sesudah putaran ke-3 → berhenti, catat
   skor terbaik dan temuannya di `eval.md`, commit, lalu tanya user. Soal eval
   sempit dan berjawaban pasti (kegagalan aslinya), bukan desain terbuka.
   Skor yang tidak naik dua putaran berturut-turut = berhenti lebih awal.
   (Ditetapkan 15 Okt 2026 sesudah eval `batas-tidak-diam` berputar 8 kali
   di skor 7–9 tanpa hasil.)
9. **Pemeriksaan hijau → commit langsung**, tanpa menunggu persetujuan; user
   meninjau setelahnya. Satu revert lebih murah daripada agen yang tertahan.
   Push ke remote tetap hanya atas permintaan eksplisit.

## Aturan kerja (non-negotiable)

1. **Non-destruktif.** Jangan hapus/pindah/rename file yang sudah ada. Semua
   pembuatan file pola "buat jika belum ada", jangan overwrite. Satu-satunya
   pemindahan rutin: dokumen riwayat/rencana yang selesai dan alat sekali pakai
   → `arsip/` (lihat **Dokumentasi**), lewat `git mv`.
2. **`laporan/` read-only by default.** `.tex`, `.bib`, `bab/`, `gambar/`
   jangan diutak-atik tanpa konfirmasi. Path relatif rapuh. Aturan detail
   (gaya tulis, konvensi tabel/gambar, struktur bab) ada di `laporan/CLAUDE.md`
   — baca itu dulu kalau kerja di `laporan/`.
3. **PRD = `model/PRD_Model_Aritmia_TinyML.pdf`** (PDF, bukan `.md`; baca pakai
   Read `pages=`). Ikuti kontrak fungsi & jebakan di sana; jangan vibe-coding.
4. **Cari dulu di repo sendiri sebelum merancang.** Rencana, skrip, dan
   mekanisme yang dibutuhkan sering SUDAH ada, tinggal dikerjakan atau diperluas.
   Contoh: sumber sinyal replay untuk uji tanpa hardware sudah ada di firmware
   (menu Sumber sinyal, atau toggle serial `y`), dan rantai penyelarasan R-peak sudah jadi di
   `model/scripts/eval_detected_segmentation.py`. Merancang
   ulang dari nol di tempat seperti itu = pekerjaan ganda yang sia-sia.

## Bukti mengalahkan kekakuan

Aturan di atas menjaga hal yang sudah terbukti. Aturan ini menjaga supaya yang
terbukti tidak membeku jadi dogma.

- **Golden reference (`firmware/test/golden_ref.h`) itu REGRESSION TEST, bukan
  pagar desain.** Yang dijamin: C dan Python menghitung hal yang sama. Yang
  TIDAK dijamin: parameternya sudah optimal. Kalau ada bukti konkret (paper
  ber-ablasi, atau eksperimen sendiri) bahwa parameter lain lebih baik, ubah
  parameternya lalu **regenerasi** golden (`python scripts/export_golden.py`
  dari `model/`) dan jalankan `pio test -e native`. Regenerasi = prosedur
  rutin. Menolak perubahan "karena nanti golden berubah" = alasan yang salah.
- **Adopsi dari paper hanya kalau papernya mengablasi klaimnya.** Kalau paper
  cuma memakai metode X tanpa pernah membandingkannya, yang kita punya bukan
  bukti melainkan preseden. Boleh ditiru — setelah kita sendiri yang mengablasi.
  Contoh: Dias 2021 mengablasi jitter (Tabel 3, 6-8, 33 ulangan) tapi tidak
  pernah mengablasi filternya, jadi jitter-nya diadopsi dan filternya tidak.
- **Jangan menyalin konstanta empiris paper kalau kita bisa mengukur sendiri.**
  Dias memakai jitter seragam ±18 sampel karena mereka tidak punya detektor.
  Kita punya, dan residunya berbentuk lain sama sekali (inti tajam ±2, ekor
  berat sampai 54). Menyalin 18 berarti melatih model melawan error yang bukan
  milik kita.
- **Knob eksperimen lewat environment, bukan lewat mengedit nilai final.**
  `config.py` membaca `PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS` (dan knob ablasi
  lain yang tercatat di `model/CLAUDE.md`); tanpa env, nilainya persis bawaan.
  Ablasi jalan tanpa menyentuh gate point. Nilai yang MENANG dikunci dengan
  mengubah bawaannya — dan itu tetap gate point.

## Cara kerja yang diminta user

- **Data, bukan asumsi.** Penyebab masalah (hardware rusak, broker lambat,
  noise dari modul) baru boleh disimpulkan setelah diukur. Kalau hipotesis
  gagal, pasang pencacah/ukur dulu, jangan menebak tersangka berikutnya dan
  jangan berputar-putar.
- **Rencana yang disetujui dijalankan sampai selesai** tanpa minta konfirmasi
  tiap langkah; berhenti hanya pada anomali atau gate point. Pekerjaan yang bisa
  paralel boleh disebar ke subagen.
- **Keputusan desain/trade-off milik user.** Sajikan opsi + rekomendasi beserta
  alasannya (rujuk PRD/data), lalu biarkan user memilih. Usulan dari riset paper
  yang menyimpang dari rencana awal ditulis ringkasannya dulu sebelum
  implementasi.
- **Eksplorasi di luar rencana tidak otomatis jadi rencana.** Cek spek/percobaan
  sampingan cukup dilaporkan; jangan ditulis ke dokumen rencana tanpa diminta.
- **Rujukan resmi menang atas ingatan.** Datasheet/dokumentasi resmi modul
  (penempatan elektroda, pin I2C, polaritas buzzer, dll.) yang dirujuk user
  diikuti; jangan berdebat dari ingatan.
- **Sederhana.** Jangan memecah fungsi/abstraksi tanpa alasan; hindari
  over-engineering.
- **Laporan hanya kalau diminta.** Saat mengerjakan program, jangan menyisipkan
  atau menyarankan pekerjaan `laporan/` sebagai langkah berikutnya.
- **Git:** commit otomatis setelah pemeriksaan hijau (Aturan keras 9); push hanya
  kalau diminta eksplisit (user sering push sendiri).
- **Akhiri tugas dengan laporan ringkas:** apa yang dikerjakan, angka hasil
  verifikasi, dan sisa pekerjaan terhadap rencana.
- **Yang dipelajari dicatat di repo**, bukan cuma di chat: keputusan & jebakan
  ke `CLAUDE.md` yang relevan, penjelasan ke walkthrough/README — tidak pernah
  ke komentar kode.

## Dokumentasi

- **Tiap pekerjaan selesai → dokumentasinya ikut ditulis**, cukup lengkap supaya
  user bisa mengulang sendiri tanpa Claude: data disimpan di mana, cara
  menariknya, cara menganalisis & membuat grafik, cara toggle/flag. Walkthrough
  model: aturan di `model/CLAUDE.md`, peta di `model/docs/README.md`.
- **Dokumen aktif = dokumentasi resmi kondisi SAAT INI.** Tanpa penanda revisi
  ("KOREKSI", "revisi dari ...", "update:"), narasi sesi, kata waktu-relatif
  ("dulu", "semula", "ternyata"), checklist progres, atau emoji penanda. Klaim
  yang pernah dikoreksi cukup ditulis versi benarnya. Rasional desain dan
  alternatif yang ditolak tetap ditulis ("Alternatif X tidak dipakai karena ...").
  Tanggal hanya sebagai metadata pengukuran ("Kondisi uji: board N16R8, 19 Sep 2026").
- **`docs/` = masih berlaku, `docs/arsip/` = catatan historis.** Dokumen
  bertanggal yang masih berjalan (daftar kerja, riset yang aksinya belum
  diputuskan, rencana yang belum selesai) ditaruh langsung di `docs/` (nama
  `YYYY-MM-DD-<topik>.md`) dan didaftar di `docs/README.md`. Isi `docs/arsip/`
  dan `model/docs/arsip/` **tidak berlaku sebagai acuan kerja**: hanya riwayat.
  Jangan dibaca sebagai konteks kerja kecuali user merujuknya atau sedang
  menelusuri asal sebuah keputusan; kondisi yang berlaku ada di README
  komponen, walkthrough, `CLAUDE.md`, dan skill.
- **Riwayat masuk arsip.** Rencana, desain, changelog, dan catatan revisi
  yang selesai dipindah ke `docs/arsip/` atau `model/docs/arsip/` lewat
  `git mv` (prosedur di `docs/README.md`), setelah hasilnya tercatat di
  dokumen yang berlaku. Riwayat yang
  dikeluarkan dari sebuah dokumen aktif → `arsip/riwayat-<nama-dokumen>.md`.
  Perubahan terhadap rencana awal dicatat dengan tanggalnya di changelog arsip.
- **Alat sekali pakai → `*/arsip/`** (mis. `firmware/arsip/`), atau dihapus
  bila tidak dirujuk lagi (git tetap menyimpannya).
- **Yang usang dibuang dari dokumen aktif & kode**, bukan ditandai "lama"
  (contoh: buzzer aktif yang sudah tidak dipakai). Kalau bermuatan informasi,
  pindahkan ke arsip.
- **Bahasa:** Indonesia baku, ringkas; desimal koma (0,6594), ribuan titik
  (85.812); istilah teknis Inggris tetap. Hal yang dijalankan (build, rekam,
  flash, kalibrasi) ditulis sebagai prosedur: langkah bernomor, perintah di blok
  kode, hasil yang diharapkan.
- **Berkas hasil** (rekaman, grafik) bernama ber-timestamp dan dikelompokkan per
  folder kategori, bukan nama generik seperti "percobaan".

## Artefak: produsen → konsumen

- `model/` → `model_int8.h` → `firmware/include/` (GENERATED, jangan edit tangan)
- `model/scripts/export_golden.py` → `firmware/test/golden_ref.h` (GENERATED)
- `model/artifacts/metrics/*.png` & `dashboard/preview.png` → figure →
  `laporan/*/gambar/` (`export_artifacts.sh --laporan`)
- Sinkron via `scripts/export_artifacts.sh`. **Jangan copy manual.**
- Kebijakan commit: **B1** — figure final + `.h` di-commit; data mentah
  MIT-BIH & `.npz` intermediate di-ignore (`.gitignore`).

## Build

- Laporan:  `cd laporan/<projek> && make pdf` → `output/main.pdf` (gitignored).
  Projek: `proposal-pa` (A4), `buku-pa`, `surat-magang`; `shared/` = preamble +
  `Makefile.inc`. **Ukuran kertas fixed per projek** (`\input ../shared/size-aX`),
  tidak ada `make a4`/`make a5`.
- Model:    `cd model && make <target>` (daftar: `make help`; ringkasan di
  `model/CLAUDE.md`). Python 3.11.9 (`model/.python-version`), venv di
  `model/.venv`, deps di `model/requirements.txt`. Script cek/eksplorasi ad-hoc
  → `model/scripts/` (dijalankan dari folder `model/`).
- Firmware: lihat **ESP32 / mikrokontroler** di bawah.
- Dashboard: `cd dashboard && docker compose up -d` (ThingsBoard CE).

## ESP32 / mikrokontroler → PlatformIO

Semua kerja ESP32/mikrokontroler (build, flash, monitor, test, cek library,
cek board/pin) **lewat PlatformIO CLI (`pio`)**, bukan Arduino IDE/CLI, bukan
`idf.py`/`esptool.py` langsung. Konfigurasi tunggal = `firmware/platformio.ini`
(env `esp32-s3` = firmware utama + test perangkat `test_hw_*` di board N16R8,
env `native` = test di PC). Jalankan dari `firmware/`.

- Build:        `pio run` (default env `esp32-s3`)
- Flash:        `pio run -t upload` · monitor: `pio device monitor` (115200)
- Port/board:   `pio device list` · `pio boards <kata>`
- Test PC:      `pio test -e native` (tanpa board) · di device: `pio test -e esp32-s3`
- Library:      `pio pkg search|show <nama>`; tambah ke `lib_deps` di
  `platformio.ini` = dependency baru → **gate point, tanya dulu**.
- Info board/framework: baca dari `~/.platformio/platforms/espressif32` &
  `~/.platformio/packages/` (versi terpasang) sebelum menebak dari ingatan.
- **Board tercolok → Claude sendiri** yang menjalankan `pio device list`, flash,
  monitor, dan membaca hasilnya. Port jangan di-hardcode: berpindah antara
  `/dev/ttyACM*` dan `/dev/ttyUSB*`.
- **Uji tanpa sensor lewat flag/mode simulasi** (replay golden, toggle serial,
  build flag), bukan salinan kode terpisah.
- **Sebelum mengubah pin/driver**, pastikan perangkat keras yang sedang dipakai
  (breadboard atau PCB rev N). Pin map tunggal ada di
  `firmware/include/perangkat.h`; penyesuaian PCB rev2 di
  `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md`.

## Diagrams & gambar laporan

- **Claude TIDAK membuat diagram/gambar ilustrasi sendiri**: tidak ada Mermaid,
  TikZ, PlantUML, Graphviz, SVG/draw.io, skrip gambar baru, atau gambar AI.
  Di posisi gambar, taruh
  **placeholder** + kartu spesifikasi isi (jenis, pesan, elemen wajib, alur
  baca, bahan di repo); **user yang menggambar**. Caption, `\label`, `\ref`, dan
  paragraf pengantar/penjelas tetap ditulis final. Templat: skill
  `struktur-pa` aturan 9.
  Sisa placeholder: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.
- Plot data eksperimen (confusion matrix, kurva, grafik latensi) hasil pipeline
  repo bukan ilustrasi: rujuk berkas yang sudah di-export. Kalau belum ada →
  placeholder + sebut skrip penghasilnya, jangan tulis skrip plot baru tanpa diminta.
- Label requirement `RM1..RM4` **TIDAK boleh muncul** di diagram apa pun.

## Menulis laporan (progres / buku PA)

Acuan penulisan = empat skill di `.claude/skills/`: `struktur-pa` (kerangka
bab, benang merah, register, placeholder gambar, QA sebelum kumpul),
`narasi-pa` (paragraf), `tabel-pa` (tabel), dan `buku-ikut-proposal` (Bab 1
dan sinkronisasi proposal). Bedah 6 laporan PA PENS yang menjadi asal
aturannya sudah diarsipkan di `docs/arsip/2026-10-10-pola-laporan-pa/` dan
tidak dijadikan acuan lagi. Aturan gaya tulis tetap `laporan/CLAUDE.md`.
Keputusan lingkup yang sudah diambil user: PA individu, subjek uji anonim
(kode S01, S02, ...), tempat uji laboratorium, TLS/keamanan transport tidak
dibahas sama sekali. Buku hanya membahas MIT-BIH: SVDB/INCART dan uji
lintas basis data tidak ditulis walau hasilnya ada di repo (19 Okt 2026).
Pustaka diutamakan terbitan 2020 ke atas, kecuali sumber asli metode/data
dan standar yang masih berlaku (arahan dosen; rasional per entri di
`docs/arsip/2026-10-19-referensi-pra-2020.md`). Buku full =
`laporan/buku-pa` (dikerjakan), buku tahap 1 = `laporan/progres-pa-1`
(buku-pa tanpa INA219 dan catu daya, isi 50–70% menurut pembimbing;
prosedur regenerasi di `laporan/CLAUDE.md`). **`laporan/proposal-pa` sudah
diserahkan dan dibekukan (15 Okt 2026): tidak disunting lagi, termasuk
`.bib`-nya.** Buku tidak memuat tabel "perubahan dari proposal" dan tidak
memberi label bernomor "Tujuan N" di judul atau kalimat; gaya mengikuti buku
AFIB (keputusan user 19 Okt 2026, skill `struktur-pa` aturan 2).

- **Label kerja internal repo TIDAK boleh muncul di teks laporan resmi**
  (`laporan/**/*.tex` yang dicetak): HW-n, Fase n / Fase A–G, Task n, T-n/K-n,
  revisi PCB (rev1, rev2, "PCB revisi kedua"),
  path berkas, nama skrip, nama env/knob (`PA_*`, env PlatformIO), dan kata
  "walkthrough". Label itu hanya untuk dokumen internal repo (`model/docs/`,
  `CLAUDE.md`, README). Di laporan, sebut isinya dengan istilah umum
  ("pengujian akuisisi sinyal tubuh", "ablasi ukuran window"). Komentar
  `% sumber:` di `.tex` tidak dicetak, jadi boleh memuat path.

## Gate points (berhenti, minta konfirmasi)

- Memindahkan/rename apa pun di `laporan/` → pakai `git mv`, konfirmasi dulu.
- Menambah dependency baru → tanya dulu; utamakan stdlib/yang sudah ada.
- Mengubah nilai final di `model/config.py` (FS, bandpass, window, label map)
  → milik user, konfirmasi dulu.
- Push ke remote → hanya atas permintaan eksplisit.
