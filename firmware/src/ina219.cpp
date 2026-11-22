#include "ina219.h"

float ina219_current_mA(int16_t shunt_reg, float r_shunt_ohm)
{
    return ((float)shunt_reg * 0.01f) / r_shunt_ohm;
}

float ina219_bus_V(uint16_t bus_reg)
{
    return (float)(bus_reg >> 3) * 0.004f;
}

#ifdef ARDUINO
#include <Wire.h>

constexpr bool WITHOUT_STOP = false;

static void write_register(uint8_t reg, uint16_t value)
{
    Wire.beginTransmission(INA219_ADDRESS);
    Wire.write(reg);
    Wire.write((uint8_t)(value >> 8));
    Wire.write((uint8_t)(value & 0xFF));
    Wire.endTransmission();
}

bool ina219_read_reg(uint8_t reg, uint16_t *out)
{
    Wire.beginTransmission(INA219_ADDRESS);
    Wire.write(reg);
    if (Wire.endTransmission(WITHOUT_STOP) != 0)
        return false;
    if (Wire.requestFrom((int)INA219_ADDRESS, 2) != 2)
        return false;
    const uint8_t hi = Wire.read(), lo = Wire.read();
    *out = ((uint16_t)hi << 8) | lo;
    return true;
}

bool ina219_begin(int pin_sda, int pin_scl)
{
    Wire.begin(pin_sda, pin_scl);
    write_register(INA219_REG_CONFIG, INA219_CONFIG);
    delay(5);
    uint16_t c;
    return ina219_read_reg(INA219_REG_CONFIG, &c) && c == INA219_CONFIG;
}

bool ina219_read(float r_shunt_ohm, float *current_mA, float *bus_V)
{
    uint16_t s, b;
    if (!ina219_read_reg(INA219_REG_SHUNT, &s) || !ina219_read_reg(INA219_REG_BUS, &b))
        return false;
    *current_mA = ina219_current_mA((int16_t)s, r_shunt_ohm);
    *bus_V = ina219_bus_V(b);
    return true;
}
#endif
