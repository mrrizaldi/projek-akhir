# dashboard/ — ThingsBoard CE dan pengukuran pipeline

Broker MQTT, rule engine, dan dashboard web dipegang satu platform: **ThingsBoard
Community Edition**. Tidak ada Mosquitto, tidak ada backend tambahan, tidak ada
web app sendiri. Alasannya ada di `bab3.tex` §deduplikasi: klaim "dedup tanpa
komponen tambahan" bergantung pada perilaku `ts_kv` ThingsBoard, sehingga
penggantian broker menggugurkan klaim tersebut.

## Jalankan

```bash
cd dashboard
docker compose up -d            # boot pertama ~2 menit; UI hidup duluan, REST
                                # baru bisa dipakai setelah skema DB terpasang
python3 smoke_test.py           # bikin device + uji jalur telemetri
python3 provision_dashboard.py  # bikin dashboard + tulis dashboard_ekg.json
```

UI di <http://localhost:8080>, login `tenant@thingsboard.org` / `tenant`.

Berhenti: `docker compose stop` (data tetap). Hapus total: `docker compose down -v`.

ThingsBoard di-self-host, bukan memakai `demo.thingsboard.io`, karena registrasi
demo diarahkan ke ThingsBoard Cloud yang retensi telemetrinya dibatasi paket, dan
uji resiliensi membutuhkan pemutusan broker secara terkendali tanpa memutus
koneksi laptop. Pemindahan ke VPS hanya memerlukan penambahan entri broker di
firmware ([`firmware/README.md`](../firmware/README.md) bagian Konfigurasi jaringan
dan broker).

## Kontrak dengan firmware

| Hal | Nilai |
|---|---|
| Host / port | Alamat IP laptop di jaringan WiFi yang sama dengan board, `1883` (plaintext); IP dan SSID laptop dicetak `make broker-info` di `model/` |
| Username MQTT | access token device |
| Password MQTT | kosong |
| Topic | `v1/devices/me/telemetry` |
| Real-time | `{"ts":…, "values":{…}}` |
| Batch flush | `[{"ts":…,"values":{…}}, …]` |
| QoS | 1, geser read pointer ring buffer hanya setelah PUBACK |

Field di dalam `values` ikut Tabel struktur payload di `bab3.tex`
§\ref{subsubsec:payload-json} — `bpm`, `rr_interval_ms`, `label`, `label_str`,
`confidence`, `signal_quality`, `ecg_snippet`.

Catatan: dokumentasi ThingsBoard menyarankan camelCase untuk nama key
(mempermudah skrip Rule Engine). Payload memakai snake_case sesuai Tabel payload
Bab 3 dan berjalan normal; node skrip Rule Engine yang ditulis tangan harus
memperhitungkan perbedaan ini.

## Mengukur target pengujian pipeline

```bash
python3 ukur_pipeline.py 150      # board tersambung, broker hidup
```

Mengukur dua target `bab3.tex` Tabel *Rencana pengukuran pada pengujian pipeline*:
**latensi end-to-end** (akuisisi → tersedia di API) dan **PDSR** (paket ber-PUBACK
/ total paket, diambil dari pencacah firmware lewat serial — bukan ditebak dari
data). Latensi dilaporkan sebagai batas bawah DAN batas atas, karena baris yang
baru terlihat bisa sudah tersedia sebelum panggilan REST dikirim; selisih dua
batas itu = ongkos alat ukurnya sendiri, dan ikut dicetak.

Skrip membaca status (`s`) lalu menyalakan replay (`y`) bila belum aktif; selama
replay, syarat waktu stabil dan RR tenang gerbang kalibrasi dilewati otomatis,
jadi tidak butuh elektroda. Hasil terukur ada di
[`mqtt-walkthrough.md`](../model/docs/mqtt-walkthrough.md) §7c.

`smoke_test.py` menguji
klaim yang paling rapuh: publikasi ulang dengan `ts` identik harus meng-UPSERT
baris, bukan menambah. Bila assert itu gagal, klaim dedup di Bab 3 tidak berlaku.

## Dashboard

`provision_dashboard.py` membangun dashboard "Pemantauan EKG" lewat REST lalu
mengekspor hasilnya ke `dashboard_ekg.json`. Dibangun dengan skrip, bukan diklik
di UI, agar dapat diulang setelah `docker compose down -v` dan agar diff-nya
terlihat di git. Skrip idempoten: dashboard dengan judul sama dihapus lebih dulu.

Tujuh widget, semuanya bawaan ThingsBoard, tidak ada widget custom dan tidak ada
JS yang ditulis tangan: kartu BPM, kartu klasifikasi, kartu kualitas sinyal,
kartu confidence, chart BPM, chart interval R-R, dan tabel riwayat.

Dua jebakan yang ditangani skrip:

- **`typeFullFqn` wajib di-prefix scope**, `"system.time_series_chart"`, bukan
  `"time_series_chart"`. Tanpa prefix, REST tetap menyimpan dashboard dengan
  status 200 dan tidak mengeluh apa pun — yang menolak cuma UI, dan tiap widget
  tampil sebagai "Problem loading widget configuration". Karena itu skrip
  memverifikasi tiap fqn lewat `/api/widgetType?fqn=...` setelah menyimpan;
  itu assert yang menangkap kegagalan yang tidak kelihatan dari REST.
- **`defaultConfig` widget bawaan berisi contoh suhu ruangan.** Kalau `units`,
  `decimals`, dan `settings.icon` tidak ditimpa, BPM tampil sebagai "76 degC"
  dengan ikon termostat. Semua override ada di tabel `WIDGETS`.

BPM dan interval R-R sengaja dipisah jadi dua chart. Digabung dalam satu chart,
BPM (60-100) gepeng menempel di dasar karena RR (600-1000) mendominasi sumbu,
dan konfigurasi sumbu-kanan (`yAxisId`) tidak menempel lewat REST. Dua chart
melakukan auto-scale sendiri tanpa konfigurasi sumbu tambahan.

## Rule chain

Tidak ada. Node **Save Timeseries** di Root Rule Chain bawaan sudah menerima
format array multiple timestamped key-value apa adanya, memakai `ts` tiap
rekaman sebagai event time. Export rule chain baru diperlukan bila ditambahkan
alarm rule (notifikasi dini).

## Multi-pasien (di luar lingkup MVP)

MVP memakai satu device untuk satu pasien. Catatan desain untuk perluasan:

ThingsBoard menyimpan tiap baris `ts_kv` milik **entity**, dan entity-nya adalah
device. Jadi kalau satu alat dipakai bergantian oleh beberapa pasien, identitas
pasien harus ikut pindah bersama datanya. Dua jalan, ongkosnya beda jauh:

- **Pasien = Customer, alat tetap satu device.** Identitas pasien ditulis sebagai
  server-side attribute yang diganti tiap sesi. Nol perubahan firmware, tapi
  histori lama ikut "berpindah" pasien saat attribute diganti — salah untuk
  rekam medis.
- **`patientId` jadi satu field di dalam `values`.** Tiap rekaman membawa
  pemiliknya sendiri, histori tetap benar secara retroaktif, dan rule chain bisa
  memakai node Change Originator untuk memecah ke Asset per pasien tanpa
  menyentuh firmware lagi. Ongkosnya ±10 byte dari ±150 byte per rekaman, artinya
  kapasitas ring buffer PSRAM turun sekitar 7% (±27.000 → ±25.000 rekaman) —
  masih jauh di atas target 4 jam.

Jalan kedua yang dipilih untuk perluasan, dan cukup satu field. Field ini tidak
ada pada MVP karena hanya ada satu pasien dan Tabel payload Bab 3 tidak memuatnya.
