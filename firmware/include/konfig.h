#ifndef KONFIG_H
#define KONFIG_H

void konfig_mulai(void);

int konfig_wifi_n(void);
const char *konfig_wifi_nama(int i);
int konfig_wifi(void);
bool konfig_pilih_wifi(int i);
bool konfig_wifi_aktif(void);
bool konfig_set_wifi_aktif(bool on);

int konfig_broker_n(void);
const char *konfig_broker_nama(int i);
const char *konfig_broker_host(int i);
int konfig_broker_port(int i);
int konfig_broker(void);
bool konfig_pilih_broker(int i);

int konfig_sumber(void);
int konfig_sumber_rekam(void);
void konfig_set_sumber(int s, int nomor);

#endif
