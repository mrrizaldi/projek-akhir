#ifndef DAYA_H
#define DAYA_H

void daya_mulai(void);
bool daya_ina_ada(void);
const char *daya_ina_teks(void);

int daya_mode(void);
void daya_set_mode(int m);
bool daya_tahap(int t);
void daya_hitung_beat(void);
void daya_layani(void);

typedef struct { char mode[4]; float i_ma, sd_ma, v, p_mw; } daya_baris_t;
void daya_tangga_mulai(void);
bool daya_tangga_aktif(void);
void daya_tangga_tick(void);
int daya_tangga_langkah(void);
int daya_tangga_hasil(daya_baris_t *keluar, int maks);
int daya_tangga_berkas(void);
bool daya_serial(const char *perintah);

#endif
