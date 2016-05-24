CC=gcc
CFLAG=-g
OBJGROUP=bme280.o bme280-i2c.o si1132.o si702x.o bmp180.o weather_board.o

all: weather_board

weather_board: $(OBJGROUP)
	$(CC) -o weather_board $(OBJGROUP) -lm

clean:
	rm *o weather_board
