import Queue
import time
from threading import Thread
import cv2
import os
import numpy

def image_worker():
	global save_queue

	while True:
		item = save_queue.get(True, None) # block until item available
		
		data_infrared = item[0]
		img_visible = item[1]
		fileprefix = item[2]
		uid = item[3]
		gid = item[4]

		print("Saving to %s" % fileprefix)

		# save the infrared data
		numpy.save(fileprefix + '-infrared-data.npy', data_infrared)
		os.chown(fileprefix + "-infrared-data.npy", uid, gid)

		# generate a PNG preview of the infrared data, coloring by temperature
		imgscaled = ((data_infrared - numpy.percentile(data_infrared,1)).astype(float) / (numpy.percentile(data_infrared,99) - numpy.percentile(data_infrared,2.5)).astype(float)) * 255
		imgscaled[imgscaled < 0] = 0
		imgscaled[imgscaled > 255] = 255
		imgscaled = cv2.convertScaleAbs(imgscaled)
		imgscaledcolored = cv2.applyColorMap(imgscaled, cv2.COLORMAP_OCEAN)
		cv2.imwrite(fileprefix + '-infrared.png', imgscaledcolored)
		os.chown(fileprefix + "-infrared.png", uid, gid)

		# save the visible data
		cv2.imwrite(fileprefix + "-visible.png",img_visible)
		os.chown(fileprefix + "-visible.png", uid, gid)

		save_queue.task_done()





num_workers = 4
queue_size = 256

save_queue = None

def initialize_queue():
	global save_queue

	save_queue = Queue.Queue(maxsize=queue_size)

	for i in range(num_workers):
		t = Thread(target=image_worker)
		t.daemon = True
		t.start()




#q.join()       # block until all tasks are done
