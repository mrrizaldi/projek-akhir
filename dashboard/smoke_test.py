#!/usr/bin/env python3
"""Uji jalur ESP32 -> broker -> ts_kv tanpa hardware dan tanpa dependency.

Dijalankan dari folder dashboard/ setelah `docker compose up -d`:

    python3 smoke_test.py

Yang dibuktikan, berurutan:
  1. Device bisa dibuat lewat REST dan token-nya bisa diambil (provisioning).
  2. MQTT CONNECT dengan username = access token, password kosong, diterima.
  3. Payload single record sampai di ts_kv dengan ts milik perangkat, bukan
     waktu kedatangan di server.
  4. Payload batch (array multiple timestamped key-value) diterima node Save
     Timeseries bawaan, tanpa rule chain tambahan.
  5. Publikasi ulang rekaman dengan ts identik meng-UPSERT, bukan menambah
     baris -- ini klaim "deduplikasi implisit" di bab3.tex, dan satu-satunya
     yang tidak bisa dibuktikan dengan membaca dokumentasi.

MQTT-nya ditulis langsung di atas socket (CONNECT/PUBLISH/PUBACK, MQTT 3.1.1).
ponytail: 60 baris socket lebih murah daripada menambah paho-mqtt ke
requirements.txt untuk satu skrip uji. Sekalian jadi referensi paling ringkas
soal urutan paket yang harus ditiru firmware -- terutama menunggu PUBACK
sebelum menggeser read pointer ring buffer.
"""
import json
import socket
import struct
import sys
import time
import urllib.error
import urllib.request

HOST = "localhost"
REST = f"http://{HOST}:8080"
MQTT_PORT = 1883
DEVICE = "esp32s3-ekg-01"
TOPIC = "v1/devices/me/telemetry"


# ---------- REST (stdlib urllib) ----------

def rest(path, body=None, token=None, method=None):
    req = urllib.request.Request(
        REST + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method or ("POST" if body is not None else "GET"),
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def provision():
    """Login sebagai tenant, buat device kalau belum ada, kembalikan (jwt, id, token)."""
    jwt = rest("/api/auth/login",
               {"username": "tenant@thingsboard.org", "password": "tenant"})["token"]
    try:
        dev = rest(f"/api/tenant/devices?deviceName={DEVICE}", token=jwt)
    except urllib.error.HTTPError as e:
        if e.code not in (404, 400):
            raise
        dev = rest("/api/device", {"name": DEVICE, "type": "ecg-monitor"}, token=jwt)
    dev_id = dev["id"]["id"]
    cred = rest(f"/api/device/{dev_id}/credentials", token=jwt)
    return jwt, dev_id, cred["credentialsId"]


def timeseries(jwt, dev_id, key, start_ts, end_ts):
    path = (f"/api/plugins/telemetry/DEVICE/{dev_id}/values/timeseries"
            f"?keys={key}&startTs={start_ts}&endTs={end_ts}&limit=1000&useStrictDataTypes=true")
    return rest(path, token=jwt).get(key, [])


# ---------- MQTT 3.1.1 seperlunya ----------

def _varlen(n):
    out = b""
    while True:
        b, n = n % 128, n // 128
        out += bytes([b | (0x80 if n else 0)])
        if not n:
            return out


class Mqtt:
    """CONNECT + PUBLISH QoS-1 + tunggu PUBACK. Tidak ada yang lain."""

    def __init__(self, host, port, username):
        self.pid = 0
        self.sock = socket.create_connection((host, port), timeout=10)
        cid = b"smoke-test"
        user = username.encode()
        # protocol name+level, connect flags (0x80 = username saja), keepalive 60
        payload = struct.pack("!H", len(cid)) + cid + struct.pack("!H", len(user)) + user
        var = b"\x00\x04MQTT\x04\x80" + struct.pack("!H", 60)
        self.sock.sendall(b"\x10" + _varlen(len(var + payload)) + var + payload)
        ack = self.sock.recv(4)
        if len(ack) < 4 or ack[0] != 0x20 or ack[3] != 0x00:
            raise RuntimeError(f"CONNACK ditolak: {ack!r} (kode {ack[3] if len(ack) > 3 else '?'})")

    def publish(self, topic, payload):
        self.pid = (self.pid % 65535) + 1
        t = topic.encode()
        var = struct.pack("!H", len(t)) + t + struct.pack("!H", self.pid)
        body = var + payload.encode()
        self.sock.sendall(b"\x32" + _varlen(len(body)) + body)   # 0x32 = PUBLISH QoS1
        ack = self.sock.recv(4)
        if len(ack) < 4 or ack[0] != 0x40 or struct.unpack("!H", ack[2:4])[0] != self.pid:
            raise RuntimeError(f"PUBACK tidak cocok: {ack!r}")

    def close(self):
        self.sock.sendall(b"\xe0\x00")   # DISCONNECT
        self.sock.close()


# ---------- payload (field-nya dari bab3.tex Tabel 3.x) ----------

def record(ts, bpm, label):
    return {
        "ts": ts,
        "values": {
            "bpm": bpm,
            "rr_interval_ms": round(60000.0 / bpm, 1),
            "label": label,
            "label_str": "Aritmia" if label else "Normal",
            "confidence": 0.93,
            "signal_quality": "good",
            "ecg_snippet": [2048, 2051, 2049, 2110, 2380, 2100, 2040, 2045],
        },
    }


def main():
    jwt, dev_id, token = provision()
    print(f"device  {DEVICE}  id={dev_id}  token={token}")

    base = int(time.time() * 1000) - 60_000
    m = Mqtt(HOST, MQTT_PORT, token)

    # 1) single record, mode real-time
    m.publish(TOPIC, json.dumps(record(base, 72.0, 0)))

    # 2) batch, mode flush backlog setelah reconnect
    batch = [record(base + 1000 * i, 70.0 + i, i % 2) for i in range(1, 6)]
    m.publish(TOPIC, json.dumps(batch))

    # 3) kirim ULANG record pertama dengan ts identik tapi nilai beda.
    #    Ini yang ditiru QoS-1 saat PUBACK hilang dan batch dikirim ulang.
    m.publish(TOPIC, json.dumps(record(base, 999.0, 1)))
    m.close()

    time.sleep(2)   # ponytail: rule engine async; 2 detik cukup untuk in-memory queue
    rows = timeseries(jwt, dev_id, "bpm", base - 5000, base + 30_000)
    by_ts = {r["ts"]: r["value"] for r in rows}

    assert len(rows) == 6, f"harus 6 baris (1 single + 5 batch), dapat {len(rows)}: {rows}"
    assert len(by_ts) == 6, "ada ts duplikat -- upsert ts_kv TIDAK terjadi"
    assert by_ts[base] == 999.0, (
        f"ts {base} bernilai {by_ts[base]}, harusnya 999.0 (ditimpa publikasi ulang)")
    assert by_ts[base + 5000] == 75.0, "urutan/ts elemen batch tidak dipertahankan"

    print(f"ok      {len(rows)} baris, ts perangkat dipertahankan, ts duplikat ter-upsert")
    print("        klaim dedup implisit bab3.tex terbukti di CE 4.2")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, ConnectionRefusedError, socket.timeout) as e:
        sys.exit(f"gagal menghubungi ThingsBoard di {HOST}: {e}\n"
                 f"sudah `docker compose up -d` dan tunggu ~90 detik?")
