#include <stdio.h>
#include <wiringPiI2C.h>
#include "si1132.h"

int si1132_begin(const char *device)
{
	si1132Fd = wiringPiI2CSetupInterface(device, Si1132_ADDR);
	if (si1132Fd < 0) {
		printf("ERROR: si1132 open failed\n");
		return -1;
	}

	if (wiringPiI2CReadReg8(si1132Fd, Si1132_REG_PARTID) != 0x32) {
		printf("ERROR: si1132 read failed the PART ID\n");
		return -1;
	}

	initialize();
}

void initialize(void)
{
	reset();

	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_UCOEF0, 0x29);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_UCOEF1, 0x89);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_UCOEF2, 0x02);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_UCOEF3, 0x00);

	Si1132_I2C_writeParam(Si1132_PARAM_CHLIST, Si1132_PARAM_CHLIST_ENUV |
		Si1132_PARAM_CHLIST_ENAUX | Si1132_PARAM_CHLIST_ENALSIR |
					Si1132_PARAM_CHLIST_ENALSVIS);

	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_INTCFG,
					Si1132_REG_INTCFG_INTOE);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_IRQEN,
					Si1132_REG_IRQEN_ALSEVERYSAMPLE);

	Si1132_I2C_writeParam(Si1132_PARAM_ALSIRADCMUX,
					Si1132_PARAM_ADCMUX_SMALLIR);
	usleep(10000);
	// fastest clocks, clock div 1
	Si1132_I2C_writeParam(Si1132_PARAM_ALSIRADCGAIN, 2);
	usleep(10000);
	// take 511 clocks to measure
	Si1132_I2C_writeParam(Si1132_PARAM_ALSIRADCCOUNTER,
					Si1132_PARAM_ADCCOUNTER_511CLK);
	// in high range mode
	Si1132_I2C_writeParam(Si1132_PARAM_ALSIRADCMISC,
					Si1132_PARAM_ALSIRADCMISC_RANGE);
	usleep(10000);
	// fastest clocks
	Si1132_I2C_writeParam(Si1132_PARAM_ALSVISADCGAIN, 3);
	usleep(10000);
	// take 511 clocks to measure
	Si1132_I2C_writeParam(Si1132_PARAM_ALSVISADCCOUNTER,
					Si1132_PARAM_ADCCOUNTER_511CLK);
	//in high range mode (not normal signal)
	Si1132_I2C_writeParam(Si1132_PARAM_ALSVISADCMISC,
					Si1132_PARAM_ALSVISADCMISC_VISRANGE);
	usleep(10000);

	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_MEASRATE0, 0xFF);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_COMMAND, Si1132_ALS_AUTO);
}

void reset()
{
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_MEASRATE0, 0);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_MEASRATE1, 0);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_IRQEN, 0);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_IRQMODE1, 0);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_IRQMODE2, 0);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_INTCFG, 0);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_IRQSTAT, 0xFF);

	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_COMMAND, Si1132_RESET);
	usleep(10000);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_HWKEY, 0x17);

	usleep(10000);
}

float Si1132_readVisible()
{
	usleep(10000);
	return wiringPiI2CReadReg16(si1132Fd, 0x22) - 250;
}

float Si1132_readIR()
{
	usleep(10000);
	return wiringPiI2CReadReg16(si1132Fd, 0x24) - 250;
}

float Si1132_readUV()
{
	usleep(10000);
	return wiringPiI2CReadReg16(si1132Fd, 0x2c);
}

void Si1132_I2C_writeParam(unsigned char param, unsigned char val)
{
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_PARAMWR, val);
	wiringPiI2CWriteReg8(si1132Fd, Si1132_REG_COMMAND, param |
							Si1132_PARAM_SET);
}
