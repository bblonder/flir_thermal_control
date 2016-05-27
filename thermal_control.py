#!/usr/bin/env python

import pwd
import sys
import time
import os
import datetime
import numpy
import cv2
import ctypes
import gi
import csv
import subprocess
import threading
import math
import atexit
import save_queue

gi.require_version('Aravis', '0.4')
from gi.repository import Aravis

import gps_poller
import weather_poller
import webcam_poller

uid = pwd.getpwnam('odroid').pw_uid
gid = pwd.getpwnam('odroid').pw_gid


def file_print(message):
	print(message)
	logfile.write("%s\n" % message)


print ("Finding results directory")
output_dir = os.path.expanduser("/home/odroid/Desktop/results_%s" % datetime.datetime.now().strftime('%y%m%d-%H%M%S'))
if not os.path.isdir(output_dir):
	print ("Creating results directory %s" % output_dir)
	os.makedirs(output_dir)
	os.chown(output_dir, uid, gid) 
else:
	print ("Found results directory")


logfilename = "%s/log.txt" % output_dir
logfile = open(logfilename, "a")
os.chown(logfilename, uid, gid) 
file_print("Opening log file")

def closefile():
	file_print("Closing log file")
	logfile.close()

atexit.register(closefile)




# load in the custom scripts
import lcd
def lcd_close_board():
	file_print("Closing LCDs")
	lcd.lcd_clear()
	for index in range(0,7):
		lcd.lcd_led_set(index, 0)

atexit.register(lcd_close_board)


def disk_free_bytes():
	stats = os.statvfs("/")
	free = stats.f_bavail * stats.f_frsize

	return free

	



# set up LCD
file_print ("Setting up LCD")
lcd.lcd_setup()
lcd.lcd_update("%.2f GB free" % (float(disk_free_bytes()) / 1024 / 1024 / 1024),0)




# get GPS going 
file_print ("Starting GPS")
gpsp = gps_poller.GpsPoller() # create the thread
gpsp.daemon = True
gpsp.start() # start it up

file_print ("Starting weather board")
wp = weather_poller.WxPoller() # create the thread
wp.daemon = True
wp.start() # start it up



file_print("Waiting for GPS")
for i in range(0,20):
	lcd.lcd_led_set(i % 7,1)
	time.sleep(0.5)
	lcd.lcd_led_set(i % 7,0)
	time.sleep(0.5)

file_print("Trying to set time from GPS")

if gps_poller.gpsd.utc != None and gps_poller.gpsd.utc != '':
	gpstime = gps_poller.gpsd.utc[0:4] + gps_poller.gpsd.utc[5:7] + gps_poller.gpsd.utc[8:10] + ' ' + gps_poller.gpsd.utc[11:13] + gps_poller.gpsd.utc[13:19]
	file_print("Setting time to GPS time %s" % gpstime)
	os.system('sudo date -u --set="%s"' % gpstime)
	file_print("Time has been set")
	lcd.lcd_update(gpstime, 0)
else:
	file_print("GPS time not available")
	lcd.lcd_update("No GPS time", 0)

# set up web cam
file_print("Finding visible camera")
#camera_visible = cv2.VideoCapture(0)
#camera_visible.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,720)
#camera_visible.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,1280)

try:
	wcp = webcam_poller.WebcamPoller()
	wcp.daemon = True
	wcp.start() # start it up
	file_print("Visible camera setup complete")
except:
	file_print("No visible camera found, exiting")
	exit()





file_print ("Finding infrared camera")
try:
	if len(sys.argv) > 1:
		camera = Aravis.Camera.new (sys.argv[1])
	else:
		camera = Aravis.Camera.new (None)
except:
	file_print ("No camera found")
	exit ()

payload = camera.get_payload ()
device = camera.get_device ()

file_print ("Initializing image capture settings")
device.set_integer_feature_value("IRFormat", 2) # 0 = signal; 2 = 0.01K Tlinear
device.set_integer_feature_value("IRFrameRate", 2) # 0 = 60 Hz, 1 = 30 Hz, 2 = 15 Hz
camera.set_region (0,0,640,480)
camera.set_frame_rate (10)
camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_16)
[x,y,width,height] = camera.get_region ()
num_buffers = 1;

file_print ("----------------------------")
file_print ("Camera vendor : %s" %(camera.get_vendor_name ()))
file_print ("Camera model  : %s" %(camera.get_model_name ()))
file_print ("Camera id     : %s" %(camera.get_device_id ()))
file_print ("ROI           : %dx%d at %d,%d" %(width, height, x, y))
file_print ("Payload       : %d" %(payload))
file_print ("Pixel format  : %s" %(camera.get_pixel_format_as_string ()))
file_print ("----------------------------")

file_print ("Start thermal stream")
stream = camera.create_stream (None, None)

file_print ("Create thermal buffers")
for i in range(0,num_buffers):
	stream.push_buffer (Aravis.Buffer.new_allocate (payload))

file_print( "Start thermal acquisition")
camera.start_acquisition ()

file_print ("Creating save queue")
save_queue.initialize_queue()
def queue_close():
	file_print("Waiting for last images to save")
	save_queue.save_queue.join()
	file_print("All images saved")

atexit.register(queue_close)




# set all LEDs high to verify
for index in range(0,7):
	lcd.lcd_led_set(index,1)
	time.sleep(0.1)
	lcd.lcd_led_set(index,0)
	time.sleep(0.1)

lcd.lcd_update("All systems OK",1)



file_print( "Entering main loop")
counter = 0
time_start = time.time()
stats = {}

program_running = True
program_paused = True
program_throttled = True

#while counter < 100:
while(program_running==True):

	(b_left, b_right) = lcd.lcd_check_buttons(50)
	if b_left == True:
		program_throttled = not program_throttled
		file_print("Left button pressed - throttle state now %d" % program_throttled)
	if b_right == True:
		program_paused = not program_paused
		file_print("Right button pressed - pause state now %d" % program_paused)
	if b_right == True and b_left == True:
		file_print("Both buttons pressed - exiting and shutting down")
		os.system("sudo shutdown now -h")

	if program_throttled==True:
		for i in range(1,5):
			time.sleep(0.25)				
			lcd.lcd_led_set(6,i%2)
	else:
		lcd.lcd_led_set(6,1)

	if program_paused==True:
		lcd.lcd_update("Paused",0)
		time.sleep(1)
	else:	
		if counter % 10 == 0:
			fps = counter / (time.time() - time_start)
			file_print("**** FPS = %.3f" % fps)

			freedisk_gb = float(disk_free_bytes()) / 1024 / 1024 / 1024
			lcd.lcd_update("Diskfree: %.2f GB" % freedisk_gb, 0)
			file_print("**** Free: %.2f GB" % freedisk_gb)

			if freedisk_gb < 0.5:
				file_print("Exiting, disk full")
				exit()

		if counter % 500 == 0:
			file_print('Non-uniformity correction')
			device.execute_command("NUCAction")
			#time.sleep(0.5)

		if counter % 1000 == 0:
			file_print('Autofocus')
			device.execute_command("AutoFocus")
			#time.sleep(3)
			distance = device.get_float_feature_value("FocusDistance")
			file_print("Setting object distance to %f meters" % distance)
			device.set_float_feature_value("ObjectDistance", distance)

		buffer = stream.pop_buffer ()

		# get camera stats
		if counter % 100 == 0:
			stats['AtmosphericTemperature'] = device.get_float_feature_value("AtmosphericTemperature")
			stats['EstimatedTransmission'] = device.get_float_feature_value("EstimatedTransmission")
			stats['ExtOpticsTemperature'] = device.get_float_feature_value("ExtOpticsTemperature")
			stats['ExtOpticsTransmission'] = device.get_float_feature_value("ExtOpticsTransmission")
			stats['ObjectDistance'] = device.get_float_feature_value("ObjectDistance")
			stats['ObjectEmissivity'] = device.get_float_feature_value("ObjectEmissivity")
			stats['ReflectedTemperature'] = device.get_float_feature_value("ReflectedTemperature")
			stats['RelativeHumidity'] = device.get_float_feature_value("RelativeHumidity")
			stats['FocusDistance'] = device.get_float_feature_value("FocusDistance")
			stats['TSens'] = device.get_float_feature_value("TSens")
			stats['alpha1'] = device.get_float_feature_value("alpha1")
			stats['alpha2'] = device.get_float_feature_value("alpha2")
			stats['B'] = device.get_float_feature_value("B")
			stats['beta1'] = device.get_float_feature_value("beta1")
			stats['beta2'] = device.get_float_feature_value("beta2")
			stats['F'] = device.get_float_feature_value("F")
			stats['J0'] = device.get_integer_feature_value("J0")
			stats['J1'] = device.get_float_feature_value("J1")
			stats['R'] = device.get_integer_feature_value("R")
			stats['X'] = device.get_float_feature_value("X")

		# get weather stats
		if counter % 10 == 0:
			(wx_status, wx_vals) = wp.wx
			if (wx_status == True):
				lcd.lcd_led_set(2,1)
			else:
				lcd.lcd_led_set(2,0)	
			stats['wx_uv_lux'] = wx_vals[0] # 0-based indexing
			stats['wx_vis_lux'] = wx_vals[1]
			stats['wx_ir_lux'] = wx_vals[2]
			stats['wx_temp_air_c'] = wx_vals[3]
			stats['wx_rel_hum_pct'] = wx_vals[4]
			stats['wx_pressure_hpa'] = wx_vals[5]

		# get gps stats
		global gpsd
		stats['gps_latitude']=gps_poller.gpsd.fix.latitude
		stats['gps_longitude']=gps_poller.gpsd.fix.longitude
		stats['gps_num_satellites']=len(gps_poller.gpsd.satellites)
		stats['gps_utc']=gps_poller.gpsd.utc
		stats['gps_time']=gps_poller.gpsd.fix.time
		if stats['gps_num_satellites']==0:
			lcd.lcd_led_set(1,0)
		else:
			lcd.lcd_led_set(1,1)
	
		# get current date
		stats['Date'] = datetime.datetime.now().strftime('%y%m%d-%H%M%S')


		file_print("**** Lat: %.3f Lon: %.3f Numsats: %d" % (stats["gps_latitude"], stats['gps_longitude'], stats['gps_num_satellites']))

		if counter % 10 == 0:
			file_print("Adjusting camera settings")
			stat_atm_temp = float(stats['wx_temp_air_c']) + 273.15
			stat_atm_rh  = float(stats['wx_rel_hum_pct'])
			device.set_float_feature_value("AtmosphericTemperature",stat_atm_temp)
			device.set_float_feature_value("RelativeHumidity",stat_atm_rh)

		fileprefix = '%s/out_%s_%d' % (output_dir, stats['Date'], counter)
		file_print("Setting output location %s" % fileprefix)
		lcd.lcd_update(stats['Date'], 0)

		if buffer:
			lcd.lcd_led_set(0,1)
			file_print('Reading infrared image data')
			#img = numpy.fromstring(ctypes.string_at(buffer.data_address(), buffer.size), dtype=numpy.uint16).reshape(480,640)
			data_infrared = numpy.ctypeslib.as_array(ctypes.cast(buffer.get_data(), ctypes.POINTER(ctypes.c_uint16)), (buffer.get_image_height(), buffer.get_image_width()))
			data_infrared = data_infrared.copy()

			file_print('Reading visible image data')
			#ret,image_visible = camera_visible.read()
			#image_visible = image_visible.copy()
			image_visible = wcp.im.copy()		

			if wcp.ret==True:
				lcd.lcd_led_set(3,1)
			else:
				lcd.lcd_led_set(3,0)

			file_print("Sending data to queue")
			save_queue.save_queue.put( (data_infrared, image_visible, fileprefix, uid, gid) )

			writer = csv.writer(open(fileprefix + '-stats.csv', 'w'),delimiter=',')
			writer.writerow(stats.keys())
			writer.writerow(stats.values())
			os.chown(fileprefix + "-stats.csv", uid, gid)

			file_print("Summarizing data")
			stat_mean = float(data_infrared.mean()) / 100.0 - 273.15 
			file_print("Mean value = %.3f" % stat_mean)
			lcd.lcd_update("%d %.1f %.2f" % (counter, stat_mean, freedisk_gb),1)

			stream.push_buffer(buffer)
		else:
			lcd.lcd_led_set(0,0)
			file_print('No buffer obtained')

		counter = counter + 1

file_print("Stopping acquisition")
camera.stop_acquisition()
