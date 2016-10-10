import numpy as np
import math, os, sys, time
from collections import deque
import matplotlib.pyplot as plt

class Localization(object):
	"""Class variables default, override in env.json"""
	NUM_POINTS    = 1000
	STRIDE_LENGTH = 30 # CM

	def __init__(self, x=None, y=None, bearing=None, plot=False):
		self.t        = np.array([x for x in range(0, Localization.NUM_POINTS)])
		self.heading  = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_x = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_y = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.rotate_z = deque(np.zeros((Localization.NUM_POINTS,)), Localization.NUM_POINTS)
		self.bearing  = bearing # Initial bearing, also the final value output of this module
		self.x        = x if x is not None else 0
		self.y        = y if y is not None else 0
		self.stride   = Localization.STRIDE_LENGTH
		self.is_plot  = plot
		self.FPS      = 30
		self.start    = time.time()
		self.new_data = False
		if self.is_plot:
			self.init_plot()

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
	
	def process_new_data(self):
		self.new_data = False
		# Run Kalman filter

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