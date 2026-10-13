#ifndef ECG_MQTT_H
#define ECG_MQTT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_SNIPPET_N 8

#define ECG_MQTT_ANTRE_TARGET 27000

#define ECG_MQTT_ANTRE_MIN 64

#define ECG_MQTT_BATCH_N 50

typedef struct {
    uint32_t ms;
    float bpm;
    float rr_ms;
    float confidence;
    int label;
    int quality_ok;
    int16_t snippet[ECG_SNIPPET_N];
} ecg_mqtt_beat_t;

size_t ecg_mqtt_payload(char *buf, size_t n, const ecg_mqtt_beat_t *b, size_t nb,
                        uint64_t ts_base_ms);

void ecg_mqtt_antre_pasang(ecg_mqtt_beat_t *mem, size_t kapasitas);
size_t ecg_mqtt_antre_kapasitas(void);

void ecg_mqtt_antre_reset(void);
size_t ecg_mqtt_antre_n(void);
size_t ecg_mqtt_antre_hilang(void);
void ecg_mqtt_antre_isi(const ecg_mqtt_beat_t *b);
size_t ecg_mqtt_antre_intip(ecg_mqtt_beat_t *keluar, size_t maks);
void ecg_mqtt_antre_buang(size_t n);

#ifdef ARDUINO
void ecg_mqtt_atur(const char *ssid, const char *pass, const char *host, uint16_t port,
                   const char *token);
void ecg_mqtt_mulai(void);
void ecg_mqtt_layani(void);
int  ecg_mqtt_tersambung(void);
int  ecg_mqtt_aktif(void);
void ecg_mqtt_set_aktif(int on);
uint32_t ecg_mqtt_terkirim(void);
uint32_t ecg_mqtt_gagal(void);
uint32_t ecg_mqtt_paket_kirim(void);
uint32_t ecg_mqtt_paket_ack(void);
uint32_t ecg_mqtt_rtt_maks(void);
uint32_t ecg_mqtt_rtt_lambat(void);
uint64_t ecg_mqtt_epoch_ms(void);
int ecg_mqtt_rssi(void);
const char *ecg_mqtt_status(void);
#endif

#ifdef __cplusplus
}
#endif
#endif
