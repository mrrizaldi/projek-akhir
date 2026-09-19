// Salin jadi include/wifi_secrets.h lalu isi. File aslinya di-.gitignore —
// kredensial tidak pernah masuk git.
//
//   cp include/wifi_secrets.example.h include/wifi_secrets.h
//
// TB_TOKEN = access token device ThingsBoard. Dicetak oleh:
//   cd dashboard && python3 smoke_test.py       -> "device ... token=XXXX"
// TB_HOST  = IP laptop yang menjalankan docker compose (bukan "localhost":
// board mencarinya di jaringan, bukan di dirinya sendiri). Cek dgn `ip addr`.
//
// Tanpa file ini firmware tetap ter-build dan tetap jalan — MQTT-nya saja yang
// nonaktif, dengan satu baris peringatan di serial saat boot.
#ifndef WIFI_SECRETS_H
#define WIFI_SECRETS_H

#define WIFI_SSID "nama-wifi"
#define WIFI_PASS "sandi-wifi"
#define TB_HOST   "192.168.1.10"
#define TB_PORT   1883
#define TB_TOKEN  "token-device-thingsboard"

#endif
