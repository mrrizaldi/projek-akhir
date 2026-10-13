// Pin map PCB rev1 dan pemasangan perangkat (AD8232, TFT, buzzer, tombol).
// Dipakai src/main.cpp dan test device test/test_hw_*, sehingga urutan
// pemasangan yang rawan (SPI sebelum buzzer) hanya ditulis di satu tempat.
#ifndef PERANGKAT_H
#define PERANGKAT_H

#include <Arduino.h>
#include <Adafruit_ST7789.h>
#include "driver/adc.h"

// AD8232: OUT ke GPIO 1 (ADC1_CH0), LO- ke GPIO 2, LO+ ke GPIO 42.
constexpr adc1_channel_t KANAL_EKG = ADC1_CHANNEL_0;
constexpr int PIN_LON = 2, PIN_LOP = 42;

// TFT ST7789 172x320. CS diikat ke GND (karena itu wajib SPI_MODE3), BLK ke 3V3.
constexpr int TFT_SCK = 9, TFT_MOSI = 8, TFT_RST = 10, TFT_DC = 11;
constexpr int TFT_W = 320, TFT_H = 172; // landscape, rotasi 1

// Modul buzzer pasif 3 pin A18009, VCC 3V3. Transistor di dalam modul membuat
// I/O aktif LOW: LOW = bunyi, HIGH = diam.
constexpr int PIN_BUZZ = 13, KANAL_BUZZ = 0;
constexpr uint32_t NADA_HZ = 2000; // knob: buzzer pasif paling keras di resonansinya, beda per part

// Tombol B1/B2/B3 ke GND, pull-up internal.
constexpr int PIN_BTN[3] = {4, 5, 6};

// INA219 di jalur baterai, VCC modul 3V3.
constexpr int I2C_SDA = 17, I2C_SCL = 18;
// Knob kalibrasi terhadap multimeter: R_baru = R_lama x (I_ina219 / I_multimeter).
constexpr float R_SHUNT = 0.1f;

constexpr int PIN_LED = 48; // NeoPixel onboard

extern Adafruit_ST7789 tft;

// Memasang semua pin perangkat: buzzer (diam), LO, tombol, ADC, lalu TFT
// (layar dikosongkan). INA219 dipasang terpisah lewat ina219_mulai().
void perangkat_mulai(void);

// true = nada NADA_HZ, false = diam (pin HIGH).
void buzzer(bool nyala);

#endif // PERANGKAT_H
