// Salin jadi include/wifi_secrets.h lalu isi. File aslinya di-.gitignore —
// kredensial tidak pernah masuk git.
//
//   cp include/wifi_secrets.example.h include/wifi_secrets.h
//
// Dua daftar; entri dipilih lewat serial (w<n>, b<n>) dan pilihannya disimpan
// di NVS. Entri 0 dipakai bila belum pernah memilih.
//
// WIFI_DAFTAR   {"ssid", "sandi"}
// BROKER_DAFTAR {"nama tampil", host, port, token}
//   host  = IP laptop yang menjalankan docker compose (cek `ip addr`), bukan
//           "localhost": board mencarinya di jaringan, bukan di dirinya sendiri.
//   token = access token device ThingsBoard, dicetak oleh
//           cd dashboard && python3 smoke_test.py   -> "device ... token=XXXX"
//
// Format lama satu entri (WIFI_SSID, WIFI_PASS, TB_HOST, TB_PORT, TB_TOKEN)
// masih diterima.
//
// Tanpa file ini firmware tetap ter-build dan tetap jalan — MQTT-nya saja yang
// nonaktif, dengan satu baris peringatan di serial saat boot.
#ifndef WIFI_SECRETS_H
#define WIFI_SECRETS_H

#define WIFI_DAFTAR { \
    {"nama-wifi", "sandi-wifi"}, \
    {"hotspot-hp", "sandi-hotspot"}, \
}

#define BROKER_DAFTAR { \
    {"laptop rumah",  "192.168.1.10", 1883, "token-device-thingsboard"}, \
    {"laptop kampus", "10.0.0.5",     1883, "token-device-thingsboard"}, \
}

#endif
