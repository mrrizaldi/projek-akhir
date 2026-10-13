// Daftar WiFi dan broker dari include/wifi_secrets.h (WIFI_DAFTAR, BROKER_DAFTAR;
// makro tunggal lama WIFI_SSID/TB_HOST diterima sebagai satu entri). Indeks
// pilihan disimpan di NVS (Preferences) sehingga bertahan lintas reboot.
#ifndef KONFIG_H
#define KONFIG_H

// Baca NVS lalu atur target ecg_mqtt. Panggil sebelum ecg_mqtt_mulai().
void konfig_mulai(void);

int konfig_wifi_n(void);
const char *konfig_wifi_nama(int i);       // SSID
int konfig_wifi(void);                     // indeks terpilih
// Simpan ke NVS lalu sambung ulang. false = indeks di luar daftar.
bool konfig_pilih_wifi(int i);

int konfig_broker_n(void);
const char *konfig_broker_nama(int i);
const char *konfig_broker_host(int i);
int konfig_broker_port(int i);
int konfig_broker(void);
bool konfig_pilih_broker(int i);

// Sumber sinyal tersimpan, untuk menu. Belum dipakai saat boot.
int konfig_sumber(void);
void konfig_set_sumber(int s);

#endif
