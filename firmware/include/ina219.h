#ifndef INA219_H
#define INA219_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define INA219_ADDRESS     0x40
#define INA219_REG_CONFIG 0x00
#define INA219_REG_SHUNT  0x01
#define INA219_REG_BUS    0x02

#define INA219_CONFIG     0x3FFF

float ina219_current_mA(int16_t shunt_reg, float r_shunt_ohm);

float ina219_bus_V(uint16_t bus_reg);

#ifdef ARDUINO
bool ina219_begin(int pin_sda, int pin_scl);
bool ina219_read(float r_shunt_ohm, float *current_mA, float *bus_V);
bool ina219_read_reg(uint8_t reg, uint16_t *out);
#endif

#ifdef __cplusplus
}
#endif
#endif
