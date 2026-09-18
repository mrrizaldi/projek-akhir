# dashboard/ — export JSON rule chain & widget ThingsBoard CE.

Broker MQTT, rule engine, dan dashboard web dipegang satu platform: **ThingsBoard
Community Edition**. Tidak ada Mosquitto, tidak ada backend tambahan, tidak ada
web app sendiri. Alasannya ada di `bab3.tex` §deduplikasi — klaim "dedup tanpa
komponen tambahan" itu bergantung pada perilaku `ts_kv` ThingsBoard; ganti broker
berarti klaim di proposal ikut gugur.

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

Kenapa self-host dan bukan `demo.thingsboard.io`: registrasi demo sudah
dibelokkan ke ThingsBoard Cloud yang retensi telemetri-nya dibatasi paket, dan
uji resiliensi butuh memutus broker secara terkendali tanpa ikut memutus koneksi
laptop. Pindah ke VPS nanti cuma ganti hostname di firmware.

## Kontrak dengan firmware

| Hal | Nilai |
|---|---|
| Host / port | host laptop, `1883` (plaintext) |
| Username MQTT | access token device |
| Password MQTT | kosong |
| Topic | `v1/devices/me/telemetry` |
| Real-time | `{"ts":…, "values":{…}}` |
| Batch flush | `[{"ts":…,"values":{…}}, …]` |
| QoS | 1, geser read pointer ring buffer hanya setelah PUBACK |

Field di dalam `values` ikut Tabel struktur payload di `bab3.tex`
§\ref{subsubsec:payload-json} — `bpm`, `rr_interval_ms`, `label`, `label_str`,
`confidence`, `signal_quality`, `ecg_snippet`.

Catatan: docs ThingsBoard menyarankan camelCase untuk nama key (mempermudah
skrip Rule Engine). Proposal sudah terlanjur menulis snake_case dan snake_case
tetap jalan normal, jadi dibiarkan. Kalau nanti ada node skrip yang ditulis
tangan, ingat bedanya.

`smoke_test.py` adalah satu-satunya uji di folder ini, dan sengaja menembak
klaim yang paling rapuh: publikasi ulang dengan `ts` identik harus meng-UPSERT
baris, bukan menambah. Kalau assert itu jatuh, kalimat dedup di Bab 3 salah.

## Dashboard

`provision_dashboard.py` membangun dashboard "Pemantauan EKG" lewat REST lalu
mengekspor hasilnya ke `dashboard_ekg.json`. Dibangun dengan skrip, bukan diklik
di UI, supaya bisa diulang setelah `docker compose down -v` dan supaya diff-nya
kelihatan di git. Skrip idempoten: dashboard lama dengan judul sama dihapus dulu.

Tujuh widget, semuanya bawaan ThingsBoard, tidak ada widget custom dan tidak ada
JS yang ditulis tangan: kartu BPM, kartu klasifikasi, kartu kualitas sinyal,
kartu confidence, chart BPM, chart interval R-R, dan tabel riwayat.

Dua jebakan yang sudah kena dan sudah dikunci di skrip:

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
auto-scale sendiri, nol konfigurasi yang bisa salah.

## Rule chain

Tidak ada. Node **Save Timeseries** di Root Rule Chain bawaan sudah menerima
format array multiple timestamped key-value apa adanya, memakai `ts` tiap
rekaman sebagai event time. Folder ini baru akan berisi export JSON begitu ada
alarm rule (notifikasi dini) atau dashboard yang perlu di-versi.

## Multi-pasien (belum dikerjakan)

MVP: satu device, satu pasien. Yang perlu diketahui sebelum itu berubah —

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

Jalan kedua yang benar, dan cuma satu field. Belum ditambahkan karena MVP tidak
memakainya dan Tabel payload di Bab 3 sudah dicetak. Tambahkan saat ada pasien
kedua, bukan sebelumnya.
