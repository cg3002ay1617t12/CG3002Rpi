from __future__ import division
import numpy as np
import math, os, sys, time, itertools
from collections import deque
import matplotlib.pyplot as plt
np.seterr(invalid='ignore')

class Localization(object):
	"""Class variables default, override in env.json"""
	NUM_POINTS    = 1000
	STRIDE_LENGTH = 30 # CM
	SAMPLES_PER_WINDOW    = 100
	SAMPLES_PER_PACKET    = 25
	SAMPLES_PER_SECOND    = 50
	VARIANCE_THRES        = 50

	def __init__(self, x=None, y=None, bearing=None, plot=False):
		self.t        = np.array([x for x in range(0, Localization.NUM_POINTS)])
		self.heading  = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_x = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_y = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_z = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.bearing  = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS) # Kalman filtered compass headings
		self.x        = x if x is not None else 0
		self.y        = y if y is not None else 0
		self.stride   = Localization.STRIDE_LENGTH
		self.is_plot  = plot
		self.FPS      = 30
		self.start    = time.time()
		self.new_data = False
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
			# print("Final estimate: %.2f" % self.est[0][0])
			# print(self.est)
			self.prev_est              = self.est
			self.prev_mea              = self.mea
			self.bearing.append(self.est[0][0])

	def get_stabilized_bearing(self):
		""" Convert values above 350 to x - 360 and calculate variance, only return readings when variance is low enough"""
		start = Localization.NUM_POINTS - Localization.SAMPLES_PER_PACKET
		window = list(itertools.islice(self.bearing, start, None))
		window = map(lambda x: 360 - x if x > 350 else x, window)
		var = np.var(window)
		if var < Localization.VARIANCE_THRES:
			return convert_to_positive(np.average(window))
		else:
			# special value to indicate unstable readings
			return -1.0

	def convert_to_positive(self, deg):
		""" Deg must be negative"""
		return (deg + 360) if deg < 0 else deg

	def run(self):
		if self.new_data:
			self.process_new_data()
		if self.is_plot:
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