#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
 
import os
from gps import *
from time import *
import time
import threading
 
gpsd = None #seting the global variable
 
#os.system('clear') #clear the terminal (optional)
 
class GpsPoller(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		global gpsd #bring it in scope
		gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
		self.current_value = None
		self.running = True #setting the thread running to true
		self.daemon = True
 
	def run(self):
		global gpsd
		while self.running:
			gpsd.next()
 

	def cleanup_gps(self):
		print "\nKilling Thread..."
		self.running = False
		self.join() # wait for the thread to finish what it's doing
		print "Done.\nExiting."


#gpsp = GpsPoller() # create the thread
#gpsp.daemon = True


#gpsp.start() # start it up

#while 1:
#	os.system('clear')
#
#	print("Value %d" % gpsp.xxx)
#
#	time.sleep(1) #set to whatever
