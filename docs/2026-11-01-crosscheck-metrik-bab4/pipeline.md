# Crosscheck metrik dan cara ukur pipeline MQTT terhadap standar dan literatur

Kondisi riset: 1 Nov 2026. Semua berkas sumber ada di
`/home/mrrizaldi/dev/projek-akhir/laporan/pustaka/belum-dirujuk/riset-pengukuran/pipeline/`
(disingkat `P/`). Berkas `.txt` dari MDPI adalah teks HTML artikel karena unduhan PDF MDPI
ditolak server (403); isinya teks lengkap, tetapi tanpa nomor halaman, jadi rujukannya ke
nomor subbab dan tabel.

Selain literatur, kode alat ukur dibaca langsung: `dashboard/ukur_pipeline.py` (baris 61–128)
dan `laporan/buku-pa/bab/bab3.tex` (tab:pengujian-pipeline), `bab4.tex` (sec pipeline).
Temuan dari kode ditandai **[kode]**.

---

## 1. Tabel crosscheck

| # | Metrik / cara ukur kami | Praktik standar / literatur (sumber + lokasi) | Status | Saran konkret |
|---|---|---|---|---|
| 1 | **PDSR** = paket ber-PUBACK pada percobaan pertama / total PUBLISH, dihitung di perangkat, batas tunggu 5 s | RFC 7680 §2.4 (hlm. 7) mendefinisikan loss satu arah dengan ambang Tmax; §2.8.2 (hlm. 11): Tmax "MUST be reported". Karena keberhasilan kami ditentukan oleh kembalinya PUBACK, definisi yang lebih tepat adalah **round-trip loss** RFC 6673 §4.3 (hlm. 7): Loss = 0 bila Src menerima paket balasan sebelum TstampSrc + Tmax. Kim 2026 Tabel 8 dan Tabel 10 menghitung "message success rate" sebagai pesan diterima subscriber / pesan dikirim; Lima 2025 §III-A (hlm. 4) menghitung loss sebagai selisih jumlah publish dan jumlah yang tiba di subscriber; Escobedo 2026 §3.2 (hlm. 11–12) mendeteksi loss dengan nomor urut di penerima. | **Beda tapi dapat dipertanggungjawabkan** | Sebut di Bab 3/4 bahwa PDSR adalah keberhasilan *round-trip* percobaan pertama (setara 1 − rasio round-trip loss RFC 6673) dengan Tmax = 5 s, Type-P = MQTT 3.1.1 PUBLISH QoS 1 di atas TCP, ukuran payload batch. Pisahkan tegas dari "rasio pengiriman aplikasi" (detak tiba di ThingsBoard / detak dihasilkan), yang di literatur disebut PDR/message success rate dan yang kami capai 100%. |
| 2 | PDSR target ≥ 95%, hasil 292/292, 253/255, 188/188 | Y.1541 §5.3.2 (hlm. 11): nilai yang diamati harus dicatat "along with any assumptions and confidence intervals". RFC 6703 §8.2 (hlm. 24): ukuran sampel (jumlah paket) harus dilaporkan. Tidak ada standar yang memberi jumlah minimum paket untuk PDR. | **Kurang, perlu ditambah** (mudah) | Tambahkan selang kepercayaan binomial eksak (Clopper–Pearson, 95%, dua sisi), dihitung dari angka buku: ulangan 1: 98,74–100%; ulangan 2: 97,20–99,90%; ulangan 3: 98,06–100%; gabungan 733/735 = 99,73% dengan CI 99,02–99,97%. Batas bawah semua ulangan di atas 95%, jadi klaim "PDSR ≥ 95%" lolos secara statistik walau sampelnya kecil. Perhitungan: untuk 0 kegagalan, batas bawah satu sisi 95% = 0,05^(1/n); n ≥ 59 paket sudah cukup untuk menyatakan > 95%, dan n ≥ 299 untuk > 99%. |
| 3 | **Latensi end-to-end** = waktu PC melihat baris di REST ThingsBoard − ts kejadian R-peak | RFC 7679 §3.4 mendefinisikan *one-way delay* dari bit pertama dikirim sampai bit terakhir diterima (wire time). Metrik kami adalah metrik aplikasi turunan yang mencakup pemrosesan di perangkat. RFC 2330 §6.3 (hlm. 7–8): untuk metrik turunan/komposisi, penyebaran ketidakpastian harus dianalisis. Adochiei 2025 §3.4 memasang stempel waktu di empat titik (publisher, broker, tulis InfluxDB, ingest Grafana) dan **mengecualikan waktu render Grafana**. Kim 2026 Tabel 8/10: dari "data generation at a sensor node" sampai "reception at the subscriber", stempel subscriber diambil sebelum tulis basis data. Lima 2025 §III-B (hlm. 5): waktu publish (user property) sampai waktu terima di subscriber. | **Sesuai** secara praktik (titik awal kami lebih ketat: kejadian, bukan publish), tetapi **definisi di buku tidak konsisten** (lihat Celah 1) | Nama metriknya diganti menjadi "latensi kejadian-ke-API" atau definisinya dinyatakan eksplisit: dari R-peak (ts) sampai baris tersedia di REST API ThingsBoard, **tanpa** waktu render dashboard. Dekomposisi (869 ms sisi perangkat, broker 1,1 ms) sudah sejalan dengan pendekatan multi-titik Adochiei dan Reiher 2022. |
| 4 | Sinkronisasi jam: perangkat SNTP + gettimeofday; selisih jam perangkat–PC dikoreksi dari `epoch_ms` di baris status serial (median 5 sampel, sekali di awal) | RFC 7679 §3.7.1 (hlm. 10–11): ketidakpastian jam total = Esynch(t) + Rsource + Rdest, dan "should be included in the error/uncertainty analysis". §3.8.3 (hlm. 15): galat sistematik "SHOULD be removed" dan galat kalibrasi e (95%) "SHOULD" dilaporkan. RFC 7680 §2.8.3 (hlm. 11): derajat sinkronisasi "MUST be reported". RFC 7679 §3.5 (hlm. 8): NTP biasa hanya beberapa ms. Literatur: Adochiei 2025 §3.4.1: NTP lokal (chrony, update 60 s), drift ±5 ms per 60 s, dan mengakui tidak ada CI atau sebaran latensi. Kim 2026 Tabel 3 dan 10: NTP tiap 30 menit, ketidakpastian tidak dilaporkan. Lima 2025 hlm. 5: load driver dan subscriber di host yang sama "to ensure the accuracy of the end-to-end delay". Reiher 2022 hlm. 5: karena jam NTP "not guaranteed to be synchronized exactly", mereka memakai latensi round-trip pada satu jam. Silva 2021 §5: publisher (laptop) dan subscriber (RPi) di mesin berbeda tanpa menyebut sinkronisasi. | **Beda tapi dapat dipertanggungjawabkan.** Pendekatan "ukur selisih jam lalu koreksi" adalah bentuk penghilangan galat sistematik RFC 7679 §3.7.3, dan lebih eksplisit daripada kebanyakan paper. **Kurang**: besarnya ketidakpastian tidak dilaporkan. | Laporkan (a) sebaran 5 sampel offset (min–maks) sebagai perkiraan Esynch; (b) ukur offset juga di **akhir** ulangan untuk menangkap skew (RFC 7679 §3.7.1 butir skew); (c) sebut resolusi: ts perangkat 1 ms, sisi PC ditentukan siklus polling. **[kode]** Stempel PC untuk offset diambil di loop yang tidur 50 ms (`time.sleep(0.05)`), jadi offset bisa bias sampai ±50 ms + latensi USB serial; arah biasnya membuat latensi tampak lebih kecil. Cukup dituliskan sebagai komponen ketidakpastian, atau kurangi tidurnya menjadi 1 ms. |
| 5 | Polling REST ±100 ms; "batas bawah" = waktu sebelum request poll yang pertama kali melihat baris | RFC 7679 §3.7.1: resolusi jam tujuan "adds ... uncertainty to any time value measured with it". RFC 6703 §4.1.2 (hlm. 11) membolehkan ambang aplikasi diterapkan di pasca-olah. | **Kurang, perlu ditambah** (penjelasan saja) | **[kode]** Baris sebenarnya muncul di antara query poll sebelumnya dan query poll saat ini. Nilai `sebelum` dari poll saat ini **bukan batas bawah sejati**: ia bisa lebih besar dari waktu muncul sebenarnya sampai satu siklus (100 ms + durasi REST). Bias ini konservatif (melebih-lebihkan latensi), jadi aman untuk klaim target. Tulis istilahnya sebagai "estimasi konservatif" dengan ketidakpastian ≈ satu siklus polling, bukan "batas bawah". |
| 6 | Statistik: **median** dinilai terhadap target 2.000 ms, p95 dilaporkan (rencana awal: "rata-rata") | RFC 6703 §3.1 (hlm. 6): "we recommend providing both the mean delay and the median delay". §5.2 (hlm. 15–16): median stabil terhadap outlier, dan "minimum, maximum, and 95th percentile have value", perbandingan mean–median informatif. RFC 7679 §5.1–5.3 (hlm. 19–20): percentile, median, minimum. Y.1541 Tabel 1 (hlm. 9): IPTD sebagai batas atas **rata-rata**. Literatur: Kim 2026 Tabel 11 (rata-rata dan maksimum), Silva 2021 §5 (AVG, STDEV, MAX, MIN, MED, CI dari 10 ulangan), Reiher 2022 §IV-D (hlm. 6): mean sebagai metrik utama + min, max, median, SD, Lima 2025 (boxplot median, tabel rata-rata), Adochiei 2025 §3.4.2 (dirata-ratakan). | **Beda tapi dapat dipertanggungjawabkan** (median didukung RFC 6703). **Kurang** karena rata-rata yang tertulis di rencana tidak dilaporkan. | Laporkan juga **rata-rata ± SD, minimum, maksimum** per ulangan. Pemakaian median dibenarkan dengan RFC 6703 §5.2. Dengan ekor panjang (p95 3.304 ms), rata-rata kemungkinan > median, dan rata-rata tetap harus ≤ 2.000 ms agar konsisten dengan rencana. Data mentah sudah ada, cukup dihitung ulang. **[kode]** p95 dihitung sebagai `v[int(0.95*(n-1))]`; RFC 2330 §11.3 (hlm. 25–26) mendefinisikan persentil sebagai nilai terkecil x dengan F(x) ≥ p, yaitu peringkat ⌈0,95n⌉. Untuk n = 292 hasilnya meleset satu peringkat (277 vs 278). Selisihnya kecil tetapi sebaiknya diseragamkan. |
| 7 | Penanganan paket hilang/terlambat dalam statistik latensi | RFC 7679 §5.1 (hlm. 19): nilai *undefined* (hilang) diperlakukan tak hingga dalam persentil. RFC 6703 §3.1: rata-rata/median dihitung pada distribusi bersyarat (yang tiba) dengan ambang tunggu panjang. | **Sesuai** (data hilang aplikasi = 0, jadi bersyarat = tak bersyarat) | Tulis satu kalimat: semua detak yang dikirim muncul di ThingsBoard dalam jendela ukur, jadi tidak ada nilai *undefined*. Detak dari 2 paket yang dikirim ulang ikut dihitung dengan latensi penuhnya, termasuk timeout 5 s. Pastikan memang demikian di data. |
| 8 | Target latensi **≤ 2 s** | ITU-T G.1010 Gambar 2 (hlm. 6): kategori **Responsive (delay ~2 s)**, sebagai kategori tak toleran error di antara Interactive (<<1 s) dan Timely (~10 s). Tabel I.2 (hlm. 9): transaksi/web/akses e-mail "Preferred < 2 s, Acceptable < 4 s", information loss "Zero". ITU-T H.810 (Continua) §6.1.7.4–6.1.7.5 (hlm. 36–37): parameter terukur (detak jantung, SpO2) = *better.medium*, E2E ~1 s; alarm fisiologis = *best.high*, E2E ~10 s; nilai "relative to transport". Skorin-Kapov 2010 Tabel 1: tele-monitoring "small delay: No"; Tabel 3: ECG max delay "approx. 1 s", loss "Zero"; Tabel 4: tele-monitoring real-time "<300 ms E2E one-way for hard real-time ECG (certain applications may tolerate <1 s E2E for ECG)", non-real-time tele-monitoring "N.A.". Zhong 2022 Tabel 3: ECG "P2PLatency <250 ms", yaitu latensi tautan WBAN titik-ke-titik (sensor–hub), **bukan** E2E sampai server. | **Defensible dengan catatan.** 2 s sejalan dengan G.1010 kategori Responsive dan berada di antara H.810 *better.medium* (~1 s, hasil per detak) dan *best.high* (~10 s, alarm). 2 s **melampaui** angka Skorin-Kapov untuk ECG real-time (<300 ms / <1 s), tetapi angka itu untuk aliran **gelombang** ECG gawat darurat, sedangkan kami mengirim **label klasifikasi per detak**. | Ganti/lengkapi rujukan anggaran latensi: G.1010 Gambar 2 + Tabel I.2 dan H.810 §6.1.7.5 sebagai dasar utama, Skorin-Kapov Tabel 1/4 untuk menunjukkan bahwa telemonitoring non-gawat-darurat tidak menuntut delay kecil. Zhong 2022 (<250 ms P2P) sebaiknya **tidak** dipakai sebagai pembanding E2E karena cakupannya tautan BAN. Opsi target p95: G.1010 "Acceptable < 4 s" (p95 terburuk 3.304 ms masih di bawahnya). Ini keputusan user. |
| 9 | Variasi delay / jitter: tidak dilaporkan | RFC 3393 §2.4 (hlm. 6) IPDV; RFC 5481 §7.3 (hlm. 29–30): PDV = D(i) − D(min) lebih disukai untuk ringkasan satu angka; RFC 6703 §3.1 (hlm. 6): "pseudo range" = persentil tinggi − minimum. Y.1541 Tabel 1: IPDV = kuantil 1−10⁻³ − minimum. Skorin-Kapov Tabel 1: tele-monitoring "small jitter: No". | **Beda tapi dapat dipertanggungjawabkan** (jitter tidak kritis untuk telemonitoring) | Opsional: laporkan PDV = p95 − min per ulangan, data sudah tersedia. Jangan pakai kuantil 99,9% karena Y.1541 §5.3.1 (hlm. 10) menyebut perlu ≥ 1000 paket. |
| 10 | **Ukuran sampel**: 3 ulangan × 120–180 s (n latensi ±200–290 detak per ulangan; 735 paket) | RFC 5481 §8.4 (hlm. 33): "test using durations that are similar in length to the session time of interest", dan konsistensi jalur Internet teramati pada skala menit. Y.1541 §5.3.2 (hlm. 10–11): interval evaluasi 1 menit disarankan, "Any minute observed should meet these objectives", CI dicatat. RFC 6703 §8.2 (hlm. 24): laporkan n; "large" harus dijelaskan dengan implikasinya. Praktik: Adochiei 10 × 60 s; Silva 10 ulangan per skenario; Lima 10 ulangan (±4 jam); Saif 2022 dan Reiher 2022 (60 s per eksperimen); Escobedo ±3 juta paket WiFi dan uji 12 jam LTE-M. | **Kurang untuk latensi/ekor**, **cukup untuk PDSR** (lihat butir 2) | (a) Pecah data yang ada menjadi interval 1 menit (±8 interval) dan laporkan median dan p95 per menit (cara Y.1541), jadi tidak perlu ukur ulang. (b) Laporkan CI persentil nonparametrik. Contoh n = 201: CI 95% untuk p95 berada di antara statistik urutan ke-185 dan ke-198, hampir rentang p92–p98,5. Inilah alasan p95 "berayun". (c) Bila ada waktu ukur: tambah ulangan sampai 10 (praktik umum) atau satu ulangan panjang 30–60 menit untuk mendekati durasi sesi monitoring (RFC 5481 §8.4). |
| 11 | **Resiliensi**: broker dibekukan (`docker pause`) 24 s, sekali; data hilang 0; flush ≤ 24,6 s; rencana: WiFi diputus paksa | Peer-review yang mengukur pemadaman terkontrol pada pipeline MQTT kesehatan **jarang ditemukan**. da Silva dkk. 2027 (LNCS, **hanya abstrak**) menguji tiga keadaan (terhubung, offline, reconnect + sinkronisasi backlog) dengan beban bertingkat dan mengukur throughput, latensi E2E, sumber daya, dan "backlog draining time". Escobedo 2026 §3.2 (hlm. 12): loss naik saat kuat sinyal seluler berfluktuasi; §4 (hlm. 15): buffering lokal baru rencana kerja lanjutan. H.810 §3.2.62: definisi *store and forward*. Saif 2022 §VII (hlm. 4–5) memakai NetEm untuk delay, rate, dan drop seragam 0–6%, tetapi bukan pemadaman. Dokumentasi Docker (`docker container pause`): memakai freezer cgroup, "the process is unaware ... that it is being suspended". | **Kurang, perlu ditambah** | `docker pause` membekukan **proses** broker saja, sedangkan WiFi radio, asosiasi AP, dan TCP di kernel host tetap hidup. **Inferensi teknis yang belum diverifikasi dengan tangkapan paket**: kernel host kemungkinan masih meng-ACK segmen TCP selama buffer terima cukup, jadi yang teruji adalah jalur **timeout PUBACK aplikasi**, bukan jalur **putus tautan** (event disconnect WiFi, asosiasi ulang, DHCP, TCP baru, CONNECT MQTT). Keduanya tidak setara. Saran: (1) tambah uji WiFi putus sungguhan (AP dimatikan/dicabut) sesuai rencana Bab 3, ≥ 3 ulangan, dengan durasi bertingkat (mis. 30 s, 5 menit, 30 menit); (2) metrik: data hilang (detak dihasilkan vs tiba, idealnya lewat nomor urut detak), waktu reconnect, waktu drain, laju drain (detak/s), dan latensi detak dari backlog; (3) bila tidak sempat, tulis di keterbatasan bahwa yang diuji adalah kegagalan broker, bukan kegagalan tautan. |
| 12 | **Duplikat**: 0 ts ganda di ThingsBoard (upsert per ts) | RFC 7680 §2.5 (hlm. 8): paket terduplikasi dihitung "received". Lima 2025 hlm. 5: ID pesan dipakai di subscriber untuk menghitung duplikat pada QoS 1. | **Kurang (logikanya melingkar)** | Karena ThingsBoard menimpa per ts, jumlah "ts ganda di ThingsBoard" **selalu 0 secara konstruksi**, sehingga tidak membuktikan ada atau tidaknya duplikat yang dikirim. Yang bisa dibuktikan: deduplikasi bekerja **bila** duplikat terjadi. Saran: hitung duplikat di sisi pengirim/broker (jumlah PUBLISH ulang = 2 pada ulangan 2) atau dengan subscriber independen (`mosquitto_sub`) yang mencatat ts, lalu tunjukkan detak dari paket yang dikirim ulang tetap tercatat satu kali di ThingsBoard. |
| 13 | Data hilang = baris unik REST vs jumlah "terkirim" perangkat (267/267) | Escobedo 2026 §2 dan §3.2: nomor urut per paket di penerima. RFC 7680 §2.4: hilang ditentukan di Dst terhadap yang dikirim Src. | **Beda tapi dapat dipertanggungjawabkan** | Pembanding idealnya detak yang **dihasilkan** detektor, bukan yang "terkirim" (pencacah terkirim tidak melihat detak yang hilang sebelum masuk antrean). Replay deterministik membuat jumlah detak yang diharapkan bisa dihitung, jadi tuliskan pembandingnya. |
| 14 | Konteks: WiFi rumah tak terisolasi, RSSI −50 dBm, sinyal replay ±1,6 detak/s | RFC 7679 §3.8 (hlm. 14–15): kalibrasi dan konteks "MUST be carefully considered and SHOULD always be reported", termasuk Type-P dan path. Y.1541 §5.3.3: ukuran paket dicatat. | **Sesuai** | Tambahkan ukuran payload paket (byte per batch), versi MQTT, kanal WiFi, dan jumlah AP sekitar bila ada. Sudah cukup untuk sidang. |

---

## 2. Daftar sumber

Status: **TL** = teks lengkap dibaca (bagian metode/tabel yang dikutip), **ABS** = hanya abstrak,
**JDL** = hanya judul/metadata.

### Standar

| Kunci usulan | Judul | Penulis | Thn | Venue | DOI | Status | Berkas |
|---|---|---|---|---|---|---|---|
| ietf_rfc7679 | A One-Way Delay Metric for IP Performance Metrics (IPPM) | Almes, Kalidindi, Zekauskas, Morton | 2016 | IETF RFC 7679 (STD 81) | 10.17487/RFC7679 | TL | `P/rfc7679.txt` |
| ietf_rfc7680 | A One-Way Loss Metric for IP Performance Metrics (IPPM) | Almes, Kalidindi, Zekauskas, Morton | 2016 | IETF RFC 7680 (STD 82) | 10.17487/RFC7680 | TL | `P/rfc7680.txt` |
| ietf_rfc2330 | Framework for IP Performance Metrics | Paxson, Almes, Mahdavi, Mathis | 1998 | IETF RFC 2330 | 10.17487/RFC2330 | TL (§6.3, §10.1, §11.3) | `P/rfc2330.txt` |
| ietf_rfc6703 | Reporting IP Network Performance Metrics: Different Points of View | Morton, Ramachandran, Maguluri | 2012 | IETF RFC 6703 | 10.17487/RFC6703 | TL | `P/rfc6703.txt` |
| ietf_rfc5481 | Packet Delay Variation Applicability Statement | Morton, Claise | 2009 | IETF RFC 5481 | 10.17487/RFC5481 | TL (§6.5, §7.3, §8.4) | `P/rfc5481.txt` |
| ietf_rfc3393 | IP Packet Delay Variation Metric for IPPM | Demichelis, Chimento | 2002 | IETF RFC 3393 | 10.17487/RFC3393 | TL (§2.4 saja) | `P/rfc3393.txt` |
| ietf_rfc6673 | Round-Trip Packet Loss Metrics | Morton | 2012 | IETF RFC 6673 | 10.17487/RFC6673 | TL (§3–5) | `P/rfc6673.txt` |
| itu_g1010 | End-user multimedia QoS categories | ITU-T | 2001 | Rec. ITU-T G.1010 (11/2001) | – | TL | `P/itu_g1010_2001.pdf` |
| itu_y1541 | Network performance objectives for IP-based services | ITU-T | 2011 | Rec. ITU-T Y.1541 (12/2011) | – | TL (§5.3, Tabel 1–2) | `P/itu_y1541_2011.pdf` |
| itu_h810 | Interoperability design guidelines for personal connected health systems: Introduction | ITU-T | 2019 | Rec. ITU-T H.810 (11/2019) | – | TL (§3.2, §6.1.7) | `P/itu_h810_2019.pdf` |

Kutipan kunci:

- RFC 7679 §3.7.1, hlm. 11: "these clock-related problems introduce a total uncertainty of
  Esynch(t)+ Rsource + Rdest. This estimate of total clock-related uncertainty should be included
  in the error/uncertainty analysis of any measurement implementation."
- RFC 7679 §3.8.3, hlm. 15: "If the systematic error can be determined, it SHOULD be removed from
  the measured values." / "You SHOULD also report the calibration error, e, such that the true
  value is the reported value plus or minus e, with 95% confidence".
- RFC 7679 §3.5, hlm. 8: "Ordinary application of NTP may allow synchronization to within several
  msec".
- RFC 7679 §5.1, hlm. 19: "In computing this percentile, undefined values are treated as infinitely
  large."
- RFC 7680 §2.8.2, hlm. 11: "The threshold, Tmax, between a large finite delay and loss ... MUST be
  reported." §2.8.3: "The degree of synchronization between the Src and Dst clocks MUST be
  reported."
- RFC 7680 §2.5, hlm. 8: "If the packet is duplicated along the path ... then the packet is counted
  as received."
- RFC 6673 §4.3, hlm. 7: "Type-P-Round-trip-Loss = 1: ... Src did not receive the last bit of the
  reflected packet before the waiting time lapsed at TstampSrc + Tmax."
- RFC 6703 §3.1, hlm. 6: "For packet delay, we recommend providing both the mean delay and the
  median delay with lost packets designated as undefined".
- RFC 6703 §5.2, hlm. 15: "The median is stable in distributions with a few outliers or without
  them." / "additional statistics such as the minimum, maximum, and 95th percentile have value when
  summarizing a distribution."
- RFC 6703 §8.2, hlm. 24: "Even if only the sample size (in terms of number of packets) is given
  for each value or summary statistic, it imparts a notion of the confidence in the result."
- RFC 2330 §6.3, hlm. 8: "minimize their uncertainties/errors, understand and document the sources
  of uncertainty/error, and quantify the amounts of uncertainty/error."
- RFC 2330 §11.3, hlm. 26: "We will use the term "percentile" to refer to the smallest value of x
  for which F(x) >= a given percentage."
- RFC 5481 §8.4, hlm. 33: "The primary recommendation here is to test using durations that are
  similar in length to the session time of interest."
- G.1010 Gambar 2, hlm. 6: "Interactive (delay <<1 s) | Responsive (delay ~2 s) | Timely
  (delay ~10 s) | Non-critical (delay >>10 s)".
- G.1010 Tabel I.2, hlm. 9 (baris transaksi prioritas tinggi): "Preferred < 2 s / Acceptable < 4 s
  ... Zero" (information loss). Catatan tabel: "In some cases, it may be more appropriate to consider
  these values as response times."
- Y.1541 Tabel 1 catatan umum, hlm. 9: "An evaluation interval of 1 minute is suggested for IPTD,
  IPDV, and IPLR and, in all cases, the interval must be recorded with the observed value."
- Y.1541 §5.3.2, hlm. 11: "the value used must be recorded with the observed value, along with any
  assumptions and confidence intervals."
- Y.1541 §5.3.1, hlm. 10: "a sample with 1000 packets is the minimum necessary to evaluate this
  bound" (untuk kuantil 1−10⁻³).
- H.810 §6.1.7.4, hlm. 36: "high latency typically refers to a maximum of 10 seconds, medium latency
  typically refers to a maximum of 1 second ... However, these latencies are transport-dependent".
- H.810 §6.1.7.5, hlm. 36–37: "better.medium: ... a measured parameter (blood pressure, blood oxygen
  saturation (SpO2), heart rate, etc.) – overall end-to-end latency = ~1 s" dan "best.high: ... both
  physiological driven alarms and equipment issued alarms – overall end-to-end latency = ~10 s".
- H.810 §3.2.62: "store and forward: This is a technique that is often used by a device when the
  connection to a partner may be intermittent."

### Paper persyaratan QoS kesehatan

| Kunci | Judul | Penulis | Thn | Venue | DOI | Status | Berkas |
|---|---|---|---|---|---|---|---|
| skorinkapov_2010 (sudah di bib) | Analysis of QoS Requirements for e-Health Services and Mapping to Evolved Packet System QoS Classes | Skorin-Kapov, Matijasevic | 2010 | Int. J. Telemedicine and Applications | 10.1155/2010/628086 | TL (PMC2952804) | `P/skorinkapov_2010.txt` |
| zhong_2022 (sudah di bib) | Technological Requirements and Challenges in Wireless Body Area Networks for Health Monitoring: A Comprehensive Survey | Zhong dkk. | 2022 | Sensors 22(9):3539 | 10.3390/s22093539 | TL (PMC9105253) | `P/zhong_2022.txt` |

- Skorin-Kapov Tabel 1: "Tele-monitoring | Low | No | No | Yes" (kolom throughput, small delay,
  small jitter, sensitivity to context).
- Skorin-Kapov Tabel 3: "Electrocardiogram (ECG) | 1–20 kbps | approx. 1 s | Zero".
- Skorin-Kapov Tabel 4: "Real-time tele-monitoring ... <300 ms E2E one-way for hard real-time ECG
  (certain applications may tolerate <1 s E2E for ECG) | Zero" dan "Non-real-time tele-monitoring
  ... Not Available (N.A.) | Zero".
- Zhong Tabel 3: "ECG | 72 kb/s | <6 | Star | <3 s | <250 ms | <10–10 | <10% | >1 week" (kolom
  Setup Time, P2PLatency, BER). Ini kebutuhan teknis aplikasi BAN, bukan E2E ke server.

### Paper benchmark MQTT / IoT kesehatan

| Kunci | Judul | Penulis | Thn | Venue | DOI | Scopus ID | Status | Berkas |
|---|---|---|---|---|---|---|---|---|
| adochiei_2025 | HL7 FHIR-Based Open-Source Framework for Real-Time Biomedical Signal Acquisition and IoMT Interoperability | Adochiei F.C. dkk. | 2025 | Applied Sciences 15(23):12803 | 10.3390/app152312803 | 105024758728 | TL (HTML; isi Tabel 3 tidak terambil) | `P/adochiei_2025.txt` |
| kim_2026 | A Comparative Performance Study of Parallel MQTT and RS485 Communication Architectures for High-Frequency IoT Sensing | Kim H.J. dkk. | 2026 | Electronics 15(4):760 | 10.3390/electronics15040760 | 105031409367 | TL (HTML) | `P/kim_2026.txt` |
| lima_2025 | Evaluation of MQTT Bridge Architectures in a Cross-Organizational Context | Lima, Oyetoyan, Heldal, Hasselbring | 2025 | arXiv:2501.14890 (preprint) | – | – | TL | `P/lima_2025.pdf` |
| silva_2021 | A Performance Analysis of Internet of Things Networking Protocols: Evaluating MQTT, CoAP, OPC UA | da Silva, Carvalho, Soares, Sofia | 2021 | Applied Sciences 11(11):4879 | 10.3390/app11114879 | – | TL (HTML) | `P/silva_2021.txt` |
| reiher_2022 | Enabling Connectivity for Automated Mobility: A Novel MQTT-based Interface Evaluated in a 5G Case Study on Edge-Cloud Lidar Object Detection | Reiher, Lampe, Woopen dkk. | 2022 | ICECCME 2022 (arXiv:2209.03630) | – | – | TL (§IV) | `P/reiher_2022.pdf` |
| saif_2022 | An Experimental Investigation of Tuning QUIC-Based Publish-Subscribe Architectures in IoT | Saif, Matrawy | 2022 | arXiv:2208.11178 (draft 2023) | – | – | TL (§VII) | `P/saif_2022.pdf` |
| escobedo_2026 (sudah di bib) | IoTHolter: An IoT Platform for Continuous Three-Lead ECG Monitoring Using Cellular Connectivity | Escobedo-Carranza dkk. | 2026 | IoT 7(3):65 | 10.3390/iot7030065 | – | TL | `laporan/pustaka/escobedo_2026.pdf` |
| dasilva_2027 | Performance and Resilience Evaluation of a Hybrid Edge–Cloud IoT System Across Connected, Offline, and Reconnection Scenarios | da Silva L.F.A., Costa P.R.S.A., Schepke C. | 2027 | LNCS | 10.1007/978-3-032-30488-9_40 | 105044214888 | ABS | – |
| dearaujo_2026 | Reconfigurable ESP32-Based IoMT Architecture with End-to-End Latency Analysis over Wi-Fi with 5G Backhaul | De Araujo L.C. dkk. | 2026 | IEEE MetroInd4.0&IoT 2026 | 10.1109/MetroInd4.0IoT69397.2026.11653168 | 105048839388 | JDL (paywall, preprint tidak ditemukan) | – |
| gaspar_2026 | The Price of Reliability: Stress-Testing MQTT in Practical IoT Communications | Gaspar L.M. dkk. | 2026 | IEEE IoT Magazine | 10.1109/MIOT.2026.3681190 | 105038632755 | JDL (paywall) | – |

Kutipan kunci:

- Adochiei §3.4: "Timestamps were instrumented at four conceptual measurement points ... (i) at the
  ESP32 publisher, (ii) upon broker reception, (iii) at InfluxDB write completion, and (iv) at data
  ingestion by Grafana ... The reported end-to-end latency excludes visualization-rendering time."
  / "no statistically meaningful confidence interval estimation or latency distribution analysis
  could be performed in this prototype."
- Adochiei §3.4.1: "Both ESP32 nodes were synchronized to a local NTP server (chrony on Ubuntu
  22.04, update interval 60 s), which maintained a drift of approximately ±5 ms over 60 s windows."
  §3.4.2: "a quantitative performance assessment was conducted across 10 consecutive acquisition
  cycles (60 s each). Key parameters ... were recorded and averaged."
- Kim 2026 Tabel 3 (konfigurasi klien): "QoS 1 ... mqtt_timeout 5 s Timeout for PUBACK or connection
  negotiation ... ntp_sync_interval 30 min". Tabel 8: "End-to-End Latency: Time elapsed from data
  generation at a sensor node to successful reception at the subscriber". Tabel 10: "Timestamp
  difference between sensor publish time and subscriber receive time | Clock synchronized via NTP".
  Tabel 11: rata-rata 98 ms, maksimum 210 ms, success rate 99,2%. §4.4.3: "The subscriber timestamp
  is recorded immediately upon message reception and before database insertion".
  Catatan: konfigurasi Kim (QoS 1, timeout PUBACK 5 s) **identik** dengan milik kami, jadi paper ini
  pembanding yang paling dekat.
- Lima 2025 §III-A, hlm. 4: "The end-to-end latency was measured by finding the difference between
  the time message was published by the gateway and the time the message was received by the
  subscriber". §III-B, hlm. 5: "Another (virtual) host machine ... was used to run the load driver
  and the subscriber to ensure the accuracy of the end-to-end delay measurements" / "Each benchmark
  parameter experiment was repeated 10 times" / "The ID was used to calculate the number of
  duplicated messages which could happen for the executions of the benchmark for QoS level 1".
- Silva 2021 §5: "all of the experiments have been repeated 10 times, and the values provided in
  this report correspond to the Average (AVG), Standard Deviation (STDEV), Maximum (MAX), Minimum
  (MIN), Median (MED), and Confidence Interval (IC)." Publisher di laptop, subscriber di Raspberry
  Pi, sinkronisasi jam tidak disebut (TTC = t2 − t1 dari dua mesin).
- Reiher 2022 §IV-B, hlm. 5: "while we set up the vehicle computer to synchronize its clock with
  the edge-cloud, the two clocks are not guaranteed to be synchronized exactly. Due to possible clock
  offsets, timestamps from vehicle and cloud cannot be compared directly". §IV-D, hlm. 6: "Our main
  performance-indicating metric is the mean of all measured latencies of a single 60 s experiment.
  Additionally, we also compute minimum, maximum, and median latency as well as the corrected
  standard deviation (jitter)."
- Saif 2022 §VII-A: "NetEm [25] was leveraged to emulate realistic resource-constrained IoT network
  conditions." Pengujian loss: "NetEm rules were applied to drop outgoing packets on the client
  interface according to a uniform distribution ... ranged from 0 to 6%".
- Escobedo 2026 §3.2, hlm. 11: ESP32 lewat WiFi "resulting in 42 lost packets after transmitting
  approximately 3 million packets, corresponding to a loss rate of 0.001%". Hlm. 12: "packet loss
  increases when the cellular signal strength fluctuates significantly". Hlm. 15: "a comprehensive
  evaluation of end-to-end latency, jitter, buffering delay ... will be addressed in future work".
- da Silva 2027 (abstrak): "evaluating the behavior of the edge node across three connectivity
  states: fully connected to the cloud, operating autonomously during disconnection, and during the
  reconnection phase with backlog synchronization ... quantitative analysis of throughput,
  end-to-end latency, resource consumption, and backlog draining time across progressively
  escalating load levels."
- Dokumentasi Docker, `docker container pause` (docs.docker.com/reference/cli/docker/container/pause/):
  pada Linux memakai freezer cgroup, "the process is unaware, and unable to capture, that it is being
  suspended, and subsequently resumed."

Sumber lokal lain yang diperiksa: `resilient_edge_cloud.pdf` (Boluda-Prieto 2026) berisi tinjauan
PRISMA dan stress test Kubernetes, tanpa protokol pemadaman tautan yang bisa dibandingkan.
`yaacoub_2020.pdf` membahas DTN dengan tunda harian, bukan metodologi ukur. `tipparaju_2021.pdf`
membahas loss BLE dengan mekanisme re-request; teks PDF-nya rusak saat diekstrak, jadi metodenya
tidak dikutip.

Tidak ditemukan / tidak terverifikasi:
- IEEE 11073-00101-2008 (pedoman RF wireless untuk perangkat medis, DOI 10.1109/IEEESTD.2008.4736537):
  paywall dan berstatus withdrawn/inactive. Tabel latensinya tidak dibaca.
- Sevin & Bayilmis (IAJIT 2021, "Table 1" kategori ISO/IEEE 11073) disebut hasil pencarian memuat
  tabel kelas latensi 11073, tetapi server-nya 503, jadi tidak dibaca dan tidak dikutip.
- "Rule of three" (Hanley & Lippman-Hand 1983) dan Clopper–Pearson 1934 tidak dibaca. Angka CI di
  atas dihitung sendiri dengan metode eksak Clopper–Pearson (inversi binomial), bukan dikutip.

---

## 3. Celah terpenting (urut dari paling berisiko di sidang)

1. **Definisi latensi tidak konsisten di buku dan berbeda dengan yang diukur.** Bab 3
   (tab:pengujian-pipeline) menulis "waktu dari akuisisi hingga pembaruan dashboard" dengan cara
   "waktu tampil di ThingsBoard", dan teks Bab 3 menulis "latensi rata-rata". Yang diukur adalah
   R-peak → baris tersedia di **REST API** (render dashboard tidak termasuk), lalu dinilai pada
   **median**. Penguji mudah menanyakan "rata-ratanya berapa?" dan "kenapa bukan sampai layar?".
   Perbaikannya murah: definisikan metrik persis seperti Adochiei §3.4 (render dikecualikan),
   laporkan rata-rata ± SD, min, maks di samping median (RFC 6703 §3.1 dan §5.2), dan pakai RFC 6703
   untuk membenarkan median.
2. **Uji resiliensi berbeda dengan rencana dan hanya sekali.** Rencana Bab 3 adalah "putus WiFi
   paksa"; yang dijalankan adalah `docker pause` broker 24 s, satu kali. Pause hanya membekukan
   proses, sedangkan tautan WiFi dan TCP tetap hidup, jadi jalur reconnect WiFi belum pernah diuji.
   Literatur memisahkan keadaan offline dan reconnect serta memvariasikan beban/backlog (da Silva
   2027). Minimal: satu uji AP mati dengan ≥ 3 ulangan dan durasi bertingkat. Bila tidak sempat,
   nyatakan sebagai keterbatasan.
3. **Ketidakpastian pengukuran latensi tidak dilaporkan.** RFC 7679 §3.7 dan §3.8.3 serta RFC 7680
   §2.8.3 (MUST) meminta derajat sinkronisasi dan galat kalibrasi dilaporkan. Komponen yang ada:
   sebaran offset 5 sampel, kemungkinan bias ±50 ms dari loop tidur alat ukur, skew sepanjang
   ulangan (offset hanya diukur di awal), dan resolusi polling ≈ 100 ms + durasi REST. Selain itu,
   istilah "batas bawah" di skrip secara teknis bukan batas bawah. Cukup satu paragraf dan satu baris
   tabel "ketidakpastian ±X ms". Target 2 s tidak terancam karena selisih median ke target ±900 ms.
4. **Ukuran sampel latensi kecil untuk ekor, dan tanpa CI.** n ±200–290 detak per ulangan membuat
   CI p95 lebar (n = 201: statistik urutan ke-185 s.d. ke-198), dan ini menjelaskan p95 yang
   berayun 1.404–3.304 ms. Tanpa ukur ulang: laporkan per-interval 1 menit (Y.1541 §5.3.2) dan CI
   persentil. Untuk PDSR, posisi kita justru kuat: CI Clopper–Pearson gabungan 99,02–99,97%.
5. **Klaim deduplikasi melingkar dan rujukan anggaran latensi kurang tepat.** "0 ts ganda di
   ThingsBoard" selalu 0 karena upsert per ts, jadi buktinya harus diambil di sisi broker/subscriber
   (Lima 2025 memakai ID pesan). Untuk anggaran latensi, Zhong 2022 (<250 ms) adalah latensi tautan
   BAN, bukan E2E. Rujukan yang lebih kuat untuk 2 s adalah G.1010 (Responsive ~2 s; Tabel I.2
   preferred < 2 s, acceptable < 4 s) dan H.810 §6.1.7.5 (parameter terukur ~1 s, alarm ~10 s). Angka
   Skorin-Kapov (<300 ms / <1 s) berlaku untuk gelombang ECG real-time gawat darurat, sedangkan
   telemonitoring non-real-time diberi "N.A.". Jelaskan bahwa yang dikirim adalah label per detak.
