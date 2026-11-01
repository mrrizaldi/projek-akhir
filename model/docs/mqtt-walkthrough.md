# HW-6 — publikasi MQTT: dari beat di alat sampai baris di dashboard

> **Ruang lingkup:** publikasi hasil klasifikasi per beat dari ESP32-S3 ke ThingsBoard CE lewat MQTT QoS 1, beserta gerbang kualitas, backlog, dan prosedur uji tanpa elektroda.
> **Kode terkait:** `firmware/src/ecg_mqtt.cpp`, `firmware/include/ecg_mqtt.h`, `firmware/src/main.cpp` (`nilai_fase()`, `publikasi()`), `firmware/test/test_mqtt/`, `dashboard/`
> **Prasyarat:** [`firmware-walkthrough.md`](firmware-walkthrough.md) §5b–5c, [`akuisisi-walkthrough.md`](akuisisi-walkthrough.md) §2

Kondisi: terverifikasi di board (N16R8, 19 Sep 2026). Seluruh mekanisme
`bab3.tex` §Pipeline Edge-to-Cloud yang Resilien terpasang, dan **6 dari 6 target
Tabel Rencana Pengukuran terukur** — 5 lulus, 1 lulus di median tapi tidak stabil
di p95 (§7c). `pio test -e native` 23/23, `pio test -e esp32-s3` 16/16, dan
telemetri mendarat di ThingsBoard lewat WiFi. Uji resiliensi lulus: broker
dibekukan 24 detik, deret waktu di dashboard **tidak berlubang** (jeda maksimum
911 ms). Angka lengkap di §7, bug yang hanya muncul di hardware di §7b.

---

## 1. Peta besar

```
        ┌──────────── SUMBER SINYAL (menu Sumber sinyal) ──────────┐
        │  replay acuan  : sim_counts[] dari golden_raw (rec 208)  │
        │  replay rekaman: /rekam/NNN.csv dimuat ke PSRAM          │
        │  sensor (ADC)  : adc1_get_raw() — AD8232, elektroda      │
        └──────────────────────────┬───────────────────────────────┘
                                   │ ISR 360 Hz → antrean 256
                                   v
   bandpass → Pan-Tompkins → selaraskan R → window+z-score → fitur RR
                                   │  (ecg_live_push)
                                   v
                        inferensi INT8 (TFLM)  →  p
                                   │
                                   v
                      ┌──── publikasi(): GERBANG ────┐
                      │ ayun_bersih_1s >= AMBANG_AYUN │
                      │ && !beat.sinyal_hilang        │
                      └──────────────┬────────────────┘
                                     v
        ring backlog 27.000 beat di PSRAM, cadangan 64 (ecg_mqtt_antre_isi)
                                     │
                                     v   ecg_mqtt_layani(), tiap loop()
                      PUBLISH QoS 1 ──► broker ──► PUBACK
                                     │                  │
                          batch <=50 │       geser ring SETELAH PUBACK
                                     v
                          ThingsBoard CE: ts_kv → widget
```

Satu kalimat: **beat yang lolos gerbang kualitas masuk ring; ring dikuras ke
broker; ring baru digeser setelah PUBACK.** Gerbang pada diagram adalah gerbang
per detak; di depannya, setiap sesi harus lulus gerbang masuk berupa fase
kalibrasi (§3.1).

---

## 2. Komponen yang dipakai ulang (jangan dibangun ulang)

| Bagian | Letak |
|---|---|
| Sumber sinyal dummy | `akuisisi.cpp` `rp_data` / `sim_counts[]`, menu Sumber sinyal atau toggle `'y'` ([firmware §5c](firmware-walkthrough.md)) |
| Broker + rule engine + dashboard | `dashboard/` (ThingsBoard CE) |
| Kontrak payload (7 field, QoS 1, topic) | `dashboard/README.md`, `bab3.tex` |
| Referensi kawat MQTT yang terbukti | `dashboard/smoke_test.py` |
| Penilai kualitas sinyal | `gerbang.cpp` `gerbang_nilai_kualitas()`, `AMBANG_AYUN` |

Modul MQTT **tidak menduplikasi satu pun** dari daftar itu. Yang ditambahkan
hanya klien MQTT, ring backlog, dan gerbangnya.

---

## 3. Fungsi per fungsi

### 3.1 Dua gerbang: fase kalibrasi, lalu kontak elektroda

Penilaian kontak berjalan tiap detik di `nilai_kontak()` (dipanggil
`gerbang_nilai_kualitas()` sesudah jendela 1 detik), fase kalibrasi dinilai per
detak di `gerbang_nilai_fase()`:

```
kontak (tiap detik)   LO+ = LO- = 0 sepanjang detik itu (diabaikan saat replay)
                      dan ayun_bersih >= AMBANG_AYUN (60)
                      dan dengung50 <= AMBANG_DENGUNG (500)
KALIBRASI -> BAIK     kontak bertahan >= PEMANASAN_MS (60 detik, dihitung sejak
                      kontak terakhir terbentuk, bukan sejak boot)
                      dan RR 300-1500 ms dengan |dRR| <= 200 ms tenang 30 detik
                      dan kontak saat itu
```

Durasi pemanasan berasal dari tiga sesi rekaman ±15 menit (21–22 Okt 2026):
ayunan bersih ≥ 60 sejak detik 0 dan RR tenang 30 detik tercapai di detik 30
pada ketiganya; 60 detik = dua kali waktu lulus terukur. Timer 10 menit sejak
sesi mulai tidak dipakai karena tidak didukung data dan membuat bip detak
senyap 10 menit walau sinyal sudah baik. Kontak kehilangan salah satu syarat →
hitungan pemanasan mulai lagi dari nol saat kontak kembali.

Selama `calibrating` **CNN tidak dijalankan** (bab3: *"inferensi CNN belum
dijalankan"*), tidak ada yang dipublikasikan, dan LED menyala biru. Detektor
tetap jalan — RR-nya justru yang dipakai menilai kelayakan. Serial mencetak
baris `calibrating | RR=… dRR=… | tenang …/30 s | ayun … | dengung … | lepas … |
kontak …/60 s` tiap 5 detik.

Sesudah fase pemantauan dimulai, fase berganti antara `good` dan `poor` tiap
detik menurut kontak (LO±, ayunan, dengung), tanpa menunggu detak dan tanpa
mengulang pemanasan; serial mencetak `kualitas: good -> poor (lepas …, ayun …,
dengung …)` dan sebaliknya. Ayunan saja tidak cukup: pada sesi 22 Okt 2026 pagi
ayunan tetap ≥ 1.400 dan RR 97–100% wajar selama dengung melonjak sampai 2.800
dan LO mencatat elektroda lepas 41–62% per berkas. Ambang dengung 500 berada di
antara nilai sesi bersih (median per menit ≤ 370) dan lonjakan kontak buruk
(≥ 790).

> **Penting: kriteria RR itu gerbang MASUK, bukan gerbang per detak.** Sesudah fase
> pemantauan mulai, `dRR` TIDAK lagi dibatasi. Menegakkan `dRR <= 200 ms`
> terus-menerus akan membungkam justru aritmia yang ingin dideteksi — beat
> ventrikular memang datang dengan `dRR` besar. `bab3.tex` juga menuliskannya
> sebagai syarat *"layak untuk fase pemantauan"*, sekali saja.

Gerbang publikasi per detak:

```c
if (!ecg_mqtt_aktif()) return;
if (fase != FASE_BAIK)  { beat_ditahan++; return; }
if (beat.sinyal_hilang) { beat_ditahan++; return; }
```

**Dua gerbang, dua mekanisme independen.** Ayunan mengukur amplitudo, RR mengukur
kelayakan ritme. Beat karangan tanpa elektroda gagal di dua-duanya sekaligus:
ayunan ~27 counts (< 60) DAN RR 0,208 s (< 300 ms). Redundansi ini disengaja, dan
senada dengan pelajaran `lepas 0%`: satu indikator bisa berbohong, dua indikator
yang salah bersamaan jauh lebih jarang.

### 3.1b Kenapa replay harus melewati gerbang kalibrasi

`golden_raw` adalah **record 208**, penuh beat ventrikular; `dRR`-nya terukur
−0,364 s dan +0,478 s. Kriteria *"dRR ≤ 200 ms selama 30 detik"* **tidak akan
pernah terpenuhi** — dan memang tidak seharusnya: kriteria itu untuk subjek
**sehat** yang duduk diam, sementara sinyal uji kita sengaja aritmik.

Dua hal itu tidak bisa dipenuhi bersamaan, jadi yang mengalah gerbangnya, dengan
pengumuman. Bypass itu **diturunkan dari sumber sinyal**, bukan disimpan sebagai
flag:

```c
if ((lewati_kalibrasi || replay || (hangat && rr_tenang)) && q.kontak)
    fase = FASE_BAIK;
```

`replay` bernilai benar untuk kedua sumber replay, acuan maupun rekaman
(`akuisisi_replay()` = sumber bukan ADC). Selama replay, gerbang waktu dan RR
dilewati dan serial mencetak `GERBANG DILEWATI (replay)` saat fase berpindah.
Kembali ke Sensor (ADC), lewat menu Sumber sinyal atau `y` kedua, memanggil
`gerbang_mulai_sesi()`, sehingga sinyal tubuh kembali ke `calibrating` dan
harus memenuhi gerbang penuh (kontak 60 detik + RR tenang 30 detik).
Tidak ada keadaan tersisa dari replay yang bisa membuka gerbang untuk sinyal
tubuh.

Toggle `k` (menu Kalibrasi → Lewati (bench)) adalah override manual untuk
bench, terpisah dari replay: `k` ON melewati syarat pemanasan dan RR untuk
jalur ADC (`GERBANG DILEWATI (bench)`), tetapi tidak melewati kontak (LO±,
ayunan, dengung). Tanpa elektroda LO bernilai 1, jadi `k` tidak lagi membuka
gerbang untuk derau ADC; uji meja tanpa elektroda memakai replay. `k` OFF memanggil `gerbang_mulai_sesi()` sehingga fase kembali ke `calibrating` dengan gerbang
penuh, termasuk bila fase sudah `good`. Status `k` terbaca di baris status
(`lewati 0/1`, §4.4).

Uji gerbang yang berlaku (replay, kontak buruk, kontak baik) ada di §3.1c.

Buzzer mengikuti fase: bip detak senyap selama `calibrating`, dan bunyi panjang
600 ms menandai kalibrasi mulai (boot, ganti sumber, Kalibrasi → Mulai ulang,
`k` OFF) dan selesai
(masuk `good`).

**Digerbangi kualitas sinyal, bukan ada-tidaknya beat.** Alasannya terukur dan
sudah masuk daftar jebakan `../CLAUDE.md`:

> Tanpa elektroda, alat mengarang aritmia: **~2 beat/detik, 57% "ARITMIA"**.
> Ambang Pan-Tompkins adaptif relatif terhadap sinyal yang ada, jadi "tidak ada
> sinyal" bukan kondisi yang ia kenali — derau 15 counts pun punya puncak.

Kalau publikasi digerbangi beat, elektroda lepas = banjir alarm palsu ke broker.
`beat_ditahan` dihitung supaya penahanan itu terlihat di `'s'`, bukan jadi data
yang hilang diam-diam.

Baris ketiga menolak beat yang keluar lewat `ECG_LIVE_TIMEOUT` (asistol /
elektroda lepas). `ecg_live.h` sudah menyuruhnya: *"Pemanggil sebaiknya
menaikkan alarm 'sinyal hilang' TERPISAH dari klasifikasi aritmia, supaya tidak
mengotori metrik."*

### 3.1c Uji gerbang kontak (22 Okt 2026)

Kondisi uji: board N16R8, firmware dengan gerbang kontak, elektroda MLII.

1. Replay acuan, tanpa elektroda (serial, USB):

   ```
   >>> y   replay ON (golden_raw)
           kualitas: calibrating -> good (GERBANG DILEWATI (replay), kontak 2 s, RR tenang 3 s, ayun 2434, dengung 19)
   >>> s   status: ... replay=1 | kualitas good | ... | LO 1 1 | ... ayun 2836
   >>> y   replay OFF (ADC)
   >>> s   status: ... replay=0 | kualitas calibrating | ... | LO 1 1 | mentah 0..9 ayun 1
   ```

   LO diabaikan selama replay; kembali ke ADC tanpa elektroda tetap
   `calibrating`.
2. Elektroda dengan kontak buruk, board dicolok USB laptop (serial, ±3,5
   menit): setiap baris `calibrating` menunjukkan `lepas 1` dan `kontak 0/60 s`;
   ayunan naik pelan 11 → 395, dengung sampai 486, RR acak 0,20–1,10 s. Gerbang
   tidak lulus.
3. Elektroda menempel baik, catu powerbank (diamati subjek di layar, tanpa log
   serial): LED biru lalu bip panjang dan LED hijau sekitar 60 detik sesudah
   elektroda menempel, bip detak mulai; klip kabel kuning dicabut ±10 detik →
   LED oranye; dipasang lagi → hijau tanpa menunggu 60 detik.

Belum diverifikasi dengan log serial: langkah 3 (transisi `calibrating -> good
(gerbang penuh, kontak 60 s ...)` dan `good -> poor (lepas 1 ...)` tercetak).

### 3.2 `confidence` — keyakinan pada KEPUTUSAN, bukan `p` mentah

```c
t.confidence = aritmia ? p : 1.0f - p;
```

`p = 0,02` untuk beat normal artinya alat **sangat yakin**. Mengirim 0,02 apa
adanya membuat widget menampilkan "keyakinan 2%" persis saat alat paling yakin.

### 3.3 `ecg_mqtt_payload()` — murni, karena itu bisa diuji

```c
size_t ecg_mqtt_payload(char *buf, size_t n, const ecg_mqtt_beat_t *b, size_t nb,
                        uint64_t ts_base_ms);
```

`nb == 1` → objek tunggal; `nb > 1` → array. Dua bentuk itu bukan gaya, itu
kontrak ThingsBoard (`dashboard/README.md`: real-time vs batch flush).

**`ts` tiap beat = `ts_base_ms + beat.ms`.** Ini inti dari klaim resiliensi:
beat yang tertahan 40 detik di backlog tetap membawa waktu **kejadian**-nya.

`beat.ms` diisi `publikasi()` dari indeks sampel puncak R, bukan dari
`millis()` saat beat keluar:

```c
t.ms = t_sesi_ms + (uint32_t)((uint64_t)beat.r_abs * 1000ULL / ECG_FS);
```

Deteksi berjalan tiap 1 detik atas ring 4 detik, sehingga beberapa beat keluar
bergerombol dalam milidetik yang sama; `millis()` saat keluar membuat dashboard
menampilkan denyut berdesakan lalu menganggur (terukur: jeda antar-`ts` minimum
28 ms, padahal RR terpendek ~200 ms). Konsekuensinya, sampel yang hilang di
antrean menggeser `ts` sebesar durasi yang hilang — karena itu `sampel hilang`
ikut dilaporkan di baris `s`.
Kalau `ts` diambil saat kirim, seluruh backlog menumpuk di satu detik dan
grafik dashboard berbohong — dan yang lebih buruk, uji dedup `smoke_test.py`
tetap lulus, jadi kesalahannya tidak akan ketahuan dari situ.

Buffer kurang → return **0**, bukan payload terpotong. JSON separuh diterima
broker sebagai sampah tanpa error yang terlihat di board. Diuji:
`test_payload_buffer_kurang`.

### 3.4 Ring backlog — dan kenapa `intip` terpisah dari `buang`

```c
size_t ecg_mqtt_antre_intip(ecg_mqtt_beat_t *keluar, size_t maks);
void   ecg_mqtt_antre_buang(size_t n);
```

Dipisah supaya **pointer baca hanya bergeser setelah PUBACK**:

```c
if (w && publish(buf, w)) {
    ecg_mqtt_antre_buang(n);          // HANYA setelah PUBACK
    terkirim += n;
}
```

Kalau digabung jadi satu `ambil()`, beat hilang setiap kali PUBACK tidak datang
— dan QoS 1 jadi hiasan. `dashboard/README.md` menulis syarat ini sebagai
kontrak: *"geser read pointer ring buffer hanya setelah PUBACK"*.

Kapasitas ring **27.000 beat** (`ECG_MQTT_ANTRE_TARGET`), dialokasikan di PSRAM
saat `setup()` lalu dipasang lewat `ecg_mqtt_antre_pasang()`; satu entri 40 byte,
total ~1,05 MB dari 8 MB. Bila alokasi PSRAM gagal, ring turun ke cadangan
statis 64 beat (`ECG_MQTT_ANTRE_MIN`) dan serial mencetak peringatan. Bagian
murni ini tidak tahu soal PSRAM, sehingga uji native cukup memasang array statis.

Ring penuh → **buang yang TERTUA**. Alat monitoring lebih butuh menit terakhir
daripada menit pertama saat koneksi baru pulih. Yang terbuang dicatat di
`ecg_mqtt_antre_hilang()`, tidak disembunyikan.

### 3.5 Klien MQTT — empat paket, tanpa library

`CONNECT` / `PUBLISH QoS1` / `PUBACK` / `PINGREQ`. Ditulis di atas `WiFiClient`.

Kawatnya **bukan tebakan**: `dashboard/smoke_test.py` sudah bicara ke broker
yang sama dengan byte yang sama (`0x10` CONNECT flags `0x80` username-saja,
`0x32` PUBLISH QoS1, cek `0x40` PUBACK + pid). Port C-nya menyalin itu.

### 3.6 Jam — `configTzTime()` + `ts_base_ms`

SNTP dimulai dengan `configTzTime("WIB-7", "pool.ntp.org", "time.google.com")`.
Zona WIB hanya memengaruhi `localtime_r()` untuk jam di layar monitor;
`gettimeofday()` tetap memberi epoch UTC, jadi `ts` tiap beat tidak berubah.
`configTime(0, 0, …)` tidak dipakai karena memaksa TZ ke UTC setiap kali WiFi
tersambung ulang.

```c
struct timeval tv;
gettimeofday(&tv, NULL);
const uint64_t kini_ms = (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)(tv.tv_usec / 1000);
ts_base_ms = kini_ms - (uint64_t)millis();
```

Epoch ms saat `millis() == 0`, dihitung sekali begitu SNTP masuk
(`tv_sec ≥ 1.700.000.000`). `gettimeofday()` dipakai, bukan `time()`: resolusi
`time()` satu detik dan pembulatannya menjadi galat sistematis di setiap `ts`
(§7b bug 6). Setelah `ts_base_ms` diketahui, tiap beat cukup menyimpan waktu
relatif `ms` (4 byte) dan waktunya direkonstruksi saat payload disusun. Tanpa jam benar, `ecg_mqtt_status()` melapor `tunggu-jam` dan
backlog **menunggu** — sengaja tidak mengirim dengan ts salah.

---

## 4. Cara memakai — toggling lengkap

### 4.1 Sekali di awal: kredensial dan broker

```bash
cd dashboard && docker compose up -d      # broker + dashboard
python3 smoke_test.py                     # cetak: device ... token=XXXX
cd ../model && make broker-info           # SSID laptop, IP LAN, port 1883, saran entri

cd ../firmware
cp include/wifi_secrets.example.h include/wifi_secrets.h
$EDITOR include/wifi_secrets.h            # isi WIFI_DAFTAR dan BROKER_DAFTAR
```

`include/wifi_secrets.h` ada di `.gitignore` — kredensial tidak pernah masuk git.
**Tanpa file itu firmware tetap ter-build dan tetap jalan**, MQTT-nya saja yang
nonaktif dengan satu baris peringatan saat boot (`#if __has_include`).

Daftar berbentuk array: `WIFI_DAFTAR {ssid, sandi}` dan
`BROKER_DAFTAR {nama tampil, host, port, token}`. `host` adalah **alamat IP**
laptop di jaringan WiFi board, bukan `localhost` (board mencarinya di jaringan,
bukan di dirinya sendiri) dan bukan nama host (firmware tidak me-resolve nama).
Akibatnya **board dan laptop harus terhubung ke SSID yang sama**; `make
broker-info` mencetak SSID laptop untuk dicocokkan. Entri aktif dipilih lewat
serial `w<n>` / `b<n>` (indeks mulai 0) dan disimpan di NVS; entri 0 dipakai
bila belum pernah memilih. Makro tunggal lama (`WIFI_SSID`, `WIFI_PASS`,
`TB_HOST`, `TB_PORT`, `TB_TOKEN`) tetap diterima sebagai daftar satu entri.
Format lengkap, server selain laptop, dan troubleshooting SSID/IP/port:
[`firmware/README.md`](../../firmware/README.md) bagian Konfigurasi jaringan dan
broker.

### 4.2 Toggle serial

| Tombol | Arti | Keluaran |
|---|---|---|
| **`y`** | **sumber sinyal: ADC ⇄ replay acuan** (menu Sumber sinyal memilih ketiga sumber, termasuk replay rekaman) | `replay ON (golden_raw)` / `replay OFF (ADC)` |
| **`m`** | **publikasi MQTT: on ⇄ off** | `mqtt ON` / `mqtt OFF` |
| **`k`** | **lewati gerbang kalibrasi** (bench saja); OFF memulai sesi baru dengan gerbang penuh | `lewati gerbang kalibrasi ON` / `OFF` |
| `q` | toggle laporan kualitas tiap detik | `kualitas \| mentah … ayun … BERSIH …` |
| `s` | status sesaat (termasuk MQTT) | lihat di bawah |
| `r` | rekam mentah ke LittleFS `/rekam/NNN.csv` (setara tombol B3) | `REKAM mulai` / `SIMPAN … -> /rekam/NNN.csv` |
| `d` / `d<n>` | dump rekaman terakhir / nomor `<n>` lewat serial | `---MULAI--- … ---SELESAI---` |
| `w` / `b` | daftar WiFi / broker; `w<n>` / `b<n>` memilih entri | `wifi *0 …` / `broker *0 nama  IP:port` |

Dua toggle itu **ortogonal**, dan itu memang tujuannya:

| | `m` OFF | `m` ON |
|---|---|---|
| **`y` ON (replay)** | uji pipeline & daya, offline | **uji MQTT tanpa elektroda** (uji meja) |
| **`y` OFF (ADC)** | akuisisi & rekam, offline | operasi normal |

### 4.3 Demo tanpa elektroda — prosedur

Prasyarat: broker hidup (`docker compose up -d` di `dashboard/`) dan
`wifi_secrets.h` terisi (§4.1). Buka serial dengan `pio device monitor` dari
`firmware/`.

| Langkah | Aksi | Hasil yang diharapkan di serial |
|---|---|---|
| 1 | boot, tunggu | `mqtt: WiFi "…" -> 192.168.x.x:1883`, lalu `mqtt: jam tersinkron, epoch_ms …` dan `mqtt tersambung, backlog 0 beat` |
| 2 | tekan `m` (bila belum ON) | `mqtt ON` |
| 3 | tekan `y`, atau menu **Sumber sinyal → REPLAY 208** | `replay ON (golden_raw)`; pojok kanan atas layar `RP 208` kuning |
| 4 | tunggu ~7 detik | `kualitas: calibrating -> good (GERBANG DILEWATI (replay), …)`, lalu baris `beat …` mulai keluar |
| 5 | tekan `s` | `mqtt online \| terkirim N \| backlog 0/27000 …` |
| 6 | buka `http://localhost:8080` | telemetri masuk di dashboard |

**Kenapa replay lolos gerbang kontak tanpa perlakuan khusus di jalur publikasi:** ayunannya
~2700 counts, jauh di atas `AMBANG_AYUN` 60, dengungnya ±10–19, dan status LO± diabaikan selama replay. Jadi dummy dan sinyal tubuh
melewati **gerbang per detak dan jalur publikasi yang sama persis** — tidak ada
cabang `if (dummy)` di `publikasi()` maupun `ecg_mqtt.cpp`. Satu-satunya
perlakuan replay adalah melewati gerbang kalibrasi selama replay menyala, dan
itu diumumkan di serial (§3.1b). Cabang khusus dummy di jalur publikasi berarti yang didemokan bukan yang
dipakai.

### 4.4 Membaca baris status

Format (tiga baris; angka contoh, `<…>` = isian):

```
status: rekam=0 n=0 | replay=1 | kualitas good | beat 44 (12 aritmia, 3 ditahan) | antrean 2 |
        sampel hilang 0 (tick 0) | LO 1 1 | mentah 1204..3550 ayun 2701 clipping 0
        mqtt online | terkirim 41 | backlog 0/27000 | hilang 0 | gagal 0 |
        paket <ack>/<kirim> PDSR <x>% | tunda alat rata <ms> ms maks <ms> ms |
        RTT maks <ms> ms (lambat <n>) | RSSI <dBm> dBm | epoch_ms <epoch>
        INA219 I=<mA> mA V=<V> V P=<mW> mW | bisu 0 | beku 0 | lewati 0 | daya -1 |
        sumber acuan 0 | menu 0 | jeda 0
```

| Kolom | Artinya |
|---|---|
| `kualitas` | fase: `calibrating`, `good`, atau `poor` |
| `ditahan` | beat yang sengaja TIDAK dipublikasi (fase bukan `good` / beat timeout) |
| `backlog` | beat menunggu di ring / kapasitas ring — tidak nol = broker sedang tak terjangkau |
| `hilang` | ring penuh, beat tertua dibuang — outage melebihi kapasitas ring (27.000 beat ≈ 4–7 jam; 64 beat bila PSRAM gagal) |
| `gagal` | PUBACK tidak datang / tidak cocok, atau paket tidak habis ditulis |
| `paket … PDSR` | paket ber-PUBACK / paket PUBLISH; PDSR dihitung per paket, bukan per beat |
| `tunda alat` | dari beat TERJADI sampai paketnya masuk ring (§7c) |
| `RTT maks (lambat)` | RTT PUBACK terburuk, dan berapa kali > 1 detik |
| `RSSI` | kuat sinyal WiFi |
| `epoch_ms` | jam board; dipakai alat ukur di laptop untuk mengoreksi selisih jam |
| `lewati` | override `k` aktif (1) atau tidak (0); replay tidak mengubahnya |
| `daya` | anak tangga ukur daya `p0`–`p5`, atau `-1` = operasi normal ([`firmware-walkthrough.md`](firmware-walkthrough.md) §5d) |
| `sumber` | `adc`, `acuan` (golden 208), atau `rekaman` diikuti nomor berkas (0 bila bukan replay rekaman) |
| `menu` | menu di layar sedang terbuka (1) atau tidak (0) |
| `jeda` | rekaman sedang dijeda (1) atau tidak (0); `rekam=1` selama sesi rekaman terbuka, termasuk saat dijeda |

`mqtt` bisa berisi: `mati` (toggle `m` off atau tanpa kredensial), `no-wifi`,
`no-broker`, `tunggu-jam` (SNTP belum masuk), `online`.

**Akuntansi kehilangan:** `beat_total − ditahan = terkirim + backlog + hilang`.
Identitas itu yang membuat uji resiliensi bisa diukur, dan ia cuma berlaku
karena replay **deterministik** — 11 beat per putaran 6,67 detik, sudah terukur
di board (`arsip/2026-09-18-robustness-changelog.md` §207).

---

## 5. Keputusan yang diambil, beserta alternatif yang ditolak

| Keputusan | Dipilih | Ditolak, dan kenapa |
|---|---|---|
| Letak data dummy | **sumber sinyal (ADC)** | *dummy di publisher* — melewati bandpass, detektor, dan inferensi. Yang teruji cuma JSON + WiFi, padahal klaim PA ini "klasifikasi di edge". Makin dekat titik injeksi ke tepi sistem, makin banyak kode nyata ikut teruji |
| Bentuk toggle | **runtime (`y`, `m`)** | *compile-time `#ifdef DUMMY`* — dua binary, dan yang didemokan bukan yang di-flash untuk operasi |
| Klien MQTT | **ditulis sendiri, 4 paket** | *PubSubClient* — gate point CLAUDE.md (jangan tambah dependency untuk yang beberapa baris selesai); kawatnya sudah terbukti di `smoke_test.py`; preseden `ina219.cpp` yang juga tanpa library. **Bila dibutuhkan QoS 2, retained, atau subscribe, pindah ke PubSubClient — itu batas atas pilihan ini** |
| Gerbang publikasi | **ayunan sinyal** | *ada-tidaknya beat* — derau pun menghasilkan beat, 57% "ARITMIA" |
| `ts` | **waktu kejadian** (`base + millis`) | *waktu kirim* — backlog menumpuk di satu detik, dan `smoke_test.py` tetap lulus jadi tidak ketahuan |
| Geser ring | **setelah PUBACK** | *saat kirim* — QoS 1 jadi hiasan |
| Ring penuh | **buang tertua** | *tolak yang baru* — alat monitoring butuh menit terakhir |
| Kredensial | **header ter-`.gitignore`** | *hardcode* (bocor) / *`build_flags` di `platformio.ini`* (ikut ter-commit) |
| Nama field | **snake_case** | *camelCase* yang disarankan docs ThingsBoard — proposal terlanjur menulis snake_case dan tetap jalan normal |

---

## 6. Yang sengaja TIDAK dilakukan

- **TLS (port 8883).** Broker jalan di jaringan lokal untuk PoC. Memindahkan
  broker ke VPS memerlukan TLS dan sertifikat di flash — di luar cakupan PoC.
- **Subscribe / RPC dari dashboard ke alat.** Tidak ada perintah yang perlu
  dikirim ke alat. `ecg_mqtt.cpp` cuma publish.
- **Backlog tahan reboot.** Ring ada di PSRAM, yang volatil — sesuai asumsi
  `bab3.tex` (wearable diisi daya rutin; kehilangan daya di luar cakupan).
  LittleFS sudah dipakai untuk rekaman mentah, jadi jalurnya tersedia bila
  dibutuhkan.
- **`ecg_sim.h` rekaman lebih panjang/beragam.** Ditambahkan **hanya bila**
  dashboard membutuhkannya ([`arsip/2026-09-18-robustness-changelog.md`](arsip/2026-09-18-robustness-changelog.md)
  Task 0); replay `golden_raw` mencukupi untuk seluruh pengukuran di §7.
- **Batch adaptif / kompresi payload.** 1 beat/detik × ~300 B tidak mendekati
  batas apa pun.

---

## 7. Angka nyata

Kondisi uji: board N16R8, 19 Sep 2026, replay ON (tanpa elektroda), broker
ThingsBoard CE di laptop pada jaringan WiFi rumah. Angka build dari `pio run`
pada kode saat ini dengan `wifi_secrets.h` terisi.

| Hal | Build inti (tanpa MQTT) | Firmware utama dengan MQTT |
|---|---|---|
| `pio test -e native` | 17/17 | **23/23** (+6 uji payload & ring) |
| `pio test -e esp32-s3` | 16/16 | **16/16** — inferensi tidak tersentuh |
| RAM (build) | 21,2% | **37,0%** (121.336 B) |
| Flash (build) | 6,6% | **13,5%** (887.873 B) |
| Ukuran payload 1 beat | — | ~330 B; batch 50 beat ~15 KB |
| Backlog | — | **27.000 beat** di PSRAM (1.054 KB, 40 B/entri) ≈ 4–7 jam |

**Catatan pengukuran build: jangan memakai angka RAM/Flash yang diukur tanpa
`wifi_secrets.h`.**
Tanpa file itu `WIFI_SSID` adalah `""`, `strlen("")` dilipat jadi konstanta oleh
kompilator, `WiFi.begin()` jadi kode mati, dan **seluruh tumpukan WiFi tidak
ikut di-link**: 26,4% / 8,0% — selisih 358 KB flash dari angka sebenarnya. Dua
build itu terlihat sama-sama "SUCCESS" dan bedanya tidak diumumkan di mana pun.

### Jalur data, terukur

| Hal | Angka |
|---|---|
| Laju beat replay | **1,60 beat/detik** (45 beat / 28,2 s) vs 1,58 terukur HW-7 |
| Baris mendarat di ThingsBoard | 171 baris / 103,2 detik, **0 ts duplikat** |
| Jeda antar-`ts` | **433–911 ms** — tidak bergerombol, tidak berlubang |
| Gerbang kualitas, tanpa elektroda | `beat 19 (7 aritmia, 19 ditahan)` → **terkirim 0** |
| Gerbang kualitas, replay | `ditahan 0` → **terkirim 100%** |
| `sampel hilang` selama semua uji | **0** |

Akuntansi `beat − ditahan = terkirim + backlog + hilang` cocok di setiap
pengambilan status. Contoh: `beat 148 = terkirim 147 + backlog 1 + hilang 0`.

### Uji ulang dengan gerbang kontak (22 Okt 2026)

Kondisi uji: board N16R8 dicolok USB laptop, firmware gerbang kontak dan
perekam sesi PSRAM, WiFi `HIFIAIR_9351` (RSSI −31 dBm), broker ThingsBoard CE
4.2.1.1 di laptop yang sama (`192.168.1.199:1883`), sumber replay acuan
(`y`), ±5,5 menit (18.40–18.45 WIB).

| Hal | Angka |
|---|---|
| Beat / terkirim / backlog / hilang / gagal | 536 / 536 / 0 / 0 / 0 |
| Paket di-ACK | 518 / 518, PDSR **100,0%** |
| Tunda di alat (deteksi → kirim) | rata-rata 849 ms, maksimum 1.402 ms |
| RTT PUBACK maksimum | 3.329 ms (9 kejadian lambat) |
| `sampel hilang` | 0 (tick 0) |

Dashboard *Pemantauan EKG* menampilkan BPM, klasifikasi, confidence, kualitas
sinyal, grafik BPM dan RR, serta riwayat per detak secara langsung; tangkapan
layar `artifacts/metrics/mqtt/20261022-1845-dashboard-replay.png`.

### Uji resiliensi — `docker pause` 24 detik

```
[30,2s] mqtt online    | terkirim  20 | backlog  1 | hilang 0 | gagal 0
[32,3s] === docker pause ===
[54,0s] mqtt no-broker | terkirim  28 | backlog 33 | hilang 0 | gagal 1
[56,1s] === docker unpause ===
[58,2s] mqtt tersambung, backlog 43 beat
[82,8s] mqtt online    | terkirim 109 | backlog  0 | hilang 0 | gagal 1
```

`pause` dipilih, bukan `stop`: container membeku sehingga CONNECT tidak dijawab
sama sekali (SYN/paket ditelan), dan itu menguji batas waktu connect **dan**
CONNACK — lebih ganas daripada `stop` yang membalas RST seketika. Bonusnya
praktis: `unpause` pulih dalam 2 detik, sementara `docker start` butuh ~55 detik
menunggu ThingsBoard boot.

Yang membuktikan klaim di proposal: 24 detik outage, tapi **jeda maksimum di
deret waktu dashboard cuma 911 ms** — backlog mengisi lubangnya dengan `ts`
asli, bukan `ts` saat kirim.

Latensi per detak (26,6 ms) tidak berubah: publikasi cuma menyalin struct ke
ring; jaringan diurus `ecg_mqtt_layani()` di luar jalur beat.

---

## 7b. Enam bug yang HANYA muncul di hardware

Keenamnya lolos `pio test -e native` dan lolos build. Bagian ini menjelaskan
kenapa "kode jadi" bukan "kode benar"; setiap bug ditulis sebagai gejala, sebab,
perbaikan yang berlaku di kode, dan hasil terukur.

### (1) Menunggu PUBACK memblokir loop → 4.493 sampel hilang

Gejala: `antrean 255/256` (penuh), `sampel hilang 4493`, `PUBACK timeout`
berulang. Sebab: `publish()` menunggu PUBACK di tempat dengan batas 3 detik,
di dalam loop yang sedang menguras antrean ADC. Antrean 256 sampel @360 Hz =
**711 ms**, jadi satu timeout saja sudah melahap antrean penuh — dan interval RR
rusak, yaitu persis kegagalan yang arsitektur HW-4 dibangun untuk mencegah.

Perbaikan: PUBACK dipungut **lintas iterasi** `loop()` (`menunggu_ack` +
`pungut_masuk()`, timeout 5 detik), bukan di dalam satu panggilan. Tambahan: `ecg_mqtt_layani()`
dibatasi tiap 20 ms — dipanggil 360×/detik, `WiFi.status()` + `time()` sebanyak
itu ikut memakan anggaran 2.778 µs/sampel.

Hasil: 4.493 → **146**.

### (2) `sock.connect()` masih blocking → 2.788 sampel hilang saat broker booting

Gejala: `sampel hilang` melompat ke 2.788 tepat saat `docker start`. Sebab:
selama broker MATI, connect gagal seketika (RST) — tidak ada kerugian. Tapi saat
broker sedang **booting**, portnya terbuka dan paketnya ditelan, jadi
`sock.connect()` menggantung ~7,7 detik.

Perbaikan: `sock.connect(ip, port, 300)` — batas 300 ms, di bawah kedalaman
antrean 711 ms. Dan `IPAddress`, bukan hostname: resolusi DNS adalah panggilan
blocking **terpisah** yang tidak ikut dibatasi argumen timeout itu.

Hasil: 2.788 → **290**. Sisa 290 berasal dari menunggu CONNACK di tempat
(1.500 ms). CONNACK karena itu juga dipungut lintas iterasi (`pungut_connack()`,
batas 2 detik), sehingga tidak ada satu pun panggilan yang menunggu jaringan di
tempat.

Hasil akhir: **0**.

### (3) `sock.write()` tanpa memeriksa nilai kembalian → paket terpotong

Gejala paling menipu: `PUBACK timeout` berulang **padahal broker sehat**, dan
**hanya** saat backlog dikuras. Log broker bersih — nol petunjuk di
sisi sana. Sebab: paket MQTT ditulis 6 kali terpisah dan nilai kembaliannya
diabaikan. Saat payload besar (16 beat ≈ 4,8 KB) socket tidak menampung
semuanya; write pendek meninggalkan paket MQTT **terpotong**, broker menunggu
sisa yang tidak pernah datang, dan tidak pernah mengirim PUBACK.

Jadi gejalanya menyamar sebagai "broker lambat", padahal pengirimnya yang
berbohong soal berapa byte yang berhasil ditulis.

Perbaikan yang berlaku di kode:

- Satu paket dirakit di **satu buffer** (`paket_buf`): payload ditulis langsung
  di belakang ruang header, lalu header MQTT ditempel mundur tepat sebelum
  payload. Dua buffer terpisah (payload + paket) memakan 32 KB RAM internal untuk
  batch 50; satu buffer memakan setengahnya.
- `kirim_sampai_habis()` mengulang `sock.write()` untuk sisa yang belum
  tertulis, dengan batas 200 ms — di bawah kedalaman antrean ADC 711 ms. Tidak
  habis dalam batas itu → `gagal++` dan `putus()`, backlog tidak digeser.
- Karena penulisan bertahap ini, `ECG_MQTT_BATCH_N` = **50** (~15 KB), batas
  bawah target `bab3.tex` 50–100 rekaman per paket.

Hasil (uji resiliensi §7): `gagal` berhenti di 1 — satu-satunya yang sah, saat
broker memang dibekukan.

### (4) PINGRESP tidak pernah dibaca → aliran baca desync

Firmware mengirim PINGREQ tiap 30 detik; broker membalas PINGRESP (2 byte,
`0xD0 0x00`) yang tidak pernah dibaca. Dua byte nyasar itu mengendap di socket
lalu terbaca sebagai dua byte pertama "PUBACK" berikutnya — aliran baca desync
permanen sampai reconnect.

Perbaikan: `pungut_masuk()` membaca header 2 byte, mengurus PUBACK, dan **membuang
isi paket lain secara utuh** supaya byte berikutnya tetap jatuh di batas paket.

Bug ini nyata dan perbaikannya benar, tetapi **bukan satu-satunya penyebab**
`PUBACK timeout`: dengan perbaikan ini saja, `gagal` masih 4 dalam 150 detik.
Penyebab sisanya adalah bug (5), yang teridentifikasi lewat pencacah RTT.

### (5) Nagle menahan segmen kecil → PUBACK terlambat 1–4,8 detik

Pencacah RTT PUBACK (`rtt_maks`, `rtt_lambat`) dan cetakan keadaan socket saat
timeout menunjuk satu arah:

```
mqtt: PUBACK lambat 1266 ms (1 beat)      <- berulang di ~1.250 ms
mqtt: PUBACK lambat 1278 ms (1 beat)
mqtt: PUBACK lambat 4235 ms (1 beat)
mqtt: PUBACK timeout, 1 beat terbang, 0 byte menunggu dibaca
                                          ^^^ socket KOSONG = bukan desync
27 kejadian >1 detik dalam 130 detik
```

`0 byte menunggu dibaca` menutup hipotesis desync: broker memang belum menjawab.
Dan nilai yang **berulang di ~1.250 ms** adalah tanda khas algoritma Nagle
berpasangan dengan delayed-ACK: segmen kecil (payload 1 beat ~330 B) ditahan
sampai ACK segmen sebelumnya datang.

Perbaikan: `sock.setNoDelay(true)` sesudah connect — satu baris.

| | tanpa `setNoDelay` | dengan `setNoDelay` |
|---|---|---|
| `gagal` / 150 dtk | 4 | **0** |
| latensi p95 | 13.259 ms | **3.402 ms** |
| latensi maksimum | 19.926 ms | **4.903 ms** |
| PDSR | 96,7% | **99,5%** |

### (6) `time()` beresolusi 1 detik → galat sistematis 1 detik di SETIAP `ts`

Bug ini tidak merusak sistem, tetapi **merusak semua pengukuran latensi**.

`sinkron_jam()` yang memakai `time(NULL)` mewarisi resolusi detik. Pembulatannya
masuk ke `ts_base_ms` dan dari situ ke **setiap** `ts` yang dikirim — galat sistematis
0–1.000 ms per boot, tetap sepanjang sesi. Gejalanya: latensi minimum bergeser
934 / 1.045 / 1.286 / 1.347 ms antar-boot tanpa ada yang berubah di sistem, dan
satu kali melompat seragam ke 3.437 ms di semua persentil sekaligus.

**Pergeseran yang seragam di semua persentil itu tanda selisih jam, bukan
latensi.** Latensi nyata menggeser ekor lebih banyak daripada median.

Perbaikan: `sinkron_jam()` memakai `gettimeofday()` (resolusi µs), dan alat ukur
di laptop (`dashboard/ukur_pipeline.py`) mengukur selisih jam kedua sisi lewat
`epoch_ms` di baris status lalu mengoreksinya. Selisih jam terukur −70 sampai
−414 ms, dan angkanya berubah drastis:

| | `time()` | `gettimeofday()` + koreksi jam |
|---|---|---|
| latensi minimum | 1.286 ms | **429 ms** |
| latensi median | 1.907 ms | **939–1.108 ms** |

**Pola yang sama di keenamnya:** gagal tanpa error, dan gejalanya menunjuk ke
tempat yang salah (broker, bukan firmware). Senada dengan jebakan op `MEAN` di
TFLM dan `float` di ISR ([`firmware-walkthrough.md`](firmware-walkthrough.md)
§5, §5b) — pola "salah tanpa berisik".

Pelajaran kedua, khusus dari (4) vs (5): **dua bug dengan gejala identik bisa
hidup berdampingan.** Memperbaiki yang satu tidak menghilangkan gejalanya, dan
satu-satunya jalan keluar adalah memasang pencacah sampai gejalanya punya angka —
bukan menalar mana yang "paling mungkin".

---

## 7c. Target `bab3.tex` Tabel *Rencana pengukuran pada pengujian pipeline*

Diukur dengan `dashboard/ukur_pipeline.py` (replay ON, tanpa elektroda): Run 1
dan 2 `ukur_pipeline.py 180` pada 19 Sep 2026, Run 3 `ukur_pipeline.py 120` pada
23 Okt 2026 07.22–07.24 dengan firmware akhir (gerbang kontak, perekam sesi
PSRAM), WiFi `HIFIAIR_9351` RSSI −40 dBm. Latensi = batas bawah keluaran skrip.

| Aspek | Target | Run 1 | Run 2 | Run 3 | Vonis |
|---|---|---|---|---|---|
| PDSR | ≥ 95% | **100,0%** (292/292) | **99,2%** (253/255) | **100,0%** (188/188) | lulus |
| Latensi median | ≤ 2 dtk | **939 ms** | **1.108 ms** | **1.014 ms** | lulus |
| Latensi p95 | ≤ 2 dtk | **1.404 ms** (lulus) | 3.304 ms (tidak lulus) | 2.251 ms (tidak lulus) | tidak stabil |
| Latensi minimum | — | 429 ms | 527 ms | 495 ms | — |
| Bufer lokal | ±27.000 | 27.000 terpasang | idem | idem | lulus |
| Integritas saat putus | tanpa kehilangan | `hilang 0` | `hilang 0` | `hilang 0` | lulus |
| Pemulihan bufer | ≤ 60 dtk | ~24 dtk (43 beat) | idem | idem | lulus |
| Deduplikasi cloud | duplikat dikenali | 0 ts duplikat | idem | 0 (267 baris unik REST = terkirim 267) | lulus |

Run 3 juga menghasilkan tangkapan dashboard yang dipakai buku
(`dashboard/preview.png` = `model/artifacts/metrics/mqtt/20261023-0724-dashboard-replay.png`,
Playwright, jendela Realtime 2 menit).

### Latensi dipecah

`tunda alat` (beat TERJADI → beat masuk ring di `publikasi()`; dengan backlog
kosong, ring dikuras dalam ≤ 20 ms) dicacah firmware dan **stabil di 7
pengukuran**: 887 / 880 / 879 / 878 / 876 / 870 / **869 ms**
(maks 1.353 ms).

```
latensi median        ~1.000 ms
  sisi alat              869 ms   <- kadens deteksi
  jaringan + cloud      ~130 ms
```

Sisi alat itu **arsitektural**: `ecg_live.h` menjalankan deteksi tiap
`ECG_LIVE_TIAP` = 1 detik atas ring 4 detik, dan beat baru boleh keluar setelah
`ECG_WIN_POST` = 128 sampel (356 ms) sesudah R. Batas bawah teoretisnya
356–1.356 ms, dan minimum terukur **429 ms** jatuh di rentang itu.

Jadi **89% latensi milik alat, dan itu kadens deteksi, bukan inefisiensi.**
Jaringan + ThingsBoard cuma ~130 ms.

### Broker bukan sumber latensi

ThingsBoard berjalan di laptop yang sama dengan 9 container lain, tetapi broker
tidak lambat. Probe 60 detik (`dashboard/probe_rtt.py`, publish 1/detik dari
laptop ke broker yang SAMA):

```
RTT PUBACK laptop -> broker, n=60
  minimum 0,4 ms   median 1,1 ms   p95 2,5 ms   maksimum 3,5 ms
  > 1000 ms: 0 dari 60
```

Broker menjawab dalam **satu milidetik**. Latensi ~1 detik di luar sisi alat yang
muncul pada pengukuran berbasis `time()` adalah galat jam bug (6); ekor yang
tersisa adalah retransmisi WiFi (di bawah). Pelajarannya: komponen jauh yang
paling sulit diukur juga paling gampang disalahkan — probe langsung lebih murah
daripada dugaan.

### Ekor p95: retransmisi TCP, dan kenapa ia tidak dikejar

RTT PUBACK dari board berkelompok di **1,2 / 2,0 / 4,2 detik** — itu backoff RTO
TCP 1–2–4, tanda segmen hilang lalu dikirim ulang. Bukan broker (lihat atas),
bukan desync (`sock.available()` = 0 byte saat timeout), dan bukan sinyal lemah
(**RSSI −50 dBm**). Sisanya kontensi kanal WiFi rumah.

Efek setelan firmware pada porsi paket ber-RTT > 1 detik:

| Setelan | paket lambat |
|---|---|
| tanpa `setNoDelay` dan tanpa `setSleep(false)` | 23/207 = 11,1% |
| `setNoDelay(true)` (bug 5) | 18/222 = 8,1% |
| `setNoDelay(true)` + `WiFi.setSleep(false)` | 11/217 = 5,1% |
| idem, run 1 / run 2 §7c | 3/292 = **1,0%** / 24/255 = 9,4% |

Angka terakhir itu **berayun 1–9% antar-run** dan itulah kenapa p95 lulus di run
1 dan gagal di run 2. Yang mengayun bukan kode, melainkan kanal.

`WiFi.setSleep(false)` **berongkos daya (~+30 mA)**. Pengukuran daya mode WiFi
harus diambil DENGAN setelan ini, karena itulah konfigurasi firmware utama.

**Keputusan: tidak dikejar lebih jauh.** Satu-satunya tuas firmware yang tersisa
adalah mengizinkan lebih dari satu PUBLISH beredar (pipelining QoS-1), dan itu
menambah pembukuan `pid → jumlah beat` plus aturan "geser ring hanya setelah ack
tertua" ke implementasi QoS-1 yang sederhana dan terbukti — ongkos nyata
untuk kejadian 1-dari-20 di jaringan bangku uji. Median lulus di dua run, PDSR
lulus, dan `bab3.tex` menyebut targetnya **indikatif** untuk pengujian yang
**fungsional, bukan klinis**. Kalau laporan butuh p95 yang bersih, ukur di AP
yang tidak padat dan laporkan n run — bukan tambal di firmware.

---

## 8. Cek pemahaman

1. Kenapa `ecg_mqtt_antre_buang()` dipisah dari `ecg_mqtt_antre_intip()`, dan
   apa yang rusak kalau digabung?
2. Alat kehilangan WiFi 2 menit lalu pulih. Berapa beat sampai di broker, dan
   `ts`-nya menunjukkan waktu apa? Bagaimana jawabannya berubah bila alokasi
   PSRAM gagal saat boot? (petunjuk: 27.000 vs 64 beat)
3. Elektroda dilepas tapi `m` masih ON. Berapa banyak yang terkirim ke broker,
   dan angka mana di baris `'s'` yang bergerak?
4. Kenapa replay tidak butuh cabang khusus untuk lolos gerbang kualitas?
5. `ts_base_ms` masih 0 (SNTP belum masuk) tapi beat terus keluar. Ke mana
   beat-beat itu pergi, dan apa yang terjadi saat jam akhirnya tersinkron?
6. Kenapa `ecg_mqtt_payload()` mengembalikan 0 alih-alih memotong payload?

---

## 9. Skrip & berkas pendukung

| Berkas | Peran |
|---|---|
| `firmware/include/ecg_mqtt.h` | kontrak; bagian murni vs jaringan dipisah `#ifdef ARDUINO` |
| `firmware/src/ecg_mqtt.cpp` | payload + ring (murni), WiFi + MQTT (board) |
| `firmware/test/test_mqtt/test_mqtt.cpp` | 6 uji: format tunggal, batch array, buffer kurang, FIFO, ring penuh buang tertua, pasang kapasitas |
| `firmware/include/wifi_secrets.example.h` | templat kredensial |
| `dashboard/smoke_test.py` | referensi kawat MQTT + uji dedup `ts_kv` |
| `dashboard/ukur_pipeline.py` | pengukur target §7c (PDSR, latensi dengan koreksi jam, dedup) |
| `dashboard/probe_rtt.py` | probe RTT PUBACK laptop → broker |
| `dashboard/README.md` | kontrak field, dan kenapa ThingsBoard |

## 10. Cakupan dan batas pengujian

- **Daya.** Tangga ukur daya `p0`–`p5` mencakup mode WiFi/MQTT (`p5`, dengan
  `WiFi.setSleep(false)` aktif seperti saat pengujian pipeline). Angkanya belum
  ada karena INA219 belum berada di jalur arus alat
  ([`firmware-walkthrough.md`](firmware-walkthrough.md) §5d).
- **Sinyal tubuh.** Seluruh angka di dokumen ini diukur dengan replay. Dua hal
  hanya dapat diuji dengan sinyal tubuh: (a) apakah `AMBANG_AYUN` 60 memisahkan
  elektroda lepas dari sinyal tubuh lemah — replay ~2700 counts terlalu jauh di
  atas ambang; (b) **gerbang kalibrasi penuh** (kontak 60 detik + RR tenang 30
  detik) beserta publikasinya, yang dilewati replay karena record 208 memang
  aritmik (§3.1b). Gerbang kontak sendiri sudah diuji dengan sinyal tubuh tanpa
  MQTT (§3.1c).
- **Latensi p95.** Ekor p95 bergantung pada kanal WiFi (§7c). Pengukuran ulang
  yang bersih memerlukan AP yang tidak padat dan laporan n run. Kadens deteksi
  firmware utama adalah bawaan `ECG_LIVE_TIAP` = `ECG_FS` (1 detik), sehingga
  bip dan gelombang di TFT tertunda 1,46 detik dari R. Build flag
  `-D ECG_LIVE_TIAP=90` menjalankan deteksi tiap 250 ms (tunda bip 0,7 detik)
  dengan akurasi deteksi DS1 setara (Se 0,9881 vs 0,9867, PPV 0,9870 vs
  0,9880) dan burst deteksi 7,2 ms per putaran (2,9% CPU). Mengubah bawaan
  firmware utama adalah gate point.
- **Dashboard.** Field `ecg_snippet` diterima dan tersimpan di ThingsBoard,
  tetapi `dashboard/dashboard_ekg.json` tidak memiliki widget yang
  menggambarkannya.

Uji fungsional yang sudah tercakup: telemetri mendarat di broker (171 baris,
laju 1,60 beat/detik, sesuai 1,58 beat/detik replay) dan uji resiliensi (jeda
maksimum 911 ms untuk outage 24 detik), §7.
