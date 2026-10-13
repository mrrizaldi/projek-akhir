#ifndef PERANGKAT_H
#define PERANGKAT_H

#include <Arduino.h>
#include <Adafruit_ST7789.h>
#include "driver/adc.h"

constexpr adc1_channel_t KANAL_EKG = ADC1_CHANNEL_0;
constexpr int PIN_LON = 2, PIN_LOP = 42;

constexpr int TFT_SCK = 9, TFT_MOSI = 8, TFT_RST = 10, TFT_DC = 11;
constexpr int TFT_W = 320, TFT_H = 172;

constexpr int PIN_BUZZ = 13, KANAL_BUZZ = 0;
constexpr uint32_t NADA_HZ = 2000;

constexpr int PIN_BTN[3] = {4, 5, 6};

constexpr int I2C_SDA = 17, I2C_SCL = 18;
constexpr float R_SHUNT = 0.1f;

constexpr int PIN_LED = 48;

extern Adafruit_ST7789 tft;

void perangkat_mulai(void);

void buzzer(bool nyala);

#endif
