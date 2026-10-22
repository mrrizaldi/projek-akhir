# CLAUDE.md — model/ (jalur TinyML)

Spesifikasi lengkap: `PRD_Model_Aritmia_TinyML.pdf` (19 hal, Fase 0–8).
Baca fase terkait sebelum menyentuh file apa pun. Jangan vibe-coding.

## Aturan

1. **`src/` = modul MURNI** (fungsi in→out, tanpa kode top-level, import-safe).
   **`scripts/` = eksekusi** (cetak, plot, tulis file). Jangan campur.
2. **Semua konstanta di `config.py`.** Jangan hardcode angka di `src/`.
3. **DS2 haram disentuh sebelum Fase 6.** Bukan validation, bukan tuning
   threshold. Sekali sentuh di Fase 6–7, itu saja.
4. **`sosfilt`, BUKAN `filtfilt`** (kausal — JEBAKAN #1 PRD). `filtfilt` mustahil
   real-time di MCU → train/deploy mismatch.
5. **Segmentasi training pakai R-peak dari ANOTASI**, bukan Pan-Tompkins
   (keputusan terkunci, PRD Fase 2).
6. **Tiap fase selesai → tulis walkthrough.** Satu file per modul di `docs/`,
   pola nama `<modul>-walkthrough.md`. Lihat "Walkthrough per fase" di bawah.
   Rencana, desain, dan changelog bertanggal masuk `docs/arsip/`, bukan `docs/`.
7. **Penjelasan tinggal di `docs/`, bukan di `src/`.** File `src/` ditulis
   sependek mungkin (nyaris tanpa komentar) supaya terbaca sebagai persamaan
   dan gampang diterjemahkan ke C. Kalau butuh menjelaskan "kenapa", tempatnya
   walkthrough — bukan docstring 40 baris.

## Perintah

```
make data      # download MIT-BIH (sekali)      make train     # Fase 5
make check     # cek kelengkapan dataset        make eval      # Fase 6
make plot0     # verifikasi Fase 0 (R-peak)     make quantize  # Fase 7
make plot1     # verifikasi Fase 1a (filter)    make export    # .h ke firmware
make plot1seg  # verifikasi Fase 1b (segmentasi)
make prep      # Fase 2 → per_record/*.npz      make test      # pytest
make split     # Fase 3 → train/test.npz         make poc       # Fase 8 checklist
make pull      # tarik rekaman dari board
make analisis FILE=data/recordings/<nama>.csv   # analisis + grafik rekaman
make pull-daya [N=<n>]   # tarik hasil tangga daya mandiri /daya/NNN.csv dari board
make broker-info         # SSID, IP LAN, port 1883/8080, saran entri wifi_secrets.h
```

`make help` menampilkan semua target (termasuk `data-semua`, `split-multi`, `clean`).

## Status fase

Satu baris per fase, hanya kondisi yang berlaku sekarang. Log per fase beserta
angka konfigurasi lama ada di
[`docs/arsip/riwayat-status-fase.md`](docs/arsip/riwayat-status-fase.md).
Uraian panjang masuk walkthrough atau Bab 4 laporan, bukan ke sini.

| Fase | Status | Kondisi & angka yang berlaku |
|---|---|---|
| 0 Data | selesai | 48 record lengkap, `fs == 360`. Rec 114 memakai MLII di indeks 1; rec 102/104 (tanpa MLII) ditolak `ValueError` |
| 1 Filter & segmentasi | selesai | bandpass 0,5–40 Hz orde 4 kausal (`sosfilt`). Group delay +4 sampel (+11,2 ms) → R di indeks `WIN_PRE + 4` = **132** |
| 2 Fitur RR & prep | selesai | `make prep`: **202.560 beat** (Normal 89,7% / Aritmia 10,3%, 215 dibuang). DS1 diaugmentasi jitter empiris (1 bersih + 2 salinan), DS2 bersih |
| 3 Split | selesai | inter-patient: **DS1 152.904 beat / DS2 49.656 beat**, `X_morph` (N,256,1). Kebocoran lintas pasien di-`raise` mekanis |
| 4 Model | selesai | dua input, **6.417 param**, tanpa dropout |
| 5 Latih | selesai | `artifacts/model_fp32.keras`, `class_weight` balanced, EarlyStopping(`val_auc`), Adam 1e-3 |
| 6 Evaluasi | selesai | threshold **0,80** dari VAL. DS2: **recall 0,6996, precision 0,6235, F1 0,6594, specificity 0,9479, AUC 0,9334**. Median recall per pasien 0,9167; terburuk rec 232 (0,3541) dan 213 (0,2246) |
| 6b Segmentasi on-device | selesai (di luar PRD) | offset detektor 38 sampel (DS1). Segmentasi tidak merusak klasifikasi: F1 beat terdeteksi 0,6499 vs anotasi 0,6594. Recall sistem 0,6035 (anotasi 0,6996) karena beat tak terdeteksi (sensitivity detektor kelas S 0,6494). `fase6b_segmentasi_deteksi.csv` |
| 6c Ketahanan jitter | selesai (di luar PRD) | dikunci: `WIN_PRE/WIN_POST = 128/128`, `JITTER_MODEL = "empiris"`, `JITTER_SALINAN = 2`, `THRESHOLD = 0,80`. HOS ditolak |
| 7 Kuantisasi | selesai | PTQ INT8 penuh (varian deploy): **22,94 KB**, recall 0,7105, F1 0,6604, AUC 0,9344, delta recall **+0,0108** |
| 8 PoC & ekspor | selesai | `make poc` 8/8 item DoD terverifikasi mekanis; `make export` → `firmware/include/model_int8.h`. Salin figure ke `laporan/` hanya dengan `--laporan` |
| HW-1 Inferensi di board | selesai | probabilitas device cocok PC (selisih maks 1 kuantum INT8), **26,6 ms per detak**, tensor arena 12.948 B |
| HW-2 Deteksi R di C | selesai | Pan-Tompkins (`ecg_detect_r`, `ecg_align_r`) cocok Python 11/11 puncak di golden |
| HW-3 Alur hidup | selesai | `src/ecg_live.cpp`: beban rata-rata 3,0% anggaran, burst puncak 33,4 ms → ADC wajib lewat ISR + antrean |
| HW-4 Firmware produksi | selesai | timer ISR 360 Hz → antrean 256 → `ecg_live` → inferensi → LED + serial; sampel hilang 0 |
| HW-5 Sinyal tubuh | selesai | data resmi = sesi 22 Okt 2026 siang (R1–R4, 927,1 s, MLII, satu subjek), keempatnya Berhasil; buku-pa Tabel kualitas rekaman. Gerbang kalibrasi berbasis kontak (LO±, ayunan 60, dengung 500, pemanasan 60 s) dari tiga sesi ±15 menit 21–22 Okt. Rekaman 10 Sep–11 Okt 2026 = uji coba (arsip). Detail: `data/recordings/README.md`, `docs/mqtt-walkthrough.md` §3.1 |
| HW-6 MQTT + ThingsBoard | selesai | gerbang kalibrasi + gerbang ayunan, backlog 27.000 beat di PSRAM. PDSR 100% / 99,2%, latensi median 939 / 1.108 ms (2 ulangan). Terbuka: daya mode WiFi. Detail: `docs/mqtt-walkthrough.md` |
| HW-7 Replay | selesai | sumber sinyal replay (menu Sumber sinyal: replay acuan 208 atau replay rekaman `/rekam/NNN.csv`; serial `y` = ADC ⇄ acuan) menggantikan ADC di ISR; 11 beat per putaran 6,67 detik, sampel hilang 0 |

## Pekerjaan terbuka

- **(13 Okt 2026) PCB rev2 — cek fisik sebelum fabrikasi.** Desain ada di
  [`../hardware/mainboard/`](../hardware/mainboard/README.md) (skematik +
  layout, `cek_board.py` lulus). Yang tersisa ada di bagian "Yang belum
  terverifikasi" README itu: jarak baris header DevKit fisik, urutan pin
  modul, ruang mekanik modul, uji breadboard jalur D1→VSYS, konektor baterai,
  dan tegangan lampu saklar. Ukur tegangan VIN_ESP setelah D2 saat dicatu
  baterai.
- **(14 Okt 2026) Wujud rakitan di buku menunggu PCB final.** Buku-pa menyebut
  "rangkaian uji dengan peta pin PCB". Setelah desain PCB final dicetak,
  perbarui tabel perangkat keras uji, foto rakitan, dan saran perangkat
  *wearable* di Bab 4/5.

Daftar hal yang BELUM selesai dan mudah terlupa. Butir bertanggal; hapus butir
hanya setelah benar-benar ditutup (catat penutupnya di walkthrough terkait).

- **(13 Okt 2026) Konsumsi daya per mode operasi.** Pengukuran daya per mode
  (idle, inferensi, WiFi/MQTT): rancangan di
  [`docs/arsip/2026-09-16-daya-design.md`](docs/arsip/2026-09-16-daya-design.md).
  Jalur ukur sudah jadi: dari laptop (serial `p0`-`p5`, `scripts/measure_power.py`
  -> `artifacts/metrics/daya/<ts>.csv`) atau mandiri dari baterai (menu Ukur daya
  / serial `V`, lalu `make pull-daya`; prosedur di `firmware/README.md` bagian
  Ukur daya tanpa laptop). INA219 sudah di jalur baterai (tangga 14 Okt 2026
  terbaca 3,69 V, ±137–154 mA tanpa WiFi; baterai bertahan hampir 1 jam).
  **Terhalang catu:** `p5` butuh WiFi ON, yang menunggu konverter 5 V (butir
  WiFi OFF di bawah). Setelah itu jalankan tangga tanpa charger, lalu isi
  `PLACEHOLDER-DATA daya` di bab4 buku-pa.
- **(14 Okt 2026) WiFi board sengaja OFF — keadaan darurat, kembalikan ke ON.**
  Keluaran konverter baterai 4,x V membuat board reset tiap ±2,5 s saat
  `WiFi.begin()`, jadi NVS board disetel **Jaringan → WiFi aktif OFF** (serial
  `m`) agar perekaman sinyal tubuh dari baterai tetap jalan. Keadaan normal
  sistem adalah WiFi ON; OFF hanya sampai catu diperbaiki. Uji WiFi/MQTT dan
  `p5` sementara dijalankan sambil dicolok USB. Penutupan, setelah user
  menyetel keluaran konverter ke 5,0–5,1 V:
  1. Nyalakan WiFi: menu **Jaringan → WiFi aktif → ON** atau serial `m`
     (baris `wifi ON (tersimpan)`).
  2. Nyalakan dari baterai tanpa USB: layar menyala, bip kalibrasi utuh sekali,
     tidak ada reset berulang. Lalu colok USB dan cek `s`: RSSI ≠ 0.
  3. Ulangi tangga daya **tanpa charger TP4056**, laptop di SSID yang sama
     dengan board dan ThingsBoard menyala, lalu `make pull-daya`. Tangga
     `/daya/003.csv` (14 Okt, tanpa WiFi, dugaan charger tercolok mulai
     +326 s) tidak dipakai untuk laporan.
  4. Hapus butir ini dan kalimat "Selama keluaran konverter belum disetel"
     di `firmware/README.md` bagian Hal yang perlu dicek pada rakitan.
- **(14 Okt 2026) Rencana, dikerjakan sesudah WiFi ON kembali: rekaman langsung
  ke server.** Rekaman panjang sekarang dipecah per 5 menit di LittleFS
  (3.456 KB, ±6 berkas, harus ditarik lewat USB). Arah yang diminta user:
  saat WiFi tersedia, sampel mentah dialirkan ke server di laptop sehingga
  durasi rekam tidak dibatasi LittleFS. Rencana awal (MQTT ke ThingsBoard
  untuk hasil klasifikasi per detak) tetap berjalan; aliran mentah adalah
  tambahan. Hal yang perlu dirancang bersama user sebelum mulai: protokol
  (topik MQTT terpisah atau HTTP), penerima di laptop yang menulis CSV dengan
  format `/rekam/NNN.csv` agar `make analisis` tetap dipakai, perilaku saat
  koneksi putus (fallback ke LittleFS), dan beban WiFi terhadap catu baterai
  (bergantung pada butir WiFi OFF di atas).

## Walkthrough per fase

Walkthrough = dokumen belajar, bukan spesifikasi (spesifikasi = PRD). Isinya
alur kode langkah demi langkah, matematika di baliknya, alasan tiap keputusan,
angka nyata, dan soal cek pemahaman.

- **Tulis begitu fase selesai, jangan tunda.** Alasan yang tidak dicatat saat
  masih hangat akan hilang, dan Bab 4 laporan mengambil bahannya dari sini.
- **Daftar dokumen + urutan baca: [`docs/README.md`](docs/README.md).** Walkthrough
  baru wajib didaftarkan di sana.
- **Kerangka tetap** (jangan bikin format baru tiap fase): peta besar (diagram
  alur) → fungsi per fungsi dengan kode + rumus → keputusan beserta alternatif
  yang ditolak → yang sengaja TIDAK dilakukan → angka nyata → cek pemahaman →
  skrip pendukung.
- Dokumen yang dijalankan (rekam, flash, kalibrasi) memakai prosedur standar:
  langkah bernomor, perintah di blok kode, hasil yang diharapkan.

## Decision point yang sudah di-lock

Tabel ini = LAMPIRAN B PRD versi hidup. Isi begitu ketok palu, jangan tunda.

| Keputusan | Nilai | Alasan singkat |
|---|---|---|
| Klasifikasi | biner (Normal/Aritmia) | inter-patient bikin F & Q recall ~0 |
| Split | inter-patient de Chazal | intra-patient = akurasi palsu |
| Filter | kausal `sosfilt` | `filtfilt` mustahil di MCU |
| Segmentasi | R-peak anotasi | jaga jalur model murni dari error detektor |
| Normalisasi | z-score per window | kebal beda amplitudo, nol kebocoran statistik |
| Pooling | GlobalAveragePooling1D | param jauh lebih kecil dari Flatten |
| Ukuran window | **128/128 = 256 sampel** | ablasi 3 seed (Fase 6c) terhadap baseline 90/160 = 250 sampel: F1 DS2 0,5660 → 0,6911. Mekanismenya terlihat per simbol: **recall S naik monoton dengan `WIN_PRE`** (90→0,268, 112→0,369, 128→0,42-0,49) karena beat supraventrikular dibedakan gelombang P & interval PR di sisi kiri window; recall V tak bergerak; **recall F turun** 0,308→0,15-0,20 (cakupan T dipangkas 160→128) — pertukaran yang disengaja, S 10× lebih banyak dari F di DS2. Varian PENENTU justru yang kalah: 112/144 juga 256 sampel, juga kelipatan 8, cakupan T lebih panjang → setara baseline. Jadi yang membayar **konteks 128 sampel sebelum R**, bukan panjang window. R di indeks **132** (128+4) |
| Augmentasi jitter | **`empiris` × 2 salinan di DS1**, DS2 tidak pernah dijitter | F1 DS2 0,5660 → 0,6354 bahkan pada data BERSIH — jitter bekerja sebagai regularisasi, bukan cuma latihan kondisi deploy. `--salinan 3` lebih buruk (0,6099), jadi 2 |
| Threshold | **0,80** | kriteria: F1 maksimum di VAL, tie-break recall bila ΔF1 < 0,005. VAL ikut ber-jitter, jadi sebaran probabilitas dan titik operasinya berbeda dari model tanpa augmentasi. Kandidat {0,80; 0,85} → recall menang → 0,80. Threshold 0,35 (titik operasi model tanpa augmentasi) memberi precision 0,19 di model ini. Reproduksi: `scripts/calibrate_threshold.py` |
| Agregasi metrik Fase 6 | **level beat** (per-record disimpan terpisah) | standar & sebanding literatur (PRD); `fase6_per_record_fp32.csv` untuk cerita sebarannya |
| `sklearn.metrics` | **tidak dipakai** — numpy | rumus TP/FN/FP/TN + AUC Mann-Whitney beberapa baris; sekalian memaksa memutuskan pembagian-nol → 0,0 bukan NaN (NaN akan merusak tabel delta Fase 7) |
| Orde Butterworth | **4** (2 biquad) | roll-off tajam; std cuma turun 5% = morfologi utuh |
| Beat tanpa `dRR` | **buang** (beat 0 & 1 tiap record) | `dRR=0` nilai SAH (ritme stabil) — sentinel bentrok data asli; biaya 88 dari ~100k beat |
| Alignment window↔label | **`prep_beats` yang menyaring** (opsi C) | semua kebijakan buang-beat di satu file; `src/` tetap murni utk port ke C |
| Jendela `RR_local_avg` | **kausal, menyusut di tepi** (10 RR terakhir, termasuk RR_prev beat ini) | simetris butuh beat masa depan → firmware harus tunda 5 beat; kausal konsisten dgn `sosfilt` Fase 1 |
| Sentinel beat tepi di `features_rr` | **NaN**, bukan 0 | senada baris `dRR`; `prep_beats` buang lewat indeks, sentinel tak pernah sampai model |
| Simbol di luar `AAMI_MAP` | **`KeyError`** (tidak di-default ke Q) | whitelist `BEAT_SYMBOLS` sudah saring di hulu; simbol asing = bocor, harus berisik |
| Record dibuang | `PACED_EXCLUDED` di `config.py` | 102/104 teknis (tanpa MLII), 107/217 metodologis (paced) |
| Strategi imbalance | **`class_weight` balanced**, dihitung sendiri: `w_c = N/(2·n_c)` → Normal 0,556 / Aritmia 4,947 | tidak menyentuh data & tidak menggandakan beat pasien yang sama (oversampling = model hafal individu, lawan semangat inter-patient); PRD melarang dipakai bareng oversampling |
| `pyserial` | **dipakai** (disetujui) — di `requirements.txt` | menarik rekaman dari board lewat serial; tidak ada padanan stdlib, dan semua alat jadi satu venv |
| `sklearn` untuk class weight | **tidak dipakai** — 3 baris numpy | rumus `balanced` cuma `N/(2·n_c)`; gate point CLAUDE.md: jangan tambah dependency (apalagi sebesar sklearn) untuk yang beberapa baris sudah selesai |
| Monitor EarlyStopping | **`val_auc`** (mode max, patience 8, `restore_best_weights`) | `val_recall` bisa dicurangi (tebak Aritmia semua → recall 1,0); `val_loss` sudah terdistorsi `class_weight` jadi tak lagi bisa ditafsir; AUC bebas threshold & tak bisa dipalsukan satu kelas |
| Metrik yang dipantau | **recall, precision, AUC** — accuracy TIDAK | accuracy 89,9% bisa dicapai dengan menebak Normal terus; menampilkannya cuma mengundang salah baca |
| Learning rate | **default adam (1e-3)** — diablasi, tetap | Dengan 1e-3 `val_auc` memuncak di epoch 0 lalu turun monoton — model produksi adalah hasil SATU epoch, 8 epoch sisanya terbuang. Diablasi 3 LR × 3 seed + 39 pasien held-out: 1e-4 menaikkan AUC di 4/4 set evaluasi, TEST-C F1 +0,124, recall F dua kali lipat (0,180→0,359), recall V naik — **tapi recall S turun 0,4473→0,3126**. 3e-4 lebih buruk lagi di S (0,2024), jadi tidak ada titik manis di tengah. Defisit S diverifikasi NYATA di titik operasi setara (6/6 titik, `scripts/cek_titik_operasi.py`) — bukan artefak threshold. Dipertahankan karena **S adalah fokus penelitian ini** dan ongkos pindah (regen `model_int8.h`+`golden_ref.h`, validasi ulang board) besar. Pertukaran ini DILAPORKAN, bukan disembunyikan. Knob `ablasi.py --lr` ditinggal. Detail: `docs/arsip/2026-09-19-faseG-changelog.md` |
| Dropout Dense 16 | **0.0 (tanpa dropout)** — diablasi | val recall: 0.0→**0,700**, 0.2→0,274, 0.3→0,359, 0.5→0,651 (AUC nyaris sama semua). Dropout cuma bikin model makin konservatif — precision naik, recall turun, padahal recall yang kurang. Overfit di sini akar masalahnya variasi antar-pasien, bukan model kegedean |
| Tipe I/O INT8 | **int8 in / int8 out** (`INT8_IO=True`) | full-INT8 end-to-end: nol kernel float, tensor arena terkecil. Firmware yang mengubah float↔int8 pakai scale/zero_point dari `model_int8.h` (jangan hardcode) |
| Sampel kalibrasi PTQ | **300, stratified dari DS1**, seed dikunci | PRD 100-500; 300 → 30 beat Aritmia, cukup mencakup ekor distribusi, konversi tetap detikan. Stratified supaya JEBAKAN #4 (kelas minoritas tak terkalibrasi) mustahil terjadi |
| QAT | **tidak dipakai** | PTQ sudah lolos target (|delta recall| 1,08% < 2%, 22,94 KB < 25 KB); QAT = latih ulang + sumber variasi baru untuk keuntungan yang belum tentu ada |
| Validation set | **DS1 record 101, 114, 201, 220, 223** (`VAL_RECORDS`; 10.349 beat per salinan = 20,3% DS1, aritmia 10,11% ≈ rasio DS1, S=310 V=714) | val jadi simulasi jujur "pasien baru" → angkanya layak dipakai pilih epoch & kalibrasi threshold; DS2 tetap haram sampai Fase 6 |
| Rec 208 wajib di train | **ya** — jangan pernah masuk val/exclude | 372 dari 414 beat kelas F di DS1 ada di record ini; tanpa dia kelas F nyaris hilang dari training |
| Model yang dikuantisasi | **varian deploy** (`build_deploy_model`), bukan model latih | TFLM menghitung op `MEAN` beda dari TFLite: PC 0,973 vs device 0,336, tanpa error. Bobot disalin apa adanya (identik 1,19e-07), nol latih ulang |
| Pengganti GlobalAveragePooling | **`DepthwiseConv1D(31)` bobot 1/31**, bukan `AveragePooling1D` | op pooling MEWARISI skala kuantisasi input (0,332); rata-rata 31 nilai jauh lebih kecil → ~3 bit resolusi hilang, recall DS2 0,655→0,528. Op konvolusi dapat skala output sendiri (0,0429, sama dgn `MEAN`) |
| `Flatten`/`Reshape` di model deploy | **dihindari** — kepala klasifikasi tetap 3-D, `Dense`→`Conv1D` kernel 1 | keduanya memunculkan `SHAPE`/`PACK`/`STRIDED_SLICE` (shape dinamis); TFLM tak punya alokasi dinamis → device memberi 0,418 vs 0,945 |
| Batas ukuran model | **25 KB** (PRD: 20 KB) | varian deploy yang benar memakan 22,94 KB; flash ESP32-S3 16 MB, batas ini soal disiplin bukan kapasitas. Disetujui eksplisit |
| Database LATIH | **mitdb saja** (`DB_LATIH` = mitdb+svdb dipakai HANYA di ablasi) | Fase D, tabel 2×2 3-6 seed: svdb menurunkan F1 -0,065 (pergeseran domain), fitur baru menambalnya +0,070, gabungannya +0,005 = bukan sinyal. incartdb lebih buruk lagi (AUC 0,8881 vs 0,9373; recall S 0,331 vs 0,498 untuk svdb, rentang TERPISAH). svdb & incartdb held-out TETAP dipakai sebagai TEST-B/TEST-C antar-database — 85.812 beat, 39 pasien. Detail: `docs/arsip/2026-09-19-faseB-changelog.md` §9 |
| Syarat database tambahan | **anotasi beat-level, alfabet WFDB** (svdb, incartdb) | `AAMI_MAP` menanganinya apa adanya. PTB-XL/CPSC/Chapman ditolak: diagnosis per-rekaman, label per-beat tak bisa diturunkan. DS2 mitdb tidak berubah satu byte. Detail: `docs/dataset-walkthrough.md` §4 |
| Laju cuplik database tambahan | **resample ke 360 Hz** (`resample_poly`), bukan mitdb diturunkan | `WIN_PRE` dalam sampel; 128 sampel @128 Hz = 1.000 ms, bukan 355 ms yang diablasi. Arah ke 360 menjaga bandpass, `ECG_FS`, dan golden tetap |
| `selaraskan` per database | **svdb & incartdb `True`, mitdb `False`** | anotasi svdb ~6 sampel lebih awal (median +10 vs +3), sistematis, di atas ambang bahaya 4 sampel. mitdb acuan golden & ablasi terkunci: menyelaraskannya menggeser R ~1 sampel |
| `ALIGN_WIN` | **16** (±44 ms) | menutup p1..p99 svdb (−9..+15) tanpa menjangkau gelombang T (72-108 sampel); `PT_REFINE_WIN` 25 untuk sebaran detektor, terlalu lebar di sini |
| Held-out database tambahan | **`sorted(records)[::4]`** (`SPLIT_SETIAP_KE = 4`), bukan seed | aturan tak bisa dipancing & bisa diverifikasi siapa pun. F held-out incartdb cuma ~13-20 beat (disengaja) → dilaporkan sebagai hitungan TP/FN mentah |
| `n_record` per database | **wajib cocok**, `build_split_multi` menolak bila tidak | aturan `[::4]` atas daftar tak lengkap memberi split berbeda tanpa suara (65/75 incartdb: I68 salah masuk, I65/I69/I73 hilang) |
| Presisi minimum nama (tahap 2) | **`MIN_PRESISI_NAMA = 0,90`**, bukan F1 | F1 memberi hadiah "namai semuanya V" (presisi 37,9%). Alat boleh diam, tidak boleh salah 6 dari 10. Detail: `docs/evaluate-walkthrough.md` §5 Tahap 2 |
| Bentuk fitur ritme | **3 kolom** (RR_prev, RR_ratio, dRR) — QRSw & rasio RR ada tapi OFF | `PA_QRSW=1` / `PA_RR_RATIO=1` menyalakannya. Di mitdb saja: F1 0,6911 → 0,6882 (bukan sinyal) dan harganya recall V 0,944 → 0,898, recall F 0,152 → 0,029. Hanya menang saat menambal kerusakan svdb. Kode C-nya sudah ada di balik `#if ECG_RR_RATIO`/`ECG_QRSW`, terkompilasi & terbukti tidak mengganggu (17/17) |
| `RR+1` / tunda 1 beat (G2) | **TIDAK dipakai** — tapi sudah diimplementasikan | Karena `PA_RR_RATIO` tidak dikunci, firmware tidak menunda beat. Kalau nanti diaktifkan: `ecg_live.cpp` menilai `idx_hist-1`, buffer TIDAK berubah (r_hist[16] sudah memuat RR+1, ring 4 detik cukup), plus `ECG_LIVE_TIMEOUT` 3 detik untuk asistol dengan sentinel rasio 1,0 |
| `MAX_RHYTHM_SCALE` | **0,05** — assert di `quantize_int8` | Skala INT8 tensor ritme diturunkan dari min/max 300 sampel kalibrasi. Satu beat ber-RR ekstrem di sana (record 207: RR_prev = 100 s) melebarkan skala ~30x dan RR normal tinggal beberapa level → cabang ritme MATI, dan gejalanya "recall S buruk", bukan error. Peluang 1,8%/seed. Nilai sehat 0,0129. Diuji dua arah |
| Strategi imbalance (K1 diuji) | **`class_weight` balanced TETAP** | P1 Tabel 4 memprediksi precision +31 poin kalau dimatikan; terukur **+0,3 poin**. Sebabnya kalibrasi threshold di HILIR menyerap efeknya (threshold 0,40 → 0,15). Pelajaran: ablasi paper yang sah pun tak transfer kalau ada langkah adaptif yang mereka tidak punya. G1 DITUTUP atas dasar ablasi sendiri |
| Tahap 2 (penamaan V/S) | **TIDAK dikirim** | Aturan lebar QRS mencapai presisi nama V 91,7% di DS2, tapi VAL maksimum cuma 43,9% — 5 pasien tidak mewakili keragaman morfologi V. §7 no.4 melarang DS2 mensertifikasi. `scripts/tahap2.py` menegakkannya sendiri: tanpa ambang yang lolos, tidak ada nama ditampilkan |
| Library TFLM | **`spaziochirale/Chirale_TensorFLowLite`** 2.0.0 | rilis terbaru di registry PlatformIO, jalan dgn framework Arduino. Kernel referensi (belum ESP-NN) → 26 ms/detak jadi baseline; pindah `esp-tflite-micro` kalau daya jadi kendala |
| Board PlatformIO | **`4d_systems_esp32s3_gen4_r8n16`** | bukan tebakan — id dari projek uji yang sudah pernah ter-flash & jalan di hardware ini |
| Segmentasi on-device | **kompensasi 38 + penyelarasan puncak ±25 + kurangi group delay 4** | tanpa salah satunya R tidak mendarat di `WIN_PRE+4` (= **132**) dan precision jatuh 4× (0,479→0,124); offset dikalibrasi di DS1 |
| Model jitter | **empiris** (ambil ulang dari `residu_ds1.npy`), bukan seragam ±18 paper | residu terukur inti-tajam-ekor-berat; seragam ±18 menggeser 80% beat yang sebetulnya terkunci. `seragam` tetap ada supaya sweep δ=0..18 sebanding Tabel 3 Dias 2021 |
| Jitter per beat | **independen**, walau kenyataannya berkorelasi per record | korelasi sebagian saling meniadakan di RR (RR = selisih dua posisi); independen melebihkan ragam RR = arah pesimistis, aman |
| Salinan bersih saat augmentasi | **selalu ikut** (`--salinan N` = N tiruan DI ATAS 1 salinan bersih) | 80% beat di alat meleset ≤1 sampel; kasus "tepat" itu mayoritas, bukan kasus pinggir |
| Knob ablasi | **environment** (`PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS`), bukan edit nilai final | tanpa env, `config.py` memberi nilai yang persis sama → ablasi tidak menyentuh gate point. Yang menang baru dikunci lewat bawaannya (tetap gate point) |
| Fitur HOS (kurtosis+skewness) | **ditolak** | 3 seed: 0,6150±0,0509 vs 0,6354±0,0428 tanpa HOS — tumpang tindih penuh. Bukan "merusak", tapi "tidak ada bukti menolong"; fitur tanpa bukti tetap harus diport ke C & dijaga. Kode + knob `PA_HOS` ditinggal untuk ablasi ulang |
| Record kanal anomali | 114 (MLII idx 1); 102 & 104 tanpa MLII → `raise` | 102/104 paced, dibuang di Fase 3 juga |
| Filter non-beat | whitelist `BEAT_SYMBOLS` di `config.py` | simbol tak dikenal ikut kebuang, bukan lolos |

## Jebakan yang sudah ketemu

- **`wfdb.io.annotation.is_qrs` tidak bisa dipakai buat filter non-beat.**
  Gejala: `[`, `]`, `x`, `)` lolos sebagai "beat". Sebab: tabel wfdb menandai
  penanda awal/akhir ventricular flutter & non-conducted P-wave sebagai QRS.
  Hindari: whitelist eksplisit `config.BEAT_SYMBOLS` (15 simbol AAMI).
- **Menyamakan PANJANG array ≠ menyejajarkan beat.** Gejala: tidak ada.
  `assert len(windows)==len(labels)` LOLOS, loss turun mulus, baru ketahuan di
  Fase 6 saat recall ~0. Sebab: `segment_beats` buang beat tepi (rec 100: beat
  0 & 2272), `compute_rr_features` buang beat tanpa RR_prev (beat 0) — himpunan
  beda, panjang bisa kebetulan sama. Rec 100 disimulasikan: 100% baris tergeser
  1 beat, 68 label salah simbol padahal aritmia asli cuma 34 (tiap 1 aritmia
  merusak 2 baris). Hindari: `prep_beats` hitung `valid_beat_indices` DULU,
  semua array diambil dari indeks yang sama. RR dihitung dari `r` UTUH baru
  di-slice — potong `r` duluan bikin beat tepi kehilangan tetangga.
- **Group delay filter kausal menggeser R-peak +4 sampel.** Gejala: garis
  R-peak anotasi meleset ~11 ms di kiri puncak pada window HASIL FILTER
  (`make plot1seg`). Sebab: `sosfilt` cuma lihat masa lalu → output tertinggal.
  **Bukan bug, jangan dikoreksi.** Geserannya konsisten (window 90/160: median 94, mean 94,03),
  jadi model belajar posisi itu dan firmware menghasilkan hal sama selama
  koefisien SOS identik. Mengoreksi di Python tanpa koreksi di C = mismatch.
- **TFLite Micro menghitung op `MEAN` beda dari TFLite biasa.** Gejala: model,
  bobot, input, dan parameter kuantisasi identik, tapi PC 0,9727 vs device
  0,3359 — semua probabilitas tertekan ke tengah, **tanpa error apa pun**.
  Sebab: `GlobalAveragePooling1D` → op `MEAN`; dua library TFLM berbeda memberi
  angka salah yang IDENTIK, jadi ini sifat TFLM, bukan bug library. Hindari:
  `build_deploy_model` menukar ke `DepthwiseConv1D` berbobot 1/31 (rata-rata yang
  sama, op konvolusi). Ketahuan cuma karena ada golden reference PC↔device.
- **Op pooling mewarisi skala kuantisasi input; op konvolusi punya skala sendiri.**
  Gejala: `AveragePooling1D` cocok di 6 beat uji golden, tapi recall DS2 jatuh
  0,655 → 0,528. Sebab: skala input 0,332 dipakai juga untuk output, padahal
  rata-rata 31 nilai jauh lebih kecil → ~3 bit resolusi terbuang. Hindari: pakai
  op konvolusi untuk rata-rata. Pelajaran umum: **cocok di segelintir sampel uji
  ≠ benar**; verifikasi ukuran-penuh tetap perlu.
- **Serial monitor merebut `/dev/ttyACM0`.** Gejala: `esptool` gagal dengan
  `Errno 11: Could not exclusively lock port` — pesannya tidak pernah menyebut
  "monitor". Sebab: tombol *Upload and Monitor* VS Code masih hidup. Hindari:
  `lsof /dev/ttyACM0` untuk menemukan PID-nya.
- **Model runtuh kalau R-peak meleset 4 sampel (11 ms).** Gejala (window 90/160): precision
  0,479 → 0,124, simetris ke dua arah (R di indeks 90 atau 98, bukan 94).
  Sebab: tiga `MaxPooling1D(2)` = stride total 8, jadi geseran 4 sampel itu
  SETENGAH bin pooling — fase representasi yang masuk GAP berubah. Model tak
  pernah melihat variasi ini karena training memakai anotasi yang presisi.
  Hindari: firmware wajib menaruh R di indeks `ECG_WIN_PRE + ECG_GROUP_DELAY`
  (**132** untuk window 128/128 — jangan hafal angkanya, `test_preproc.cpp`
  memakai rumusnya). Ketahanan terhadap geseran kecil dilatih lewat augmentasi
  jitter (Fase 6c).
- **Refraktori 200 ms Pan-Tompkins memblokir beat prematur.** Gejala:
  sensitivity detektor kelas S cuma 0,6494 vs Normal 0,9614. Sebab: beat
  supraventrikular datang terlalu cepat setelah detak sebelumnya, tepat di
  jendela refraktori. Efeknya berlipat dengan recall klasifikasi S yang sudah
  0,3034. Trade-off menurunkan refraktori bisa diukur dgn
  `scripts/eval_detected_segmentation.py`.
- **Beban alur hidup bursty, bukan merata.** Gejala: rata-rata cuma 82 us/sampel
  (3% anggaran) tapi satu sampel bisa memakan 33,4 ms — 12x anggaran. Sebab:
  deteksi berjalan sekaligus atas ring 4 detik, dan kebetulan bersamaan dengan
  inferensi beat yang baru ditemukan. Hindari: akuisisi ADC di timer ISR menaruh
  ke antrean (min 13 sampel), pemrosesan menguras di loop utama. Kalau berurutan
  di satu alur, ~12 sampel hilang tiap detik dan interval RR rusak.
- **`.venv` tidak kepakai walau ada.** Gejala: `make plot1` →
  `ModuleNotFoundError: No module named 'numpy'`. Sebab: `PY := python` ambil
  pyenv shim, bukan `.venv/bin/python`. Hindari: `PY` di Makefile memilih
  `.venv/bin/python` otomatis kalau ada (tak perlu `source activate`).
- **Telemetri akuisisi bisa berbohong — tiga cara.** (1) **`lepas 0%` dari LO AD8232
  BUKAN jaminan ada sinyal** — LO cuma butuh satu jalur impedansi rendah, dan
  elektroda RL sendirian sudah memuaskannya; enam rekaman kosong semuanya
  melapor `lepas 0%`. (2) **Nama file `make pull` = waktu TARIK, bukan waktu
  rekam** (`pull_recording.py:77` pakai `datetime.now()`) — rekaman basi
  terlihat baru kalau lupa menekan REC. (3) **Ohmmeter di rangkaian bertegangan
  memberi angka salah tanpa tanda apa pun** — RA–LA terbaca ~0 Ohm (disimpulkan
  korslet), diulang dengan daya mati jadi ribuan ohm. Hindari: jadikan **ayunan
  ADC absolut** wasitnya, bukan flag. Konversi: 12-bit + atten 11 dB =
  0,757 mV/count, gain AD8232 ~1100 → EKG sehat ~2 mV (~3000 counts);
  **di bawah ~0,1 mV (~150 counts) berarti tidak ada biopotensial sama sekali**,
  dan itu bukan masalah penempatan lead (penempatan buruk memangkas 3–5x,
  bukan 50x).
- **Seed dikunci, hasil tetap berubah.** Gejala: `np.random.seed(42)` +
  `tf.random.set_seed(42)`, kode identik, dijalankan dua kali → F1 DS2 0,6209 vs
  0,5882 (varian jitter). Sebab: penjadwalan thread oneDNN di CPU mengubah urutan
  penjumlahan float; selisih kecil itu memilih epoch berhenti yang berbeda lewat
  EarlyStopping, dan `restore_best_weights` mengembalikan bobot yang lain.
  Hindari: **jangan pernah menyimpulkan ablasi dari satu run.** Minimal 3, lapor
  rerata ± rentang. Di repo ini selisih < ~0,04 F1 bukan sinyal.
- **Melatih dengan data yang "dirusak" menaikkan angka di data BERSIH.** Gejala
  (yang menyenangkan): augmentasi jitter menaikkan F1 DS2 anotasi 0,5660 →
  0,6354, padahal DS2 anotasi tidak punya jitter sama sekali. Sebab: model lama
  bergantung pada fase window yang persis (tiga `MaxPooling1D(2)`, stride 8);
  jitter memaksanya belajar bentuk yang tak bergantung fase — regularisasi, sama
  seperti random crop di penglihatan komputer. Pelajaran: augmentasi yang meniru
  error deploy bukan cuma "menyiapkan kondisi buruk", ia memperbaiki modelnya.
- **Penalaran fisiologis yang masuk akal bisa salah, dan ablasi yang benar
  membuktikannya.** Gejala: argumen "`WIN_PRE=90` sudah memuat gelombang P
  (interval PR 43-72 sampel), jadi 128 milik paper cuma membeli garis dasar"
  terdengar kuat — dan kalah. `w128` (128/127) F1 0,6775 vs 0,5660 baseline.
  Kunci pembuktiannya varian ketiga: `w112` (112/144) punya panjang 256 yang
  SAMA, habis dibagi 8, cakupan T lebih panjang — hasilnya setara baseline. Jadi
  yang membayar bukan panjang window, bukan kelipatan 8, tapi **konteks pre-R**.
  Hindari: setiap klaim "X sudah cukup" butuh varian pembanding yang mengisolasi
  X, bukan sekadar varian yang lebih besar.
- **Float di dalam ISR membunuh ESP32 — pelan-pelan, bukan seketika.** Gejala:
  `Guru Meditation Error: Core 1 panic'ed (Coprocessor exception)`, `EXCCAUSE
  0x00000004`, lalu reboot. Muncul di **detik 18**, bukan detik 0, jadi lolos
  uji 20 detik dan lolos build. Sebab: ESP32 tidak menyimpan register FPU saat
  masuk ISR; operasi float di sana merusak state FPU task yang diinterupsi, dan
  panic baru meledak saat task itu dijadwalkan lagi. Hindari: konversi di
  `setup()` ke tabel integer, ISR cuma menyalin (`sim_counts[]` di `main.cpp`).
  **Gejala turunannya lebih menipu dari crash-nya**: board reboot diam-diam →
  `replay` kembali `false` → pengukuran berikutnya melaporkan angka yang masuk
  akal (2 beat/detik) tapi dari objek yang salah (derau ADC, bukan replay).
- **Cara membuka port serial menentukan apakah board reset.** Gejala: board
  boot ulang (`=== MONITOR ARITMIA SIAP ===`) begitu skrip membuka port, toggle
  yang "sudah ditekan" hilang, dan **sesi rekam yang sedang berjalan hilang
  seluruhnya** (disangga di PSRAM sampai berhenti). Terukur 22 Okt 2026 di
  `/dev/ttyACM0` (USB-Serial-JTAG ESP32-S3): pola `s.dtr = s.rts = False`
  sebelum `s.open()` me-reset board 5 dari 5 kali, termasuk sesi rekam
  `rekam=1 n=1803` yang hilang; `serial.Serial(port, baud)` bawaan tanpa
  menyentuh DTR/RTS tidak me-reset 3 dari 3 kali dan sesi rekam bertahan
  (n 1.450 → 3.461 antar dua pembukaan). `make pull` memakai pola bawaan, jadi
  aman. Pola DTR/RTS False dipakai hanya bila boot bersih memang diinginkan
  (`measure_power.py` menunggu `MONITOR ARITMIA SIAP`; `pull_daya.py` dan
  `uji_alur_rekam.py` menunggu board menjawab). Setelah membuka port,
  **verifikasi state** dari balasan board (`replay ON`, `rekam=1`, ayunan di
  `s`), jangan diasumsikan.
- **Tanpa elektroda, alat mengarang aritmia: ~2 beat/detik, 57% "ARITMIA".**
  Sebab: ambang Pan-Tompkins adaptif relatif terhadap sinyal yang ada, jadi
  "tidak ada sinyal" bukan kondisi yang ia kenali — derau 15 counts pun punya
  puncak. Konsekuensi untuk HW-6: **publikasi MQTT wajib digerbangi penilai
  kualitas sinyal (`AMBANG_AYUN`), bukan oleh ada-tidaknya beat.** Kalau tidak,
  elektroda lepas = banjir alarm palsu ke broker.
- **"Epoch" menyesatkan sebagai satuan lama latih — model produksi adalah
  hasil SATU epoch.** Gejala: tidak ada. Training selesai normal, metrik wajar,
  nol error. Ketahuan cuma karena kurva `val_auc` dicetak saat mendiagnosis hal
  lain (Fase G/T7). Sebab: DS1 teraugmentasi 121.857 beat ÷ `BATCH_SIZE` 64 =
  **1.905 langkah gradien per epoch**; untuk 6.417 param dengan Adam 1e-3, satu
  epoch sudah cukup menghafal. `val_auc` memuncak di **epoch 0** lalu turun
  monoton, `patience=8` melatih 8 epoch yang seluruhnya dibuang. Augmentasi ×3
  di Fase 6c melipatgandakan langkah/epoch dan **tak ada yang meninjau ulang
  jadwal latihnya**. Hindari: setiap kali ukuran data latih berubah, cetak
  kurva `val_auc` sekali dan lihat di mana puncaknya — jangan menilai lama latih
  dari jumlah epoch. Detail: `docs/arsip/2026-09-19-faseG-changelog.md` §2.
- **Ambang 0,04 berlaku untuk RERATA 3 SEED, bukan cuma satu run.** Gejala:
  konfigurasi identik, seed identik, dijalankan dua kali pada hari yang sama →
  F1 DS2 0,6911 vs 0,6535 (selisih 0,0376). Sebab: sama dengan jebakan oneDNN
  di atas, tapi tidak hilang hanya karena dirata-rata 3 seed. Konsekuensi:
  mengulang 3 seed **tidak** mengangkat selisih kecil jadi sinyal; yang
  menaikkan daya pisah adalah set uji lebih besar (`ablasi.py --lintas-db`,
  39 pasien held-out). Sebagian vonis "bukan sinyal" Fase A–F jadi lebih lemah,
  bukan lebih kuat.
- **Menunggu jaringan di dalam loop yang menguras antrean ADC = sampel hilang.**
  Gejala: `antrean 255/256`, `sampel hilang 4493`, `PUBACK timeout` berulang.
  Sebab: antrean 256 sampel @360 Hz cuma **711 ms** dalam, jadi panggilan
  blocking apa pun yang lebih lama dari itu mulai membuang sampel dan merusak
  interval RR — persis kegagalan yang arsitektur HW-4 (ADC di ISR) dibangun untuk
  mencegah. Tiga pelaku ditemukan berurutan: tunggu PUBACK 3 dtk (4.493 hilang),
  `sock.connect()` tanpa batas saat broker BOOTING (2.788), tunggu CONNACK 1,5 dtk
  (290). Hindari: semua tunggu jaringan dipungut **lintas iterasi** `loop()`
  (state machine), dan `sock.connect(ip, port, 300)` — pakai `IPAddress`, karena
  resolusi DNS adalah panggilan blocking TERPISAH yang tidak ikut dibatasi
  argumen timeout. Hasil akhir: **0**. Detail: `docs/mqtt-walkthrough.md` §7b.
- **`sock.write()` yang tidak habis bikin paket MQTT terpotong, dan gejalanya
  menunjuk ke broker.** Gejala: `PUBACK timeout` berulang padahal broker sehat,
  HANYA saat backlog dikuras, dan **log broker bersih** — nol petunjuk di sisi
  sana. Sebab: paket ditulis 6 kali terpisah dan nilai kembaliannya diabaikan;
  payload besar (16 beat ≈ 4,8 KB) tidak habis ditulis, broker menunggu sisa yang
  tidak pernah datang. Hindari: rakit SATU paket, SATU `write()`, dan periksa
  panjangnya. Pelajaran umum: pengirim yang tidak memeriksa berapa byte yang
  benar-benar terkirim akan menyalahkan penerima.
- **Angka RAM/Flash bisa berbohong kalau kredensial belum ada.** Gejala: build
  "SUCCESS" melapor RAM 26,4% / Flash 8,0%; dengan `wifi_secrets.h` terisi angka
  yang sama jadi **33,1% / 13,4%** — selisih 358 KB flash. Sebab: tanpa file itu
  `WIFI_SSID` adalah `""`, `strlen("")` dilipat jadi konstanta, `WiFi.begin()`
  jadi kode mati, dan seluruh tumpukan WiFi tidak ikut di-link. Bedanya tidak
  diumumkan di mana pun. Hindari: ukur ukuran build dalam konfigurasi yang
  SAMA dengan yang dipakai, dan sebut kondisinya saat mencatat angkanya.
- **Nagle menahan segmen kecil; PUBACK jadi terlambat 1–4,8 detik.** Gejala:
  `PUBACK timeout` acak walau broker sehat, latensi end-to-end berekor panjang
  (p95 13,3 dtk), dan RTT PUBACK yang **berulang di ~1.250 ms**. Sebab: payload
  satu beat ~330 B = segmen kecil, dan Nagle menahannya sampai ACK segmen
  sebelumnya datang; berpasangan dengan delayed-ACK broker jadi ~1,25 detik.
  Hindari: `sock.setNoDelay(true)` sesudah connect. Hasil: p95 13.259 → **3.402
  ms**, `gagal` 4 → **0**, PDSR 96,7 → 99,5%. Yang menemukannya bukan penalaran
  melainkan **pencacah RTT + mencetak `sock.available()` saat timeout** (0 byte =
  bukan desync, broker memang belum menjawab).
- **Paket MQTT yang tidak diminta harus tetap dibaca.** Gejala: sama dengan di
  atas, jadi dua bug bergejala identik hidup berdampingan dan memperbaiki yang
  satu tidak menghilangkan gejalanya. Sebab: PINGREQ dikirim tiap 30 dtk, PINGRESP
  (2 byte `0xD0 0x00`) tidak pernah dibaca, mengendap di socket, lalu terbaca
  sebagai dua byte pertama PUBACK berikutnya → aliran baca desync sampai
  reconnect. Hindari: baca header 2 byte dan **buang isi paket lain secara utuh**
  supaya byte berikutnya jatuh di batas paket. Pelajaran: kalau perbaikan yang
  benar tidak menghilangkan gejala, jangan menalar tersangka berikutnya — pasang
  pencacah sampai gejalanya punya angka.
- **`time()` beresolusi 1 detik, dan galatnya menyamar sebagai latensi.** Gejala:
  latensi end-to-end minimum bergeser 934/1.045/1.286/1.347 ms antar-boot tanpa
  ada yang berubah di sistem, lalu sekali melompat seragam ke 3.437 ms di SEMUA
  persentil. Sebab: `ts_base_ms` dihitung dari `time(NULL)` yang beresolusi detik,
  jadi pembulatannya masuk ke setiap `ts` yang dikirim — galat sistematis 0–1.000
  ms per boot, tetap sepanjang sesi. Hindari: `gettimeofday()`, dan alat ukur di
  sisi lain WAJIB mengukur selisih jam kedua sisi lalu mengoreksinya (board
  mencetak `epoch_ms` di baris status). **Tanda pembeda:** pergeseran yang seragam
  di semua persentil = selisih jam; latensi nyata menggeser ekor lebih banyak
  daripada median. Galat ini mudah dibaca sebagai
  latensi broker, padahal RTT broker yang diukur langsung hanya 1,1 ms median
  (`dashboard/probe_rtt.py`).
- **Menyalahkan komponen jauh sebelum mengukurnya.** Gejala: latensi p95 buruk,
  dan penjelasan paling masuk akal ("ThingsBoard berbagi laptop dengan 9 container")
  ditulis ke dokumen tanpa diuji. Sebab: komponen yang paling sulit diukur juga
  yang paling gampang disalahkan. Hindari: probe langsung — 40 baris Python
  publish 1/detik ke broker yang SAMA membuktikan RTT-nya 1,1 ms median, nol
  kejadian >1 detik, dalam 60 detik. Pola RTT board yang berkelompok di
  **1,2 / 2,0 / 4,2 detik** justru menunjuk backoff RTO TCP 1-2-4 = paket hilang
  di WiFi, dan RSSI −50 dBm menutup dugaan sinyal lemah.
- **`import config` gagal dari `scripts/`.** Gejala: `ModuleNotFoundError` walau
  dijalankan dari `model/`. Sebab: `python scripts/x.py` menaruh `scripts/` di
  `sys.path[0]`, bukan cwd. Hindari: shim 1 baris `sys.path.insert` (lihat
  `scripts/plot_fase0.py`); `conftest.py` sudah menangani sisi pytest.

## Kanal knowledge

Sesi Claude Code di folder ini **tidak** mewarisi riwayat sesi lain (riwayat
tersimpan per direktori kerja). File ini satu-satunya yang selalu termuat —
tulis keputusan ke sini, bukan cuma ke chat.
