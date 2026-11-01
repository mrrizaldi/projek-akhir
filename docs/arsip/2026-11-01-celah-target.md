# Celah terhadap target (1 Nov 2026)

**Status:** daftar kerja aktif. Butir yang selesai dicoret dari daftar ini dan
penutupnya dicatat di dokumen terkait (walkthrough, `model/CLAUDE.md`, buku).
**Sumber target:** Tujuan Bab 1, rencana pengujian Bab 3
(`tab:pengujian-model`, `tab:pengujian-pipeline`), PRD
(`model/PRD_Model_Aritmia_TinyML.pdf`, DoD hal. 17 dan Lampiran C hal. 18),
`model/CLAUDE.md` §Pekerjaan terbuka, `hardware/mainboard/README.md` §Yang belum
terverifikasi.
**Cara pindai:** `grep -rn PLACEHOLDER laporan/buku-pa/bab`, tabel ketercapaian
dan keterbatasan Bab 4, lalu tiap target Bab 3 dicocokkan dengan cara ukurnya di
Bab 4.

Ringkasnya: target berangka yang **belum diukur sama sekali hanya satu**, yaitu
konsumsi daya per mode. Sisanya terpenuhi dengan catatan cakupan (metrik diukur
berbeda dari rencana, satu ulangan, satu subjek), atau berupa pekerjaan
perangkat keras dan gambar.

## A. Target yang belum terpenuhi

| # | Target | Sumber | Status | Penghalang | Aksi berikutnya |
|---|---|---|---|---|---|
| A1 | Arus dan daya per mode operasi (6 tingkat `p0`–`p5`) | `bab3.tex` rencana daya; PRD Lampiran C | Belum diukur (`bab4.tex` `\PlaceholderData` daya) | Tingkat 5 butuh WiFi; board reset tiap ±2,5 s saat `WiFi.begin()` dengan konverter 4,x V | User menyetel konverter ke 5,0–5,1 V. Lalu: WiFi ON (`m`), tangga dari baterai tanpa charger, `make pull-daya`, isi Bab 4 |
| A2 | Biaya arus radio tanpa mode tidur (perkiraan ±30 mA) | `bab4.tex` butir Latensi | Belum diukur | Sama dengan A1 | Terukur sekaligus di tingkat 5 tangga A1 |
| A3 | Status jalur model on-device | Tujuan Bab 1 butir 2 | Sebagian tercapai, hanya karena A1 | A1 | Sesudah A1: ketercapaian, abstrak, Bab 5 |
| A4 | Latensi inferensi saat WiFi/MQTT aktif | `bab3.tex` `tab:pengujian-model` | Diukur 26,6 ms tanpa radio | Tidak ada (board via USB cukup) | Ukur ulang latensi inferensi dengan WiFi ON lewat USB |
| A5 | Latensi p95 (acuan ≤ 2.000 ms, bukan target) | `bab4.tex` `tab:target-pipeline` | 1.404 / 3.304 / 2.251 ms pada tiga ulangan | Kontensi kanal WiFi (dugaan) | Ulangi di titik akses tidak padat, lebih banyak ulangan |

## B. Target terpenuhi dengan cakupan lebih sempit dari rencana

| # | Target | Rencana Bab 3 | Yang diukur Bab 4 | Untuk menutup |
|---|---|---|---|---|
| B1 | Integritas data saat putus | WiFi diputus paksa, kapasitas ±4–7 jam | Broker dibekukan 24 s sekali, konfigurasi antrean 64 | Ulangi dengan WiFi diputus sungguhan pada ring 27.000 entri, paket 50 |
| B2 | Pemenuhan bufer | Entri dihitung saat streaming dan putus | Kapasitas terpasang; terisi 43 dari 27.000 (0,16%) | Bagian dari B1, dengan backlog panjang |
| B3 | Waktu flush | Sejak pulih sampai bufer habis | ≤ 24,6 s pada paket kecil | Bagian dari B1 |
| B4 | Latensi end-to-end | Rata-rata, sampai dashboard tampil | Median, sampai baris terbaca di REST API (±100 ms) | Cukup ditulis eksplisit di Bab 4 sebagai perubahan metrik beserta alasan |
| B5 | Pipeline dengan subjek sehat | Sinyal tubuh dikirim lewat MQTT | Seluruh pengiriman dengan sinyal replay | Satu sesi sinyal tubuh dengan WiFi ON (setelah A1 atau lewat USB tanpa charger) |
| B6 | Gerbang kalibrasi: transisi pada kontak baik | Kontak 60 s + R-R tenang 30 s | Diamati di layar dengan catu powerbank, tanpa log serial | Satu uji lewat USB dengan charger laptop dicabut, simpan log `calibrating -> good` dan `good -> poor` |
| B7 | Kesetaraan C dan Python | Data acuan | Satu potongan 6,67 s rekaman 208 tanpa kelas S | Opsional: data acuan kedua yang memuat detak S |
| B8 | Beban preprocessing pada window 256 | `tab:parameter-eksperimen` baris d | 82 µs dan 33,4 ms diukur pada window 250 | Ukur ulang beban dengan firmware sekarang (perangkat saja) |
| B9 | Uji amati manusia (bunyi, layar, tombol) | `bab3.tex` rencana perangkat keras | Dinilai lewat menu, hasil tidak disimpan | Catat hasil tes perangkat ke berkas |

## C. Target PRD yang tidak disebut di Bab 4

| # | Target PRD | Kondisi | Usulan |
|---|---|---|---|
| C1 | Model INT8 < 20 KB (PRD hal. 3, 16, 17) | 22,94 KB; batas 25 KB disetujui user (`model/CLAUDE.md` decision "Batas ukuran model") | Sebut di Bab 4 bahwa batas dilonggarkan beserta alasan (varian deploy) |
| C2 | Window 250 sampel (PRD hal. 5) | 256 lewat ablasi tiga seed | Sudah dibahas di ablasi Bab 4, tidak perlu aksi |
| C3 | Sensitivity Pan-Tompkins > 99% di rekaman 100 (PRD hal. 9) | Bab 4 melaporkan 13/13 pada 10 s pertama dan 0,9469 di DS2 | Jalankan `bench_pantompkins.py 100` dan laporkan angka seluruh rekaman 100 |
| C4 | Reproducible dengan seed terkunci (PRD DoD) | Tidak terpenuhi: F1 0,6911 vs 0,6535 pada run identik (oneDNN) | Tulis sebagai keterbatasan di Bab 4 |

## D. Perangkat keras dan gambar

| # | Pekerjaan | Siapa | Catatan |
|---|---|---|---|
| D1 | Cek fisik PCB rev2: jarak header DevKit, urutan pin modul, ruang mekanik, jalur D1→VSYS, konektor baterai, tegangan lampu saklar | User | `hardware/mainboard/README.md` §Yang belum terverifikasi |
| D2 | Tabel perangkat keras, foto rakitan, saran wearable di Bab 4/5 | User + Claude | Sesudah PCB dicetak |
| D3 | 12 gambar placeholder (9 di Bab 3, 3 di Bab 4) | User | `laporan/buku-pa/gambar/daftar-placeholder.md`. `fig:4-bufer` adalah plot data, perlu keputusan apakah skrip plotnya ditulis |
| D4 | Aturan alarm ThingsBoard dan widget `ecg_snippet` | Claude | Keduanya disebut belum ada di Bab 3/4; opsional |

## E. Isi buku yang basi (menunggu izin sunting `laporan/`)

| # | Lokasi | Isi sekarang | Fakta | Usulan |
|---|---|---|---|---|
| E1 | `bab4.tex` butir Konsumsi Daya (baris ±866) | Board masih dicatu USB dan pin masukan INA219 mengambang | INA219 sudah di jalur baterai: `model/artifacts/metrics/daya/20261014-1629-board-003.csv` (3,69 V, ±137 mA, mode 0) | Penghalang = tingkat WiFi menunggu konverter 5 V; angka 14 Okt tidak dipakai karena charger diduga tercolok |
| E2 | `bab4.tex` analisis jalur model (baris ±1082) | "INA219 belum dirakit pada jalur catu baterai" | Sama dengan E1 | Sama dengan E1 |
| E3 | `bab5.tex` Saran 1 (baris ±38) | "INA219 perlu dirakit pada sisi baterai" | Sama dengan E1 | Saran diganti: setel konverter 5 V lalu jalankan tangga |
| E4 | `docs/arsip/README.md` baris firmware-menu-plan | "Paragraf tombol/menu di Bab 3 laporan belum disesuaikan" | Bab 3 sudah memuat menu dan pohon menu | Arsip read-only; dibiarkan, dicatat di sini |

## F. Temuan firmware terbuka

| # | Temuan | Langkah berikutnya |
|---|---|---|
| F1 | Rekaman mulai sendiri sesaat setelah board dicolok USB (22 dan 23 Okt) | Cetak sumber pemicu di `rekam_toggle()` (tombol B3 / serial `r`), lalu colok ulang beberapa kali |
| F2 | Sesi rekam hilang bila daya putus sebelum `SIMPAN`; jalur live kehilangan ±4,7 s per bagian saat menyimpan | Tercatat di `firmware/README.md` §Batasan yang disengaja. Akar: ISR akuisisi tidak aman-IRAM. Dikerjakan hanya bila diminta |
| F3 | Antrean puncak naik 12 → 21 sampel (`bab4.tex` butir alur hidup) | Telusuri dengan pencacah isi antrean per tahap |
| F4 | Refraktori 200 ms sebagai penyebab sensitivity S 0,6494 | Ablasi refraktori dengan `model/scripts/eval_detected_segmentation.py` |

## Urutan yang disarankan

1. A1 (konverter 5 V oleh user) membuka A1–A3, B5, dan uji ThingsBoard dari baterai.
2. B6 dan A4 bisa dikerjakan sekarang lewat USB, tanpa menunggu konverter.
3. E1–E3 begitu izin sunting buku diberikan.
4. C1, C3, C4 adalah tambahan kecil di Bab 4 yang menutup celah terhadap PRD.
5. D1–D3 berjalan paralel oleh user.
