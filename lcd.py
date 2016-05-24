import wiringpi2
#import datetime
 
# --LCD
LCD_ROW = 2 # 16 Char
LCD_COL = 16 # 2 Line
LCD_BUS = 4 # Interface 4 Bit mode
 
PORT_LCD_RS = 7 # GPIOY.BIT3(#83)
PORT_LCD_E = 0 # GPIOY.BIT8(#88)
PORT_LCD_D4 = 2 # GPIOX.BIT19(#116)
PORT_LCD_D5 = 3 # GPIOX.BIT18(#115)
PORT_LCD_D6 = 1 # GPIOY.BIT7(#87)
PORT_LCD_D7 = 4 # GPIOX.BIT4(#104)
# --LCD
 
# --LED
led_pins = [21, 22, 23, 24, 11, 26, 27]
# --LED

lcdRow = 0 # LCD Row
lcdCol = 0 # LCD Column

lcdHandle = None

def lcd_setup():
	wiringpi2.wiringPiSetup()

	global lcdHandle

	lcdHandle = wiringpi2.lcdInit(LCD_ROW, LCD_COL, LCD_BUS,
		PORT_LCD_RS, PORT_LCD_E,
		PORT_LCD_D4, PORT_LCD_D5,
		PORT_LCD_D6, PORT_LCD_D7, 0, 0, 0, 0);

	# set to read mode
	for number in led_pins:
 		wiringpi2.pinMode(number,1)

	# set to write mode
	wiringpi2.pinMode(5,0)
	wiringpi2.pinMode(6,0)

	# clear the state
	lcd_clear()
	for i in range(0,7):
		lcd_led_set(i,0)

	return lcdHandle


def lcd_update(string, row):
	string = string[0:16]
	string = string.ljust(16)
        wiringpi2.lcdPosition(lcdHandle, lcdCol, lcdRow + row)
	wiringpi2.lcdPuts(lcdHandle, string)
        #wiringpi2.lcdPosition(lcdHandle, lcdCol, lcdRow + 1)
        #wiringpi2.lcdPrintf(lcdHandle, string_bottom)


def lcd_clear():
	wiringpi2.lcdClear(lcdHandle)


def lcd_led_set(lcd_id, state):
	wiringpi2.digitalWrite(led_pins[lcd_id],state)






def lcd_check_buttons(delay):
	lbutton = 0
	rbutton = 0

	wiringpi2.delay(delay)
	if wiringpi2.digitalRead(5) == 0: # Left button
		print("left button pressed")
		lbutton = 1

	if wiringpi2.digitalRead(6) == 0: # Right button
		print("right button pressed")
		rbutton = 1

	return (lbutton, rbutton)



#lcd_setup()
#lcd_clear()
#lcd_led_set(0,0)
#lcd_update("testing123", 0)
#lcd_update("fish",1)
