import matplotlib.pyplot as plt
import numpy as np
import sys
import numpy.linalg as la

X_DIM            = 30
Y_DIM            = 30
NUM_SENSORS      = 4
N_CYCLE          = 6
dest             = np.array([25, 25])
src              = (0,0)
state            = [np.array([0,0]), 0] # X,Y,bearing where bearing is UP (0), DOWN (180), LEFT (270), RIGHT (90)
agent_map        = [] # global map reflecting agent's current knowledge of the map, 1 is unexplored, -1 is visited, -2 is obstacle, 2 is no obstacle
obstacle_field   = []
obstacle_density = 0.3
sensor           = ['front', 'left', 'right', 'back']
moves_x          = [0]
moves_y          = [0]
dfs_branches     = []
branches         = {}
backtrack_penalty = -1
curr_dest        = dest

def update_map(loc, marker):
	global agent_map
	if marker == 'obstacle':
		value = -2
	elif marker == 'visited':
		value = backtrack_penalty
	elif marker == 'free':
		value = 2
	else:
		value = 0
	agent_map[loc[0], loc[1]] = value

def plotter(ax):
	ax.cla()
	ax.set_xticks(np.arange(0,30,1))
	ax.set_yticks(np.arange(0,30,1))
	ax.set_xlim(-1, 30)
	ax.set_ylim(-1, 30)
	ax.scatter(moves_x[:-1], moves_y[:-1], **{'c':'r', 's':40, 'marker':"x"})
	ax.scatter(moves_x[-1:], moves_y[-1:], **{'c':'r', 's':40, 'marker':"o"})
	indices = np.where(agent_map==-2)
	ax.scatter(indices[0], indices[1], **{'marker':"*"})
	indices = np.where(agent_map==2)
	ax.scatter(indices[0], indices[1], **{'marker':"+"})
	# plt.pause(1)
	x = raw_input("Press [Enter] to continue\n")
	if x == 'q':
		sys.exit(1)

def within_map(x, y):
	return (x >= 0) and (x < X_DIM) and (y >= 0) and (y < Y_DIM)

def calculate_next_move():
	""" 
		Find max of 1/(1+ obstacle_density) v . w where v is unit vector of next step, w is direction of target - curr
		obstacle_density is sum of all obstacles discovered in direction of v
	"""
	def calc_obs_density(slice_):
		if not isinstance(slice_, np.ndarray):
			slice_ = np.array([slice_])
		else:
			if len(slice_) == 0:
				return 0.0
		weights     = np.where(slice_==1, slice_, -1 * np.ones(slice_.shape))
		obs_sum     = np.dot(weights, np.power((1/np.e), np.array([x for x in range(1, 1+slice_.shape[0])])))
		obs_density = obs_sum / slice_.shape[0]
		return obs_density

	def calc_penalty(slice_):
		if not isinstance(slice_, np.ndarray):
			slice_ = np.array([slice_])
		else:
			if len(slice_) == 0:
				return 0.0
		return np.ma.average(slice_)

	def look_ahead(x, y):
		""" count number of spaces reachable in new state"""
		free_config = 0
		if within_map(x+1, y) and (agent_map[x+1,y] != -2):
			free_config += 1
		if within_map(x, y+1) and (agent_map[x,y+1] != -2):
			free_config += 1
		if within_map(x-1, y) and (agent_map[x-1,y] != -2):
			free_config += 1
		if within_map(x, y-1) and (agent_map[x, y-1] != -2):
			free_config += 1
		return (free_config - 1) / 2 # Do not count position where agent came from

	direction = (curr_dest - state[0]) / la.norm(curr_dest - state[0])
	# print(direction)
	dots = []
	dist_to_dir = {}
	# alpha = np.e * (1 - 1 / np.e)
	alpha = 2 * np.e ** 2 / (1 + np.e)
	for i in range(-1,2): # X
		for j in range(-1,2): # Y
			# Calculate max. dot product with direction vector
			# If within map
			new_i = state[0][0] + i
			new_j = state[0][1] + j
			if new_i >= 0 and new_i < 30 and new_j >= 0 and new_j < 30:
				# Exclude diagonal moves
				if (i == 0 or j == 0) and (not (i == 0 and j == 0)):
					is_obs = (agent_map[state[0][0]+i, state[0][1]+j] == -2)
					x = state[0][0]
					y = state[0][1]
					try:
						if i == -1 and j == 0:
							slice_ = agent_map[0:x, y]
							obs_density = calc_penalty(slice_)
						elif i == 0 and j == 1:
							slice_ = agent_map[x, y+1:]
							obs_density = calc_penalty(slice_)
						elif i == 1 and j == 0:
							slice_ = agent_map[x+1:, y]
							obs_density = calc_penalty(slice_)
						elif i == 0 and j == -1:
							slice_ = agent_map[x, 0:y]
							obs_density = calc_penalty(slice_)
						else:
							pass
					except Exception as e:
						print e
						obs_density = 0.0
					obs_density = np.nan_to_num(obs_density)
					free_config  = look_ahead(new_i, new_j)
					move_vec = np.array([i,j])
					if is_obs:
						product = -1 * np.inf
						# product = np.dot(move_vec, direction) - alpha * (obs_density + np.inf)
					else:
						# product = np.dot(move_vec, direction) + agent_map[state[0][0] + move_vec[0], state[0][1] + move_vec[1]]
						product = np.dot(move_vec, direction) + obs_density + free_config
						# product = np.dot(move_vec, direction) - alpha * (obs_density)
					# print(i, j, product)
					dots.append(product)
					dist_to_dir[product] = np.array([i,j])
	if len(dots) == 0:
		print("No legal move!")
	else:
		if len(filter(lambda x: x!=-np.inf, dots)) > 1:
			try:
				added = branches[str(state[0][0])+str(state[0][1])]
			except KeyError as e:
				dfs_branches.append(state[0]) # Save location of branching to come back later
				branches[str(state[0][0])+str(state[0][1])] = 1
			print("Branches: %d" % len(dfs_branches))
		# print(dots)
	return dist_to_dir[max(dots)]

def detect_cycle(n):
	"""n is int referring to length of cycle (number of steps)"""
	if len(moves_x) < n+1:
		return False
	else:
		origin = (moves_x[-n-1], moves_y[-n-1])
		end    = (moves_x[-1], moves_y[-1])
		if origin == end:
			return True
		else:
			return False

def bearing_to_vec(bearing):
	"""Given bearing in degrees, return a unit vec (x,y) in that direction"""
	return np.array([np.cos((np.pi / 180) * bearing - np.pi / 2), np.sin((np.pi / 180) * bearing + np.pi / 2)])

def vec_to_bearing(vec, bearing):
	"""Given unit vector and agent's current bearing, return direction to turn in degrees"""
	pass

def detect_obstacle(direction='front', mode='random'):
	"""
		Two modes of operation - random(ly) senses a random direction while directed senses in direction.
		Obstacle is reported relative to agent's bearing. Can only be one of FRONT, LEFT, RIGHT, BACK
	"""
	global state
	bearing = state[1]
	if mode == 'random':
		sense_dir = sensor[np.random.choice(3, 1)[0]]
	else:
		sense_dir = direction
	if sense_dir == 'front':
		loc = state[0] + bearing_to_vec(bearing)
	elif sense_dir == 'left':
		loc = state[0] + bearing_to_vec((bearing - 90) % 360)
	elif sense_dir == 'back':
		loc = state[0] + bearing_to_vec((bearing + 180) % 360)
	else:
		# right
		loc = state[0] + bearing_to_vec((bearing + 90) % 360)
	is_obstacle = (obstacle_field[loc[0], loc[1]]==1)
	# if is_obstacle: print("Obstacle [%d, %d, %s]" % (state[0][0], state[0][1], sense_dir))
	return (loc, is_obstacle)

def move(coord, backtrack=False):
	"""Agent must turn to face the right bearing before moving forward by 1 step, coord is vector of movement"""
	global state
	print("Move [%d, %d]" % (coord[0], coord[1]))
	new_state = state[0] + coord
	if obstacle_field[new_state[0], new_state[1]] == 1:
		update_map(new_state, 'obstacle')
		print("Obstacle encountered! Illegal move!")
	else:
		update_map(new_state, 'visited')
		state[0] = new_state
		if not backtrack:
			moves_x.append(state[0][0])
			moves_y.append(state[0][1])

def init(ax1, ax2):
	global obstacle_field, agent_map
	a = np.random.random((30, 30))
	obstacle_field = np.where(a > (1 - obstacle_density), np.ones(a.shape), np.zeros(a.shape))
	obstacle_field[src[0], src[1]] = 0 # Clear player's spawn location
	obstacle_field[dest[0], dest[0]] = 0 # Clear destination
	agent_map = np.ones(obstacle_field.shape)
	ax2.set_xticks(np.arange(0,30,1))
	ax2.set_yticks(np.arange(0,30,1))
	indices = np.where(obstacle_field==1)
	ax2.scatter(indices[0], indices[1], marker="*") # Orignal obstacle map
	ax1.set_xticks(np.arange(0,30,1))
	ax1.set_yticks(np.arange(0,30,1))
	ax1.set_xlim(-1, 30)
	ax1.set_ylim(-1, 30)
	indices = np.where(agent_map==-2)
	ax1.scatter(indices[0], indices[1], marker="*") # Agent's map
	# plt.imshow(obstacle_field, cmap='hot', interpolation='nearest')
	ax1.grid() # Call this once as it toggles state 
	ax2.grid()
	plt.ion()
	plt.show()

def main():
	global curr_dest
	np.random.seed()
	fig, (ax1, ax2)  = plt.subplots(2,1, figsize=(17,8))
	init(ax1, ax2)
	win   = False
	count = 0
	while (not win):
		for x in range(0, NUM_SENSORS):
			(loc, is_obstacle) = detect_obstacle(direction=sensor[x], mode='directed')
			if is_obstacle:
				update_map(loc, 'obstacle')
			else:
				update_map(loc, 'free')
		plotter(ax1)
		coord = calculate_next_move()
		move(coord)
		count += 1
		if detect_cycle(N_CYCLE):
			try:
				curr_dest = dfs_branches.pop()
				print("Cycle detected, backtrack to last branch [%d, %d]" % (curr_dest[0], curr_dest[1]))
				index = 1
				while (state[0][0] != curr_dest[0]) or (state[0][1] != curr_dest[1]):
					prev_x = moves_x[-1*index]
					prev_y = moves_y[-1*index]
					move(np.array([prev_x - state[0][0], prev_y - state[0][1]]), backtrack=False)
					index += 2
					plotter(ax1)
					count+= 1
			except IndexError as e:
				print("Error! No last branch to backtrack to...There exists no path to the dest.")
				sys.exit(1)
			print("Reached last checkpoint [%d, %d]" % (curr_dest[0], curr_dest[1]))
			curr_dest = dest
		if state[0][0] == dest[0] and state[0][1] == dest[1]:
			win = True
		if count > 100: break
	if win: 
		print("Won in %d moves" % count)
	else:
		print("Lost in %d moves" % count)

if __name__ == "__main__":
	main()
