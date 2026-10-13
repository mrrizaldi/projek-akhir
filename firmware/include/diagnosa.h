#ifndef DIAGNOSA_H
#define DIAGNOSA_H

#include <stdint.h>

typedef struct {
    bool lulus;
    char ringkas[64];
} diag_hasil_t;

diag_hasil_t diag_buzzer(void);
diag_hasil_t diag_layar(void);
diag_hasil_t diag_adc(void);
diag_hasil_t diag_ina219(void);
diag_hasil_t diag_tombol(uint32_t batas_ms);

#endif
