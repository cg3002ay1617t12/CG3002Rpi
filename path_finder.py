import json, requests, math, heapq, pprint

class PathFinder(object):
	def __init__(self, building='Com1', level='1'):
		self.__request_url = 'http://showmyway.comp.nus.edu.sg/getMapInfo.php?Building=' + str(building) + '&Level=' + str(level)

		self.__wifi_radius = 150
		self.__reach_radius = 50

		self.__node_info = None
		self.__adjacency_matrix = None
		self.__num_node = -1
		self.__angle_of_north = -1

		self.__x_coordinate = -1
		self.__y_coordinate = -1
		self.__angle = -1

		self.__source = -1
		self.__target = -1

		self.__shortest_path = []
		self.__visited_nodes = []
		self.__next_node = -1

		self.__instruction = []

		self.__update_node_info()

	""" PUBLIC FUNCTION """
	# def is_initialized(self):
	# 	return (self.__node_info != None and self.__adjacency_matrix != None and self.__angle_of_north != -1 and self.__num_node != -1)

	def is_ready(self):
		return (self.__x_coordinate != -1 and self.__y_coordinate != -1 and self.__angle != -1)

	def update_coordinate(self, x_coordinate, y_coordinate, angle_from_north):
		self.__x_coordinate = x_coordinate
		self.__y_coordinate = y_coordinate
		self.__angle = self.__get_angle_wrt_grid(angle_from_north)
		# self.__angle = angle_from_north

		node_reached = -1
		reached = False

		if self.__next_node != -1:
			if self.__is_reached(self.__next_node, self.__x_coordinate, self.__y_coordinate):
				node_reached = self.__next_node
				reached = True
				self.__update_visited_nodes(self.__next_node)
			else:
				self.__update_instruction()

		return reached, node_reached

	def update_source_and_target(self, source, target):
		if not self.is_ready():
			return False

		if source < 1 or target < 1 or source > self.__num_node or target > self.__num_node:
			return False

		self.__source = source
		self.__target = target

		self.__update_shortest_path()

		self.update_coordinate(self.__x_coordinate, self.__y_coordinate, self.__get_angle_wrt_north(self.__angle))

	def get_audio_next_instruction(self):
		if self.__node_info == None:
			return 'Not Ready'

		if not self.__instruction:
			return 'No Instruction'

		instruction = self.__instruction[0]

		from_index = instruction['from_index']
		to_index = instruction['to_index']

		if from_index == 0:
			from_name = 'Current Position'
		else:
			from_name = self.__node_info[from_index]['name']

		to_name = self.__node_info[to_index]['name']

		distance = instruction['distance']
		
		angle = instruction['angle']

		right = True

		if angle > 180:
			right = False
			angle = 360 - angle

		audio_string = ""

		if right:
			audio_string += 'Turn Right %.2f And Go, %d' % (angle, distance)
		else:
			audio_string += 'Turn Left %.2f And Go, %d' % (angle, distance)

		return audio_string

	def get_audio_reached(self, reached_index):
		if self.__node_info == None:
			return 'Not Ready'

		reached_name = self.__node_info[reached_index]['name']

		audio_string = 'Reached Node, ' +  str(reached_index) + ',' + str(reached_name)

		return audio_string

	def get_angle_of_north(self):
		return self.__angle_of_north

	def get_x_coordinate(self):
		return self.__x_coordinate

	def get_y_coordinate(self):
		return self.__y_coordinate

	def get_coordinates_from_node(self, node):
		try:
			node_info = self.__node_info[node]
			return (node_info['x'], node_info['y'])
		except KeyError as e:
			print(e)
			return (-1, -1)

	def get_last_visited_node(self):
		if self.__visited_nodes:
			return self.__visited_nodes[-1]
		else:
			return None

	""" PRIVATE FUNCTION """

	def __is_reached(self, node_index, user_x, user_y):
		node_x = self.__node_info[node_index]['x']
		node_y = self.__node_info[node_index]['y']

		if self.__get_distance(user_x, user_y, node_x, node_y) < self.__reach_radius:
			return True
		else:
			return False

	def __update_visited_nodes(self, node):
		if node not in self.__visited_nodes:
			self.__visited_nodes.append(node)

		self.__update_instruction()

	def __update_node_info(self):
		try:
			request_info = requests.get(self.__request_url)
		except:
			print 'Error >> PathFinder::__update_node_info: Request could not get resource from url.'
			raise ValueError()

		try:
			json_request_info = json.loads(request_info.text)
		except:
			print 'Error >> PathFinder::__update_node_info: JSON could not be decoded. Check building and level'
			raise ValueError()

		if json_request_info['info'] is None:
			print 'Error >> PathFinder::__update_node_info: JSON is empty. Check building and level'
			raise ValueError()

		# wifi_info = {}

		# for node in json_request_info['wifi']:
		#   wifi_info[int(node['nodeId']) - 1] = {
		#     'name': node['nodeName'],
		#     'mac': node['macAddr'],
		#     'x': int(node['x']),
		#     'y': int(node['y'])
		#   }

		self.__node_info = {}

		for node in json_request_info['map']:
			self.__node_info[int(node['nodeId'])] = {
			'name': node['nodeName'],
			'neighbour' : [int(node_index.strip()) for node_index in str(node['linkTo']).split(',')],
			'x': int(node['x']),
			'y': int(node['y']),
			'wifi': []
			}

		# for node_id, node in self.__node_info.items():
		#   node_x = node['x']
		#   node_y = node['y']
			
		#   for wifi_id, wifi in wifi_info.items():
		#     wifi_x = wifi['x']
		#     wifi_y = wifi['y']

		#     delta_x = node_x - wifi_x
		#     delta_y = node_y - wifi_y

		#     diff = int(math.sqrt(delta_x * delta_x + delta_y * delta_y))
			
		#     if diff < self.__wifi_radius:
		#       self.__node_info[node_id]['wifi'].append((wifi['name'], wifi['mac']))

		self.__angle_of_north = int(json_request_info['info']['northAt'])

		self.__update_adjacency_matrix()

	def __update_adjacency_matrix(self):
		self.__num_node = len(self.__node_info)

		self.__adjacency_matrix = [[-1 for row in range(self.__num_node + 1)] for col in range(self.__num_node + 1)]

		for index, node in self.__node_info.iteritems():
			current_index = index
			current_x = node['x']
			current_y = node['y']

			for neighbour_index in node['neighbour']:
				neighbour_x = self.__node_info[neighbour_index]['x']
				neighbour_y = self.__node_info[neighbour_index]['y']

				delta_x = current_x - neighbour_x 
				delta_y = current_y - neighbour_y

				weight = int(math.sqrt(delta_x * delta_x + delta_y * delta_y))

				self.__adjacency_matrix[current_index][neighbour_index] = weight
				self.__adjacency_matrix[neighbour_index][current_index] = weight

	def __update_shortest_path(self):
		start_index = self.__source
		end_index = self.__target

		priority_queue = []
		visited = [False] * (self.__num_node + 1)
		# distance = [0 for i in range(self.__num_node + 1)]
		predecesor = [-1 for i in range(self.__num_node + 1)]

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

			for neighbour_index, neighbour_weight in enumerate(self.__adjacency_matrix[pop_index]):
				if neighbour_weight != -1 and not visited[neighbour_index]:
					push_weight = pop_weight + neighbour_weight
					push_index = neighbour_index
					push_predecesor = pop_index

					push_tuple = (push_weight, push_index, push_predecesor)

					heapq.heappush(priority_queue, push_tuple)

		self.__shortest_path = []

		while 1:
			self.__shortest_path.append(end_index)
			if end_index == start_index:
				break
			end_index = predecesor[end_index]

		self.__shortest_path.reverse()

		self.__update_instruction()

		# return shortest_path, distance

	def __update_instruction(self):
		self.__instruction = []

		remaining_path = []

		for index in self.__shortest_path:
			if index not in self.__visited_nodes:
				remaining_path.append(index)

		if not remaining_path:
			self.__instruction =  []
			self.__next_node = -1
			return 

		self.__next_node = remaining_path[0]

		prev_x = self.__x_coordinate
		prev_y = self.__y_coordinate
		prev_index = 0
		prev_angle = self.__angle

		for index in remaining_path:
			curr_name = self.__node_info[index]['name']
			curr_x = self.__node_info[index]['x']
			curr_y = self.__node_info[index]['y']
			curr_index = index

			distance = self.__get_distance(prev_x, prev_y, curr_x, curr_y)
			curr_angle = self.__get_angle(prev_x, prev_y, curr_x, curr_y)

			self.__instruction.append({
				'from_index': prev_index,
				'to_index': curr_index,
				'distance': distance,
				'angle': self.__get_angle_change(prev_angle, curr_angle)
			})

			prev_name = curr_name
			prev_x = curr_x
			prev_y = curr_y
			prev_index = curr_index
			prev_angle = curr_angle

	def __get_distance(self, x1, y1, x2, y2):
		x_diff = x2 - x1
		y_diff = y2 - y1

		return int(math.sqrt(x_diff * x_diff + y_diff * y_diff))

	def __get_angle_wrt_grid(self, angle):
		angle = angle + self.__angle_of_north

		angle = self.__convert_angle_to_convention(angle)

		return angle

	def __get_angle_wrt_north(self, angle):
		angle = angle - self.__angle_of_north

		angle = self.__convert_angle_to_convention(angle)

		return angle

	def __get_angle(self, x1, y1, x2, y2):
		x_diff = x2 - x1
		y_diff = y2 - y1

		angle = int(math.degrees(math.atan2(x_diff, y_diff)))

		angle = self.__convert_angle_to_convention(angle)

		return angle

	def __get_angle_change(self, angle_1, angle_2):
		angle = angle_2 - angle_1

		angle = self.__convert_angle_to_convention(angle)

		return angle

	def __convert_angle_to_convention(self, angle):
		while angle < 0:
			angle += 360

		while angle >= 360:
			angle -= 360

		return angle


if __name__ == "__main__":
	def test_visit(building, level):
		print 'testing::test_visit(): started visit test'

		pf = PathFinder(building, level)

		source = 1
		target = pf._PathFinder__num_node

		pf.update_coordinate(0, 0, 0)
		pf.update_source_and_target(source, target)

		shortest_path = pf._PathFinder__shortest_path

		for i in range(source, target + 1):
			reached, node_reached = pf.update_coordinate(pf._PathFinder__node_info[i]['x'], pf._PathFinder__node_info[i]['y'], 0)
			if reached:
				if node_reached not in shortest_path:
					print 'Error'
					print 'source' + str(source)
					print 'target' + str(target)
					print 'node reached: ' + str(node_reached)
					print 'shortest path: ' + str(shortest_path)

		print 'testing::test_visit(): completed visit test'

	def test_angle(building, level):
		print 'testing::test_angle(): started angle test'

		pf = PathFinder(building, level)

		source = 1
		target = 1

		pf.update_coordinate(0, 0, 0)
		pf.update_source_and_target(source, target)
		sign_x = [0, 1, 1, 1, 0, -1, -1, -1]
		sign_y = [1, 1, 0, -1, -1, -1, 0, 1]

		for i in range(0, 8):
			x_coordinate = pf._PathFinder__node_info[1]['x'] + (100 * sign_x[i])
			y_coordinate = pf._PathFinder__node_info[1]['y'] + (100 * sign_y[i])
			angle_of_user_from_north = 0
			expected_angle = pf._PathFinder__convert_angle_to_convention((360 - pf._PathFinder__angle_of_north) + 180 + (i * 45))

			for j in range(0, 8):
				pf.update_coordinate(x_coordinate, y_coordinate, angle_of_user_from_north + (j * 45))
				if pf._PathFinder__instruction[0]['angle'] != pf._PathFinder__convert_angle_to_convention(expected_angle - (j * 45)):
					print 'Error'
					print 'user x: ' + str(x_coordinate)
					print 'user y: ' + str(y_coordinate)
					print 'user angle from north: ' + str(pf._PathFinder__convert_angle_to_convention(angle_of_user_from_north))
					print 'next x: ' + str(pf._PathFinder__node_info[1]['x'])
					print 'next y: ' + str(pf._PathFinder__node_info[1]['y'])
					print 'next angle: ' + str(pf._PathFinder__instruction[0]['angle'])
					print 'expected angle: ' + str(pf._PathFinder__convert_angle_to_convention(expected_angle))

		print 'testing::test_angle(): completed angle test'

	def test_instruction(building, level):
		print 'testing::test_instruction(): started instruction test'

		pf = PathFinder(building, level)

		source = 1
		target = pf._PathFinder__num_node

		pf.update_coordinate(0, 0, 0)
		pf.update_source_and_target(source, target)

		shortest_path = pf._PathFinder__shortest_path
		instruction = pf._PathFinder__instruction

		len_instruction = len(instruction)

		for i in range(0, len(shortest_path)):
			reached, node_reached = pf.update_coordinate(pf._PathFinder__node_info[shortest_path[i]]['x'], pf._PathFinder__node_info[shortest_path[i]]['y'], 0)
			
			len_instruction -= 1

			if len_instruction != len(pf._PathFinder__instruction):
				print 'Error'
				print 'instruction: ' + str(pf._PathFinder__instruction)

		if len_instruction != 0:
			print 'Error'

		print 'testing::test_instruction(): completed instruction test'

	def test_update(building, level):
		print 'testing::test_update(): started update test'

		pf = PathFinder(building, level)

		source = 1
		target = 1

		pf.update_coordinate(pf._PathFinder__node_info[1]['x'], pf._PathFinder__node_info[1]['y'], 0)
		pf.update_source_and_target(source, target)

		instruction = pf._PathFinder__instruction

		if len(instruction) != 0:
			print 'Error'
			print 'instruction'

		print 'testing::test_update(): completed update test'
	
	building = 'Com1'
	level = '2'

	""" uncomment any of these tests to run tests """
	test_visit(building, level)
	test_angle(building, level)
	test_instruction(building, level)
	test_update(building, level)

	pf = PathFinder(building, level)
	# pf = PathFinder()
