import json, requests, math, heapq, pprint

class PathFinder(object):
	def __init__(self, building, level):
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

		self.__update_node_info(building, level)

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

		# self.update_coordinate(self.__x_coordinate, self.__y_coordinate, self.__get_angle_wrt_north(self.__angle))

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

		#audio_string = 'From, ' + str(from_name) + ' To Node, ' + str(to_index) + ',' + str(to_name) + ':'
		audio_string = ''

		if right:
			audio_string += 'Turn Right, ' + str(angle) + ' And Go, ' + str(distance)
		else:
			audio_string += 'Turn Left, ' + str(angle) + ' And Go, ' + str(distance)

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
		node_info = self.__node_info[node]
		try:
			return (node_info['x'], node_info['y'])
		except KeyError as e:
			print(e)
			return (-1, -1)	

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

	def __update_node_info(self, building, level):
		# if building == 0:
		# 	building_name = 'DemoBuilding'

		# 	# if level == 1 or level == 2 or level == 3:
		# 	# 	print 'Demo Building Level ' + str(level)
		# 	# else:
		# 	# 	print 'Error >> PathFinder::__update_node_info: Demo Building Level ' + str(level) + ' does not exist'
		# 	# 	raise ValueError()

		# elif building == 1:
		# 	building_name = 'Com1'

		# 	# if level == 1 or level == 2:
		# 	# 	print 'Com 1 Level ' +  str(level)
		# 	# else:
		# 	# 	print 'Error >> PathFinder::__update_node_info: Com 1 Level ' + str(level) + ' does not exist'
		# 	# 	raise ValueError()

		# elif building == 2:
		# 	building_name = 'Com2'

		# 	# if level == 2 or level == 3:
		# 	# 	print 'Com 2 Level ' +  str(level)
		# 	# else:
		# 	# 	print 'Error >> PathFinder::__update_node_info: Com 2 Level ' + str(level) + ' does not exist'
		# 	# 	raise ValueError()

		# else:
		# 	# print 'Error >> PathFinder::__update_node_info: Input Building does not exist'
		# 	# raise ValueError()
		# 	building_name = building # Incase of stupid digits for building 

		building_name = building # Incase of stupid digits for building 

		request_url = 'http://showmyway.comp.nus.edu.sg/getMapInfo.php?Building=' + str(building_name) + '&Level=' + str(level)

		try:
			request_info = requests.get(request_url)
			request_info = request_info.text

		except:
			if building == 0 and level == 1:
				request_info = json.dumps({"info":{"northAt":"180"},"map":[{"nodeId":"1","x":"200","y":"100","nodeName":"Entrance","linkTo":"2"},{"nodeId":"2","x":"400","y":"100","nodeName":"Room 1","linkTo":"1, 3"},{"nodeId":"3","x":"400","y":"200","nodeName":"Room 2","linkTo":"2, 4, 8"},{"nodeId":"4","x":"600","y":"200","nodeName":"Male Toilet","linkTo":"3, 6"},{"nodeId":"5","x":"600","y":"500","nodeName":"Female Toilet","linkTo":"8, 6"},{"nodeId":"6","x":"600","y":"300","nodeName":"Corridor","linkTo":"4, 5, 7"},{"nodeId":"7","x":"800","y":"300","nodeName":"TO level 2","linkTo":"6"},{"nodeId":"8","x":"400","y":"500","nodeName":"Room 3","linkTo":"3, 5"}],"wifi":[{"nodeId":"1","x":"300","y":"150","nodeName":"ap-101","macAddr":"29:11:A1:8B:C2:D0"},{"nodeId":"2","x":"700","y":"270","nodeName":"ap-102","macAddr":"9A:22:5B:1C:D4:5E"},{"nodeId":"3","x":"500","y":"500","nodeName":"ap-103","macAddr":"F9:33:0A:92:9C:D9"},{"nodeId":"4","x":"500","y":"350","nodeName":"ap-104","macAddr":"B1:44:A6:BB:EC:D0"}]})
			elif building == 0 and level == 2:
				request_info = json.dumps({"info":{"northAt":"180"},"map":[{"nodeId":"1","x":"800","y":"300","nodeName":"TO level 1,3","linkTo":"2"},{"nodeId":"2","x":"800","y":"100","nodeName":"Corridor","linkTo":"1,3"},{"nodeId":"3","x":"600","y":"100","nodeName":"Still Corridor","linkTo":"2,4"},{"nodeId":"4","x":"400","y":"100","nodeName":"Some more Corridor","linkTo":"3,5"},{"nodeId":"5","x":"200","y":"100","nodeName":"End of Corridor","linkTo":"4"}],"wifi":[{"nodeId":"2","x":"700","y":"200","nodeName":"ap-201","macAddr":"1C:DD:5E:AA:22:5B"}]})
			elif building == 0 and level == 3:
				request_info = json.dumps({"info":{"northAt":"180"},"map":[{"nodeId":"1","x":"800","y":"300","nodeName":"TO level 2","linkTo":"2,4"},{"nodeId":"2","x":"600","y":"500","nodeName":"North Point","linkTo":"1,3,5"},{"nodeId":"3","x":"600","y":"300","nodeName":"Center Point","linkTo":"1,2,4,5"},{"nodeId":"4","x":"600","y":"100","nodeName":"South Point","linkTo":"1,3,5"},{"nodeId":"5","x":"400","y":"300","nodeName":"West Point","linkTo":"2,3,4"}],"wifi":[{"nodeId":"1","x":"500","y":"450","nodeName":"ap-301","macAddr":"29:11:A1:8B:C2:D0"},{"nodeId":"2","x":"700","y":"270","nodeName":"ap-302","macAddr":"9A:22:5B:1C:D4:5E"}]})
			elif building == 1 and level == 1:
				request_info = json.dumps({"info":{"northAt":"315"},"map":[{"nodeId":"1","x":"500","y":"1200","nodeName":"Front Door","linkTo":"2"},{"nodeId":"2","x":"700","y":"1200","nodeName":"Front Mid","linkTo":"1, 3"},{"nodeId":"3","x":"700","y":"1100","nodeName":"1m","linkTo":"2, 4"},{"nodeId":"4","x":"700","y":"900","nodeName":"2m","linkTo":"3, 5"},{"nodeId":"5","x":"700","y":"600","nodeName":"3m","linkTo":"4, 6"},{"nodeId":"6","x":"700","y":"180","nodeName":"4.2m","linkTo":"5, 7, 8"},{"nodeId":"7","x":"500","y":"180","nodeName":"Dead End","linkTo":"6"},{"nodeId":"8","x":"900","y":"180","nodeName":"Back Door","linkTo":"6"}],"wifi":[]})
			elif building == 1 and level == 2:
				request_info = json.dumps({"info":{"northAt":"315"},"map":[{"nodeId":"1","x":"0","y":"2436","nodeName":"TO LT15","linkTo":"2 "},{"nodeId":"2","x":"2152","y":"2436","nodeName":"P2","linkTo":"1, 3, 4 "},{"nodeId":"3","x":"2152","y":"731","nodeName":"Linkway","linkTo":"2"},{"nodeId":"4","x":"2883","y":"2436","nodeName":"P4","linkTo":"2, 5, 6, 7"},{"nodeId":"5","x":"2883","y":"1787","nodeName":"P5","linkTo":"4, 8 "},{"nodeId":"6","x":"2883","y":"2924","nodeName":"Seminar Room 6","linkTo":"4"},{"nodeId":"7","x":"3776","y":"2436","nodeName":"Lobby ","linkTo":"4, 10"},{"nodeId":"8","x":"3330","y":"1787","nodeName":"P8","linkTo":"5, 9, 10 "},{"nodeId":"9","x":"3330","y":"934","nodeName":"Seminar Room 2","linkTo":"8"},{"nodeId":"10","x":"3776","y":"1787","nodeName":"P10","linkTo":"7, 8, 11"},{"nodeId":"11","x":"5603","y":"1787","nodeName":"Student Area","linkTo":"10, 12, 13, 14"},{"nodeId":"12","x":"5603","y":"2924","nodeName":"Seminar Room 1","linkTo":"11"},{"nodeId":"13","x":"5603","y":"609","nodeName":"P13","linkTo":"11, 36"},{"nodeId":"14","x":"7065","y":"1787","nodeName":"P14","linkTo":"11, 15, 37 "},{"nodeId":"15","x":"7065","y":"2802","nodeName":"P15","linkTo":"14, 32 "},{"nodeId":"16","x":"7065","y":"731","nodeName":"P16","linkTo":"18, 37"},{"nodeId":"17","x":"9014","y":"2802","nodeName":"P17","linkTo":"39, 19, 21 "},{"nodeId":"18","x":"8283","y":"731","nodeName":"P18","linkTo":"16, 20, 22"},{"nodeId":"19","x":"9014","y":"2193","nodeName":"Executive Classroom","linkTo":"17"},{"nodeId":"20","x":"8283","y":"1056","nodeName":"Tutorial Room 11","linkTo":"18"},{"nodeId":"21","x":"9460","y":"2802","nodeName":"P21","linkTo":"17, 23, 24 "},{"nodeId":"22","x":"9744","y":"731","nodeName":"P22","linkTo":"18, 25, 34"},{"nodeId":"23","x":"9460","y":"3248","nodeName":"Seminar Room 9","linkTo":"21"},{"nodeId":"24","x":"11003","y":"2802","nodeName":"P24","linkTo":"21, 27, 28"},{"nodeId":"25","x":"9744","y":"1056","nodeName":"NUS Hacker's Room","linkTo":"22"},{"nodeId":"26","x":"11003","y":"691","nodeName":"P26","linkTo":"34, 28, 29 "},{"nodeId":"27","x":"11003","y":"3248","nodeName":"Seminar Room 11","linkTo":"24 "},{"nodeId":"28","x":"11003","y":"1259","nodeName":"P28","linkTo":"24, 26, 30"},{"nodeId":"29","x":"11571","y":"691","nodeName":"P29","linkTo":"26, 31 "},{"nodeId":"30","x":"12180","y":"731","nodeName":"TO Canteen","linkTo":"28 "},{"nodeId":"31","x":"11815","y":"406","nodeName":"TO COM2-2-1","linkTo":"29 "},{"nodeId":"32","x":"7552","y":"2802","nodeName":"P32","linkTo":"15, 33, 39 "},{"nodeId":"33","x":"7552","y":"3086","nodeName":"Seminar Room 7","linkTo":"32"},{"nodeId":"34","x":"10272","y":"731","nodeName":"P34","linkTo":"22, 26, 35 "},{"nodeId":"35","x":"10272","y":"447","nodeName":"Tutorial Room 5","linkTo":"34 "},{"nodeId":"36","x":"4263","y":"609","nodeName":"Cerebro","linkTo":"13"},{"nodeId":"37","x":"7065","y":"1543","nodeName":"P37","linkTo":"14, 16, 38 "},{"nodeId":"38","x":"7552","y":"1543","nodeName":"SR3 Front","linkTo":"37"},{"nodeId":"39","x":"8811","y":"2802","nodeName":"P39","linkTo":"17, 32, 40 "},{"nodeId":"40","x":"8811","y":"2436","nodeName":"SR3 Back","linkTo":"39"}],"wifi":[{"nodeId":"1","x":"569","y":"2599","nodeName":"arc-0201-a","macAddr":"e8:ba:70:61:c9:60"},{"nodeId":"2","x":"2274","y":"2599","nodeName":"arc-0202-a","macAddr":"e8:ba:70:61:af:20"},{"nodeId":"3","x":"2964","y":"731","nodeName":"arc-0204-a","macAddr":"04:da:d2:74:cf:30"},{"nodeId":"4","x":"5400","y":"934","nodeName":"arc-0205-a","macAddr":"e8:ba:70:52:3b:e0"},{"nodeId":"5","x":"4060","y":"609","nodeName":"arc-0205-b","macAddr":"e8:ba:70:52:bf:80"},{"nodeId":"6","x":"4263","y":"2315","nodeName":"arc-0206-a","macAddr":"e8:ba:70:52:0b:40"},{"nodeId":"7","x":"6578","y":"2924","nodeName":"arc-0206-b","macAddr":"e8:ba:70:52:1e:90"},{"nodeId":"8","x":"8445","y":"2842","nodeName":"arc-0212-a","macAddr":"e8:ba:70:52:ab:e0"},{"nodeId":"9","x":"10435","y":"2964","nodeName":"arc-0210-a","macAddr":"e8:ba:70:61:b3:50"},{"nodeId":"10","x":"7796","y":"1706","nodeName":"arc-0212-b","macAddr":"50:06:04:8d:d0:10"},{"nodeId":"11","x":"8608","y":"1868","nodeName":"arc-0213-a","macAddr":"04:da:d2:74:c8:70"},{"nodeId":"12","x":"10800","y":"1097","nodeName":"arc-0214-a","macAddr":"e8:ba:70:52:bd:80"},{"nodeId":"13","x":"9866","y":"731","nodeName":"arc-0239-a","macAddr":"e8:ba:70:61:a8:80"},{"nodeId":"14","x":"6902","y":"934","nodeName":"arc-0241-a","macAddr":"28:93:fe:d3:8b:20"}]})
			elif building == 2 and level == 2:
				request_info = json.dumps({"info":{"northAt":"305"},"map":[{"nodeId":"1","x":"61","y":"4024","nodeName":"TO COM1-2-31","linkTo":"17"},{"nodeId":"2","x":"1585","y":"2561","nodeName":"P2","linkTo":"3, 5, 17"},{"nodeId":"3","x":"1342","y":"2378","nodeName":"Uncle Soo's Office","linkTo":"2"},{"nodeId":"4","x":"2134","y":"2317","nodeName":"Colin's Office","linkTo":"5"},{"nodeId":"5","x":"1951","y":"2195","nodeName":"P5","linkTo":"2, 4, 19"},{"nodeId":"6","x":"2988","y":"1098","nodeName":"P6","linkTo":"7, 11, 19"},{"nodeId":"7","x":"3353","y":"732","nodeName":"P7","linkTo":"6, 8"},{"nodeId":"8","x":"4085","y":"732","nodeName":"P8","linkTo":"7, 9, 10"},{"nodeId":"9","x":"4085","y":"976","nodeName":"Discussion Room 6","linkTo":"8"},{"nodeId":"10","x":"8047","y":"732","nodeName":"End of Corridor","linkTo":"8"},{"nodeId":"11","x":"3475","y":"1646","nodeName":"Glass Door","linkTo":"6, 12"},{"nodeId":"12","x":"3780","y":"1829","nodeName":"Wooden Door","linkTo":"11, 13"},{"nodeId":"13","x":"4146","y":"2012","nodeName":"Another Door","linkTo":"12, 14"},{"nodeId":"14","x":"4329","y":"2317","nodeName":"Stairwell","linkTo":"13, 15"},{"nodeId":"15","x":"3841","y":"2744","nodeName":"Halfway","linkTo":"14, 16"},{"nodeId":"16","x":"3719","y":"2622","nodeName":"TO COM2-3-11","linkTo":"15"},{"nodeId":"17","x":"1159","y":"2927","nodeName":"P17","linkTo":"1, 2, 18"},{"nodeId":"18","x":"915","y":"2805","nodeName":"Bimlesh's Office","linkTo":"17"},{"nodeId":"19","x":"2622","y":"1464","nodeName":"P19","linkTo":"5, 6, 20"},{"nodeId":"20","x":"2378","y":"1342","nodeName":"Damith's Office","linkTo":"19"}],"wifi":[{"nodeId":"1","x":"366","y":"3658","nodeName":"arc-0215-a","macAddr":"e8:ba:70:61:b6:50"},{"nodeId":"2","x":"1464","y":"2683","nodeName":"arc2-0261-a","macAddr":"50:06:04:8d:ac:c0"},{"nodeId":"3","x":"2500","y":"1585","nodeName":"arc-0229-a","macAddr":"e8:ba:70:61:a8:f0"},{"nodeId":"4","x":"3841","y":"732","nodeName":"arc2-0254-a","macAddr":"e8:ba:70:52:3e:80"},{"nodeId":"5","x":"5548","y":"671","nodeName":"arc2-0250-a","macAddr":"e8:ba:70:61:ad:b0"},{"nodeId":"6","x":"7681","y":"671","nodeName":"arc2-0243-a","macAddr":"e8:ba:70:52:53:10"}]})
			elif building == 2 and level == 3:
				request_info = json.dumps({"info":{"northAt":"305"},"map":[{"nodeId":"1","x":"61","y":"4024","nodeName":"TO COM1-3-18","linkTo":"16"},{"nodeId":"2","x":"2988","y":"1098","nodeName":"P2","linkTo":"3, 7, 14 "},{"nodeId":"3","x":"3353","y":"732","nodeName":"P3","linkTo":"2, 4 "},{"nodeId":"4","x":"3902","y":"732","nodeName":"P4","linkTo":"3, 5, 12 "},{"nodeId":"5","x":"3902","y":"976","nodeName":"Discussion Room 7","linkTo":"4"},{"nodeId":"6","x":"8047","y":"732","nodeName":"End of Corridor","linkTo":"12"},{"nodeId":"7","x":"3475","y":"1646","nodeName":"Glass Door","linkTo":"2, 8"},{"nodeId":"8","x":"3780","y":"1829","nodeName":"Wooden Door","linkTo":"7, 9"},{"nodeId":"9","x":"4146","y":"2012","nodeName":"Another Door","linkTo":"8, 10"},{"nodeId":"10","x":"4207","y":"2134","nodeName":"Stairwell","linkTo":"9, 11"},{"nodeId":"11","x":"3719","y":"2622","nodeName":"TO COM2-2-16","linkTo":"10"},{"nodeId":"12","x":"4085","y":"732","nodeName":"P12","linkTo":"4, 6, 13"},{"nodeId":"13","x":"4085","y":"976","nodeName":"Discussion Room 8","linkTo":"12"},{"nodeId":"14","x":"2134","y":"1951","nodeName":"P14","linkTo":"2, 15, 16 "},{"nodeId":"15","x":"2317","y":"2012","nodeName":"Henry's Room","linkTo":"14"},{"nodeId":"16","x":"1524","y":"2500","nodeName":"Mysterious Pt","linkTo":"1, 14"}],"wifi":[{"nodeId":"1","x":"1037","y":"2988","nodeName":"arc-0334-a","macAddr":"e8:ba:70:52:51:70"},{"nodeId":"2","x":"2195","y":"1829","nodeName":"arc-0324-a","macAddr":"e8:ba:70:61:b1:60"},{"nodeId":"3","x":"3719","y":"732","nodeName":"arc2-0348-a","macAddr":"28:93:fe:c8:a8:e0"},{"nodeId":"4","x":"5487","y":"671","nodeName":"arc2-0318-a","macAddr":"70:10:5c:7d:39:b0"},{"nodeId":"5","x":"7255","y":"732","nodeName":"arc2-0339-a","macAddr":"e8:ba:70:52:bf:b0"},{"nodeId":"6","x":"9205","y":"732","nodeName":"arc2-0332-a","macAddr":"e8:ba:70:52:c5:20"}]})
			else:
				print 'Error >> PathFinder::__update_node_info: Unexpected combination of building and level input.'
				raise ValueError()

		try:
			json_request_info = json.loads(request_info)
		except:
			print 'Error >> PathFinder::__update_node_info: JSON could not be decoded.'
			raise ValueError()

		if json_request_info['info'] is None:
			print 'Error >> PathFinder::__update_node_info: JSON is empty.'
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

		pf.update_coordinate(pf._PathFinder__node_info[1]['x'], pf._PathFinder__node_info[1]['y'], 0)

		instruction = pf._PathFinder__instruction

		if len(instruction) != 0:
			print 'Error'
			print 'instruction'

		print 'testing::test_update(): completed update test'
	
	""" uncomment any of these tests to run tests """
	# building = 0
	# level = 1

	# test_visit(building, level)
	# test_angle(building, level)
	# test_instruction(building, level)
	# test_update(building, level)
