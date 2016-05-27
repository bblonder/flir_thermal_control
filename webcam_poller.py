#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
 
import os
import cv2
from time import *
import time
import threading
 
camera_visible = None #seting the global variable
 
#os.system('clear') #clear the terminal (optional)
 
class WebcamPoller(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		global camera_visible #bring it in scope

		camera_visible = cv2.VideoCapture(0)
		camera_visible.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,720)
		camera_visible.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,1280)

		self.current_value = None
		self.running = True #setting the thread running to true
		self.daemon = True

		self.im = None
		self.ret = 0
 
	def run(self):
		global camera_visible
		while self.running:
			(ret, im) = camera_visible.read()
			self.im = im
			self.ret = ret
 
