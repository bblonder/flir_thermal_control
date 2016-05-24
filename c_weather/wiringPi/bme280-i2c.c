#include <stdio.h>
#include <math.h>
#include <wiringPiI2C.h>
#include "bme280-i2c.h"

s32 bme280_begin(const char *device)
{
	s32 com_rslt = 0;

	bme280Fd = wiringPiI2CSetupInterface(device, BME280_I2C_ADDRESS1);
	if (bme280Fd < 0) {
		printf("ERROR: bme280 open failed\n");
		return -1;
	}

	I2C_routine();

	if (bme280_init(&bme280) < 0) {
		return -1;
	}

	com_rslt += bme280_set_power_mode(BME280_NORMAL_MODE);
	com_rslt += bme280_set_oversamp_humidity(BME280_OVERSAMP_2X);
	com_rslt += bme280_set_oversamp_pressure(BME280_OVERSAMP_2X);
	com_rslt += bme280_set_oversamp_temperature(BME280_OVERSAMP_2X);
	usleep(100000);

	return com_rslt;
}

float bme280_readAltitude(int pressure, float seaLevel)
{
	float atmospheric = (float)pressure/100.0;
	return 44330.0 * (1.0 - pow(atmospheric/seaLevel, 0.1903));
}

s8 BME280_I2C_bus_write(u8 dev_addr, u8 reg_addr, u8 *reg_data, u8 cnt)
{
	s32 iError = BME280_INIT_VALUE;
	u8 stringpos = BME280_INIT_VALUE;
	unsigned char wbuf[2];
	for (stringpos = BME280_INIT_VALUE; stringpos < cnt; stringpos++) {
		wbuf[1] = *(reg_data + stringpos);
		wbuf[0] = reg_addr + stringpos;
		wiringPiI2CWriteReg16(bme280Fd, wbuf[0], wbuf[1]);
	}
	return (s8)iError;
}

s8 BME280_I2C_bus_read(u8 dev_addr, u8 reg_addr, u8 *reg_data, u8 cnt)
{
	s32 iError = BME280_INIT_VALUE;
	u8 stringpos = BME280_INIT_VALUE;
	unsigned char rbuf[2];
	int i;
	for (stringpos = BME280_INIT_VALUE; stringpos < cnt; stringpos++) {
		rbuf[0] = reg_addr + stringpos;
		rbuf[0] = wiringPiI2CReadReg8(bme280Fd, rbuf[0]);

		if (rbuf[0] < 0) iError = -1;
		else *(reg_data + stringpos) = rbuf[0];
	}
	return (s8)iError;
}

void BME280_delay_msek(u16 msek)
{
	usleep(msek*1000);
}

s8 I2C_routine(void) {
	bme280.bus_write = BME280_I2C_bus_write;
	bme280.bus_read = BME280_I2C_bus_read;
	bme280.dev_addr = BME280_I2C_ADDRESS1;
	bme280.delay_msec = BME280_delay_msek;

	return BME280_INIT_VALUE;
}
