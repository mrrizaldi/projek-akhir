#include "ina219.h"

float ina219_arus_mA(int16_t shunt_reg, float r_shunt_ohm)
{
    return ((float)shunt_reg * 0.01f) / r_shunt_ohm;
}

float ina219_bus_V(uint16_t bus_reg)
{
    return (float)(bus_reg >> 3) * 0.004f;
}
