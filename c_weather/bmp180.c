#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <math.h>
#include <linux/i2c-dev.h>
#include "bmp180.h"

int bmp180_begin(const char *device)
{
	int status = 0;

	bmp180Fd = open(device, O_RDWR);
	if (bmp180Fd < 0) {
		printf("ERROR: bmp180 open failed\n");
		return -1;
	}

	status = ioctl(bmp180Fd, I2C_SLAVE, BMP180_ADDRESS);
	if (status < 0) {
		printf("ERROR: bmp180 ioctl error\n");
		close(bmp180Fd);
		return -1;
	}

	if (BMP180_I2C_read8(BMP180_CHIPID) != 0x55) {
		printf("ERROR: bmp180 read failed the PART ID\n");
		return -1;
	}
	readCoefficients();
}

void BMP180_I2C_writeCommand(unsigned char reg, unsigned char value)
{
	unsigned char wbuf[2];
	wbuf[0] = reg;
	wbuf[1] = value;
	write(bmp180Fd, wbuf, 2);
}

unsigned char BMP180_I2C_read8(unsigned char reg)
{
	write(bmp180Fd, &reg, 1);
	read(bmp180Fd, &reg, 1);
	return reg;
}

unsigned short BMP180_I2C_read16(unsigned char reg)
{
	unsigned char rbuf[2];
	write(bmp180Fd, &reg, 1);
	read(bmp180Fd, rbuf, 2);
	return (unsigned short)(rbuf[0] << 8 | rbuf[1]);
}

short BMP180_I2C_reads16(unsigned char reg)
{
	unsigned short i;
	i = BMP180_I2C_read16(reg);
	return (short)i;
}

void readCoefficients(void)
{
	ac1 = BMP180_I2C_reads16(BMP180_CAL_AC1);
	ac2 = BMP180_I2C_reads16(BMP180_CAL_AC2);
	ac3 = BMP180_I2C_reads16(BMP180_CAL_AC3);
	ac4 = BMP180_I2C_read16(BMP180_CAL_AC4);
	ac5 = BMP180_I2C_read16(BMP180_CAL_AC5);
	ac6 = BMP180_I2C_read16(BMP180_CAL_AC6);
	b1 = BMP180_I2C_reads16(BMP180_CAL_B1);
	b2 = BMP180_I2C_reads16(BMP180_CAL_B2);
	mb = BMP180_I2C_reads16(BMP180_CAL_MB);
	mc = BMP180_I2C_reads16(BMP180_CAL_MC);
	md = BMP180_I2C_reads16(BMP180_CAL_MD);
}

float readRawTemperature()
{
	BMP180_I2C_writeCommand(BMP180_CONTROL, BMP180_READTEMPCMD);
	usleep(5000);

	return BMP180_I2C_read16(BMP180_TEMPDATA);
}

float readRawPressure()
{
	unsigned int raw;

	BMP180_I2C_writeCommand(BMP180_CONTROL, BMP180_READPRESSURECMD + (oversampling << 6));

	if (oversampling == BMP180_ULTRALOWPOWER)
		usleep(5000);
	else if (oversampling == BMP180_STANDARD)
		usleep(8000);
	else if (oversampling == BMP180_HIGHRES)
		usleep(14000);
	else
		usleep(26000);

	raw = BMP180_I2C_read16(BMP180_PRESSUREDATA);

	raw <<= 8;
	raw |= BMP180_I2C_read8(BMP180_PRESSUREDATA+2);
	raw >>= (8 - oversampling);

	return raw;
}

int computeB5(int ut)
{
	int X1 = (ut - (int)ac6) * ((int)ac5) >> 15;
	int X2 = ((int)mc << 11) / (X1 + (int)md);
	return X1 + X2;
}

float BMP180_readPressure(void)
{
	int UT, UP, B3, B5, B6, X1, X2, X3, p;
	unsigned int B4, B7;

	UT = readRawTemperature();
	UP = readRawPressure();

	B5 = computeB5(UT);
	B6 = B5 - 4000;
	X1 = ((int)b2 * ((B6 * B6) >> 12)) >> 11;
	X2 = ((int)ac2 * B6) >> 11;
	X3 = X1 + X2;
	B3 = ((((int)ac1*4 + X3) << oversampling) + 2)/4;

	X1 = ((int)ac3 * B6) >> 13;
	X2 = ((int)b1 * ((B6*B6) >> 12)) >> 16;
	X3 = ((X1 + X2) + 2) >> 2;
	B4 = ((unsigned int)ac4 * (unsigned int)(X3 + 32768)) >> 15;
	B7 = ((unsigned int)UP - B3) * (unsigned int)(50000UL >> oversampling);

	if (B7 < 0x80000000) {
	  p = (B7 * 2) / B4;
	} else {
	  p = (B7 / B4) * 2;
	}
	X1 = (p >> 8) * (p >> 8);
	X1 = (X1 * 3038) >> 16;
	X2 = (-7357 * p) >> 16;
	
	p = p + ((X1 + X2 + (int)3791)>>4);
	
	return p;
}

float BMP180_readTemperature(void)
{
	int UT, B5;
	float temp;

	UT = readRawTemperature();

	B5 = computeB5(UT);
	temp = (B5+8) >> 4;
	temp /= 10;
	return temp;
}

float BMP180_readAltitude(float sealevelPressure)
{
	float altitude;
	float pressure = BMP180_readPressure();
	altitude = 44330 * (1.0 - pow(pressure/sealevelPressure/100, 0.1903));

	return altitude;
}

float BMP180_readSealevelPressure(float altitude_meters)
{
	float pressure = BMP180_readPressure();
	return (int)(pressure / pow(1.0-altitude_meters/44330, 5.255));
}
