# Crosscheck metrik Bab 4 terhadap standar dan literatur (1 Nov 2026)

**Status:** aktif, menunggu keputusan user (bagian 4). Aksi yang diambil dari sini dicatat di
[`2026-11-01-celah-target.md`](2026-11-01-celah-target.md) atau dokumen terkait.
**Pertanyaan:** apakah metrik dan cara ukur di `laporan/buku-pa/bab/bab4.tex`
(`tab:parameter-eksperimen`) sesuai standar baku dan praktik paper, dinilai dari
metode di teks lengkap, bukan dari abstrak.
**Cara:** lima riset paralel per kategori metrik, memakai Scopus, WebSearch, dan
unduhan teks lengkap. Laporan rinci per kategori, berisi tabel crosscheck, daftar
sumber dengan kutipan persis dan halaman, serta lima celah teratas, ada di folder
[`2026-11-01-crosscheck-metrik-bab4/`](2026-11-01-crosscheck-metrik-bab4/).
PDF dan teks unduhan (127 berkas, gitignored) ada di
`laporan/pustaka/belum-dirujuk/riset-pengukuran/{klasifikasi,tinyml,akuisisi,pipeline,daya}/`.

| Kategori Bab 4 | Laporan rinci | Sumber teks lengkap |
|---|---|---|
| a, b. Klasifikasi dan kuantisasi | [klasifikasi.md](2026-11-01-crosscheck-metrik-bab4/klasifikasi.md) | 16 |
| c, d. Kinerja di perangkat dan preprocessing | [tinyml.md](2026-11-01-crosscheck-metrik-bab4/tinyml.md) | 19 |
| e. Akuisisi sinyal tubuh | [akuisisi.md](2026-11-01-crosscheck-metrik-bab4/akuisisi.md) | 18 |
| f. Pipeline edge-to-cloud | [pipeline.md](2026-11-01-crosscheck-metrik-bab4/pipeline.md) | 18 |
| g. Konsumsi daya (rencana) | [daya.md](2026-11-01-crosscheck-metrik-bab4/daya.md) | 15 |

Teks standar berbayar tidak terbaca: ANSI/AAMI EC57 dan EC13, IEC 60601-2-25,
-2-27, -2-47, dan -1-11, serta Kligfield 2007. Isinya dikutip lewat implementasi
rujukan (PhysioNet `bxb`/`sumstats` untuk EC57) atau kutipan sekunder, dan
ditandai di laporan rinci.

## 1. Vonis per kategori

| Kategori | Sesuai standar/literatur | Beda, tetapi dapat dipertanggungjawabkan | Kurang |
|---|---|---|---|
| a. Klasifikasi | Split inter-patient de Chazal, rekaman pacemaker dibuang, Q dibuang, statistik gross, accuracy bukan acuan, threshold dari VAL per pasien, recall sistem dengan pencocokan ±150 ms (`tab:segmentasi-deteksi`) | Kelas biner (EC57 hanya mengenal VEB dan SVEB), 5 menit pertama tidak dibuang (konvensi paper inter-patient), median per pasien (EC57 "average" = rerata per rekaman) | PR-AUC dan MCC belum ada; +P detektor QRS tidak ditulis; rerata per rekaman belum ada |
| b. Kuantisasi | Ambang Δ relatif terhadap float32 sejalan dengan MLPerf Inference ("within 1% of FP32") | 0,02 adalah ambang rancangan sendiri; Zambrano 2026 memakai akurasi dengan split per detak (penulisnya mengakui kebocoran) | Δ per kelas S/V/F dan persentase label yang berubah tidak dilaporkan; Busia 2024 menunjukkan dampak INT8 terpusat di kelas S |
| c. Kinerja di perangkat | Ukuran model, `arena_used_bytes` (cara TFLM), pembanding 200 ms lebih ketat daripada literatur (Tran 2025: 400 ms) | RAM/Flash dari laporan build, bukan puncak runtime | Latensi dari 7 inferensi tanpa ulangan (MLPerf Tiny: ≥ 10 s dan ≥ 10 iterasi, 5 run, median); maks tidak dilaporkan walau sudah dicetak kode |
| d. Preprocessing real-time | Kesetaraan C–Python lebih ketat daripada semua paper ECG yang dibaca; kriteria "antrean < kapasitas" sesuai Liu & Layland (asumsi A2, buffering) | Angka 82 µs adalah utilisasi agregat (waktu sibuk / jumlah sampel) | Puncak 33,4 ms dari 6,67 s adalah *maximal observed*, bukan WCET (Wilhelm 2008); belum diukur dengan WiFi aktif dan pada window 256 |
| e. Akuisisi | Pita 0,5–40 Hz (CinC 2017 AliveCor, BITalino), definisi dengung 50 Hz identik PLIratio Gajdzik 2026, cek sampel jenuh, rentang RR 30–200 BPM | Ambang 15% dan 90% buatan sendiri (Rahman 2022: tidak ada ambang SQI baku); filter kausal non-linear phase sah untuk ritme, bukan ST | R-peak/HR tidak divalidasi terhadap acuan (EC13: ±10% atau ±5 bpm); autokorelasi > 0,25 tanpa rujukan; penilaian per rekaman, bukan per jendela 10 s; rentang dinamis ±1,3–1,5 mV terhadap ±5 mV IEC 60601-2-25 |
| f. Pipeline | PDSR = round-trip loss RFC 6673 §4.3 dengan Tmax 5 s; koreksi selisih jam lebih eksplisit daripada Adochiei 2025, Kim 2026, Silva 2021; target 2 s sejalan ITU-T G.1010 (Responsive ~2 s, Tabel I.2 preferred < 2 s, acceptable < 4 s) | Median sebagai statistik utama (RFC 6703 §5.2) | Rata-rata, SD, min, maks belum dilaporkan (RFC 6703 §3.1); ketidakpastian jam tidak dilaporkan (RFC 7679 §3.7, RFC 7680 §2.8.3 MUST); uji putus = `docker pause` sekali, jalur reconnect WiFi tidak teruji |
| g. Daya | Rata-rata per mode dari INA219 sah, karena ADC ΔΣ mengintegrasikan, bukan mencuplik titik (datasheet hlm. 11) | Sisi baterai memuat efisiensi konverter (MLPerf mengukur satu rel tetap) | Config `0x3FFF` mencuplik arus ±50% waktu; tanpa kalibrasi; satu kali tangga tanpa ulangan; energi per inferensi dan umur baterai belum direncanakan |

## 2. Yang sudah tertutup di buku

Empat butir dari laporan rinci sudah ditangani Bab 4 dan tidak perlu aksi:

1. **Klasifikasi end-to-end dengan detektor** (klasifikasi.md celah 1).
   `tab:segmentasi-deteksi` melaporkan recall sistem 0,6035 dengan R dari
   Pan-Tompkins dan pencocokan ±150 ms (`model/scripts/eval_detected_segmentation.py`,
   `src/evaluate.pair_detected`).
2. **DS2 dipakai untuk ablasi** (klasifikasi.md celah 2). Bab 4 menulisnya
   sebagai keterbatasan di paragraf himpunan data dan paragraf recall per pasien.
3. **Zhong 2022 sebagai pembanding latensi end-to-end** (pipeline.md butir 8).
   Bab 3 mengutip Zhong hanya untuk BER, dan anggaran latensi merujuk
   Skorin-Kapov 2010.
4. **Duplikat QoS 1** (pipeline.md butir 12). Bab 4 sudah menyatakan bahwa nol
   ts ganda tidak berarti duplikat tidak pernah tiba, dan mekanismenya diuji
   dengan smoke test penerbitan ulang.

+P detektor sudah dapat dihitung dari angka Bab 4: 47.074 / (47.074 + 2.194) =
0,9555.

## 3. Aksi, dikelompokkan menurut biaya

### A. Cukup ditulis (tanpa ukur ulang)

| # | Aksi | Dasar |
|---|---|---|
| A1 | Definisi latensi diseragamkan: dari R-peak (ts) sampai baris tersedia di REST API, render dashboard tidak termasuk; median dibenarkan dengan RFC 6703 §5.2 | Bab 3 `tab:pengujian-pipeline` menulis "pembaruan dashboard" dan "rata-rata" (sama dengan celah-target B4) |
| A2 | PDSR ditulis sebagai keberhasilan round-trip percobaan pertama (RFC 6673), Tmax 5 s, beserta CI Clopper–Pearson: gabungan 733/735 = 99,02–99,97%, ulangan terendah 97,20% | Dihitung ulang dengan `scipy.stats.beta`: 292/292 98,74–100, 253/255 97,20–99,90, 188/188 98,06–100 |
| A3 | Rujukan anggaran 2 s ditambah ITU-T G.1010 Gambar 2 dan Tabel I.2, serta ITU-T H.810 §6.1.7.5 (parameter terukur ~1 s, alarm ~10 s) | pipeline.md butir 8 |
| A4 | +P detektor QRS 0,9555 ditambahkan ke `tab:sensitivity-detektor`, dengan jendela 150 ms disebut | EC57 meminta QRS Se dan +P (`bxb -w 0.15`) |
| A5 | Satu kalimat protokol: seluruh rekaman dipakai (bukan learning period 5 menit EC57), Q dibuang 7 detak (Mondéjar 2019), metrik biner bukan VEB/SVEB EC57 | klasifikasi.md butir 1, 4, 5 |
| A6 | Ambang Δrecall 0,02 ditulis sebagai ambang rancangan; Zambrano dipakai hanya sebagai contoh besaran | klasifikasi.md butir 15 |
| A7 | Batas cakupan akuisisi: pita 0,5–40 Hz untuk ritme, bukan ST; gerbang ΔRR hanya fase kalibrasi; rentang dinamis ±1,3–1,5 mV sebagai batasan rancangan yang menjelaskan sampel jenuh di puncak R | akuisisi.md butir 1, 2, 8 |
| A8 | Bila validasi R-peak/HR tidak dikerjakan: hasil akuisisi ditulis sebagai status fungsional, bukan akurasi (preseden Torad 2026 §4) | akuisisi.md celah 1 |
| A9 | Latensi inferensi: angka maks dari 7 detak (sudah dicetak `test_inference`) dikutip, dan 9 `Invoke()` sebelum pengukuran disebut sebagai warm-up | tinyml.md bagian 0 |
| A10 | Uji putus koneksi ditulis sebagai kegagalan broker, bukan kegagalan tautan, bila uji WiFi putus tidak dikerjakan | pipeline.md butir 11 (sama dengan celah-target B1) |

### B. Hitung ulang dari data yang sudah ada

| # | Aksi | Data |
|---|---|---|
| B1 | PR-AUC (garis prevalensi 0,11) dan MCC pada threshold 0,80 di DS2 | `model/data/processed/test.npz` + model float32 |
| B2 | Rerata recall per rekaman (statistik "average" EC57) di samping median | `model/artifacts/metrics/fase6_per_record_fp32.csv` |
| B3 | Δ float32 vs INT8 per kelas S/V/F dan persentase detak yang labelnya berubah | Evaluasi INT8 DS2 yang sudah ada |
| B4 | Latensi pipeline: rata-rata ± SD, min, maks; median dan p95 per interval 1 menit (ITU-T Y.1541); p95 dengan peringkat ⌈0,95n⌉ (RFC 2330 §11.3), bukan `int(0.95*(n-1))` di `dashboard/ukur_pipeline.py:112` | Log ulangan 1–3, bila sampel per detak tersimpan |
| B5 | Kualitas rekaman per jendela 10 s dengan tiga aturan Orphanidou (HR 40–180, jeda RR ≤ 3 s, rasio RR maks/min < 2,2) dan korelasi template (ambang 0,66), dilaporkan sebagai persentase jendela lulus | Empat rekaman resmi 22 Okt 2026 |
| B6 | Anotasi manual R-peak semi-otomatis atas 927 s (koreksi keluaran Pan-Tompkins), lalu Se dan +P dengan toleransi 150 ms | Rekaman yang sama; kerja manual user |

### C. Ukur ulang di board

| # | Aksi | Catatan |
|---|---|---|
| C1 | Latensi inferensi: 5 run × 1.000 `Invoke()`, 10 pertama dibuang; lapor median, p99, maks; diulang dengan WiFi+MQTT aktif (A/B) | Menutup celah-target A4; literatur belum punya data A/B ini |
| C2 | Beban preprocessing ≥ 30 menit dengan sinyal tubuh dan WiFi aktif, window 256: histogram per panggilan, high-water mark antrean, sampel hilang | Menutup celah-target B8 |
| C3 | `ESP.getMinFreeHeap()` dan `uxTaskGetStackHighWaterMark()` sesudah run panjang | RAM puncak runtime |
| C4 | Kesetaraan INT8 di board atas ratusan window DS2 termasuk kelas S; uji kernel (input int8 identik) dipisah dari uji rantai | Sama dengan celah-target B7 |
| C5 | Uji WiFi putus sungguhan (AP dimatikan), ≥ 3 ulangan, durasi bertingkat; data hilang dihitung terhadap detak yang dihasilkan | Sama dengan celah-target B1 |
| C6 | Derau intrinsik: masukan AD8232 dihubung-singkat 10 s; batas IEC 60601-2-25 30 µV p-p ≈ 44 count, 15 µV RMS ≈ 22 count | Uji bangku tanpa alat tambahan |
| C7 | Opsional: rekaman simultan dengan Polar H10, Bland-Altman HR dan persentase jendela dalam ±5 bpm/±10% (EC13) | Perlu alat |

### D. Ubah firmware sebelum daya diukur

| # | Aksi | Dasar |
|---|---|---|
| D1 | `INA219_CONFIG` `0x3FFF` → `0x39FF` (bus 532 µs, shunt 128 sampel), baca hanya saat CNVR = 1 lalu hapus lewat Power Register; cakupan arus ±50% → 99,2%, tanpa bacaan ganda. Jalankan ulang `test_ina219` dan `test_hw_ina219` | `firmware/include/ina219.h:15`; datasheet INA219 hlm. 9–10, Tabel 5 hlm. 20, hlm. 23. Mode 111 mengonversi shunt lalu bus bergantian, 68,10 ms masing-masing |
| D2 | Kalibrasi: offset nol 60 s tanpa beban, lalu gain dengan 3 beban resistor daya terhadap DMM, regresi linear | Prasetyawati 2023; Espressif melarang DMM seri pada ESP32 (burden voltage) |
| D3 | Tangga ≥ 5 kali dari catu bench 3,7 V di posisi sel, mW sebagai metrik utama, lapor median dan rentang | MLPerf Tiny median 5 run; Moura 2026 |
| D4 | Metrik tambahan: energi per inferensi ≈ (P_p3 − P_p2) × T / N_beat; waktu operasi dari uji habis-baterai di `p5` | MLPerf Tiny µJ/inferensi; derating baterai tidak ditemukan bersumber |
| D5 | Angka "+30 mA" untuk `setSleep(false)` dihapus dari rencana dan diukur | Tidak bersumber; datasheet ESP32-S3 Tabel 5-7 dan 5-9 mengisyaratkan selisih lebih besar |

## 4. Keputusan user

Fokus kerja: buku tahap 1 `progres-pa-1` lebih dulu (keputusan user 1 Nov 2026).
Butir di luar cakupan buku tahap 1 (pipeline, daya) ditunda.

| # | Pertanyaan | Keputusan |
|---|---|---|
| 1 | Butir A dimasukkan ke buku | Belum diputuskan. Yang relevan untuk `progres-pa-1` hanya A4–A9 dan B1–B3, B5, karena pipeline dan daya tidak ada di buku tahap 1 |
| 2 | Target p95 latensi (opsi ITU-T G.1010 "acceptable < 4 s", p95 terburuk 3.304 ms) | Ditunda, di luar buku tahap 1 |
| 3 | D1, config INA219 `0x39FF` + CNVR sebelum tangga daya | Ditunda, di luar buku tahap 1 |
| 4 | Validasi R-peak/HR | A8: hasil akuisisi ditulis sebagai status fungsional, bukan akurasi, karena belum ada alat medis acuan. B6 dan C7 tidak dikerjakan. Penulisannya dikerjakan nanti bersama butir A lain |

## 5. Rujukan kandidat `referensi.bib`

Belum ditambahkan. Kunci, DOI, dan kutipan ada di laporan rinci. Yang paling
berguna untuk butir A: `ietf_rfc6703`, `ietf_rfc7679`, `ietf_rfc6673`,
`itu_g1010`, `itu_h810` (pipeline); `banbury_2021` MLPerf Tiny (kinerja dan
daya); `luz_2016`, `mondejar_2019`, `saito_2015` (sudah ada PDF), `chicco_2023`
(klasifikasi); `gajdzik_2026`, `orphanidou_2015` (sudah ada PDF),
`clifford_2017`, `torad_2026` (akuisisi); `ti_ina219`, `prasetyawati_2023`
(daya). DOI Reddi 2020, Wilhelm 2008, dan Liu & Layland 1973 dicek di Scopus
(85092007781, 43949126892, 84974687699). DOI Scrugli 2022 belum dicek.

## 6. Catatan proses

- Dua riset mengirim alamat email user satu kali ke API Unpaywall saat mencari
  versi open access. Riset berikutnya tidak boleh memakai email user untuk
  layanan pihak ketiga.
- Klaim teknis yang dicek langsung: config INA219 (`firmware/include/ina219.h:15`),
  rumus p95 dan loop tidur 50 ms (`dashboard/ukur_pipeline.py:47,112`), rentang
  dinamis ((4.095 − 1.900) × 0,757 / 1.100 = 1,51 mV; 1.900 × 0,757 / 1.100 =
  1,31 mV), CI Clopper–Pearson, dan DOI di bagian 5.
