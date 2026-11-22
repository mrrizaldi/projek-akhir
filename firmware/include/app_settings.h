#ifndef APP_SETTINGS_H
#define APP_SETTINGS_H

void settings_begin(void);

int settings_wifi_n(void);
const char *settings_wifi_name(int i);
int settings_wifi(void);
bool settings_choose_wifi(int i);
bool settings_wifi_active(void);
bool settings_set_wifi_active(bool on);

int settings_broker_n(void);
const char *settings_broker_name(int i);
const char *settings_broker_host(int i);
int settings_broker_port(int i);
int settings_broker(void);
bool settings_choose_broker(int i);

int settings_source(void);
int settings_source_recording(void);
void settings_set_source(int s, int number);

#endif
