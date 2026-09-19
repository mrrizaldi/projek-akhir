#!/usr/bin/env python3
"""Ukur RTT PUBACK dari LAPTOP ke broker yang sama, ~1 pesan/detik.

Kalau laptop juga melihat RTT ~1,25 detik, penyebabnya ThingsBoard/beban host —
bukan WiFi, bukan ESP32, bukan klien MQTT kita. Device terpisah supaya telemetri
esp32s3-ekg-01 tidak terkotori.
"""
import json, socket, statistics, struct, sys, time, urllib.request

HOST, DEVICE = "http://localhost:8080", "probe-rtt"

def rest(path, body=None, token=None):
    req = urllib.request.Request(HOST + path,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json",
                 **({"X-Authorization": "Bearer " + token} if token else {})},
        method="POST" if body else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

jwt = rest("/api/auth/login", {"username": "tenant@thingsboard.org", "password": "tenant"})["token"]
try:
    dev = rest(f"/api/tenant/devices?deviceName={DEVICE}", token=jwt)
except urllib.error.HTTPError:
    dev = rest("/api/device", {"name": DEVICE, "type": "probe"}, token=jwt)
token = rest(f"/api/device/{dev['id']['id']}/credentials", token=jwt)["credentialsId"]

def varlen(n):
    out = b""
    while True:
        b, n = n % 128, n // 128
        out += bytes([b | (0x80 if n else 0)])
        if not n:
            return out

sock = socket.create_connection(("127.0.0.1", 1883), timeout=10)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
cid, user = b"probe-rtt", token.encode()
pay = struct.pack("!H", len(cid)) + cid + struct.pack("!H", len(user)) + user
var = b"\x00\x04MQTT\x04\x80" + struct.pack("!H", 60)
sock.sendall(b"\x10" + varlen(len(var + pay)) + var + pay)
assert sock.recv(4)[3] == 0, "CONNACK ditolak"

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
TOPIK = b"v1/devices/me/telemetry"
rtt = []
for i in range(N):
    body = json.dumps({"ts": int(time.time()*1000), "values": {"probe": i}}).encode()
    v = struct.pack("!H", len(TOPIK)) + TOPIK + struct.pack("!H", (i % 65535) + 1)
    t0 = time.time()
    sock.sendall(b"\x32" + varlen(len(v + body)) + v + body)
    ack = sock.recv(4)
    rtt.append((time.time() - t0) * 1000)
    assert ack[0] == 0x40, f"bukan PUBACK: {ack!r}"
    time.sleep(0.6)
sock.sendall(b"\xe0\x00"); sock.close()

r = sorted(rtt)
print(f"RTT PUBACK laptop -> broker, n={len(r)}, payload ~60 B")
print(f"  minimum : {r[0]:7.1f} ms")
print(f"  median  : {statistics.median(r):7.1f} ms")
print(f"  p95     : {r[int(0.95*(len(r)-1))]:7.1f} ms")
print(f"  maksimum: {r[-1]:7.1f} ms")
print(f"  > 1000 ms: {sum(1 for x in r if x > 1000)} dari {len(r)}")
