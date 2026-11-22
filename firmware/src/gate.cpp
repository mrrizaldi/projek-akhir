#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "gate.h"

#include <Arduino.h>

#include "akuisisi.h"
#include "board.h"
#include "rekam.h"
#include "tampilan.h"

constexpr int ADC_UPPER = 4090, ADC_LOWER = 5;

constexpr float RR_MIN_S = 0.300f, RR_MAX_S = 1.500f;
constexpr float DRR_MAX_S = 0.200f;
constexpr uint32_t BEEP_CALIBRATION_MS = 600;

static int phase;
static uint32_t t_rr_violation;
static uint32_t t_session_ms;
static uint32_t t_contact;
static bool skip_calibration;
static bool report_quality;
static gate_quality_t q;

constexpr float GAIN_50HZ = 0.342f;
constexpr float FREQUENCY_MAINS_HZ = 50.0f;

const gate_quality_t &gate_quality(void) { return q; }
uint32_t gate_t_session_ms(void) { return t_session_ms; }
uint32_t gate_quiet_ms(void) { return millis() - t_rr_violation; }
uint32_t gate_contact_ms(void) { return q.contact ? millis() - t_contact : 0; }
int gate_phase(void) { return phase; }
bool gate_skip(void) { return skip_calibration; }
bool gate_report(void) { return report_quality; }
void gate_set_report(bool on) { report_quality = on; }

void gate_begin_session(void)
{
    tampilan_bunyi(BEEP_CALIBRATION_MS);
    ecg_live_reset();
    t_session_ms = millis();
    phase = PHASE_CALIBRATION;
    t_rr_violation = millis();
    q.contact = false;
    tampilan_hapus_jadwal();
}

void gate_set_skip(bool on)
{
    if (rekam_tolak("lewati kalibrasi")) return;
    skip_calibration = on;
    if (!on) gate_begin_session();
}

const char *gate_phase_name(void)
{
    return phase == PHASE_CALIBRATION ? "calibrating" : (phase == PHASE_GOOD ? "good" : "poor");
}

void gate_assess_phase(const ecg_beat_t &beat)
{
    const float rr = beat.rr[0];
    const float drr = fabsf(beat.rr[2]);
    const bool rr_plausible = rr >= RR_MIN_S && rr <= RR_MAX_S && drr <= DRR_MAX_S;
    if (!rr_plausible) t_rr_violation = millis();

    const bool replay = akuisisi_replay();

    if (phase != PHASE_CALIBRATION) return;
    const bool warm = gate_contact_ms() >= WARMUP_MS;
    const bool rr_quiet = millis() - t_rr_violation >= RR_QUIET_MS;
    if ((skip_calibration || replay || (warm && rr_quiet)) && q.contact) {
        phase = PHASE_GOOD;
        tampilan_bunyi(BEEP_CALIBRATION_MS);
        Serial.printf("kualitas: calibrating -> good (%s, kontak %lu s, RR tenang %lu s, ayun %d, dengung %d)\n",
                      replay ? "GERBANG DILEWATI (replay)"
                      : skip_calibration ? "GERBANG DILEWATI (bench)" : "gerbang penuh",
                      (unsigned long)(gate_contact_ms() / 1000),
                      (unsigned long)((millis() - t_rr_violation) / 1000), q.swing_clean, q.hum50);
    }
}

static void assess_contact(void)
{
    const bool good = (akuisisi_replay() || !q.leadoff) && q.swing_clean >= THRESHOLD_SWING
                      && q.hum50 <= THRESHOLD_HUM;
    if (good && !q.contact) t_contact = millis();
    q.contact = good;
    if (phase == PHASE_CALIBRATION) return;
    const int next_phase = good ? PHASE_GOOD : PHASE_BAD;
    if (next_phase != phase)
        Serial.printf("kualitas: %s -> %s (lepas %d, ayun %d, dengung %d)\n", gate_phase_name(),
                      good ? "good" : "poor", (int)q.leadoff, q.swing_clean, q.hum50);
    phase = next_phase;
}

void gate_report_calibration(const ecg_beat_t &beat)
{
    static uint32_t t_report;
    if (millis() - t_report <= 5000) return;
    t_report = millis();
    Serial.printf("calibrating | RR=%.3fs dRR=%+.3fs | tenang %lu/%lu s | "
                  "ayun %d (ambang %d) | dengung %d (ambang %d) | lepas %d | kontak %lu/%lu s | "
                  "lewati=%d replay=%d\n",
                  beat.rr[0], beat.rr[2],
                  (unsigned long)((millis() - t_rr_violation) / 1000),
                  (unsigned long)(RR_QUIET_MS / 1000), q.swing_clean, THRESHOLD_SWING,
                  q.hum50, THRESHOLD_HUM, (int)q.leadoff,
                  (unsigned long)(gate_contact_ms() / 1000),
                  (unsigned long)(WARMUP_MS / 1000), (int)skip_calibration,
                  (int)akuisisi_replay());
}

void gate_assess_quality(float raw)
{
    static size_t n, n_leadoff;
    static float f_min, f_max;
    static int m_min, m_max;

    static float g1, g2;
    static const float coef = 2.0f * cosf(2.0f * (float)M_PI * FREQUENCY_MAINS_HZ / ECG_FS);

    const float f = ecg_live_tersaring_terakhir();
    const int m = (int)raw;
    if (n == 0) { f_min = f_max = f; m_min = m_max = m; g1 = g2 = 0.0f; n_leadoff = 0; }
    if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) n_leadoff++;

    const float g0 = coef * g1 - g2 + raw;
    g2 = g1; g1 = g0;

    if (f < f_min) f_min = f;
    if (f > f_max) f_max = f;
    if (m < m_min) m_min = m;
    if (m > m_max) m_max = m;

    if (++n < ECG_FS) return;
    n = 0;
    q.swing = (int)(f_max - f_min);
    const float amp50 = 2.0f * sqrtf(fmaxf(g1 * g1 + g2 * g2 - coef * g1 * g2, 0.0f)) / ECG_FS;
    q.hum50 = (int)(2.0f * amp50);
    q.swing_clean = (int)fmaxf(q.swing - GAIN_50HZ * 2.0f * amp50, 0.0f);
    q.raw_min = m_min;
    q.raw_max = m_max;
    q.clipping = (m_max >= ADC_UPPER || m_min <= ADC_LOWER);
    q.leadoff = n_leadoff > 0;
    assess_contact();
    if (report_quality)
        Serial.printf("kualitas | mentah %4d..%4d | ayun %4d - dengung50 %4d = "
                      "BERSIH %4d (ambang %d) | clipping %d | LO %d %d\n",
                      q.raw_min, q.raw_max, q.swing, q.hum50,
                      q.swing_clean, THRESHOLD_SWING,
                      (int)q.clipping, digitalRead(PIN_LOP), digitalRead(PIN_LON));
}
#endif
