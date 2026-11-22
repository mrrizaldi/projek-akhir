#ifndef DIAGNOSTICS_H
#define DIAGNOSTICS_H

#include <stdint.h>

typedef struct {
    bool pass;
    char summary[64];
} diag_result_t;

diag_result_t diag_buzzer(void);
diag_result_t diag_screen(void);
diag_result_t diag_adc(void);
diag_result_t diag_ina219(void);
diag_result_t diag_button(uint32_t limit_ms);

#endif
