#ifdef ARDUINO
#include "diagnostics.h"

#include <stdarg.h>
#include "soc/gpio_struct.h"
#include "soc/gpio_sig_map.h"
#include "soc/gpio_periph.h"
#include "soc/io_mux_reg.h"

#include "ina219.h"
#include "board.h"

constexpr uint32_t FILL_MIN_US = 5000;
constexpr int READ_ADC_ONE_SECOND = 360;
constexpr uint32_t WAIT_AVERAGE_INA219_MS = 70;
constexpr float V_BUS_MAX = 32.0f, I_SCALE_FULL_MA = 3200.0f, V_BUS_SUPPLY_MIN = 1.0f;

static diag_result_t result(bool pass, const char *fmt, ...)
{
    diag_result_t h;
    h.pass = pass;
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(h.summary, sizeof h.summary, fmt, ap);
    va_end(ap);
    Serial.printf("[diag] %s: %s\n", pass ? "LULUS" : "GAGAL", h.summary);
    return h;
}

static int level_buzzer() { return (GPIO.in >> PIN_BUZZ) & 1; }

static float portion_low(uint32_t us)
{
    int low = 0, n = 0;
    const uint32_t t0 = micros();
    while (micros() - t0 < us) {
        low += !level_buzzer();
        n++;
    }
    return (float)low / n;
}

diag_result_t diag_buzzer(void)
{
    PIN_INPUT_ENABLE(GPIO_PIN_MUX_REG[PIN_BUZZ]);

    const auto &cfg = GPIO.func_out_sel_cfg[PIN_BUZZ];
    if (cfg.func_sel != LEDC_LS_SIG_OUT0_IDX + CHANNEL_BUZZ)
        return result(false, "Buzzer GPIO%d lepas dari LEDC (SPI sesudah buzzer?)", PIN_BUZZ);
    if (!cfg.inv_sel)
        return result(false, "Buzzer LEDC tidak dibalik (output_invert)");
    if (!((GPIO.enable >> PIN_BUZZ) & 1))
        return result(false, "Buzzer GPIO%d output nonaktif (jadi INPUT)", PIN_BUZZ);

    buzzer(false);
    delay(5);
    if (portion_low(5000) > 0.0f)
        return result(false, "Buzzer LOW saat diam: bunyi terus (aktif-LOW)");

    buzzer(true);
    delay(5);
    const float p = portion_low(5000);
    buzzer(false);
    const int percent = (int)lroundf(p * 100);
    if (fabsf(p - 0.5f) > 0.15f)
        return result(false, "Buzzer nada bukan kotak: LOW %d%%", percent);

    Serial.println("DENGARKAN: tiga bip pendek.");
    for (int i = 0; i < 3; i++) {
        buzzer(true);
        delay(80);
        buzzer(false);
        delay(250);
    }
    if (!level_buzzer())
        return result(false, "Buzzer tidak kembali HIGH sesudah bip");
    return result(true, "Buzzer GPIO%d ok LOW %d%% %u Hz, dengar 3 bip", PIN_BUZZ, percent,
                 (unsigned)TONE_HZ);
}

diag_result_t diag_screen(void)
{
    if (tft.width() != TFT_W || tft.height() != TFT_H)
        return result(false, "Layar ukuran %dx%d, harus %dx%d", tft.width(), tft.height(), TFT_W, TFT_H);

    const uint32_t t0 = micros();
    tft.fillScreen(ST77XX_BLUE);
    const uint32_t us = micros() - t0;

    const uint16_t color[4] = {ST77XX_RED, ST77XX_GREEN, ST77XX_BLUE, ST77XX_WHITE};
    for (int i = 0; i < 4; i++)
        tft.fillRect(i * TFT_W / 4, 0, TFT_W / 4, TFT_H, color[i]);
    tft.setTextSize(4);
    tft.setTextColor(ST77XX_BLACK, ST77XX_YELLOW);
    tft.setCursor(80, 70);
    tft.print("TFT OK");
    Serial.println("LIHAT LAYAR: pita merah-hijau-biru-putih dan tulisan \"TFT OK\".");
    delay(2000);

    const unsigned ms = (us + 500) / 1000;
    if (us <= FILL_MIN_US) return result(false, "Layar fill %u us: SPI tidak mengirim?", (unsigned)us);
    if (us >= 500000) return result(false, "Layar fill %u ms: terlalu lambat", ms);
    return result(true, "Layar %dx%d ok fill %u ms", TFT_W, TFT_H, ms);
}

diag_result_t diag_adc(void)
{
    for (int i = 0; i < 100; i++) {
        const int v = adc1_get_raw(CHANNEL_ECG);
        if (v < 0 || v > 4095) return result(false, "ADC GPIO1 error (%d)", v);
    }
    int lo = 4095, hi = 0;
    for (int i = 0; i < READ_ADC_ONE_SECOND; i++) {
        const int v = adc1_get_raw(CHANNEL_ECG);
        if (v < lo) lo = v;
        if (v > hi) hi = v;
        delayMicroseconds(2700);
    }
    const int lop = digitalRead(PIN_LOP), lon = digitalRead(PIN_LON);
    return result(true, "ADC %d..%d ayun %d LO+%d LO-%d%s", lo, hi, hi - lo, lop, lon,
                 (lop || lon) ? " lepas" : "");
}

diag_result_t diag_ina219(void)
{
    if (!ina219_begin(I2C_SDA, I2C_SCL))
        return result(false, "INA219 0x%02X tidak menjawab (SDA%d SCL%d)", INA219_ADDRESS, I2C_SDA, I2C_SCL);
    delay(WAIT_AVERAGE_INA219_MS);

    float mA = 0, V = 0;
    uint16_t sh, bus;
    if (!ina219_read(R_SHUNT, &mA, &V) || !ina219_read_reg(INA219_REG_SHUNT, &sh)
        || !ina219_read_reg(INA219_REG_BUS, &bus))
        return result(false, "INA219 baca register gagal");
    Serial.printf("INA219 mentah: shunt 0x%04X (%d x 10 uV) | bus 0x%04X, CNVR %d OVF %d\n",
                  sh, (int16_t)sh, bus, (bus >> 1) & 1, bus & 1);

    const int mV = (int)lroundf(V * 1000), iA = (int)lroundf(mA);
    if (V < 0.0f || V > V_BUS_MAX || fabsf(mA) > I_SCALE_FULL_MA)
        return result(false, "INA219 di luar rentang V=%d mV I=%dmA", mV, iA);
    if (V < V_BUS_SUPPLY_MIN)
        return result(true, "INA219 0x%02X ok V=%d,%02d I=-- bus<1V:bukan jalur catu",
                     INA219_ADDRESS, mV / 1000, (mV % 1000) / 10);
    return result(true, "INA219 0x%02X ok V=%d,%02d I=%dmA", INA219_ADDRESS, mV / 1000,
                 (mV % 1000) / 10, iA);
}

diag_result_t diag_button(uint32_t limit_ms)
{
    constexpr uint32_t DEBOUNCE_MS = 50;
    bool pressed[3], done[3] = {};
    uint32_t t_change[3] = {};
    for (int k = 0; k < 3; k++) pressed[k] = digitalRead(PIN_BTN[k]) == LOW;
    Serial.printf("TEKAN B1, B2, B3 masing-masing sekali (batas %u ms).\n", (unsigned)limit_ms);

    int n = 0;
    const uint32_t t0 = millis();
    while (n < 3 && millis() - t0 < limit_ms) {
        for (int k = 0; k < 3; k++) {
            const bool current = digitalRead(PIN_BTN[k]) == LOW;
            if (current == pressed[k] || millis() - t_change[k] < DEBOUNCE_MS) continue;
            pressed[k] = current;
            t_change[k] = millis();
            if (current && !done[k]) {
                done[k] = true;
                n++;
                Serial.printf("  B%d (GPIO%d) ok\n", k + 1, PIN_BTN[k]);
                buzzer(true);
                delay(20);
                buzzer(false);
            }
        }
        delay(2);
    }
    return result(n == 3, "Tombol B1%s B2%s B3%s%s", done[0] ? "+" : "-", done[1] ? "+" : "-",
                 done[2] ? "+" : "-", n == 3 ? " ok" : " (batas waktu)");
}
#endif
