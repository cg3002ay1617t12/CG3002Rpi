import numpy as np
import math, random, os, sys, signal, time, serial, itertools
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

np.set_printoptions(threshold=np.inf)
random.seed()

NUM_POINTS = 1000
SAMPLES_PER_PACKET = 25
PIPE = '/Users/Jerry/CG3002Rpi/pipe'
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

ax = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
ay = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
az = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
xg = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
yg = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
zg = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
xu = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
yu = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
zu = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
a  = deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
a_l= deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
a_h= deque(np.zeros((NUM_POINTS,)), NUM_POINTS)
step = 0
interrupt_count = 0

def filter_sig(start, data, coefficients):
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

def generate_data(amp=10, period=4, noise=1):
	"""Generate sinuisoidal data to test our filter 
	amp is amplitude in ms^-2 and period is time in seconds, noise is std of noise term"""
	t = np.linspace(0,100, NUM_POINTS)
	data = amp * np.sin( t / period) + np.random.normal(0, noise, NUM_POINTS)
	return (t, data)

def generate_z(amp=10, period=4, noise=1):
	"""Generate accelerometer readings which is a linear combination of high frequency from user and 0 frequency from gravity"""
	t = np.linspace(0,100, NUM_POINTS)
	data = amp * np.sin( t / period) + np.random.normal(0, noise, NUM_POINTS) + np.ones((NUM_POINTS,))* -9.89
	return (t, data)

def plot(lines, data):
	data = np.array(data)
	lines.set_ydata(data)
	plt.pause(0.01)

def init():
	fig, (axx, axy, axz) = plt.subplots(3, 1, figsize=(10,10))
	axx.grid(True)
	axy.grid(True)
	axz.grid(True)
	axx.set_xticks(np.arange(0,NUM_POINTS,NUM_POINTS/20))
	axx.set_ylim(-10,10)
	axx.set_xlim(0,NUM_POINTS)
	axx.set_xlabel('samples / n')
	axx.set_ylabel('acceleration (m/s^2')
	axx.set_title("x(t)")
	axy.set_xticks(np.arange(0,NUM_POINTS,NUM_POINTS/20))
	axy.set_ylim(-10,10)
	axy.set_xlim(0,NUM_POINTS)
	axy.set_xlabel('samples / n')
	axy.set_ylabel('acceleration (m/s^2')
	axy.set_title("y(t)")
	axz.set_xticks(np.arange(0,NUM_POINTS,NUM_POINTS/20))
	axz.set_ylim(-10,10)
	axz.set_xlim(0,NUM_POINTS)
	axz.set_xlabel('samples / n')
	axz.set_ylabel('acceleration (m/s^2')
	axz.set_title("z(t)")
	linex, = axx.plot(t, np.array(ax), color="red", linestyle="solid")
	liney, = axy.plot(t, np.array(ay), color="green", linestyle="solid")
	linez, = axz.plot(t, np.array(az), color="blue", linestyle="solid")
	plt.ion()
	plt.show()
	return (fig, axx, axy, axz, linex, liney, linez)

def setup_comm():
	pid = os.getpid()
	fpid = open('./pid', 'w')
	fpid.write(str(pid))
	fpid.close()
	
	PIPE = '/Users/Jerry/CG3002Rpi/pipe'
	pipe_desc = os.open(PIPE, os.O_RDONLY)
	pipe = os.fdopen(pipe_desc)
	return pipe

def count_steps(z_c_idx, p_t_idx):
	global step
	if len(z_c_idx) == 0 or len(p_t_idx) == 0:
		return
	j = 0
	for i in range(0,len(z_c_idx)):
		v = z_c_idx[i]
		try:
			while (p_t_idx[j] < v):
				j += 1
			step += 1
			print("Step detected: %d" % step)
		except Exception as e:
			break

t = np.array([x for x in range(0, NUM_POINTS)])
def main():
	global count,ax,ay,az,xg,yg,zg,xu,yu,zu,a,a_l,a_h,step,interrupt_count
	# Define variables
	THRES = 2 # threshold for peaks, to be determined empirically
	FPS  = 30
	start = time.time()
	pipe = setup_comm()
	def serial_handler(signum, frame, *args, **kwargs):
		global interrupt_count
		def process(datum):
			try:
				(x,y,z) = map(lambda x: x.strip('\r\n'), datum.split(','))
				ax.append(float(x))
				ay.append(float(y))
				az.append(float(z))
			except ValueError as e:
				print e
		line_count = SAMPLES_PER_PACKET
		buffer_ = []
		while line_count > 0:
			data = pipe.readline()
			buffer_.append(data)
			line_count -= 1
		map(process, buffer_)
		window = NUM_POINTS - SAMPLES_PER_PACKET
		xg.extend(filter_sig([xg[-2], xg[-1]], itertools.islice(ax, window, None), COEFFICIENTS_LOW_0_HZ))
		yg.extend(filter_sig([yg[-2], yg[-1]], itertools.islice(ay, window, None), COEFFICIENTS_LOW_0_HZ))
		zg.extend(filter_sig([zg[-2], zg[-1]], itertools.islice(az, window, None), COEFFICIENTS_LOW_0_HZ))

		xu.extend(np.array(list(itertools.islice(ax, window, None))) - np.array(list(itertools.islice(xg, window, None))))
		yu.extend(np.array(list(itertools.islice(ay, window, None))) - np.array(list(itertools.islice(yg, window, None))))
		zu.extend(np.array(list(itertools.islice(az, window, None))) - np.array(list(itertools.islice(zg, window, None))))

		# Isolate user acceleration in direction of gravity
		a.extend(np.array(list(itertools.islice(xu, window, None)))
			* np.array(list(itertools.islice(xg, window, None))) 
			+ np.array(list(itertools.islice(yu, window, None)))
			* np.array(list(itertools.islice(yg, window, None)))
			+ np.array(list(itertools.islice(zu, window, None)))
			* np.array(list(itertools.islice(zg, window, None))))

		# Remove all signals above 5 Hz
		a_l.extend(filter_sig([a_l[-2], a_l[-1]], itertools.islice(a, window, None), COEFFICIENTS_LOW_5_HZ))
		# Remove slow peaks
		a_h.extend(filter_sig([a_h[-2], a_h[-1]], itertools.islice(a_l, window, None), COEFFICIENTS_HIGH_1_HZ))

		interrupt_count += 1
		if interrupt_count % 4 == 0:
			steps_window = NUM_POINTS - 4 * SAMPLES_PER_PACKET
			# find negative zero crossings
			combined_window = list(itertools.islice(a_h, steps_window, None))
			f_two_shifted = np.hstack(([1,1], np.sign(combined_window)))
			f_one_b_one_shifted = np.hstack(([1], np.sign(combined_window), [1]))
			b_two_shifted = np.hstack((np.sign(combined_window), [1,1]))
			zero_crossings = np.multiply(b_two_shifted, f_one_b_one_shifted)
			negative_zero_crossings = np.multiply(np.where(zero_crossings==-1, zero_crossings, np.zeros(len(zero_crossings))), f_two_shifted)
			z_c_idx = np.where(negative_zero_crossings[2:]==1)[0]
			# print(z_c_idx)

			# Find positive threshold crossings
			translated = np.sign(combined_window - np.ones(len(combined_window))*THRES)
			f_two_shifted = np.hstack(([1,1], translated))
			f_one_b_one_shifted = np.hstack(([1], translated,[1]))
			b_two_shifted = np.hstack((translated,[1,1]))
			thres_crossings = np.multiply(b_two_shifted, f_one_b_one_shifted)
			positive_thres_crossings = np.multiply(np.where(thres_crossings==-1, thres_crossings, np.zeros(len(thres_crossings))), f_two_shifted)
			p_t_idx = np.where(positive_thres_crossings[2:]==-1)[0]
			# print(p_t_idx)

			count_steps(z_c_idx, p_t_idx)
	
	# Register signals and handlers
	signal.signal(signal.SIGUSR1, serial_handler)
	(fig, axx, axy, axz, linex, liney, linez) = init()
	steps = 0
	while True:
		# Before filter
		
		# Step counting
		if (time.time() - start) > 1/FPS:
			start = time.time()
			plot(linex, a_h)
			plot(liney, yu)
			plot(linez, zu)
			fig.canvas.draw()

	# (x, ax) = generate_data(amp=3, period=0.5, noise=0.01) # x(t)
	# (y, ay) = generate_data(amp=3, period=0.5, noise=0.01) # y(t)
	# (z, az) = generate_z(amp=3, period=10000, noise=0.01) # z(t)
	
	# Acceleration due to gravity
	plot(axx, t, xg, "solid", "x_g(t)")
	plot(axy, t, yg, "dashed", "y_g(t)")
	plot(axz, t, zg, "dotted", "z_g(t)")

	# Acceleration due to user
	xu = ax - xg
	yu = ay - yg
	zu = az - zg
	plot(axx, t, xu, "solid", "x_u(t)")
	plot(axy, t, yu, "dashed", "y_u(t)")
	plot(axz, t, zu, "dotted", "z_u(t)")

	# Isolate user acceleration in direction of gravity
	a = xu * xg + yu * yg + zu * zg
	plot(time, a, "solid", "User acceleration in direction of gravity")

	# Remove all signals above 5 Hz
	a_l = filter_sig(a, COEFFICIENTS_LOW_5_HZ)
	# Remove slow peaks
	a_h = filter_sig(a_l, COEFFICIENTS_HIGH_1_HZ)
	plot(x, a_h, "solid", "Final smoothed signal")

	# find negative zero crossings
	f_two_shifted = np.hstack(([1,1], np.sign(a_h)))
	f_one_b_one_shifted = np.hstack(([1], np.sign(a_h), [1]))
	b_two_shifted = np.hstack((np.sign(a_h), [1,1]))
	zero_crossings = np.multiply(b_two_shifted, f_one_b_one_shifted)
	negative_zero_crossings = np.multiply(np.where(zero_crossings==-1, zero_crossings, np.zeros(len(zero_crossings))), f_two_shifted)
	z_c_idx = np.where(negative_zero_crossings[2:]==1)[0]
	# print(z_c_idx)

	# Find positive threshold crossings
	translated = np.sign(a_h - np.ones(len(a_h))*THRES)
	f_two_shifted = np.hstack(([1,1], translated))
	f_one_b_one_shifted = np.hstack(([1], translated,[1]))
	b_two_shifted = np.hstack((translated,[1,1]))
	thres_crossings = np.multiply(b_two_shifted, f_one_b_one_shifted)
	positive_thres_crossings = np.multiply(np.where(thres_crossings==-1, thres_crossings, np.zeros(len(thres_crossings))), f_two_shifted)
	p_t_idx = np.where(positive_thres_crossings[2:]==-1)[0]
	# print(p_t_idx)

	# Count steps - a step is counted only if a threshold crossing occurs after a negative zero crossing
	j = 0
	count = 0
	for i in range(0,len(z_c_idx)):
		v = z_c_idx[i]
		try:
			while (p_t_idx[j] < v):
				j += 1
			count += 1
		except Exception as e:
			print e
			break
	print("Num of steps is : %d" % count)

if __name__ == "__main__":
	main()