#!/usr/bin/env python

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
from imutils.video import VideoStream

gi.require_version('Aravis', '0.4')
from gi.repository import Aravis

import gps_poller
import weather_poller

# load in the custom scripts
import lcd
def lcd_close_board():
	print("Closing LCDs")
	lcd.lcd_clear()
	for index in range(0,7):
		lcd.lcd_led_set(index, 0)

atexit.register(lcd_close_board)


def disk_free_bytes():
	stats = os.statvfs("/")
	free = stats.f_bavail * stats.f_frsize

	return free



uid = int(os.environ.get('SUDO_UID'))
gid = int(os.environ.get('SUDO_GID'))


# set up LCD
print ("Setting up LCD")
lcd.lcd_setup()
lcd.lcd_update("Thermal control",0)

# set up web cam
print("Finding visible camera")
#camera_visible = cv2.VideoCapture(0)
#camera_visible.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,720)
#camera_visible.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,1280)
vs = None
try:
	vs = VideoStream(0,resolution=(1280,720),framerate=24)
	vs.start()
	print("Visible camera setup complete")
except:
	print("No visible camera found, exiting")
	exit()


print "Finding results directory"
output_dir = os.path.expanduser("~/Desktop/results_%s" % datetime.datetime.now().strftime('%y%m%d-%H%M%S'))
if not os.path.isdir(output_dir):
	print "Creating results directory %s" % output_dir
	os.makedirs(output_dir)
	os.chown(output_dir, uid, gid)
else:
	print ("Found results directory")

print "Finding infrared camera"
try:
	if len(sys.argv) > 1:
		camera = Aravis.Camera.new (sys.argv[1])
	else:
		camera = Aravis.Camera.new (None)
except:
	print ("No camera found")
	exit ()

payload = camera.get_payload ()
device = camera.get_device ()

print "Initializing image capture settings"
device.set_integer_feature_value("IRFormat", 2) # 0 = signal; 2 = 0.01K Tlinear
device.set_integer_feature_value("IRFrameRate", 2) # 0 = 60 Hz, 1 = 30 Hz, 2 = 15 Hz
camera.set_region (0,0,640,480)
camera.set_frame_rate (10)
camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_16)
[x,y,width,height] = camera.get_region ()
num_buffers = 5;

print "----------------------------"
print "Camera vendor : %s" %(camera.get_vendor_name ())
print "Camera model  : %s" %(camera.get_model_name ())
print "Camera id     : %s" %(camera.get_device_id ())
print "ROI           : %dx%d at %d,%d" %(width, height, x, y)
print "Payload       : %d" %(payload)
print "Pixel format  : %s" %(camera.get_pixel_format_as_string ())
print "----------------------------"

print "Start thermal stream"
stream = camera.create_stream (None, None)

print "Create thermal buffers"
for i in range(0,num_buffers):
	stream.push_buffer (Aravis.Buffer.new_allocate (payload))

print "Start thermal acquisition"
camera.start_acquisition ()

print "Creating save queue"
save_queue.initialize_queue()
def queue_close():
	print("Waiting for last images to save")
	save_queue.save_queue.join()
	print("All images saved")

atexit.register(queue_close)


# get GPS going 
print "Starting GPS"
gpsp = gps_poller.GpsPoller() # create the thread
gpsp.daemon = True
gpsp.start() # start it up

print "Starting weather board"
wp = weather_poller.WxPoller() # create the thread
wp.daemon = True
wp.start() # start it up


# set all LEDs high to verify
for index in range(0,7):
	lcd.lcd_led_set(index,1)
	time.sleep(0.1)
	lcd.lcd_led_set(index,0)
	time.sleep(0.1)

lcd.lcd_update("All systems OK",1)



print "Entering main loop"
counter = 0
time_start = time.time()
stats = {}

program_running = True
program_paused = True
program_throttled = True

#while counter < 100:
while(program_running==True):
	if counter % 10 == 0:
		(b_left, b_right) = lcd.lcd_check_buttons(50)
		if b_left == True:
			program_throttled = not program_throttled
			print("Left button pressed - throttle state now %d" % program_throttled)
		if b_right == True:
			program_paused = not program_paused
			print("Right button pressed - pause state now %d" % program_paused)

	if program_throttled==True:
		print("Throttling for 1 second")
		for i in range(1,5):
			time.sleep(0.25)				
			lcd.lcd_led_set(6,i%2)
	else:
		lcd.lcd_led_set(6,1)

	if program_paused==True:
		print("Paused")
		lcd.lcd_update("Paused",0)
		time.sleep(1)
	else:	
		if counter % 10 == 0:
			fps = counter / (time.time() - time_start)
			print("**** FPS = %.3f" % fps)

			freedisk_gb = float(disk_free_bytes()) / 1024 / 1024 / 1024
			lcd.lcd_update("Diskfree: %.2f GB" % freedisk_gb, 0)
			print("**** Free: %.2f GB" % freedisk_gb)

			if freedisk_gb < 0.5:
				print("Exiting, disk full")
				exit()

		if counter % 500 == 0:
			print('Non-uniformity correction')
			device.execute_command("NUCAction")
			#time.sleep(0.5)

		if counter % 1000 == 0:
			print('Autofocus')
			device.execute_command("AutoFocus")
			#time.sleep(3)
			distance = device.get_float_feature_value("FocusDistance")
			print("Setting object distance to %f meters" % distance)
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


		print("**** Lat: %.3f Lon: %.3f Numsats: %d" % (stats["gps_latitude"], stats['gps_longitude'], stats['gps_num_satellites']))

		if counter % 10 == 0:
			print("Adjusting camera settings")
			stat_atm_temp = float(stats['wx_temp_air_c']) + 273.15
			stat_atm_rh  = float(stats['wx_rel_hum_pct'])
			device.set_float_feature_value("AtmosphericTemperature",stat_atm_temp)
			device.set_float_feature_value("RelativeHumidity",stat_atm_rh)

		fileprefix = '%s/out_%s_%d' % (output_dir, stats['Date'], counter)
		print("Setting output location %s" % fileprefix)
		lcd.lcd_update(stats['Date'], 0)

		if buffer:
			lcd.lcd_led_set(0,1)
			print('Reading infrared image data')
			#img = numpy.fromstring(ctypes.string_at(buffer.data_address(), buffer.size), dtype=numpy.uint16).reshape(480,640)
			data_infrared = numpy.ctypeslib.as_array(ctypes.cast(buffer.get_data(), ctypes.POINTER(ctypes.c_uint16)), (buffer.get_image_height(), buffer.get_image_width()))
			data_infrared = data_infrared.copy()

			print('Reading visible image data')
			#ret,image_visible = camera_visible.read()
			#image_visible = image_visible.copy()
			image_visible = vs.read()		

			if vs.stream.grabbed==True:
				lcd.lcd_led_set(3,1)
			else:
				lcd.lcd_led_set(3,0)

			print("Sending data to queue")
			save_queue.save_queue.put( (data_infrared, image_visible, fileprefix, uid, gid) )

			writer = csv.writer(open(fileprefix + '-stats.csv', 'w'),delimiter=',')
			writer.writerow(stats.keys())
			writer.writerow(stats.values())
			os.chown(fileprefix + "-stats.csv", uid, gid)

			print("Summarizing data")
			stat_mean = float(data_infrared.mean()) / 100.0 - 273.15 
			print("Mean value = %.3f" % stat_mean)
			lcd.lcd_update("%d %.1f %.2f" % (counter, stat_mean, freedisk_gb),1)

			stream.push_buffer(buffer)
		else:
			lcd.lcd_led_set(0,0)
			print('No buffer obtained')

		counter = counter + 1

print("Stopping acquisition")
camera.stop_acquisition()
