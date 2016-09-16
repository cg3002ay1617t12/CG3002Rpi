import matplotlib.pyplot as plt
import numpy as np

# X, Y coordinates
dest = np.array([25, 25])
src  = (0,0)
state = [np.array([0,0]), 0] # X,Y,bearing where bearing is UP (0), DOWN (180), LEFT (270), RIGHT (90)
agent_map = [] # global map reflecting agent's current knowledge of the map
obstacle_field = []
obstacle_density = 0.2
sensor = ['front', 'left', 'right']
moves_x = [0]
moves_y = [0]

def update_map(loc, ax):
	agent_map[loc[0], loc[1]] += 1
	# agent_map[state[0][0], state[0][1]] = 0.5 # Plot player's location
	ax.set_xticks(np.arange(0,30,1))
	ax.set_yticks(np.arange(0,30.,1))
	plt.grid()
	ax.scatter(x=moves_x[:-1], y=moves_y[:-1], c='r', s=40, marker="x")
	ax.scatter(x=moves_x[-1:], y=moves_y[-1:], c='r', s=50, marker="o")
	indices = np.where(agent_map==1)
	ax.scatter(indices[0], indices[1], marker="+")
	# plt.imshow(agent_map, cmap='hot', interpolation='nearest')
	plt.subplot(2,1,2)
	# plt.imshow(obstacle_field, cmap='hot', interpolation='nearest')
	indices = np.where(obstacle_field==1)
	plt.scatter(indices[0], indices[1], marker="+")
	plt.show()

def calculate_next_move():
	direction = dest - state[0]
	dots = []
	dist_to_dir = {}
	for i in range(-1,2): # X
		for j in range(-1,2): # Y
			# Calculate max. dot product with direction vector
			# If within map
			if state[0][0] + i >= 0 and state[0][0] + i < 30 and state[0][1] + j >= 0 and state[0][1] + j < 30:
				# Exclude diagonal moves
				if i == 0 or j == 0:
					# if no obstacle
					if agent_map[state[0][0]+i, state[0][1]+j] == 0:
						move_vec = np.array([i,j])
						product = np.dot(move_vec, direction)
						dots.append(product)
						dist_to_dir[product] = np.array([i,j])
	if len(dots) == 0:
		print("No legal move!")
	else:
		# print(dots)
		pass
	return dist_to_dir[max(dots)]

def bearing_to_vec(bearing):
	"""Given bearing in degrees, return a unit vec (x,y) in that direction"""
	return np.array([np.cos((np.pi / 180) * bearing - np.pi / 2), np.sin((np.pi / 180) * bearing + np.pi / 2)])

def detect_obstacle():
	"""Obstacle is reported relative to agent's bearing. Can only be one of FRONT, LEFT, RIGHT"""
	global state
	sense_dir = sensor[np.random.choice(3, 1)]
	bearing = state[1]
	if sense_dir == 'front':
		loc = state[0] + bearing_to_vec(bearing)
	elif sense_dir == 'left':
		loc = state[0] + bearing_to_vec((bearing - 90) % 360)
	else:
		loc = state[0] + bearing_to_vec((bearing + 90) % 360)
	is_obstacle = (obstacle_field[loc[0], loc[1]]==1)
	if is_obstacle: print("Obstacle [%d, %d, %s]" % (state[0][0], state[0][1], sense_dir))
	return (loc, is_obstacle)

def move(coord, ax):
	"""Agent must turn to face the right bearing before moving forward by 1 step, coord is vector of movement"""
	global state
	print("Move [%d, %d]" % (coord[0], coord[1]))
	new_state = state[0] + coord
	if obstacle_field[new_state[0], new_state[1]] == 1:
		update_map(new_state, ax)
		print("Obstacle encountered! Illegal move!")
	else:
		state[0] = new_state
		moves_x.append(state[0][0])
		moves_y.append(state[0][1])

def init():
	global obstacle_field, agent_map
	a = np.random.random((30, 30))
	obstacle_field = np.where(a > (1 - obstacle_density), np.ones(a.shape), np.zeros(a.shape))
	obstacle_field[src[0], src[1]] = 0 # Clear player's spawn location
	obstacle_field[dest[0], dest[0]] = 0 # Clear destination
	agent_map = np.zeros(obstacle_field.shape)
	plt.subplot(2,1,2)
	ax = plt.gca()
	ax.set_xticks(np.arange(0,30,1))
	ax.set_yticks(np.arange(0,30.,1))
	plt.grid()
	indices = np.where(obstacle_field==1)
	plt.scatter(indices[0], indices[1], marker="+")
	# plt.imshow(obstacle_field, cmap='hot', interpolation='nearest')
	plt.show()
	
def main():
	init()
	win   = False
	count = 0
	fig   = plt.figure()
	ax    = fig.add_subplot(2,1,1)
	while (not win):
		(loc, is_obstacle) = detect_obstacle()
		if is_obstacle:
			update_map(loc, ax)
		coord = calculate_next_move()
		move(coord, ax)
		count += 1
		if state[0][0] == dest[0] and state[0][1] == dest[1]:
			win = True
	print("Won in %d moves" % count)

if __name__ == "__main__":
	main()
