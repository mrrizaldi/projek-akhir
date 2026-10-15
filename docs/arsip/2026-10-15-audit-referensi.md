# Audit daftar pustaka buku PA (laporan/buku-pa/referensi.bib)

Kondisi uji: 15 Okt 2026. Sumber verifikasi: Scopus (MCP `scopus`) untuk
keberadaan dokumen, jurnal, tanggal, dan DOI; metadata lengkap (penulis,
volume, halaman) diambil dari Crossref lewat DOI yang dikembalikan Scopus.
Laporan ini tidak mengubah apa pun di `laporan/`.

## a. Status tool Scopus

- Tool tersedia dan berfungsi. Kuota 20.000 permintaan; sisa **19.948**
  (dipakai 52 permintaan: 35 pencarian + 18 detail abstrak).
- `get_abstract_details` pada langganan ini tidak mengembalikan daftar
  penulis, volume, maupun abstrak, sehingga volume/halaman/penulis diambil
  dari Crossref (`api.crossref.org/works/<DOI>`). DOI-nya identik dengan
  yang dikembalikan Scopus, jadi metadatanya tetap terverifikasi.
- Dua kandidat tidak ada di Scopus dan ditandai **BELUM TERVERIFIKASI**:
  `david_2021` (MLSys tidak terindeks Scopus; metadata dari
  proceedings.mlsys.org) dan `aami_ec57_2012` (dokumen standar, bukan
  publikasi; dicek di webstore ANSI). Entri non-publikasi yang sudah ada
  (`who_cvd`, `oasis_mqtt5`, `mulyawan_2026`, `analog_ad8232`) juga di luar
  jangkauan Scopus; itu wajar untuk tipe sumbernya.

## b. Tabel audit (28 entri; 22 dikutip, 6 tidak dikutip)

Hitungan `n×` = jumlah `\cite{}` di `bab1`–`bab5` + abstrak. Proposal memakai
bib yang sama minus `dias_2021`, jadi temuan metadata berlaku untuk keduanya.

| Key | n× | Scopus | Relevansi | Alasan | Tindakan |
|---|---|---|---|---|---|
| who_cvd | 1 | n/a (web WHO) | Relevan | Angka mortalitas CVD, bab1. | Pertahankan |
| al_quayed_2026 | 4 | Ada | Tangensial | Paper keamanan siber IoT kesehatan; angka 152,3 ms memang berasal dari paper ini (bab2:9, bab2:392 sah), tetapi dipakai juga sebagai definisi edge computing (bab2:71) dan klaim umum "sistem IoT jantung mengirim mentah ke cloud" (bab3:9). | Pertahankan di bab2:9 & bab2:392; ganti dengan `shi_2016` di bab2:71 dan bab3:9. Perbaiki jurnal (lihat d). |
| tinyml_iot_review | 6 | Ada | Relevan (5×), Tidak relevan (1×) | SLR TinyML-IoT cocok untuk klaim TinyML/edge (bab1:13, bab2:11, 71, 79, 377). Di bab2:204 dipakai untuk menjelaskan cara kerja AD8232, yang tidak dibahas SLR itu. | Pertahankan; di bab2:204 ganti dengan `analog_ad8232` (datasheet) atau `ardeti_2024`. Perbaiki DOI (lihat d). |
| resilient_edge_cloud | 8 | Ada | Tangensial | Arsitektur industri manufaktur berbasis Kubernetes. Dipakai untuk klaim umum resiliensi/bufer edge pada IoT kesehatan (bab1:15, bab2:11, bab3:9, bab3:457, bab4:64), untuk deskripsi ThingsBoard (bab2:242, tidak ada hubungannya), dan sebagai penelitian terkait (bab2:397). | Pertahankan hanya di bab2:397. Ganti: bab1:15/bab2:11/bab3:9 → `escobedo_2026` + `yaacoub_2020`; bab3:457/bab4:64 → `tipparaju_2021` + `escobedo_2026`; bab2:242 → `reoukadji_2025`. Lengkapi volume/DOI (lihat d). |
| mekhfioui_2025 | 5 | Ada | Relevan | 1D-CNN ringan + GAP untuk sinyal jantung di embedded. | Pertahankan; tambah halaman/DOI. |
| xie_2021 | 1 | Ada | Relevan | Penelitian terkait noise ECG ambulatory. | Pertahankan; **jurnal & penulis salah** (lihat d). |
| karri_2023 | 1 | Ada | Relevan | Penelitian terkait QRS + klasifikasi embedded. | Pertahankan; `number` sebenarnya article number (lihat d). |
| laiu_2026 | 3 | Ada | Tangensial | Federated TinyML untuk keamanan siber, evaluasi simulasi. Dipakai sebagai sumber klaim umum kuantisasi INT8 (bab2:129, bab3:379). | Pertahankan di bab2:372 (penelitian terkait, gap sudah diakui); ganti bab2:129 & bab3:379 dengan `jacob_2018` + `david_2021`. |
| crespi_2026 | 1 | Ada | Tangensial | Pruning tidak dipakai pada PA ini; kalimat bab2:134 hanya menyebut angka paper itu. | Pilihan user: hapus kalimat + entri (rekomendasi), atau pertahankan sebagai konteks. |
| oasis_mqtt5 | 1 | n/a (spesifikasi) | Relevan | Definisi MQTT dan QoS. | Pertahankan; tambah `lee_2013` untuk klaim "QoS-1/2 agar data tidak hilang" yang kini tanpa sitasi. |
| kim_2023 | 5 | Ada | Relevan | TinyCES, 1D-CNN INT8 di Cortex-M4. | Pertahankan; **nama penulis pertama salah** (lihat d). |
| elhadad_2025 | 0 | Ada (tapi beda) | Tidak dikutip | Entri bib menyebut Elhadad & Rayan 2025; dokumen dengan judul itu di Scopus/Crossref adalah Wang & Sun, 2024. | Hapus. |
| khan_2025 | 0 | Ada | Tidak dikutip | Osteoartritis lutut; key tidak cocok penulis (Bharanidivya). | Hapus. |
| sheeba_rani_2026 | 3 | Ada | Relevan | Wearable kardiovaskular TFLite di Cortex-M4. | Pertahankan; tambah halaman/DOI. |
| fahoum_2026 | 0 | Ada | Tidak dikutip | PPG, bukan ECG. | Hapus. |
| xiang_2026 | 0 | Ada | Tidak dikutip | Tekanan darah. | Hapus. |
| chowdhury_2023 | 1 | Ada | Tangensial | Auskultasi suara jantung, dipakai eksplisit sebagai benchmark daya Cortex-M4 dan teks sudah mengakui bedanya. | Pertahankan (boleh dihapus bila subbab penelitian terkait diramping). Tambah halaman/DOI. |
| kumaran_2026 | 0 | Ada | Tidak dikutip | DRL penjadwalan cloud-edge; volume di bib salah (329, Crossref: 346). | Hapus. |
| verma_2024 | 0 | Ada | Tidak dikutip | Kendali kemacetan jaringan IoT. | Hapus. |
| ecg_goldberger | 3 | Ada (buku, ed. 10, 2023) | Relevan | Lead II, morfologi ECG. | Pertahankan. |
| pan_tompkins_1985 | 1 | Ada | Relevan | Deteksi R-peak. | Pertahankan. |
| sornmo_laguna_2005 | 3 | Ada (buku) | Relevan | Noise ECG, filter bandpass. | Pertahankan (DOI buku: 10.1016/B978-0-12-437552-9.X5000-4, opsional). |
| moody_mark_2001 | 4 | Ada | Relevan | MIT-BIH. | Pertahankan. |
| dechazal_2004 | 6 | Ada | Relevan | DS1/DS2 inter-patient, pemetaan AAMI. | Pertahankan. |
| mulyawan_2026 | 6 | n/a (PA PENS) | Relevan | Penelitian pendahulu. | Pertahankan. |
| zambrano_2026 | 6 | Ada | Relevan | TinyML aritmia di MCU murah; pembanding langsung. | Pertahankan. |
| goldberger_2000_physionet | 1 | Ada | Relevan | Sitasi resmi SVDB/INCART via PhysioNet. | Pertahankan. |
| dias_2021 | 5 | Ada | Relevan | Augmentasi jitter, inter-patient single-lead. | Pertahankan. |

Ringkasan tindakan: 6 entri dihapus (tidak dikutip), 4 entri tangensial
dikurangi cakupan sitasinya (al_quayed, resilient_edge_cloud, laiu, +
tinyml_iot_review di satu kalimat), 1 entri keputusan user (crespi), sisanya
dipertahankan.

## c. Kandidat tambahan (semua ada di `usulan.bib`)

Pengganti untuk sitasi tangensial:

| Key baru | Terverifikasi | Topik | Kalimat / bab yang cocok |
|---|---|---|---|
| shi_2016 | Scopus, IEEE IoT J. Q1 | Definisi & manfaat edge computing (latensi, privasi, operasi mandiri) | bab2:71 (definisi edge), bab1:13, bab3:9 menggantikan `al_quayed_2026` |
| escobedo_2026 | Scopus, MDPI IoT | ESP32 dual-core memisahkan akuisisi ECG dan MQTT, deteksi packet loss, 12 jam tanpa kehilangan paket | bab1:15, bab2:11, bab3:9, bab3:457, bab4:64 menggantikan `resilient_edge_cloud` |
| tipparaju_2021 | Scopus, Biosensors Q1 | Antrean/bundling paket untuk mencegah kehilangan data pada ekosistem wearable kesehatan | bab3:457 (bufer aplikasi di atas pustaka MQTT), bab4:64 |
| yaacoub_2020 | Scopus, IEEE Network Q1 | Store-and-forward (DTN) untuk data pemantauan pasien mHealth saat konektivitas terputus | bab2:11, bab3:385 (prinsip pertahankan data di edge) |
| reoukadji_2025 | Scopus, iJOE | ThingsBoard sebagai penyimpanan telemetri + visualisasi untuk IoT kesehatan dengan edge | bab2:242 menggantikan `resilient_edge_cloud` |
| jacob_2018 | Scopus, CVPR | Kuantisasi integer-only, skema skala/zero-point (Persamaan kuantisasi) | bab2:129, bab2 Persamaan `eq:kuantisasi`, bab3:379 menggantikan `laiu_2026` |
| david_2021 | **BELUM TERVERIFIKASI di Scopus** (MLSys 2021 vol. 3) | TensorFlow Lite Micro | bab2 paragraf framework TinyML, bab3:379 |
| analog_ad8232 | BELUM TERVERIFIKASI (datasheet, bukan publikasi) | Cara kerja AD8232 | bab2:204 menggantikan `tinyml_iot_review` |
| ardeti_2024 | Scopus, BSPC Q1 | Kerangka monitoring ECG real-time berbasis AD8232 | alternatif bab2:204 bila datasheet tidak diinginkan |

Tambahan untuk topik yang belum bersumber atau sumbernya lemah:

| Key baru | Terverifikasi | Topik | Kalimat / bab yang cocok |
|---|---|---|---|
| aami_ec57_2012 | BELUM TERVERIFIKASI di Scopus (standar ANSI/AAMI) | Kelas AAMI N/S/V/F/Q, protokol pelaporan | bab3:205 (skema anotasi AAMI), bab3:230, bab4:34 |
| young_2018 | Scopus, J. Electrocardiology | Pendamping peer-reviewed standar IEC/AAMI | sampingan `aami_ec57_2012` |
| luz_2016 | Scopus, CMPB Q1, survei standar | Kritik evaluasi intra-patient, pentingnya paradigma inter-patient dan AAMI | bab2:319, bab2:509, bab4:1240 |
| bahrami_2025 | Scopus, Cardiovasc. Eng. Technol. | Perbandingan langsung inter/intra/patient-specific pada DL | bab2:319 (angka intra-patient optimistis) |
| kiranyaz_2016 | Scopus, IEEE TBME Q1 | 1D-CNN real-time untuk klasifikasi ECG per detak | bab2:91 (CNN pada sinyal 1D), bab3:258 |
| saito_2015 | Scopus, PLOS ONE | Precision-recall lebih informatif dari ROC/accuracy pada kelas tak seimbang | bab4:34 (accuracy tidak dijadikan acuan), Subbab evaluasi-metrik |
| safdar_2023 | Scopus, BSPC Q1 | Augmentasi data ECG untuk klasifikasi | bab2:343 pendamping `dias_2021` |
| li_2020 | Scopus, IEEE OJCAS | Evaluasi 9 algoritma QRS (termasuk Pan-Tompkins) untuk sensor wearable daya rendah | bab3:163 (Pan-Tompkins di MCU) |
| degiovanni_2023 | Scopus, IEEE TBME Q1 | Deteksi R-peak adaptif pada sensor ECG wearable | opsional bab3:163 |
| bui_2021 | Scopus, BSPC Q1 | Filter IIR real-time untuk ECG di sistem embedded | bab3:156 (biquad kausal) |
| lee_2013 | Scopus, ICOIN | Korelasi loss/delay MQTT per QoS | bab2:232 (QoS-1/2 untuk data kritis) |
| mounika_2026 | Scopus, Sens. Actuators A Q1 | Monitoring ECG kontinu berbasis ESP32 ke cloud | bab3:151 atau bab2 landasan ESP32 |
| yahyati_2025 | Scopus, IEEE Access | Tinjauan TinyML di healthcare 2025 | bab1:13, bab2:79 pendamping `tinyml_iot_review` |

Pencarian "MQTT + store-and-forward + ECG" spesifik tidak menghasilkan jurnal
Q1/Q2 yang persis; kombinasi `escobedo_2026` (ESP32+MQTT+ECG, deteksi loss),
`tipparaju_2021` (antrean lokal wearable kesehatan), dan `yaacoub_2020`
(store-and-forward mHealth) adalah yang paling dekat.

## d. Metadata yang salah atau tidak lengkap di bib sekarang

Versi benar sudah ditulis di `usulan.bib` dengan key yang sama (ganti entri
lama dengan entri baru).

| Key | Kesalahan | Nilai benar (Scopus/Crossref) |
|---|---|---|
| al_quayed_2026 | Jurnal ditulis "Computers, Materials and Continua" | *Computer Modeling in Engineering & Sciences* (CMES), vol. 146 no. 1, hlm. 1–10, DOI 10.32604/cmes.2025.074799; penulis tunggal F. Al-Quayed |
| tinyml_iot_review | DOI placeholder `10.1016/j.jii.2025.xxx` | DOI 10.1016/j.jii.2026.101065, art. 101065; penulis lengkap 6 orang |
| resilient_edge_cloud | Tanpa volume/halaman/DOI | vol. 213, art. 111795, DOI 10.1016/j.cie.2025.111795 |
| xie_2021 | Jurnal "Sensors", penulis "Xie, W." | *Future Generation Computer Systems*, vol. 116, hlm. 103–116, penulis pertama Xie, Xiaoyun; judul "A multi-stage ..." |
| karri_2023 | `number = {119221}` | 119221 adalah article number (pages), bukan nomor terbitan |
| kim_2023 | Penulis "Kim, M." | Kim, Eunchan et al.; hlm. 1751–1764; DOI 10.32604/cmc.2023.031663 |
| elhadad_2025 | Penulis & tahun tidak cocok dokumen mana pun | Dokumen berjudul sama: Wang, Y. & Sun, L., CMPB vol. 254, 2024 (entri dihapus karena tidak dikutip) |
| khan_2025 | Key tidak cocok penulis (Bharanidivya) | dihapus |
| kumaran_2026 | vol. 329 | vol. 346, art. 116176 (dihapus) |
| verma_2024 | Penulis "Verma, M.", tanpa nomor | Verma, Lal Pratap et al., vol. 10 no. 22 (dihapus) |
| mekhfioui_2025, laiu_2026, crespi_2026, sheeba_rani_2026, chowdhury_2023, fahoum_2026, xiang_2026 | Tanpa DOI dan/atau halaman; penulis hanya "and others" | Dilengkapi di `usulan.bib` (yang dihapus tidak ditulis ulang) |
| goldberger_2000_physionet | DOI tidak tercatat di Scopus tetapi benar di Crossref/Circulation | tidak perlu diubah |

Catatan gaya: sejumlah entri lama memakai `author = {X and others}`; IEEEtran
akan mencetak "et al." tetapi daftar pustaka PA PENS lazimnya menulis penulis
lengkap, maka `usulan.bib` menulis semua penulis.

## Ringkasan

- Entri diaudit: 28 (22 dikutip, 6 tidak dikutip → hapus).
- Entri dengan metadata salah/kurang: 11 diperbaiki di `usulan.bib`
  (10 entri lama ditulis ulang dengan key sama, termasuk 3 yang hanya perlu
  DOI/halaman; 4 entri hapus tidak ditulis ulang).
- Pengganti untuk sitasi tangensial: 9 key baru (`shi_2016`, `escobedo_2026`,
  `tipparaju_2021`, `yaacoub_2020`, `reoukadji_2025`, `jacob_2018`,
  `david_2021`, `analog_ad8232`, `ardeti_2024`).
- Tambahan topik: 13 key baru (`aami_ec57_2012`, `young_2018`, `luz_2016`,
  `bahrami_2025`, `kiranyaz_2016`, `saito_2015`, `safdar_2023`, `li_2020`,
  `degiovanni_2023`, `bui_2021`, `lee_2013`, `mounika_2026`, `yahyati_2025`).
- `usulan.bib`: 33 entri (22 baru + 11 perbaikan entri lama), 3 di antaranya
  BELUM TERVERIFIKASI di Scopus (`david_2021`, `aami_ec57_2012`,
  `analog_ad8232`).
- Sisa kuota Scopus: 19.948 dari 20.000.
