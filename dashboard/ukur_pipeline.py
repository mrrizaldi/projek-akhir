#!/usr/bin/env python3
"""Ukur dua target bab3.tex Tabel 'Rencana pengukuran pada pengujian pipeline':

  1. Latensi end-to-end <= 2 detik  (akuisisi -> tampil di dashboard)
  2. PDSR >= 95%                    (paket ber-PUBACK / total paket)

Latensi diukur dengan MENJEJALI REST ThingsBoard: begitu sebuah ts baru terlihat,
latensi = (waktu laptop melihatnya) - (ts perangkat). ts perangkat adalah waktu
KEJADIAN beat (dihitung dari indeks sampel), jadi angka ini mencakup seluruh
rantai: deteksi -> inferensi -> antre -> MQTT -> rule engine -> tersedia di API.

Batas ketelitian yang jujur:
  - periode polling (~100 ms) masuk sebagai bias KE ATAS; latensi sebenarnya
    lebih kecil atau sama. Dilaporkan juga latensi minimum sebagai batas bawah.
  - jam board (SNTP pool.ntp.org) vs jam laptop: dua-duanya NTP, selisih puluhan
    ms. Kalau hasilnya negatif, itu tanda skew dan dilaporkan apa adanya.

PDSR diambil dari pencacah firmware lewat serial ('s'), bukan ditebak dari data.
"""
import json, re, statistics, sys, threading, time, urllib.request
import serial

HOST, DEVICE = "http://localhost:8080", "esp32s3-ekg-01"
DURASI = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0

# Dijalankan dari folder dashboard/ dengan board tersambung dan broker hidup:
#   python3 ukur_pipeline.py 150
# Skrip menyalakan replay + melewati gerbang kalibrasi lewat serial, jadi tidak
# butuh elektroda. Butuh pyserial (ada di model/requirements.txt).


def rest(path, body=None, token=None):
    req = urllib.request.Request(HOST + path,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json",
                 **({"X-Authorization": "Bearer " + token} if token else {})},
        method="POST" if body else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


jwt = rest("/api/auth/login", {"username": "tenant@thingsboard.org", "password": "tenant"})["token"]
dev_id = rest(f"/api/tenant/devices?deviceName={DEVICE}", token=jwt)["id"]["id"]

# --- serial: hidupkan replay + lewati stabilisasi, lalu ambil status di akhir ---
s = serial.Serial(); s.port, s.baudrate, s.timeout = "/dev/ttyACM0", 115200, 0.2
s.dtr = s.rts = False
s.open()
baris = []
henti = threading.Event()


def pembaca():
    while not henti.is_set():
        b = s.readline()
        if b:
            baris.append(b.decode("utf-8", "replace").rstrip())


threading.Thread(target=pembaca, daemon=True).start()
print("== boot + WiFi ==")
time.sleep(14)
for c in ("k", "y"):            # k = lewati stabilisasi, y = replay ON
    s.write(c.encode()); s.flush(); time.sleep(1.5)
print(f"== mengukur {DURASI:g} detik ==")

# --- polling latensi ---
terlihat, lat_bawah, lat_atas, rest_ms = set(), [], [], []
t0 = time.time()
while time.time() - t0 < DURASI:
    sebelum = int(time.time() * 1000)
    kini = sebelum
    try:
        rows = rest(f"/api/plugins/telemetry/DEVICE/{dev_id}/values/timeseries"
                    f"?keys=bpm&startTs={kini-20000}&endTs={kini+5000}&limit=500"
                    "&useStrictDataTypes=true", token=jwt).get("bpm", [])
    except Exception as e:
        print("  REST gagal:", e); time.sleep(0.5); continue
    sesudah = int(time.time() * 1000)
    rest_ms.append(sesudah - sebelum)
    # Baris ini terlihat di suatu titik antara `sebelum` dan `sesudah`. Memakai
    # `sesudah` membebankan lambatnya REST ke sistem; memakai `sebelum` memberi
    # batas BAWAH yang bebas dari itu. Dilaporkan dua-duanya.
    for r in rows:
        if r["ts"] not in terlihat:
            terlihat.add(r["ts"])
            lat_bawah.append(sebelum - r["ts"])
            lat_atas.append(sesudah - r["ts"])
    time.sleep(0.1)

s.write(b"s"); s.flush(); time.sleep(2.5)
henti.set(); time.sleep(0.3); s.close()

# --- hasil ---
print(f"\n{'='*66}\nLATENSI END-TO-END (akuisisi -> tersedia di API ThingsBoard)")
def p95(v):
    v = sorted(v)
    return v[int(0.95 * (len(v) - 1))]

if lat_bawah:
    lo, hi = sorted(lat_bawah), sorted(lat_atas)
    print(f"  n                       : {len(lo)} beat")
    print(f"  REST polling (alat ukur): median {statistics.median(rest_ms):.0f} ms, "
          f"maks {max(rest_ms)} ms  <- bias, bukan sistem")
    print(f"  {'':22}   {'batas BAWAH':>14} {'batas ATAS':>14}")
    print(f"  minimum               : {lo[0]:>11} ms {hi[0]:>11} ms")
    print(f"  median                : {statistics.median(lo):>11.0f} ms {statistics.median(hi):>11.0f} ms")
    print(f"  p95                   : {p95(lo):>11} ms {p95(hi):>11} ms")
    print(f"  maksimum              : {lo[-1]:>11} ms {hi[-1]:>11} ms")
    vonis = 'LULUS' if statistics.median(lo) <= 2000 else 'GAGAL'
    print(f"  target bab3 <= 2000 ms : median batas bawah -> {vonis}")
else:
    print("  TIDAK ADA DATA")

print(f"\nPDSR (dari pencacah firmware)")
st = [b for b in baris if "paket" in b and "PDSR" in b]
for b in st:
    print("  " + b.strip())
m = re.search(r"paket (\d+)/(\d+) PDSR ([\d.]+)%", " ".join(st))
if m:
    ack, kirim, pdsr = int(m.group(1)), int(m.group(2)), float(m.group(3))
    print(f"  paket ber-PUBACK   : {ack} / {kirim}")
    print(f"  PDSR               : {pdsr:.1f}%")
    print(f"  target bab3        : >= 95%  ->  {'LULUS' if pdsr >= 95 else 'GAGAL'}")
for b in baris:
    if "backlog:" in b or "kualitas:" in b or "calibrating" in b:
        print("  [serial] " + b.strip())
