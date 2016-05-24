CC = gcc
CFLAG = -g
OBJGROUP = si1132.o bme280-i2c.o bme280.o weather_board.o

EXTRA_LIBS = -lwiringPi -lpthread

all: weather_board

weather_board: $(OBJGROUP)
	$(CC) -o weather_board  $(OBJGROUP) $(EXTRA_LIBS) -lm

clean:
	rm *o weather_board
