import json, requests, math, heapq, pprint

class PathFinder(object):
	def __init__(self):
		self.request_url = 'http://showmyway.comp.nus.edu.sg/getMapInfo.php?Building=Com1&Level=2'
		# self.request_url = 'http://showmyway.comp.nus.edu.sg/getMapInfo.php?Building=DemoBuilding&Level=1'
		self.wifi_radius = 150
		self.reach_radius = 50

		self.node_info = None
		self.adjacency_matrix = None
		self.num_node = -1
		self.angle_of_north = -1

		self.x_coordinate = -1
		self.y_coordinate = -1
		self.angle = -1

		self.source = -1
		self.target = -1

		self.shortest_path = []
		self.visited_nodes = []
		self.next_node = -1

		self.instruction = []

		self.update_node_info()

	def is_ready(self):
		return (self.node_info != None and self.adjacency_matrix != None and self.x_coordinate != -1 and self.y_coordinate != -1)

	def update_coordinate(self, x_coordinate, y_coordinate, angle_from_north):
		self.x_coordinate = x_coordinate
		self.y_coordinate = y_coordinate
		# print(x_coordinate, y_coordinate)
		self.angle = self.get_angle_wrt_north(angle_from_north)

		node_reached = -1
		reached = False

		if self.next_node != -1:
			if self.is_reached(self.next_node, x_coordinate, y_coordinate):
				node_reached = self.next_node
				reached = True
				self.update_visited_nodes(self.next_node)
			else:
				self.update_instruction()

		return reached, node_reached

	def coordinates_from_node(self, node):
		node_info = self.node_info[node]
		return (node_info['x'], node_info['y'])

	def is_reached(self, node_index, user_x, user_y):
		node_x = self.node_info[node_index]['x']
		node_y = self.node_info[node_index]['y']

		if self.get_distance(user_x, user_y, node_x, node_y) < self.reach_radius:
			return True
		else:
			return False

	def update_source_and_target(self, source, target):
		self.source = source
		self.target = target

		self.update_shortest_path()

	def update_visited_nodes(self, node):
		if node not in self.visited_nodes:
			self.visited_nodes.append(node)

		self.update_instruction()

	def update_node_info(self):
		request_info = requests.get(self.request_url)

		json_request_info = json.loads(request_info.text)

		# wifi_info = {}

		# for node in json_request_info['wifi']:
		#   wifi_info[int(node['nodeId']) - 1] = {
		#     'name': node['nodeName'],
		#     'mac': node['macAddr'],
		#     'x': int(node['x']),
		#     'y': int(node['y'])
		#   }

		self.node_info = {}

		for node in json_request_info['map']:
			self.node_info[int(node['nodeId'])] = {
			'name': node['nodeName'],
			'neighbour' : [int(node_index.strip()) for node_index in str(node['linkTo']).split(',')],
			'x': int(node['x']),
			'y': int(node['y']),
			'wifi': []
			}

		# for node_id, node in self.node_info.items():
		#   node_x = node['x']
		#   node_y = node['y']
			
		#   for wifi_id, wifi in wifi_info.items():
		#     wifi_x = wifi['x']
		#     wifi_y = wifi['y']

		#     delta_x = node_x - wifi_x
		#     delta_y = node_y - wifi_y

		#     diff = int(math.sqrt(delta_x * delta_x + delta_y * delta_y))
			
		#     if diff < self.wifi_radius:
		#       self.node_info[node_id]['wifi'].append((wifi['name'], wifi['mac']))

		self.angle_of_north = int(json_request_info['info']['northAt'])

		self.update_adjacency_matrix()

	def update_adjacency_matrix(self):
		self.num_node = len(self.node_info)

		self.adjacency_matrix = [[-1 for row in range(self.num_node + 1)] for col in range(self.num_node + 1)]

		for index, node in self.node_info.iteritems():
			current_index = index
			current_x = node['x']
			current_y = node['y']

			for neighbour_index in node['neighbour']:
				neighbour_x = self.node_info[neighbour_index]['x']
				neighbour_y = self.node_info[neighbour_index]['y']

				delta_x = current_x - neighbour_x 
				delta_y = current_y - neighbour_y

				weight = int(math.sqrt(delta_x * delta_x + delta_y * delta_y))

				self.adjacency_matrix[current_index][neighbour_index] = weight
				self.adjacency_matrix[neighbour_index][current_index] = weight

	def update_shortest_path(self):
		start_index = self.source
		end_index = self.target

		if start_index < 1 or end_index < 1 or start_index > self.num_node or end_index > self.num_node:
			return [-1], [-1]

		priority_queue = []
		visited = [False] * (self.num_node + 1)
		# distance = [0 for i in range(self.num_node + 1)]
		predecesor = [-1 for i in range(self.num_node + 1)]

		init_weight = 0
		init_index = start_index
		init_predecesor = -1

		init_tuple = (init_weight, init_index, init_predecesor)

		heapq.heappush(priority_queue, init_tuple)

		while priority_queue:
			pop_tuple = heapq.heappop(priority_queue)

			pop_weight = pop_tuple[0]
			pop_index = pop_tuple[1]
			pop_predecesor = pop_tuple[2]

			if not visited[pop_index]:
				visited[pop_index] = True
				# distance[pop_index] = pop_weight
				predecesor[pop_index] = pop_predecesor

			# Since execution speed is not the bottle neck, process until all nodes are visited
			# if pop_index == end_index:
			#   break

			for neighbour_index, neighbour_weight in enumerate(self.adjacency_matrix[pop_index]):
				if neighbour_weight != -1 and not visited[neighbour_index]:
					push_weight = pop_weight + neighbour_weight
					push_index = neighbour_index
					push_predecesor = pop_index

					push_tuple = (push_weight, push_index, push_predecesor)

					heapq.heappush(priority_queue, push_tuple)

		self.shortest_path = []

		while 1:
			self.shortest_path.append(end_index)
			if end_index == start_index:
				break
			end_index = predecesor[end_index]

		self.shortest_path.reverse()

		self.update_instruction()

		# return shortest_path, distance

	def update_instruction(self):
		self.instruction = []

		remaining_path = []

		for index in self.shortest_path:
			if index not in self.visited_nodes:
				remaining_path.append(index)

		self.next_node = remaining_path[0]

		prev_x = self.x_coordinate
		prev_y = self.y_coordinate
		prev_index = 0
		prev_angle = self.angle

		for index in remaining_path:
			curr_name = self.node_info[index]['name']
			curr_x = self.node_info[index]['x']
			curr_y = self.node_info[index]['y']
			curr_index = index

			distance = self.get_distance(prev_x, prev_y, curr_x, curr_y)

			curr_angle = self.get_angle(prev_x, prev_y, curr_x, curr_y)

			self.instruction.append({
				'from_index': prev_index,
				'to_index': curr_index,
				'distance': distance,
				'angle': self.get_angle_change(prev_angle, curr_angle)
			})

			prev_name = curr_name
			prev_x = curr_x
			prev_y = curr_y
			prev_index = curr_index
			prev_angle = curr_angle

	def get_distance(self, x1, y1, x2, y2):
		x_diff = x2 - x1
		y_diff = y2 - y1

		return int(math.sqrt(x_diff * x_diff + y_diff * y_diff))

	def get_angle_wrt_north(self, angle):
		angle = self.angle_of_north - angle

		while angle < 0:
			angle += 360

		if angle > 180:
			angle -= 360

		return angle

	def get_angle(self, x1, y1, x2, y2):
		x_diff = x2 - x1
		y_diff = y2 - y1

		angle = int(math.degrees(math.atan2(x_diff, y_diff)))

		while angle < 0:
			angle += 360

		if angle > 180:
			angle -= 360

		return angle

	def get_angle_change(self, angle_1, angle_2):
		angle = angle_2 - angle_1

		while angle < 0:
			angle += 360

		if angle > 180:
			angle -= 360

		return angle

	def get_audio_next_instruction(self, instruction):
		if not instruction:
			return 'No Instruction'

		instruction = instruction[0]

		from_index = instruction['from_index']
		to_index = instruction['to_index']

		if from_index == 0:
			from_name = 'Current Position'
		else:
			from_name = self.node_info[from_index]['name']

		to_name = self.node_info[to_index]['name']

		distance = instruction['distance']
		
		angle = instruction['angle']

		right = True

		if angle < 0:
			right = False
			angle *= -1

		audio_string = 'From Node ' + str(from_index) + ' ' + str(from_name) + ' To Node ' + str(to_index) + ' ' + str(to_name) + ':'

		if right:
			audio_string += 'Turn Right ' + str(angle) + ' And Go ' + str(distance)
		else:
			audio_string += 'Turn Left ' + str(angle) + ' And Go ' + str(distance)

		return audio_string

	def get_audio_reached(self, reached_index):
		reached_name = self.node_info[reached_index]['name']

		audio_string = 'Reached Node ' +  str(reached_index) + ' ' + str(reached_name)

		return audio_string

if __name__ == "__main__":
	x = 2352
	y = 2636
	a = 0
	src = 12
	dst = 24
	vst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

	pf = PathFinder()

	if pf.is_ready():
		pf.update_source_and_target(src, dst) # update_source_and_target should only be used if ready

	reached, node_reached = pf.update_coordinate(x, y, a)
	if reached:
		print pf.get_audio_reached(node_reached)

	if pf.is_ready():
		pf.update_source_and_target(src, dst) # update_source_and_target should only be used if ready

	print 'Before Update'
	print pf.get_audio_next_instruction(pf.instruction)
	# for i in pf.instruction:
	#   print i

	for i in vst:
		pf.update_visited_nodes(i) # update_visited_nodes is not meant to be called, called for testing purposes for now

	print 'After Update'
	print pf.get_audio_next_instruction(pf.instruction)
	# for i in pf.instruction:
	#   print i

	print 'After Moving'

	reached, node_reached = pf.update_coordinate(5603, 1750, 0)

	if reached:
		print pf.get_audio_reached(node_reached)

	print pf.get_audio_next_instruction(pf.instruction)
	# for i in pf.instruction:
	#   print i
