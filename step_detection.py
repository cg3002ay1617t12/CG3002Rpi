import numpy as np
import math, random
import matplotlib.pyplot as plt
# import pyserial

np.set_printoptions(threshold=np.inf)
random.seed()

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

def filter_sig(data, coefficients):
	filtered_data = [0,0]
	for i in range(2, len(data)):
		filtered_data.append(coefficients['alpha'][0] * 
							data[i] * coefficients['beta'][0] +
							data[i-1] * coefficients['beta'][1] +
							data[i-2] * coefficients['beta'][2] -
							filtered_data[i-1] * coefficients['alpha'][1] -
							filtered_data[i-2] * coefficients['alpha'][2])
	return filtered_data

def generate_data(amp=10, period=4, noise=1):
	"""Generate sinuisoidal data to test our filter 
	amp is amplitude in ms^-2 and period is time in seconds, noise is std of noise term"""
	NUM_POINTS = 5000
	t = np.linspace(0,100, NUM_POINTS)
	data = amp * np.sin( t / period) + np.random.normal(0, noise, NUM_POINTS)
	return (t, data)

def generate_z(amp=10, period=4, noise=1):
	"""Generate accelerometer readings which is a linear combination of high frequency from user and 0 frequency from gravity"""
	NUM_POINTS = 5000
	t = np.linspace(0,100, NUM_POINTS)
	data = amp * np.sin( t / period) + np.random.normal(0, noise, NUM_POINTS) + np.ones((NUM_POINTS,))* -9.89
	return (t, data)

def plot(x, y, linestyle, title):
	plt.plot(x, y, linestyle=linestyle)
	plt.xlabel('time (s)')
	plt.ylabel('acceleration (m/s^2')
	plt.title(title)
	plt.grid(True)
	plt.show()

def main():
	THRES = 1 # threshold for peaks, to be determined empirically

	(x, ax) = generate_data(amp=3, period=0.5, noise=0.01) # x(t)
	(y, ay) = generate_data(amp=3, period=0.5, noise=0.01) # y(t)
	(z, az) = generate_z(amp=3, period=10000, noise=0.01) # z(t)

	# Before filter
	plot(x, ax, "solid", "x(t)")
	plot(y, ay, "dashed", "y(t)")
	plot(z, az, "dotted", "z(t)")

	xg = filter_sig(ax, COEFFICIENTS_LOW_0_HZ)
	yg = filter_sig(ay, COEFFICIENTS_LOW_0_HZ)
	zg = filter_sig(az, COEFFICIENTS_LOW_0_HZ)

	# Acceleration due to gravity
	plot(x, xg, "solid", "x_g(t)")
	plot(y, yg, "dashed", "y_g(t)")
	plot(z, zg, "dotted", "z_g(t)")

	# Acceleration due to user
	xu = ax - xg
	yu = ay - yg
	zu = az - zg
	plot(x, xu, "solid", "x_u(t)")
	plot(x, yu, "dashed", "y_u(t)")
	plot(x, zu, "dotted", "z_u(t)")

	# Isolate user acceleration in direction of gravity
	a = xu * xg + yu * yg + zu * zg
	plot(x, a, "solid", "User acceleration in direction of gravity")

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
	print(z_c_idx)

	# Find positive threshold crossings
	translated = np.sign(a_h - np.ones(len(a_h))*THRES)
	f_two_shifted = np.hstack(([1,1], translated))
	f_one_b_one_shifted = np.hstack(([1], translated,[1]))
	b_two_shifted = np.hstack((translated,[1,1]))
	thres_crossings = np.multiply(b_two_shifted, f_one_b_one_shifted)
	positive_thres_crossings = np.multiply(np.where(thres_crossings==-1, thres_crossings, np.zeros(len(thres_crossings))), f_two_shifted)
	p_t_idx = np.where(positive_thres_crossings[2:]==-1)[0]
	print(p_t_idx)

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