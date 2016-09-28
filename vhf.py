import matplotlib.pyplot as plt
import numpy as np
import sys, heapq
import numpy.linalg as la

class LocalPathFinder(object):
	sensor            = ['front', 'left', 'right', 'back']
	NUM_SENSORS       = 4
	N_CYCLE           = 6
	backtrack_penalty = -1
	
	def __init__(self, xsize=None, ysize=None, dest=None, src=None, bearing=None, mode='debug', obstacle_density=0.3):
		self.X_DIM            = xsize if xsize is not None else 30
		self.Y_DIM            = ysize if ysize is not None else 30
		self.dest             = dest if dest is not None else np.array([25, 25])
		self.src              = src if src is not None else (0,0)
		# X,Y,bearing where bearing is UP (0), DOWN (180), LEFT (270), RIGHT (90)
		self.state            = [src, bearing] if src is not None and bearing is not None else [np.array([0,0]), 0]
		self.agent_map        = [] # global map reflecting agent's current knowledge of the map, 1 is unexplored, -1 is visited, -2 is obstacle, 2 is no obstacle
		self.obstacle_field   = []
		self.obstacle_density = obstacle_density if obstacle_density is not None else 0.3
		self.moves_x          = [self.src[0]]
		self.moves_y          = [self.src[1]]
		self.dfs_branches     = [] # Stack containing branches encountered so far
		self.curr_dest        = self.dest
		self.mode             = mode
		self.win              = False
		self.count            = 0
		self.init_sim()

	def update_map(self, loc, marker):
		if marker == 'obstacle':
			value = -2
		elif marker == 'visited':
			value = LocalPathFinder.backtrack_penalty
		elif marker == 'free':
			value = 2
		else:
			value = 0
		prev_value = self.agent_map[loc[0], loc[1]]
		# Do not overwrite if already visited
		if not prev_value == -1:
			self.agent_map[loc[0], loc[1]] = value

	def plotter(self, ax):
		ax.cla()
		ax.set_xticks(np.arange(0,30,1))
		ax.set_yticks(np.arange(0,30,1))
		ax.set_xlim(-1, 30)
		ax.set_ylim(-1, 30)
		ax.scatter(self.moves_x[-1:], self.moves_y[-1:], **{'c':'r', 's':40, 'marker':"o"}) # Current location
		indices = np.where(self.agent_map==-1)
		ax.scatter(indices[0], indices[1], **{'c':'r', 's':40, 'marker':"x"}) # Visited
		indices = np.where(self.agent_map==-2)
		ax.scatter(indices[0], indices[1], **{'marker':"*"})
		indices = np.where(self.agent_map==2)
		ax.scatter(indices[0], indices[1], **{'marker':"+"})
		if self.mode == 'demo':
			plt.pause(0.5)
		else:
			# Debug
			x = raw_input("Press [Enter] to continue\n")
			if x == 'q':
				sys.exit(1)

	def within_map(self, x, y):
		return (x >= 0) and (x < self.X_DIM) and (y >= 0) and (y < self.Y_DIM)

	def calc_dir(self, src=None, dest=None):
		""" Returns unit vector representing direction from src to dest, src and dest must be np.ndarray"""
		if src is None:
			src = self.src
		if dest is None:
			dest = self.dest
		return (dest - src) / la.norm(dest - src)

	def calc_dist(self, src, dest):
		if src is None:
			src = self.src
		if dest is None:
			dest = self.dest
		return la.norm(dest - src)

	def calc_steps(self, coord):
		""" Calculates number of steps needed to backtrack to the given coord"""
		for x in range(0, len(self.moves_x)):
			step_x = self.moves_x[-x]
			step_y = self.moves_y[-x]
			if step_x == coord[0] and step_y == coord[1]:
				return x
		return len(moves_x)

	def select_branch(self, n):
		""" For all branches, check whether valid paths still exist and calculate a score based on how close those paths are to the dest"""
		choices = []
		if n / len(self.dfs_branches) > 10:
			print("Infinite recursion detected...exiting")
			sys.exit()
		n = min(len(self.dfs_branches), n)
		for i,b in enumerate(self.dfs_branches[-n:]):
			score = 0
			distance  = self.calc_dist(b, self.dest)
			direction = self.calc_dir(b, self.dest)
			up = b + np.array([0,1])
			down = b + np.array([0,-1])
			left = b + np.array([-1,0])
			right = b + np.array([1,0])
			if self.within_map(up[0], up[1]) and (self.agent_map[up[0], up[1]] == 2):
				score += 1 + np.dot(np.array([0,1]), direction) / distance - self.calc_steps(b)
			if self.within_map(down[0], down[1]) and (self.agent_map[down[0], down[1]] == 2):
				score += 1 + np.dot(np.array([0,-1]), direction) / distance - self.calc_steps(b)
			if self.within_map(left[0], left[1]) and (self.agent_map[left[0], left[1]] == 2):
				score += 1 + np.dot(np.array([-1,0]), direction) / distance - self.calc_steps(b)
			if self.within_map(right[0], right[1]) and (self.agent_map[right[0], right[1]] == 2):
				score += 1 + np.dot(np.array([1,0]), direction) / distance - self.calc_steps(b)
			if score == 0:
				# Prune branches with no more unvisited and free paths
				print("Pruned (%d, %d)" % (self.dfs_branches[len(self.dfs_branches) - n + i][0], self.dfs_branches[len(self.dfs_branches) - n + i][1]))
			else:
				print(self.dfs_branches[len(self.dfs_branches) - n + i], score)
				choices.append([i, score])
		try:
			choice = max(choices, key=lambda x: x[1])[0]
		except ValueError as e:
			# Increase search size, TODO - risk of inifinite recursion here
			return self.select_branch(n+5)
		result = self.dfs_branches[choice - n]
		while (n > choice + 1):
			self.dfs_branches.pop()
			n -= 1
		return result

	def reversi(self):
		""" Clean up the agent_map by running a conversion algorithm - i.e. +2 which are surrounded by -1 will be converted to -1 automatically because there is no point exploring them"""
		for x in range(0,self.agent_map.shape[1]):
			frontier = []
			for y in range(0, self.agent_map.shape[0]):
				v = self.agent_map[x,y]
				if v == -1:
					frontier.append(y)
			for i in range(0,len(frontier),2):
				if i+1 >= len(frontier): break
				start = frontier[i]
				end   = frontier[i+1]
				self.agent_map[x,start+1:end] = -1
		return

	def calculate_next_move(self, greedy=True):
		""" 
			Find max of 1/(1+ obstacle_density) v . w where v is unit vector of next step, w is direction of target - curr
			obstacle_density is sum of all obstacles discovered in direction of v
		"""
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
			if self.within_map(x+1, y) and (self.agent_map[x+1,y] != -2):
				free_config += 1
			if self.within_map(x, y+1) and (self.agent_map[x,y+1] != -2):
				free_config += 1
			if self.within_map(x-1, y) and (self.agent_map[x-1,y] != -2):
				free_config += 1
			if self.within_map(x, y-1) and (self.agent_map[x, y-1] != -2):
				free_config += 1
			return (free_config - 1) / 2 # Do not count position where agent came from

		direction = (self.curr_dest - self.state[0]) / la.norm(self.curr_dest - self.state[0])
		# print(direction)
		dots = []
		dist_to_dir = {}
		# alpha = np.e * (1 - 1 / np.e)
		alpha = 2 * np.e ** 2 / (1 + np.e)
		for i in range(-1,2): # X
			for j in range(-1,2): # Y
				# Calculate max. dot product with direction vector
				# If within map
				new_i = self.state[0][0] + i
				new_j = self.state[0][1] + j
				if new_i >= 0 and new_i < self.X_DIM and new_j >= 0 and new_j < self.Y_DIM:
					# Exclude diagonal moves
					if (i == 0 or j == 0) and (not (i == 0 and j == 0)):
						is_obs = (self.agent_map[self.state[0][0]+i, self.state[0][1]+j] == -2)
						x = self.state[0][0]
						y = self.state[0][1]
						try:
							if i == -1 and j == 0:
								slice_ = self.agent_map[0:x, y]
								obs_density = calc_penalty(slice_)
							elif i == 0 and j == 1:
								slice_ = self.agent_map[x, y+1:]
								obs_density = calc_penalty(slice_)
							elif i == 1 and j == 0:
								slice_ = self.agent_map[x+1:, y]
								obs_density = calc_penalty(slice_)
							elif i == 0 and j == -1:
								slice_ = self.agent_map[x, 0:y]
								obs_density = calc_penalty(slice_)
							else:
								pass
						except Exception as e:
							print e
							obs_density = 0.0
						obs_density = np.nan_to_num(obs_density)
						free_config  = look_ahead(new_i, new_j)
						move_vec = np.array([i,j])
						if greedy:
							if is_obs:
								product = -1 * np.inf
								# product = np.dot(move_vec, direction) - alpha * (obs_density + np.inf)
							else:
								# product = np.dot(move_vec, direction) + agent_map[state[0][0] + move_vec[0], state[0][1] + move_vec[1]]
								product = np.dot(move_vec, direction) + obs_density + free_config
								# product = np.dot(move_vec, direction) - alpha * (obs_density)
						else:
							is_visited = (self.agent_map[self.state[0][0]+i, self.state[0][1]+j] == -1)
							if is_obs or is_visited:
								product = -1 * np.inf
							else:
								product = np.dot(move_vec, direction) + obs_density + free_config
						# print(i, j, product)
						dots.append(product)
						dist_to_dir[product] = np.array([i,j])
		if len(dots) == 0:
			print("No legal move!")
		else:
			choices = len(filter(lambda x: x!=-np.inf, dots)) - 1
			for c in range(0, choices):
				self.dfs_branches.append(self.state[0]) # Save location of branching to come back later
				# print("Branches: %d" % len(self.dfs_branches))
		return dist_to_dir[max(dots)]

	def detect_cycle(n):
		"""n is int referring to length of cycle (number of steps)"""
		if len(self.moves_x) < n+1:
			return False
		else:
			origin = (self.moves_x[-n-1], self.moves_y[-n-1])
			end    = (self.moves_x[-1], self.moves_y[-1])
			if origin == end:
				return True
			else:
				return False

	def bearing_to_vec(self, bearing):
		"""Given bearing in degrees, return a unit vec (x,y) in that direction"""
		if bearing is None: bearing = self.bearing
		return np.array([np.cos((np.pi / 180) * bearing - np.pi / 2), np.sin((np.pi / 180) * bearing + np.pi / 2)])

	def vec_to_bearing(self, vec, bearing):
		"""Given unit vector and agent's current bearing, return direction to turn in degrees"""
		pass

	def detect_obstacle(self, direction='front', mode='random'):
		"""
			Two modes of operation - random(ly) senses a random direction while directed senses in direction.
			Obstacle is reported relative to agent's bearing. Can only be one of FRONT, LEFT, RIGHT, BACK
		"""
		bearing = self.state[1]
		if mode == 'random':
			sense_dir = LocalPathFinder.sensor[np.random.choice(3, 1)[0]]
		else:
			sense_dir = direction
		if sense_dir == 'front':
			loc = self.state[0] + self.bearing_to_vec(bearing)
		elif sense_dir == 'left':
			loc = self.state[0] + self.bearing_to_vec((bearing - 90) % 360)
		elif sense_dir == 'back':
			loc = self.state[0] + self.bearing_to_vec((bearing + 180) % 360)
		else:
			# right
			loc = self.state[0] + self.bearing_to_vec((bearing + 90) % 360)
		if not self.within_map(loc[0], loc[1]): raise Exception("Out of Map")	
		is_obstacle = (self.obstacle_field[loc[0], loc[1]]==1)
		# if is_obstacle: print("Obstacle [%d, %d, %s]" % (state[0][0], state[0][1], sense_dir))
		return (loc, is_obstacle)

	def move(self, coord, backtrack=False):
		"""Agent must turn to face the right bearing before moving forward by 1 step, coord is vector of movement"""
		global state
		print("Move [%d, %d]" % (coord[0], coord[1]))
		new_state = self.state[0] + coord
		if self.obstacle_field[new_state[0], new_state[1]] == 1:
			self.update_map(new_state, 'obstacle')
			# print("Obstacle encountered! Illegal move!")
		else:
			self.update_map(new_state, 'visited')
			self.state[0] = new_state
			if not backtrack:
				self.moves_x.append(self.state[0][0])
				self.moves_y.append(self.state[0][1])

	def init_sim(self):
		"""Initialize obstacle field and agent_map, depending on whether its live or a simulation"""
		a = np.random.random((self.X_DIM, self.Y_DIM))
		self.dfs_branches.append(self.state[0])
		self.obstacle_field = np.where(a > (1 - self.obstacle_density), np.ones(a.shape), np.zeros(a.shape))
		self.obstacle_field[self.src[0], self.src[1]] = 0 # Clear player's spawn location
		self.obstacle_field[self.dest[0], self.dest[0]] = 0 # Clear destination
		self.agent_map = np.ones(self.obstacle_field.shape)
		self.agent_map[self.state[0][0], self.state[0][1]] = -1
		
	def init_plot(self, ax1, ax2):
		if ax1 is None: ax1 = self.ax1
		if ax2 is None: ax2 = self.ax2
		ax2.set_xticks(np.arange(0,self.X_DIM,1))
		ax2.set_yticks(np.arange(0,self.Y_DIM,1))
		indices = np.where(self.obstacle_field==1)
		ax2.scatter(indices[0], indices[1], marker="*") # Orignal obstacle map
		ax1.set_xticks(np.arange(0,self.X_DIM,1))
		ax1.set_yticks(np.arange(0,self.Y_DIM,1))
		ax1.set_xlim(-1, self.X_DIM)
		ax1.set_ylim(-1, self.Y_DIM)
		indices = np.where(self.agent_map==-2)
		ax1.scatter(indices[0], indices[1], marker="*") # Agent's map
		ax1.grid() # Call this once as it toggles state 
		ax2.grid()
		plt.ion()
		plt.show()

	def out_of_options(self):
		options = 0
		x = self.state[0][0]
		y = self.state[0][1]
		if self.within_map(x+1, y) and (self.agent_map[x+1,y] > 0):
			options += 1
		if self.within_map(x, y+1) and (self.agent_map[x,y+1] > 0):
			options += 1
		if self.within_map(x-1, y) and (self.agent_map[x-1,y] > 0):
			options += 1
		if self.within_map(x, y-1) and (self.agent_map[x, y-1] > 0):
			options += 1
		return (options == 0)

	def run(self, plot=False):
		np.random.seed()
		if plot:
			self.fig, (self.ax1, self.ax2)  = plt.subplots(2,1, figsize=(17,8))
			self.init_plot(self.ax1, self.ax2)
		if not self.win:
			for x in range(0, LocalPathFinder.NUM_SENSORS):
				try:
					(loc, is_obstacle) = self.detect_obstacle(direction=LocalPathFinder.sensor[x], mode='directed')
					if is_obstacle:
						self.update_map(loc, 'obstacle')
					else:
						self.update_map(loc, 'free')
				except Exception as e:
					pass
			if plot: self.plotter(self.ax1)
			if self.out_of_options():
				try:
					self.curr_dest = self.select_branch(6)
					# print("Backtrack to last branch [%d, %d]" % (self.curr_dest[0], self.curr_dest[1]))
					index = 2
					while True:
						if (self.state[0][0] == self.curr_dest[0]) and (self.state[0][1] == self.curr_dest[1]):
							break
						prev_x = self.moves_x[-1*index]
						prev_y = self.moves_y[-1*index]
						self.move(np.array([prev_x - self.state[0][0], prev_y - self.state[0][1]]), backtrack=False)
						index += 2
						if plot: self.plotter(self.ax1)
						self.count+= 1
				except (ValueError, IndexError) as e:
					pass
					# print("Error! No last branch to backtrack to...There exists no path to the dest.")
				# print("Reached last checkpoint [%d, %d]" % (self.curr_dest[0], self.curr_dest[1]))
				# Discard steps taken since checkpoint
				while index > 2:
					self.moves_x.pop()
					self.moves_y.pop()
					index -= 1
				self.curr_dest = self.dest
			else:
				coord = self.calculate_next_move(greedy=False)
				self.move(coord)
				self.count += 1
			if self.state[0][0] == self.dest[0] and self.state[0][1] == self.dest[1]:
				self.win = True
			# if count > 100: break
		if self.win: 
			# print("Won in %d moves" % self.count)
			pass

	def run_to_end(self, plot=False):
		np.random.seed()
		if plot:
			self.fig, (self.ax1, self.ax2)  = plt.subplots(2,1, figsize=(17,8))
			self.init_plot(self.ax1, self.ax2)
		win   = False
		count = 0
		while (not win):
			for x in range(0, LocalPathFinder.NUM_SENSORS):
				try:
					(loc, is_obstacle) = self.detect_obstacle(direction=LocalPathFinder.sensor[x], mode='directed')
					if is_obstacle:
						self.update_map(loc, 'obstacle')
					else:
						self.update_map(loc, 'free')
				except Exception as e:
					pass
			if plot: self.plotter(self.ax1)
			if self.out_of_options():
				try:
					self.curr_dest = self.select_branch(6)
					print("Backtrack to last branch [%d, %d]" % (self.curr_dest[0], self.curr_dest[1]))
					index = 2
					while True:
						if (self.state[0][0] == self.curr_dest[0]) and (self.state[0][1] == self.curr_dest[1]):
							break
						prev_x = self.moves_x[-1*index]
						prev_y = self.moves_y[-1*index]
						self.move(np.array([prev_x - self.state[0][0], prev_y - self.state[0][1]]), backtrack=False)
						index += 2
						if plot: self.plotter(self.ax1)
						count+= 1
				except (ValueError, IndexError) as e:
					print("Error! No last branch to backtrack to...There exists no path to the dest.")
					sys.exit(1)
				print("Reached last checkpoint [%d, %d]" % (self.curr_dest[0], self.curr_dest[1]))
				# Discard steps taken since checkpoint
				while index > 2:
					self.moves_x.pop()
					self.moves_y.pop()
					index -= 1
				self.curr_dest = self.dest
			else:
				coord = self.calculate_next_move(greedy=False)
				self.move(coord)
				count += 1
			if self.state[0][0] == self.dest[0] and self.state[0][1] == self.dest[1]:
				win = True
			# if count > 100: break
		if win: 
			print("Won in %d moves" % count)
		else:
			print("Lost in %d moves" % count)

def main(plot=True, mode='demo'):
	lpf = LocalPathFinder(30, 30, np.array([25,25]), np.array([0,0]), 0, mode=mode)
	lpf.run_to_end(plot)

if __name__ == "__main__":
	if len(sys.argv) == 2:
		if sys.argv[1] == 1:
			plot = True
		else:
			plot = False
		main(plot=plot)
	elif len(sys.argv) == 3:
		if sys.argv[1] == 'true':
			plot = True
		else:
			plot = False
		main(plot=plot, mode=sys.argv[2])
	else:
		main()