#include "ina219.h"

float ina219_arus_mA(int16_t shunt_reg, float r_shunt_ohm)
{
    return ((float)shunt_reg * 0.01f) / r_shunt_ohm;
}

float ina219_bus_V(uint16_t bus_reg)
{
    return (float)(bus_reg >> 3) * 0.004f;
}

#ifdef ARDUINO
#include <Wire.h>

static void tulis(uint8_t reg, uint16_t nilai)
{
    Wire.beginTransmission(INA219_ALAMAT);
    Wire.write(reg);
    Wire.write((uint8_t)(nilai >> 8));
    Wire.write((uint8_t)(nilai & 0xFF));
    Wire.endTransmission();
}

static bool baca(uint8_t reg, uint16_t *out)
{
    Wire.beginTransmission(INA219_ALAMAT);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) // repeated start; != 0 = NACK
        return false;
    if (Wire.requestFrom((int)INA219_ALAMAT, 2) != 2)
        return false;
    const uint8_t hi = Wire.read(), lo = Wire.read();
    *out = ((uint16_t)hi << 8) | lo;
    return true;
}

bool ina219_mulai(int pin_sda, int pin_scl)
{
    Wire.begin(pin_sda, pin_scl);
    tulis(INA219_REG_CONFIG, INA219_CONFIG);
    delay(5);
    uint16_t c;
    return baca(INA219_REG_CONFIG, &c) && c == INA219_CONFIG;
}

bool ina219_baca(float r_shunt_ohm, float *arus_mA, float *bus_V)
{
    uint16_t s, b;
    if (!baca(INA219_REG_SHUNT, &s) || !baca(INA219_REG_BUS, &b))
        return false;
    *arus_mA = ina219_arus_mA((int16_t)s, r_shunt_ohm);
    *bus_V = ina219_bus_V(b);
    return true;
}
#endif
