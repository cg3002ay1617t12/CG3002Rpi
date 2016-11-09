import cv2, io
import numpy as np
from picamera import PiCamera
from time import time

class ObstacleDetector(object):
	
	def __init__(self):
		self.cam = PiCamera()
		self.banana_cascade = cv2.CascadeClassifier('banana_classifier.xml')

	def test(self):
		img = cv2.imread('img/banana5.jpg')

		bans = banana_cascade.detectMultiScale(img, 1.2, 5)
		for (x,y,w,h) in bans:
			cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
			roi_color = img[y:y+h, x:x+w]

		cv2.imshow('img',img)
		cv2.waitKey(0)
		cv2.destroyAllWindows()

	def run(self):
		# Take a picture
		stream = io.BytesIO()
		self.cam.start_preview()
		time.sleep(2)
		pi_img = self.cam.capture(stream, format='jpeg')
		data = np.fromstring(stream.getvalue(), dtype=np.uint8)
		cv_img = cv2.imdecode(data, 1)
		
		# Detect banana
		banana = self.banana_cascade.detectMultiScale(cv_img, 1.2, 5)
		print(banana)
		for (x,y,w,h) in banana:
			cv2.rectangle(cv_img,(x,y),(x+w,y+h),(255,0,0),2)
			roi_color = cv_img[y:y+h, x:x+w]
		
		# Write to file
		cv2.imwrite("./img_classified.jpg", cv_img)

		if len(banana) > 0:
			return True
		else:
			return False

if __name__ == "__main__":
	detector = ObstacleDetector()
	detector.test()