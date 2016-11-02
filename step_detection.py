import numpy as np
import math, random, os, sys, signal, time, serial, itertools
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class StepDetector(object):
	NUM_POINTS            = 1000
	SAMPLES_PER_PACKET    = 25
	SAMPLES_PER_WINDOW    = 100
	INTERRUPTS_PER_WINDOW = SAMPLES_PER_WINDOW / SAMPLES_PER_PACKET
	PIPE                  = './data_pipe'
	COEFFICIENTS_LOW_0_HZ = {
	    'alpha': [1, -1.979133761292768, 0.979521463540373],
	    'beta':  [0.000086384997973502, 0.000172769995947004, 0.000086384997973502]
	  }
	COEFFICIENTS_LOW_5_HZ = {
		'alpha': [1, -1.80898117793047, 0.827224480562408],
		'beta':  [0.095465967120306, -0.172688631608676, 0.095465967120306]
	}
	COEFFICIENTS_HIGH_1_HZ = {
		'alpha': [1, -1.905384612118461, 0.910092542787947],
		'beta':  [0.953986986993339, -1.907503180919730, 0.953986986993339]
	}
	def __init__(self, thres=None, data_pipe=None, plot=False):
		random.seed()
		self.total_steps     = 0
		self.curr_steps      = 0
		self.interrupt_count = 0
		self.data_pipe       = data_pipe
		self.t               = np.array([x for x in range(0, StepDetector.NUM_POINTS)])
		self.ax              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.ay              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.az              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.xg              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.yg              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.zg              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.xu              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.yu              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.zu              = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.a               = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.a_l             = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.a_h             = deque(np.zeros((StepDetector.NUM_POINTS,)), StepDetector.NUM_POINTS)
		self.THRES           = 3 if thres is None else thres # threshold for peaks, to be determined empirically
		self.FPS             = 30
		self.is_plot         = plot
		self.new_data        = False # flag to synchronize between interrupts and data processing
		self.start           = time.time()
		self.prev            = (-1, -1, -1) # (x, y, bearing) of last step taken
		# if data_pipe is None: self.setup_comm()
		if self.is_plot:
			self.init_plot()

	def filter_sig(self, start, data, coefficients):
		data = list(data)
		filtered_data = start
		for i in range(2, len(data)):
			filtered_data.append(coefficients['alpha'][0] * 
								data[i] * coefficients['beta'][0] +
								data[i-1] * coefficients['beta'][1] +
								data[i-2] * coefficients['beta'][2] -
								filtered_data[i-1] * coefficients['alpha'][1] -
								filtered_data[i-2] * coefficients['alpha'][2])
		return filtered_data[2:]

	def generate_data(self, amp=10, period=4, noise=1):
		"""Generate sinuisoidal data to test our filter 
		amp is amplitude in ms^-2 and period is time in seconds, noise is std of noise term"""
		t = np.linspace(0,100, NUM_POINTS)
		data = amp * np.sin( t / period) + np.random.normal(0, noise, NUM_POINTS)
		return (t, data)

	def generate_z(self, amp=10, period=4, noise=1):
		"""Generate accelerometer readings which is a linear combination of high frequency from user and 0 frequency from gravity"""
		t = np.linspace(0,100, NUM_POINTS)
		data = amp * np.sin( t / period) + np.random.normal(0, noise, NUM_POINTS) + np.ones((NUM_POINTS,))* -9.89
		return (t, data)

	def plot(self, lines, data):
		data = np.array(data)
		lines.set_ydata(data)
		plt.pause(0.01)

	def init_plot(self):
		self.fig, (self.axx, self.axy, self.axz) = plt.subplots(3, 1, figsize=(10,10))
		self.axx.grid(True)
		self.axy.grid(True)
		self.axz.grid(True)
		self.axx.set_xticks(np.arange(0,StepDetector.NUM_POINTS,StepDetector.NUM_POINTS/20))
		self.axx.set_ylim(-10,10)
		self.axx.set_xlim(0,StepDetector.NUM_POINTS)
		self.axx.set_xlabel('samples / n')
		self.axx.set_ylabel('acceleration (m/s^2')
		self.axx.set_title("x(t)")
		self.axy.set_xticks(np.arange(0,StepDetector.NUM_POINTS,StepDetector.NUM_POINTS/20))
		self.axy.set_ylim(-10,10)
		self.axy.set_xlim(0,StepDetector.NUM_POINTS)
		self.axy.set_xlabel('samples / n')
		self.axy.set_ylabel('acceleration (m/s^2')
		self.axy.set_title("y(t)")
		self.axz.set_xticks(np.arange(0,StepDetector.NUM_POINTS,StepDetector.NUM_POINTS/20))
		self.axz.set_ylim(-10,10)
		self.axz.set_xlim(0,StepDetector.NUM_POINTS)
		self.axz.set_xlabel('samples / n')
		self.axz.set_ylabel('acceleration (m/s^2')
		self.axz.set_title("z(t)")
		self.linex, = self.axx.plot(self.t, np.array(self.ax), color="red", linestyle="solid")
		self.liney, = self.axy.plot(self.t, np.array(self.ay), color="green", linestyle="solid")
		self.linez, = self.axz.plot(self.t, np.array(self.az), color="blue", linestyle="solid")
		plt.ion()
		plt.show()

	def decr_step(self):
		""" Need to work backwards to update new x,y coordinates"""
		self.total_steps -= 1

	def reset_step(self):
		self.total_steps = 0
		self.curr_steps  = 0

	def incr_step(self):
		""" Need to take another step forward in the last recorded bearing"""
		self.total_steps += 1
		self.curr_steps = 1

	def setup_comm(self):
		pid = os.getpid()
		fpid = open('./pid', 'w')
		fpid.write(str(pid))
		fpid.close()
		pipe_desc = os.open(StepDetector.PIPE, os.O_RDONLY)
		pipe = os.fdopen(pipe_desc)
		self.data_pipe = pipe

	def count_steps(self, z_c_idx, p_t_idx):
		steps = 0
		if len(z_c_idx) == 0 or len(p_t_idx) == 0:
			return steps
		j = 0
		for i in range(0,len(z_c_idx)):
			v = z_c_idx[i]
			try:
				while (p_t_idx[j] < v):
					j += 1
				steps += 1
				# print("Step detected: %d" % self.step)
			except Exception as e:
				break
		return steps

	def process_new_data(self):
		self.new_data = False
		window = StepDetector.NUM_POINTS - StepDetector.SAMPLES_PER_PACKET
		self.xg.extend(self.filter_sig([self.xg[-2], self.xg[-1]], itertools.islice(self.ax, window, None), StepDetector.COEFFICIENTS_LOW_0_HZ))
		self.yg.extend(self.filter_sig([self.yg[-2], self.yg[-1]], itertools.islice(self.ay, window, None), StepDetector.COEFFICIENTS_LOW_0_HZ))
		self.zg.extend(self.filter_sig([self.zg[-2], self.zg[-1]], itertools.islice(self.az, window, None), StepDetector.COEFFICIENTS_LOW_0_HZ))

		self.xu.extend(np.array(list(itertools.islice(self.ax, window, None))) - np.array(list(itertools.islice(self.xg, window, None))))
		self.yu.extend(np.array(list(itertools.islice(self.ay, window, None))) - np.array(list(itertools.islice(self.yg, window, None))))
		self.zu.extend(np.array(list(itertools.islice(self.az, window, None))) - np.array(list(itertools.islice(self.zg, window, None))))

		# Isolate user acceleration in direction of gravity
		self.a.extend(np.array(list(itertools.islice(self.xu, window, None)))
			* np.array(list(itertools.islice(self.xg, window, None))) 
			+ np.array(list(itertools.islice(self.yu, window, None)))
			* np.array(list(itertools.islice(self.yg, window, None)))
			+ np.array(list(itertools.islice(self.zu, window, None)))
			* np.array(list(itertools.islice(self.zg, window, None))))

		# Remove all signals above 5 Hz
		self.a_l.extend(self.filter_sig([self.a_l[-2], self.a_l[-1]], itertools.islice(self.a, window, None), StepDetector.COEFFICIENTS_LOW_5_HZ))
		# Remove slow peaks
		self.a_h.extend(self.filter_sig([self.a_h[-2], self.a_h[-1]], itertools.islice(self.a_l, window, None), StepDetector.COEFFICIENTS_HIGH_1_HZ))

		self.interrupt_count += 1
		# print("Interrupted %d" % self.interrupt_count)
		if self.interrupt_count % StepDetector.INTERRUPTS_PER_WINDOW == 0:
			steps_window_start = StepDetector.NUM_POINTS - (StepDetector.SAMPLES_PER_WINDOW)
			steps_window_end   = steps_window_start + StepDetector.INTERRUPTS_PER_WINDOW * StepDetector.SAMPLES_PER_PACKET 
			# find negative zero crossings
			combined_window = list(itertools.islice(self.a_h, steps_window_start, steps_window_end))
			negative_zero_crossings = np.zeros(len(combined_window))
			sign = np.sign(combined_window)
			for x in range(1, sign.shape[0]):
				if sign[x-1] == 1 and sign[x] == -1:
					negative_zero_crossings[x] = 1
			z_c_idx = np.where(negative_zero_crossings==1)[0]

			# Find positive threshold crossings
			translated = np.sign(combined_window - np.ones(len(combined_window))*self.THRES)

			positive_thres_crossings = np.zeros(translated.shape)
			for x in range(1, translated.shape[0]):
				if translated[x-1] == -1 and translated[x] == 1:
					positive_thres_crossings[x] = -1
			p_t_idx = np.where(positive_thres_crossings==-1)[0]
			self.curr_steps  = self.count_steps(p_t_idx, z_c_idx)
			self.total_steps = self.total_steps + self.curr_steps
			if self.curr_steps > 0:
				self.curr_steps = 1 # Force steps to be detected one at a time
				print("[STEP COUNTER] Step %d, with threshold %.2f" % (self.curr_steps, self.THRES))

	def run(self):
		if self.new_data:
			self.process_new_data()
		if self.is_plot:
			if (time.time() - self.start) > 1/self.FPS:
				start = time.time()
				self.plot(self.linex, self.a_h)
				self.plot(self.liney, self.yu)
				self.plot(self.linez, self.zu)
				self.fig.canvas.draw()

def main():
	counter = StepDetector(plot=True)
	counter.run()

	# (x, ax) = generate_data(amp=3, period=0.5, noise=0.01) # x(t)
	# (y, ay) = generate_data(amp=3, period=0.5, noise=0.01) # y(t)
	# (z, az) = generate_z(amp=3, period=10000, noise=0.01) # z(t)

if __name__ == "__main__":
	main()
