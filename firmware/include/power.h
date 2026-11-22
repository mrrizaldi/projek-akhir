#ifndef POWER_H
#define POWER_H

void power_begin(void);
bool power_ina_present(void);
const char *power_ina_text(void);

int power_mode(void);
void power_set_mode(int m);
bool power_stage(int t);
void power_count_beat(void);
void power_service(void);

typedef struct { char mode[4]; float i_ma, sd_ma, v, p_mw; } power_row_t;
void power_sweep_begin(void);
bool power_sweep_active(void);
void power_sweep_tick(void);
int power_sweep_step(void);
int power_sweep_result(power_row_t *out, int max_count);
int power_sweep_file(void);
bool power_serial(const char *command);

#endif
