import cv2
from picamera import PiCamera

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
		img = self.cam.capture('./img.jpg')

		# Detect banana
		banana = self.banana_cascade.detectMultiScale(img, 1.2, 5)
		print(banana)
		for (x,y,w,h) in banana:
			cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
			roi_color = img[y:y+h, x:x+w]
		
		# Write to file
		cv2.imwrite("./img_classified.jpg", img)

		if len(banana) > 0:
			return True
		else:
			return False

if __name__ == "__main__":
	detector = ObstacleDetector()
	detector.test()