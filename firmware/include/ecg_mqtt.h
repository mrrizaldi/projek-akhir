#ifndef ECG_MQTT_H
#define ECG_MQTT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_SNIPPET_N 8

#define ECG_MQTT_QUEUE_TARGET 27000

#define ECG_MQTT_QUEUE_MIN 64

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

void ecg_mqtt_queue_attach(ecg_mqtt_beat_t *mem, size_t capacity);
size_t ecg_mqtt_queue_capacity(void);

size_t ecg_mqtt_queue_n(void);
size_t ecg_mqtt_queue_lost(void);
void ecg_mqtt_queue_fill(const ecg_mqtt_beat_t *b);
size_t ecg_mqtt_queue_peek(ecg_mqtt_beat_t *beats_out, size_t max_count);
void ecg_mqtt_queue_drop(size_t n);

#ifdef ARDUINO
void ecg_mqtt_configure(const char *ssid, const char *pass, const char *host, uint16_t port,
                   const char *token);
void ecg_mqtt_begin(void);
void ecg_mqtt_service(void);
int  ecg_mqtt_active(void);
void ecg_mqtt_set_active(int on);
uint32_t ecg_mqtt_sent(void);
uint32_t ecg_mqtt_failed(void);
uint32_t ecg_mqtt_packet_send(void);
uint32_t ecg_mqtt_packet_ack(void);
uint32_t ecg_mqtt_rtt_max(void);
uint32_t ecg_mqtt_rtt_slow(void);
uint64_t ecg_mqtt_epoch_ms(void);
int ecg_mqtt_rssi(void);
const char *ecg_mqtt_status(void);
#endif

#ifdef __cplusplus
}
#endif
#endif
