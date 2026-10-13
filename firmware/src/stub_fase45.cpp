// STUB SEMENTARA — diisi agen fase 4/5. Definisi weak: definisi asli di
// diagnosa.cpp / daya.cpp otomatis menggantikannya saat digabung; berkas ini
// lalu boleh dihapus. Kontrak: include/stub_fase45.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "stub_fase45.h"

#include <Arduino.h>

#define LEMAH __attribute__((weak))

static diag_hasil_t belum()
{
    diag_hasil_t h = {false, "belum ada (fase 4)"};
    return h;
}
LEMAH diag_hasil_t diag_buzzer(void) { return belum(); }
LEMAH diag_hasil_t diag_layar(void) { return belum(); }
LEMAH diag_hasil_t diag_adc(void) { return belum(); }
LEMAH diag_hasil_t diag_ina219(void) { return belum(); }
LEMAH diag_hasil_t diag_tombol(uint32_t) { return belum(); }

LEMAH void daya_tangga_mulai(void) { Serial.println("daya: tangga mandiri belum ada (fase 5)"); }
LEMAH bool daya_tangga_aktif(void) { return false; }
LEMAH void daya_tangga_tick(void) {}
LEMAH int daya_tangga_langkah(void) { return -1; }
LEMAH int daya_tangga_hasil(daya_baris_t *, int) { return 0; }
LEMAH int daya_tangga_berkas(void) { return 0; }
LEMAH bool daya_serial(const char *) { Serial.println("daya: belum ada (fase 5)"); return false; }
#endif
