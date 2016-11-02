from __future__ import division
import numpy as np
import math, os, sys, time, itertools
from collections import deque
import matplotlib.pyplot as plt
from audio import tts
np.seterr(invalid='ignore')
import time

class Localization(object):
	"""Class variables default, override in env.json"""
	NUM_POINTS    = 1000
	STRIDE_LENGTH = 30 # CM
	SAMPLES_PER_WINDOW    = 100
	SAMPLES_PER_PACKET    = 25
	SAMPLES_PER_SECOND    = 50
	VARIANCE_THRES        = 10000

	def __init__(self, x=None, y=None, bearing=None, north=0, plot=False):
		""" 
			North is measured clockwise from the +ve y-axis as given by the json map 
			Bearing is measured clockwise from North
		"""
		self.t                  = np.array([x_ for x_ in range(0, Localization.NUM_POINTS)])
		self.heading            = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_x           = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_y           = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_z           = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.bearing            = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS) # Kalman filtered compass headings
		self.stabilized_bearing = -1 # Last updated stabilized bearing reading
		self.x                  = x if x is not None else 0
		self.y                  = y if y is not None else 0
		self.north              = north
		self.stride             = Localization.STRIDE_LENGTH
		self.is_plot            = plot
		self.FPS                = 30
		self.start              = time.time()
		self.new_data           = False
		self.prev_step          = -1 # Bearing of last step taken
		if self.is_plot:
			self.init_plot()
		# Variables for kalman filter
		self.delta_t      = 1 / Localization.SAMPLES_PER_SECOND
		self.prev_est     = np.array([[0],[0]]) # bearing, angular velocity
		self.A            = np.array([[1, self.delta_t], [0, 1]])
		self.C            = np.eye(2) # Measurement matrix
		self.Q            = np.array([[10, 0], [0, 10]]) # Process noise covariance matrix, assume no noise
		self.prev_R       = np.array([[400, 0],[0, 25]]) # Measurement covariance matrix
		self.H            = np.eye(2) # Matrix to allow calculation of Kalman gain
		self.prev_cov_p   = np.array([[400, 0], [0, 25]]) # Previous predicted process covariance matrix
		self.prev_mea     = np.array([[0],[0]])

	def reset(self, x=None, y=None):
		self.x = x if x is not None else 0
		self.y = y if y is not None else 0

	def update_coordinates(self, x, y):
		self.x = x
		self.y = y

	def process_new_data(self):
		self.new_data = False
		# Kalman filter
		# Equation of motion : X_t = AX_t-1 + Bu_t + w_t, assume no angular acceleration, so = 0
		# Equation of motion : X = X_o + omega * t
		skip  = 1
		start = Localization.NUM_POINTS - Localization.SAMPLES_PER_PACKET
		heading_window  = itertools.islice(self.heading, start, None, skip)
		velocity_window = list(itertools.islice(self.rotate_x, start, None, skip))
		for (i, mea) in enumerate(heading_window):
			self.predicted_state       = np.dot(self.A, self.prev_est)
		 	self.predicted_cov_p       = np.dot(np.dot(self.A, self.prev_cov_p), self.A.T) + self.Q
		 	self.predicted_cov_p[0][1] = 0 # Zero out cross terms for numerical stability
		 	self.predicted_cov_p[1][0] = 0 # Zero out cross terms for numerical stability
		 	self.mea                   = np.dot(self.C, np.array([[mea], [velocity_window[i]]]))
		 	self.K                     = np.nan_to_num(np.true_divide(np.dot(self.predicted_cov_p, self.H), np.dot(np.dot(self.H, self.predicted_cov_p), self.H.T) + self.prev_R))
		 	self.est                   = self.predicted_state + np.dot(self.K, (self.mea - np.dot(self.H, self.predicted_state)))
		 	self.cov_p                 = np.dot((np.eye(2) - np.dot(self.K, self.H)), self.predicted_cov_p)
		 	self.prev_cov_p            = self.cov_p
		# 	# print("Final estimate: %.2f" % self.est[0][0])
		# 	# print(self.est)
		 	self.prev_est              = self.est
		 	self.prev_mea              = self.mea
		 	self.bearing.append(self.est[0][0])
		pass

	def get_stabilized_bearing(self, filtered=False):
		""" Convert values above 350 to x - 360 and calculate variance, only return readings when variance is low enough"""
		start = Localization.NUM_POINTS - Localization.SAMPLES_PER_PACKET
		if filtered:
			window = list(itertools.islice(self.bearing, start, None))
		else:
			window = list(itertools.islice(self.heading, start, None))
		# window = map(lambda x: 360 - x if x > 350 else x, window)
		# var = np.var(window)
		# if var < Localization.VARIANCE_THRES:
		return self.convert_to_positive(window[-1]) #np.average(window))
	#	else:
	#		# special value to indicate unstable readings
	#		return -1.0

	def convert_to_positive(self, deg):
		""" Deg must be negative"""
		return (deg + 360) if deg < 0 else deg

	def incr_step(self):
		self.calculate_new_position(1, incr=True)

	def decr_step(self):
		self.calculate_new_position(1, incr=False)

	def calculate_new_position(self, steps_taken, direction=None, incr=False):
		if direction is None:
			update_prev = False
			direction = self.prev_step if incr else (self.prev_step + 180) % 360
		else:
			update_prev = True
		theta = (90 - self.north - direction)
		if theta >= 180:
			theta = theta - 360
		elif theta <= -180:
			theta = 360 + theta
		else:
			print("[LOCALIZATION] Error calculating theta!")
		hypo  = Localization.STRIDE_LENGTH * steps_taken
		self.x = self.x + math.floor(hypo * math.cos(math.pi * theta / 180))
		self.y = self.y + math.floor(hypo * math.sin(math.pi * theta / 180))
		print("[LOCALIZATION] New position: (%d, %d) Bearing: %.2f" %(int(self.x), int(self.y), direction))
		if update_prev:
			self.prev_step = direction

	def run(self, steps_taken, angle=None):
		direction = self.get_stabilized_bearing()
		update_direction = angle if angle is not None else direction
		if direction == -1:
			if (time.time() - self.start) > 5:
				self.start = time.time()
				print("[LOCALIZATION] Not receiving compass readings")
				tts("ERROR, Check connection with Arduino... Reset when ready")
		if direction >= 0:
			# Update stabilized bearing
			if time.time() - self.start > 5:
				self.start = time.time()
				print("[LOCALIZATION] Updated stabilized bearing %d" % (direction))
			self.stabilized_bearing = direction
		if self.new_data:
			# Update incoming data
			self.process_new_data()
		if steps_taken > 0 and direction > 0:
			print("[LOCALIZATION] %d steps taken in %.2f" % (steps_taken, direction))
			# Update x, y
			self.calculate_new_position(steps_taken, update_direction)
		if self.is_plot:
			# Update plot
			if (time.time() - self.start) > 1/self.FPS:
				start = time.time()
				self.plot(self.linex, self.rotate_x)
				self.plot(self.liney, self.rotate_y)
				self.plot(self.linez, self.rotate_z)
				self.plot(self.lineh[0], self.heading)
				self.fig.canvas.draw()

	def plot(self, lines, data):
		data = np.array(data)
		lines.set_ydata(data)
		plt.pause(0.01)

	def init_plot(self):
		self.fig, (self.axx, self.axy, self.axz, self.axh) = plt.subplots(4, 1, figsize=(10,10))
		self.axx.grid(True)
		self.axy.grid(True)
		self.axz.grid(True)
		self.axh.grid(True)
		self.axx.set_xticks(np.arange(0,Localization.NUM_POINTS,Localization.NUM_POINTS/20))
		self.axx.set_ylim(-180,180)
		self.axx.set_xlim(0,Localization.NUM_POINTS)
		self.axx.set_xlabel('samples / n')
		self.axx.set_ylabel('angular velocity (deg/s)')
		self.axx.set_title("Omega_x(t)")
		self.axy.set_xticks(np.arange(0,Localization.NUM_POINTS,Localization.NUM_POINTS/20))
		self.axy.set_ylim(-180,180)
		self.axy.set_xlim(0,Localization.NUM_POINTS)
		self.axy.set_xlabel('samples / n')
		self.axy.set_ylabel('angular velocity (deg/s)')
		self.axy.set_title("Omega_y(t)")
		self.axz.set_xticks(np.arange(0,Localization.NUM_POINTS,Localization.NUM_POINTS/20))
		self.axz.set_ylim(-180,180)
		self.axz.set_xlim(0,Localization.NUM_POINTS)
		self.axz.set_xlabel('samples / n')
		self.axz.set_ylabel('angular velocity (deg/s)')
		self.axz.set_title("Omega_z(t)")
		self.axh.set_xticks(np.arange(0,Localization.NUM_POINTS,Localization.NUM_POINTS/20))
		self.axh.set_ylim(0,360)
		self.axh.set_xlim(0,Localization.NUM_POINTS)
		self.axh.set_xlabel('samples / n')
		self.axh.set_ylabel('Degrees')
		self.axh.set_title("Compass heading")
		self.linex, = self.axx.plot(self.t, np.array(self.rotate_x), color="red", linestyle="solid")
		self.liney, = self.axy.plot(self.t, np.array(self.rotate_y), color="green", linestyle="solid")
		self.linez, = self.axz.plot(self.t, np.array(self.rotate_z), color="blue", linestyle="solid")
		self.lineh  = self.axh.plot(self.t, np.array(self.heading), color="black", linestyle="solid")
		plt.ion()
		plt.show()
