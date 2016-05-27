import time
import threading
import subprocess

def check_weather():
	wx = subprocess.check_output('/home/odroid/Desktop/control/c_weather/weather_board')
	if "ERROR" in wx:
		status = 0
		wx_split = [float('nan')] * 6
		print("weather board not logging")
	else:
		status = 1
		wx_split = wx.split("\n")
	
	return (status, wx_split)

class WxPoller(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.running = True #setting the thread running to true
		self.daemon = True
 
	def run(self):
		while self.running:
			self.wx = check_weather()
			time.sleep(1) 

	def cleanup_wx(self):
		print "\nKilling Thread..."
		self.running = False
		self.join() # wait for the thread to finish what it's doing
		print "Done.\nExiting."

