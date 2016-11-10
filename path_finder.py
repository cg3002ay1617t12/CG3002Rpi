import json, heapq, pprint, math, os, time

class PathFinder(object):
	def __init__(self):
		# self.__wifi_radius = 150
		
		try:
			self.__env         = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read()) 
			self.__stride_length = self.__env['STRIDE_LENGTH']
		except Exception as e:
			print("[PATH FINDER] Environment file not found, using defaults instead")
			self.__stride_length = 60

		self.__x_coordinate = -1
		self.__y_coordinate = -1
		self.__angle = -1

		self.__reach_radius = math.ceil(1.5 * self.__stride_length)
		self.__node_info = None
		self.__adjacency_matrix = None
		self.__num_node = -1
		self.__angle_of_north = self.__set_angle_of_north()

		self.__source = -1
		self.__target = -1

		self.__shortest_path = []
		self.__visited_nodes = []
		self.__next_node = -1

		self.__instruction = []

		self.__update_node_info()

		""""""
		self.time = time.time()

	""" PUBLIC FUNCTION """
	# def is_initialized(self):
	# 	return (self.__node_info != None and self.__adjacency_matrix != None and self.__angle_of_north != -1 and self.__num_node != -1)

	def is_ready(self):
		return (self.__x_coordinate != -1 and self.__y_coordinate != -1 and self.__angle != -1)
    
	def get_next_coordinates(self):
		try:
			return self.get_coordinates_from_node(self.__next_node)
		except Exception as e:
			return (None, None)

	def update_coordinate(self, x_coordinate, y_coordinate, angle_from_north):
		self.__x_coordinate = x_coordinate
		self.__y_coordinate = y_coordinate
		self.__angle = self.__get_angle_wrt_grid(angle_from_north)
		# self.__angle = angle_from_north

		node_reached = -1
		reached = False

		if time.time() - self.time > 5:
			self.time = time.time()

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

		if (source <= 100) or (source >= 141 and source <= 200) or (source >= 221 and source <= 300) or (source >= 317):
			return False

		if (target <= 100) or (target >= 141 and target <= 200) or (target >= 221 and target <= 300) or (target >= 317):
			return False

		self.__source = source
		self.__target = target

		# self.__visited_nodes = []

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
			audio_string += ' Right %d, Go %d to %s' % (math.floor(angle), math.floor(distance/self.__stride_length), to_name)
		else:
			audio_string += ' Left %d, Go %d to %s' % (math.floor(angle), math.floor(distance/self.__stride_length), to_name)

		return audio_string

	def get_audio_reached(self, reached_index):
		if self.__node_info == None:
			return 'Not Ready'

		reached_name = self.__node_info[reached_index]['name']

		# if reached_index < 20: change reached_index 

		audio_string = 'Reached Node, ' +  str(reached_index) + ' , ' + str(reached_name) + ' '

		return audio_string

	def get_angle_of_north(self):
		return self.__angle_of_north

	def __set_angle_of_north(self):
		if self.__x_coordinate < 100000:
			return 315
		else:
			return 305

	def get_angle_to_next_node(self):
		# return angle_wrt_north
		if self.__next_node == -1:
			print '[PATH_FINDER] __next_node: ' + str(self.__next_node)
			return -1

		next_node = self.__next_node

		if self.__shortest_path == []:
			print '[PATH_FINDER] __shortest_path: ' + str(self.__shortest_path)
			return -1

		curr_node = 0

		for index, node in enumerate(self.__shortest_path):
			if node == next_node:
				if index > 0:
					curr_node = self.__shortest_path[index - 1]

		if curr_node == 0:
			print '[PATH_FINDER] curr_node: ' + str(curr_node)
			return 0

		curr_node_info = self.__node_info[curr_node]
		next_node_info = self.__node_info[next_node]

		angle = self.__get_angle(curr_node_info['x'], curr_node_info['y'], next_node_info['x'], next_node_info['y'])

		angle = self.__get_angle_wrt_north(angle)

		return angle

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
			return (None, None)

	def get_prev_visited_node(self):
		if self.__visited_nodes:
			return self.__node_info[self.__visited_nodes[-1]]['name']
		else:
			return "None"

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

		# building_name = building # Incase of stupid digits for building 

		# request_url = 'http://showmyway.comp.nus.edu.sg/getMapInfo.php?Building=' + str(building_name) + '&Level=' + str(level)

		# try:
		# 	request_info = requests.get(request_url)
		# 	request_info = request_info.text

		# except:
		# 	if building == 0 and level == 1:
		# 		request_info = json.dumps({"info":{"northAt":"180"},"map":[{"nodeId":"1","x":"200","y":"100","nodeName":"Entrance","linkTo":"2"},{"nodeId":"2","x":"400","y":"100","nodeName":"Room 1","linkTo":"1, 3"},{"nodeId":"3","x":"400","y":"200","nodeName":"Room 2","linkTo":"2, 4, 8"},{"nodeId":"4","x":"600","y":"200","nodeName":"Male Toilet","linkTo":"3, 6"},{"nodeId":"5","x":"600","y":"500","nodeName":"Female Toilet","linkTo":"8, 6"},{"nodeId":"6","x":"600","y":"300","nodeName":"Corridor","linkTo":"4, 5, 7"},{"nodeId":"7","x":"800","y":"300","nodeName":"TO level 2","linkTo":"6"},{"nodeId":"8","x":"400","y":"500","nodeName":"Room 3","linkTo":"3, 5"}],"wifi":[{"nodeId":"1","x":"300","y":"150","nodeName":"ap-101","macAddr":"29:11:A1:8B:C2:D0"},{"nodeId":"2","x":"700","y":"270","nodeName":"ap-102","macAddr":"9A:22:5B:1C:D4:5E"},{"nodeId":"3","x":"500","y":"500","nodeName":"ap-103","macAddr":"F9:33:0A:92:9C:D9"},{"nodeId":"4","x":"500","y":"350","nodeName":"ap-104","macAddr":"B1:44:A6:BB:EC:D0"}]})
		# 	elif building == 0 and level == 2:
		# 		request_info = json.dumps({"info":{"northAt":"180"},"map":[{"nodeId":"1","x":"800","y":"300","nodeName":"TO level 1,3","linkTo":"2"},{"nodeId":"2","x":"800","y":"100","nodeName":"Corridor","linkTo":"1,3"},{"nodeId":"3","x":"600","y":"100","nodeName":"Still Corridor","linkTo":"2,4"},{"nodeId":"4","x":"400","y":"100","nodeName":"Some more Corridor","linkTo":"3,5"},{"nodeId":"5","x":"200","y":"100","nodeName":"End of Corridor","linkTo":"4"}],"wifi":[{"nodeId":"2","x":"700","y":"200","nodeName":"ap-201","macAddr":"1C:DD:5E:AA:22:5B"}]})
		# 	elif building == 0 and level == 3:
		# 		request_info = json.dumps({"info":{"northAt":"180"},"map":[{"nodeId":"1","x":"800","y":"300","nodeName":"TO level 2","linkTo":"2,4"},{"nodeId":"2","x":"600","y":"500","nodeName":"North Point","linkTo":"1,3,5"},{"nodeId":"3","x":"600","y":"300","nodeName":"Center Point","linkTo":"1,2,4,5"},{"nodeId":"4","x":"600","y":"100","nodeName":"South Point","linkTo":"1,3,5"},{"nodeId":"5","x":"400","y":"300","nodeName":"West Point","linkTo":"2,3,4"}],"wifi":[{"nodeId":"1","x":"500","y":"450","nodeName":"ap-301","macAddr":"29:11:A1:8B:C2:D0"},{"nodeId":"2","x":"700","y":"270","nodeName":"ap-302","macAddr":"9A:22:5B:1C:D4:5E"}]})
		# 	elif building == 1 and level == 1:
		# 		request_info = json.dumps({"info":{"northAt":"315"},"map":[{"nodeId":"1","x":"500","y":"1200","nodeName":"Front Door","linkTo":"2"},{"nodeId":"2","x":"700","y":"1200","nodeName":"Front Mid","linkTo":"1, 3"},{"nodeId":"3","x":"700","y":"1100","nodeName":"1m","linkTo":"2, 4"},{"nodeId":"4","x":"700","y":"900","nodeName":"2m","linkTo":"3, 5"},{"nodeId":"5","x":"700","y":"600","nodeName":"3m","linkTo":"4, 6"},{"nodeId":"6","x":"700","y":"180","nodeName":"4.2m","linkTo":"5, 7, 8"},{"nodeId":"7","x":"500","y":"180","nodeName":"Dead End","linkTo":"6"},{"nodeId":"8","x":"900","y":"180","nodeName":"Back Door","linkTo":"6"}],"wifi":[]})
		# 	elif building == 1 and level == 2:
		# 		request_info = json.dumps({"info":{"northAt":"315"},"map":[{"nodeId":"1","x":"0","y":"2436","nodeName":"TO LT15","linkTo":"2 "},{"nodeId":"2","x":"2152","y":"2436","nodeName":"P2","linkTo":"1, 3, 4 "},{"nodeId":"3","x":"2152","y":"731","nodeName":"Linkway","linkTo":"2"},{"nodeId":"4","x":"2883","y":"2436","nodeName":"P4","linkTo":"2, 5, 6, 7"},{"nodeId":"5","x":"2883","y":"1787","nodeName":"P5","linkTo":"4, 8 "},{"nodeId":"6","x":"2883","y":"2924","nodeName":"Seminar Room 6","linkTo":"4"},{"nodeId":"7","x":"3776","y":"2436","nodeName":"Lobby ","linkTo":"4, 10"},{"nodeId":"8","x":"3330","y":"1787","nodeName":"P8","linkTo":"5, 9, 10 "},{"nodeId":"9","x":"3330","y":"934","nodeName":"Seminar Room 2","linkTo":"8"},{"nodeId":"10","x":"3776","y":"1787","nodeName":"P10","linkTo":"7, 8, 11"},{"nodeId":"11","x":"5603","y":"1787","nodeName":"Student Area","linkTo":"10, 12, 13, 14"},{"nodeId":"12","x":"5603","y":"2924","nodeName":"Seminar Room 1","linkTo":"11"},{"nodeId":"13","x":"5603","y":"609","nodeName":"P13","linkTo":"11, 36"},{"nodeId":"14","x":"7065","y":"1787","nodeName":"P14","linkTo":"11, 15, 37 "},{"nodeId":"15","x":"7065","y":"2802","nodeName":"P15","linkTo":"14, 32 "},{"nodeId":"16","x":"7065","y":"731","nodeName":"P16","linkTo":"18, 37"},{"nodeId":"17","x":"9014","y":"2802","nodeName":"P17","linkTo":"39, 19, 21 "},{"nodeId":"18","x":"8283","y":"731","nodeName":"P18","linkTo":"16, 20, 22"},{"nodeId":"19","x":"9014","y":"2193","nodeName":"Executive Classroom","linkTo":"17"},{"nodeId":"20","x":"8283","y":"1056","nodeName":"Tutorial Room 11","linkTo":"18"},{"nodeId":"21","x":"9460","y":"2802","nodeName":"P21","linkTo":"17, 23, 24 "},{"nodeId":"22","x":"9744","y":"731","nodeName":"P22","linkTo":"18, 25, 34"},{"nodeId":"23","x":"9460","y":"3248","nodeName":"Seminar Room 9","linkTo":"21"},{"nodeId":"24","x":"11003","y":"2802","nodeName":"P24","linkTo":"21, 27, 28"},{"nodeId":"25","x":"9744","y":"1056","nodeName":"NUS Hacker's Room","linkTo":"22"},{"nodeId":"26","x":"11003","y":"691","nodeName":"P26","linkTo":"34, 28, 29 "},{"nodeId":"27","x":"11003","y":"3248","nodeName":"Seminar Room 11","linkTo":"24 "},{"nodeId":"28","x":"11003","y":"1259","nodeName":"P28","linkTo":"24, 26, 30"},{"nodeId":"29","x":"11571","y":"691","nodeName":"P29","linkTo":"26, 31 "},{"nodeId":"30","x":"12180","y":"731","nodeName":"TO Canteen","linkTo":"28 "},{"nodeId":"31","x":"11815","y":"406","nodeName":"TO 2-2-1","linkTo":"29 "},{"nodeId":"32","x":"7552","y":"2802","nodeName":"P32","linkTo":"15, 33, 39 "},{"nodeId":"33","x":"7552","y":"3086","nodeName":"Seminar Room 7","linkTo":"32"},{"nodeId":"34","x":"10272","y":"731","nodeName":"P34","linkTo":"22, 26, 35 "},{"nodeId":"35","x":"10272","y":"447","nodeName":"Tutorial Room 5","linkTo":"34 "},{"nodeId":"36","x":"4263","y":"609","nodeName":"Cerebro","linkTo":"13"},{"nodeId":"37","x":"7065","y":"1543","nodeName":"P37","linkTo":"14, 16, 38 "},{"nodeId":"38","x":"7552","y":"1543","nodeName":"SR3 Front","linkTo":"37"},{"nodeId":"39","x":"8811","y":"2802","nodeName":"P39","linkTo":"17, 32, 40 "},{"nodeId":"40","x":"8811","y":"2436","nodeName":"SR3 Back","linkTo":"39"}],"wifi":[{"nodeId":"1","x":"569","y":"2599","nodeName":"arc-0201-a","macAddr":"e8:ba:70:61:c9:60"},{"nodeId":"2","x":"2274","y":"2599","nodeName":"arc-0202-a","macAddr":"e8:ba:70:61:af:20"},{"nodeId":"3","x":"2964","y":"731","nodeName":"arc-0204-a","macAddr":"04:da:d2:74:cf:30"},{"nodeId":"4","x":"5400","y":"934","nodeName":"arc-0205-a","macAddr":"e8:ba:70:52:3b:e0"},{"nodeId":"5","x":"4060","y":"609","nodeName":"arc-0205-b","macAddr":"e8:ba:70:52:bf:80"},{"nodeId":"6","x":"4263","y":"2315","nodeName":"arc-0206-a","macAddr":"e8:ba:70:52:0b:40"},{"nodeId":"7","x":"6578","y":"2924","nodeName":"arc-0206-b","macAddr":"e8:ba:70:52:1e:90"},{"nodeId":"8","x":"8445","y":"2842","nodeName":"arc-0212-a","macAddr":"e8:ba:70:52:ab:e0"},{"nodeId":"9","x":"10435","y":"2964","nodeName":"arc-0210-a","macAddr":"e8:ba:70:61:b3:50"},{"nodeId":"10","x":"7796","y":"1706","nodeName":"arc-0212-b","macAddr":"50:06:04:8d:d0:10"},{"nodeId":"11","x":"8608","y":"1868","nodeName":"arc-0213-a","macAddr":"04:da:d2:74:c8:70"},{"nodeId":"12","x":"10800","y":"1097","nodeName":"arc-0214-a","macAddr":"e8:ba:70:52:bd:80"},{"nodeId":"13","x":"9866","y":"731","nodeName":"arc-0239-a","macAddr":"e8:ba:70:61:a8:80"},{"nodeId":"14","x":"6902","y":"934","nodeName":"arc-0241-a","macAddr":"28:93:fe:d3:8b:20"}]})
		# 	elif building == 2 and level == 2:
		# 		request_info = json.dumps({"info":{"northAt":"305"},"map":[{"nodeId":"1","x":"61","y":"4024","nodeName":"TO 1-2-31","linkTo":"17"},{"nodeId":"2","x":"1585","y":"2561","nodeName":"P2","linkTo":"3, 5, 17"},{"nodeId":"3","x":"1342","y":"2378","nodeName":"Uncle Soo's Office","linkTo":"2"},{"nodeId":"4","x":"2134","y":"2317","nodeName":"Colin's Office","linkTo":"5"},{"nodeId":"5","x":"1951","y":"2195","nodeName":"P5","linkTo":"2, 4, 19"},{"nodeId":"6","x":"2988","y":"1098","nodeName":"P6","linkTo":"7, 11, 19"},{"nodeId":"7","x":"3353","y":"732","nodeName":"P7","linkTo":"6, 8"},{"nodeId":"8","x":"4085","y":"732","nodeName":"P8","linkTo":"7, 9, 10"},{"nodeId":"9","x":"4085","y":"976","nodeName":"Discussion Room 6","linkTo":"8"},{"nodeId":"10","x":"8047","y":"732","nodeName":"End of Corridor","linkTo":"8"},{"nodeId":"11","x":"3475","y":"1646","nodeName":"Glass Door","linkTo":"6, 12"},{"nodeId":"12","x":"3780","y":"1829","nodeName":"Wooden Door","linkTo":"11, 13"},{"nodeId":"13","x":"4146","y":"2012","nodeName":"Another Door","linkTo":"12, 14"},{"nodeId":"14","x":"4329","y":"2317","nodeName":"Stairwell","linkTo":"13, 15"},{"nodeId":"15","x":"3841","y":"2744","nodeName":"Halfway","linkTo":"14, 16"},{"nodeId":"16","x":"3719","y":"2622","nodeName":"TO 2-3-11","linkTo":"15"},{"nodeId":"17","x":"1159","y":"2927","nodeName":"P17","linkTo":"1, 2, 18"},{"nodeId":"18","x":"915","y":"2805","nodeName":"Bimlesh's Office","linkTo":"17"},{"nodeId":"19","x":"2622","y":"1464","nodeName":"P19","linkTo":"5, 6, 20 "},{"nodeId":"20","x":"2378","y":"1342","nodeName":"Damith's Office","linkTo":"19"}],"wifi":[{"nodeId":"1","x":"366","y":"3658","nodeName":"arc-0215-a","macAddr":"e8:ba:70:61:b6:50"},{"nodeId":"2","x":"1464","y":"2683","nodeName":"arc2-0261-a","macAddr":"50:06:04:8d:ac:c0"},{"nodeId":"3","x":"2500","y":"1585","nodeName":"arc-0229-a","macAddr":"e8:ba:70:61:a8:f0"},{"nodeId":"4","x":"3841","y":"732","nodeName":"arc2-0254-a","macAddr":"e8:ba:70:52:3e:80"},{"nodeId":"5","x":"5548","y":"671","nodeName":"arc2-0250-a","macAddr":"e8:ba:70:61:ad:b0"},{"nodeId":"6","x":"7681","y":"671","nodeName":"arc2-0243-a","macAddr":"e8:ba:70:52:53:10"}]})
		# 	elif building == 2 and level == 3:
		# 		request_info = json.dumps({"info":{"northAt":"305"},"map":[{"nodeId":"1","x":"61","y":"4024","nodeName":"TO 1-3-18","linkTo":"16"},{"nodeId":"2","x":"2988","y":"1098","nodeName":"P2","linkTo":"3, 7, 14 "},{"nodeId":"3","x":"3353","y":"732","nodeName":"P3","linkTo":"2, 4 "},{"nodeId":"4","x":"3902","y":"732","nodeName":"P4","linkTo":"3, 5, 12 "},{"nodeId":"5","x":"3902","y":"976","nodeName":"Discussion Room 7","linkTo":"4"},{"nodeId":"6","x":"8047","y":"732","nodeName":"End of Corridor","linkTo":"12"},{"nodeId":"7","x":"3475","y":"1646","nodeName":"Glass Door","linkTo":"2, 8"},{"nodeId":"8","x":"3780","y":"1829","nodeName":"Wooden Door","linkTo":"7, 9"},{"nodeId":"9","x":"4146","y":"2012","nodeName":"Another Door","linkTo":"8, 10"},{"nodeId":"10","x":"4207","y":"2134","nodeName":"Stairwell","linkTo":"9, 11"},{"nodeId":"11","x":"3719","y":"2622","nodeName":"TO 2-2-16","linkTo":"10"},{"nodeId":"12","x":"4085","y":"732","nodeName":"P12","linkTo":"4, 6, 13"},{"nodeId":"13","x":"4085","y":"976","nodeName":"Discussion Room 8","linkTo":"12"},{"nodeId":"14","x":"2134","y":"1951","nodeName":"P14","linkTo":"2, 15, 16 "},{"nodeId":"15","x":"2317","y":"2012","nodeName":"Henry's Room","linkTo":"14"},{"nodeId":"16","x":"1524","y":"2500","nodeName":"Mysterious Pt","linkTo":"1, 14"}],"wifi":[{"nodeId":"1","x":"1037","y":"2988","nodeName":"arc-0334-a","macAddr":"e8:ba:70:52:51:70"},{"nodeId":"2","x":"2195","y":"1829","nodeName":"arc-0324-a","macAddr":"e8:ba:70:61:b1:60"},{"nodeId":"3","x":"3719","y":"732","nodeName":"arc2-0348-a","macAddr":"28:93:fe:c8:a8:e0"},{"nodeId":"4","x":"5487","y":"671","nodeName":"arc2-0318-a","macAddr":"70:10:5c:7d:39:b0"},{"nodeId":"5","x":"7255","y":"732","nodeName":"arc2-0339-a","macAddr":"e8:ba:70:52:bf:b0"},{"nodeId":"6","x":"9205","y":"732","nodeName":"arc2-0332-a","macAddr":"e8:ba:70:52:c5:20"}]})
		# 	else:
		# 		print '[PATH FINDER] Error >> PathFinder::__update_node_info: Unexpected combination of building and level input.'
		# 		raise ValueError()

		# COM1L2 
		# request_info = json.dumps({u'info': {u'northAt': u'315'}, u'map': [{u'y': u'102436', u'x': u'100000', u'nodeId': u'101', u'nodeName': u'TO LT15', u'linkTo': u'102'}, {u'y': u'102436', u'x': u'102152', u'nodeId': u'102', u'nodeName': u'P2', u'linkTo': u'101, 103, 104'}, {u'y': u'100731', u'x': u'102152', u'nodeId': u'103', u'nodeName': u'Linkway', u'linkTo': u'102'}, {u'y': u'102436', u'x': u'102883', u'nodeId': u'104', u'nodeName': u'P4', u'linkTo': u'102, 105, 106, 107'}, {u'y': u'101787', u'x': u'102883', u'nodeId': u'105', u'nodeName': u'P5', u'linkTo': u'104, 108'}, {u'y': u'102924', u'x': u'102883', u'nodeId': u'106', u'nodeName': u'Seminar Room 6', u'linkTo': u'104'}, {u'y': u'102436', u'x': u'103776', u'nodeId': u'107', u'nodeName': u'Lobby ', u'linkTo': u'104, 110'}, {u'y': u'101787', u'x': u'103330', u'nodeId': u'108', u'nodeName': u'P8', u'linkTo': u'105, 109, 110'}, {u'y': u'100934', u'x': u'103330', u'nodeId': u'109', u'nodeName': u'Seminar Room 2', u'linkTo': u'108'}, {u'y': u'101787', u'x': u'103776', u'nodeId': u'110', u'nodeName': u'P10', u'linkTo': u'107, 108, 111'}, {u'y': u'101787', u'x': u'105603', u'nodeId': u'111', u'nodeName': u'Student Area', u'linkTo': u'110, 112, 113, 114'}, {u'y': u'102924', u'x': u'105603', u'nodeId': u'112', u'nodeName': u'Seminar Room 1', u'linkTo': u'111'}, {u'y': u'100609', u'x': u'105603', u'nodeId': u'113', u'nodeName': u'P13', u'linkTo': u'111, 136'}, {u'y': u'101787', u'x': u'107065', u'nodeId': u'114', u'nodeName': u'P14', u'linkTo': u'111, 115, 137'}, {u'y': u'102802', u'x': u'107065', u'nodeId': u'115', u'nodeName': u'P15', u'linkTo': u'114, 132'}, {u'y': u'100731', u'x': u'107065', u'nodeId': u'116', u'nodeName': u'P16', u'linkTo': u'118, 137'}, {u'y': u'102802', u'x': u'109014', u'nodeId': u'117', u'nodeName': u'P17', u'linkTo': u'139, 119, 121'}, {u'y': u'100731', u'x': u'108283', u'nodeId': u'118', u'nodeName': u'P18', u'linkTo': u'116, 120, 122'}, {u'y': u'102193', u'x': u'109014', u'nodeId': u'119', u'nodeName': u'Executive Classroom', u'linkTo': u'117'}, {u'y': u'101056', u'x': u'108283', u'nodeId': u'120', u'nodeName': u'Tutorial Room 11', u'linkTo': u'118'}, {u'y': u'102802', u'x': u'109460', u'nodeId': u'121', u'nodeName': u'P21', u'linkTo': u'117, 123, 124'}, {u'y': u'100731', u'x': u'109744', u'nodeId': u'122', u'nodeName': u'P22', u'linkTo': u'118, 125, 134'}, {u'y': u'103248', u'x': u'109460', u'nodeId': u'123', u'nodeName': u'Seminar Room 9', u'linkTo': u'121'}, {u'y': u'102802', u'x': u'111003', u'nodeId': u'124', u'nodeName': u'P24', u'linkTo': u'121, 127, 128'}, {u'y': u'101056', u'x': u'109744', u'nodeId': u'125', u'nodeName': u"NUS Hacker's Room", u'linkTo': u'122'}, {u'y': u'100691', u'x': u'111003', u'nodeId': u'126', u'nodeName': u'P26', u'linkTo': u'134, 128, 129'}, {u'y': u'103248', u'x': u'111003', u'nodeId': u'127', u'nodeName': u'Seminar Room 11', u'linkTo': u'124'}, {u'y': u'101259', u'x': u'111003', u'nodeId': u'128', u'nodeName': u'P28', u'linkTo': u'124, 126, 130'}, {u'y': u'100691', u'x': u'111571', u'nodeId': u'129', u'nodeName': u'P29', u'linkTo': u'126, 131'}, {u'y': u'100731', u'x': u'112180', u'nodeId': u'130', u'nodeName': u'TO Canteen', u'linkTo': u'128'}, {u'y': u'100406', u'x': u'111815', u'nodeId': u'131', u'nodeName': u'TO 2-2-1', u'linkTo': u'129, 201'}, {u'y': u'102802', u'x': u'107552', u'nodeId': u'132', u'nodeName': u'P32', u'linkTo': u'115, 133, 139'}, {u'y': u'103086', u'x': u'107552', u'nodeId': u'133', u'nodeName': u'Seminar Room 7', u'linkTo': u'132'}, {u'y': u'100731', u'x': u'110272', u'nodeId': u'134', u'nodeName': u'P34', u'linkTo': u'122, 126, 135'}, {u'y': u'100447', u'x': u'110272', u'nodeId': u'135', u'nodeName': u'Tutorial Room 5', u'linkTo': u'134'}, {u'y': u'100609', u'x': u'104263', u'nodeId': u'136', u'nodeName': u'Cerebro', u'linkTo': u'113'}, {u'y': u'101543', u'x': u'107065', u'nodeId': u'137', u'nodeName': u'P37', u'linkTo': u'114, 116, 138'}, {u'y': u'101543', u'x': u'107552', u'nodeId': u'138', u'nodeName': u'SR3 Front', u'linkTo': u'137'}, {u'y': u'102802', u'x': u'108811', u'nodeId': u'139', u'nodeName': u'P39', u'linkTo': u'117, 132, 140'}, {u'y': u'102436', u'x': u'108811', u'nodeId': u'140', u'nodeName': u'SR3 Back', u'linkTo': u'139'}]})
		# COM2L2
		# request_info = json.dumps({u'info': {u'northAt': u'305'}, u'map': [{u'y': u'204024', u'x': u'200061', u'nodeId': u'201', u'nodeName': u'TO 1-2-31', u'linkTo': u'217'}, {u'y': u'202561', u'x': u'201585', u'nodeId': u'202', u'nodeName': u'P2', u'linkTo': u'203, 205, 217'}, {u'y': u'202378', u'x': u'201342', u'nodeId': u'203', u'nodeName': u"Uncle Soo's Office", u'linkTo': u'202'}, {u'y': u'202317', u'x': u'202134', u'nodeId': u'204', u'nodeName': u"Colin's Office", u'linkTo': u'205'}, {u'y': u'202195', u'x': u'201951', u'nodeId': u'205', u'nodeName': u'P5', u'linkTo': u'202, 204, 219'}, {u'y': u'201098', u'x': u'202988', u'nodeId': u'206', u'nodeName': u'P6', u'linkTo': u'207, 211, 219'}, {u'y': u'200732', u'x': u'203353', u'nodeId': u'207', u'nodeName': u'P7', u'linkTo': u'206, 208'}, {u'y': u'200732', u'x': u'204085', u'nodeId': u'208', u'nodeName': u'P8', u'linkTo': u'207, 209, 210'}, {u'y': u'200976', u'x': u'204085', u'nodeId': u'209', u'nodeName': u'Discussion Room 6', u'linkTo': u'208'}, {u'y': u'200732', u'x': u'208047', u'nodeId': u'210', u'nodeName': u'End of Corridor', u'linkTo': u'208'}, {u'y': u'201646', u'x': u'203475', u'nodeId': u'211', u'nodeName': u'Glass Door', u'linkTo': u'206, 212'}, {u'y': u'201829', u'x': u'203780', u'nodeId': u'212', u'nodeName': u'Wooden Door', u'linkTo': u'211, 213'}, {u'y': u'202012', u'x': u'204146', u'nodeId': u'213', u'nodeName': u'Another Door', u'linkTo': u'212, 214'}, {u'y': u'202317', u'x': u'204329', u'nodeId': u'214', u'nodeName': u'Stairwell', u'linkTo': u'213, 215'}, {u'y': u'202744', u'x': u'203841', u'nodeId': u'215', u'nodeName': u'Halfway', u'linkTo': u'214, 216'}, {u'y': u'202622', u'x': u'203719', u'nodeId': u'216', u'nodeName': u'TO 2-3-11', u'linkTo': u'215, 311'}, {u'y': u'202927', u'x': u'201159', u'nodeId': u'217', u'nodeName': u'P17', u'linkTo': u'201, 202, 218'}, {u'y': u'202805', u'x': u'200915', u'nodeId': u'218', u'nodeName': u"Bimlesh's Office", u'linkTo': u'217'}, {u'y': u'201464', u'x': u'202622', u'nodeId': u'219', u'nodeName': u'P19', u'linkTo': u'205, 206, 220'}, {u'y': u'201342', u'x': u'202378', u'nodeId': u'220', u'nodeName': u"Damith's Office", u'linkTo': u'219'}]})
		# COM2L3
		# request_info = json.dumps({u'info': {u'northAt': u'305'}, u'map': [{u'y': u'304024', u'x': u'300061', u'nodeName': u'TO 1-3-18', u'nodeId': u'301', u'linkTo': u'316'}, {u'y': u'301098', u'x': u'302988', u'nodeName': u'P2', u'nodeId': u'302', u'linkTo': u'303, 307, 314'}, {u'y': u'300732', u'x': u'303353', u'nodeName': u'P3', u'nodeId': u'303', u'linkTo': u'302, 304'}, {u'y': u'300732', u'x': u'303902', u'nodeName': u'P4', u'nodeId': u'304', u'linkTo': u'303, 305, 312'}, {u'y': u'300976', u'x': u'303902', u'nodeName': u'Discussion Room 7', u'nodeId': u'305', u'linkTo': u'304'}, {u'y': u'300732', u'x': u'308047', u'nodeName': u'End of Corridor', u'nodeId': u'306', u'linkTo': u'312'}, {u'y': u'301646', u'x': u'303475', u'nodeName': u'Glass Door', u'nodeId': u'307', u'linkTo': u'302, 308'}, {u'y': u'301829', u'x': u'303780', u'nodeName': u'Wooden Door', u'nodeId': u'308', u'linkTo': u'307, 309'}, {u'y': u'302012', u'x': u'304146', u'nodeName': u'Another Door', u'nodeId': u'309', u'linkTo': u'308, 310'}, {u'y': u'302134', u'x': u'304207', u'nodeName': u'Stairwell', u'nodeId': u'310', u'linkTo': u'309, 311'}, {u'y': u'302622', u'x': u'303719', u'nodeName': u'TO 2-2-16', u'nodeId': u'311', u'linkTo': u'216, 310'}, {u'y': u'300732', u'x': u'304085', u'nodeName': u'P12', u'nodeId': u'312', u'linkTo': u'304, 306, 313'}, {u'y': u'300976', u'x': u'304085', u'nodeName': u'Discussion Room 8', u'nodeId': u'313', u'linkTo': u'312'}, {u'y': u'301951', u'x': u'302134', u'nodeName': u'P14', u'nodeId': u'314', u'linkTo': u'302, 315, 316'}, {u'y': u'302012', u'x': u'302317', u'nodeName': u"Henry's Room", u'nodeId': u'315', u'linkTo': u'314'}, {u'y': u'302500', u'x': u'301524', u'nodeName': u'Mysterious Pt', u'nodeId': u'316', u'linkTo': u'301, 314'}]})
		# Merged
		# request_info = json.dumps({u'info': {u'northAt': u'305'}, u'map': [{u'y': u'102436', u'x': u'100000', u'nodeId': u'101', u'nodeName': u'TO LT15', u'linkTo': u'102'}, {u'y': u'102436', u'x': u'102152', u'nodeId': u'102', u'nodeName': u'P2', u'linkTo': u'101, 103, 104'}, {u'y': u'100731', u'x': u'102152', u'nodeId': u'103', u'nodeName': u'Linkway', u'linkTo': u'102'}, {u'y': u'102436', u'x': u'102883', u'nodeId': u'104', u'nodeName': u'P4', u'linkTo': u'102, 105, 106, 107'}, {u'y': u'101787', u'x': u'102883', u'nodeId': u'105', u'nodeName': u'P5', u'linkTo': u'104, 108'}, {u'y': u'102924', u'x': u'102883', u'nodeId': u'106', u'nodeName': u'Seminar Room 6', u'linkTo': u'104'}, {u'y': u'102436', u'x': u'103776', u'nodeId': u'107', u'nodeName': u'Lobby ', u'linkTo': u'104'}, {u'y': u'101787', u'x': u'103330', u'nodeId': u'108', u'nodeName': u'P8', u'linkTo': u'105, 109, 110'}, {u'y': u'100934', u'x': u'103330', u'nodeId': u'109', u'nodeName': u'Seminar Room 2', u'linkTo': u'108'}, {u'y': u'101787', u'x': u'103776', u'nodeId': u'110', u'nodeName': u'P10', u'linkTo': u'107, 108, 111'}, {u'y': u'101787', u'x': u'105603', u'nodeId': u'111', u'nodeName': u'Student Area', u'linkTo': u'110, 112, 113, 114'}, {u'y': u'102924', u'x': u'105603', u'nodeId': u'112', u'nodeName': u'Seminar Room 1', u'linkTo': u'111'}, {u'y': u'100609', u'x': u'105603', u'nodeId': u'113', u'nodeName': u'P13', u'linkTo': u'111, 136'}, {u'y': u'101787', u'x': u'107065', u'nodeId': u'114', u'nodeName': u'P14', u'linkTo': u'111, 115, 137'}, {u'y': u'102802', u'x': u'107065', u'nodeId': u'115', u'nodeName': u'P15', u'linkTo': u'114, 132'}, {u'y': u'100731', u'x': u'107065', u'nodeId': u'116', u'nodeName': u'P16', u'linkTo': u'118, 137'}, {u'y': u'102802', u'x': u'109014', u'nodeId': u'117', u'nodeName': u'P17', u'linkTo': u'139, 119, 121'}, {u'y': u'100731', u'x': u'108283', u'nodeId': u'118', u'nodeName': u'P18', u'linkTo': u'116, 120, 122'}, {u'y': u'102193', u'x': u'109014', u'nodeId': u'119', u'nodeName': u'Executive Classroom', u'linkTo': u'117'}, {u'y': u'101056', u'x': u'108283', u'nodeId': u'120', u'nodeName': u'Tutorial Room 11', u'linkTo': u'118'}, {u'y': u'102802', u'x': u'109460', u'nodeId': u'121', u'nodeName': u'P21', u'linkTo': u'117, 123, 124'}, {u'y': u'100731', u'x': u'109744', u'nodeId': u'122', u'nodeName': u'P22', u'linkTo': u'118, 125, 134'}, {u'y': u'103248', u'x': u'109460', u'nodeId': u'123', u'nodeName': u'Seminar Room 9', u'linkTo': u'121'}, {u'y': u'102802', u'x': u'111003', u'nodeId': u'124', u'nodeName': u'P24', u'linkTo': u'121, 127, 128'}, {u'y': u'101056', u'x': u'109744', u'nodeId': u'125', u'nodeName': u"NUS Hacker's Room", u'linkTo': u'122'}, {u'y': u'100691', u'x': u'111003', u'nodeId': u'126', u'nodeName': u'P26', u'linkTo': u'134, 128, 129'}, {u'y': u'103248', u'x': u'111003', u'nodeId': u'127', u'nodeName': u'Seminar Room 11', u'linkTo': u'124'}, {u'y': u'101259', u'x': u'111003', u'nodeId': u'128', u'nodeName': u'P28', u'linkTo': u'124, 126, 130'}, {u'y': u'100691', u'x': u'111571', u'nodeId': u'129', u'nodeName': u'P29', u'linkTo': u'126, 131'}, {u'y': u'100731', u'x': u'112180', u'nodeId': u'130', u'nodeName': u'TO Canteen', u'linkTo': u'128'}, {u'y': u'100406', u'x': u'111815', u'nodeId': u'131', u'nodeName': u'TO 2-2-1', u'linkTo': u'129, 201'}, {u'y': u'102802', u'x': u'107552', u'nodeId': u'132', u'nodeName': u'P32', u'linkTo': u'115, 133, 139'}, {u'y': u'103086', u'x': u'107552', u'nodeId': u'133', u'nodeName': u'Seminar Room 7', u'linkTo': u'132'}, {u'y': u'100731', u'x': u'110272', u'nodeId': u'134', u'nodeName': u'P34', u'linkTo': u'122, 126, 135'}, {u'y': u'100447', u'x': u'110272', u'nodeId': u'135', u'nodeName': u'Tutorial Room 5', u'linkTo': u'134'}, {u'y': u'100609', u'x': u'104263', u'nodeId': u'136', u'nodeName': u'Cerebro', u'linkTo': u'113'}, {u'y': u'101543', u'x': u'107065', u'nodeId': u'137', u'nodeName': u'P37', u'linkTo': u'114, 116, 138'}, {u'y': u'101543', u'x': u'107552', u'nodeId': u'138', u'nodeName': u'SR3 Front', u'linkTo': u'137'}, {u'y': u'102802', u'x': u'108811', u'nodeId': u'139', u'nodeName': u'P39', u'linkTo': u'117, 132, 140'}, {u'y': u'102436', u'x': u'108811', u'nodeId': u'140', u'nodeName': u'SR3 Back', u'linkTo': u'139'}, {u'y': u'204024', u'x': u'200061', u'nodeId': u'201', u'nodeName': u'TO 1-2-31', u'linkTo': u'131, 217'}, {u'y': u'202561', u'x': u'201585', u'nodeId': u'202', u'nodeName': u'P2', u'linkTo': u'203, 205, 217'}, {u'y': u'202378', u'x': u'201342', u'nodeId': u'203', u'nodeName': u"Uncle Soo's Office", u'linkTo': u'202'}, {u'y': u'202317', u'x': u'202134', u'nodeId': u'204', u'nodeName': u"Colin's Office", u'linkTo': u'205'}, {u'y': u'202195', u'x': u'201951', u'nodeId': u'205', u'nodeName': u'P5', u'linkTo': u'202, 204, 219'}, {u'y': u'201098', u'x': u'202988', u'nodeId': u'206', u'nodeName': u'P6', u'linkTo': u'207, 211, 219'}, {u'y': u'200732', u'x': u'203353', u'nodeId': u'207', u'nodeName': u'P7', u'linkTo': u'206, 208'}, {u'y': u'200732', u'x': u'204085', u'nodeId': u'208', u'nodeName': u'P8', u'linkTo': u'207, 209, 210'}, {u'y': u'200976', u'x': u'204085', u'nodeId': u'209', u'nodeName': u'Discussion Room 6', u'linkTo': u'208'}, {u'y': u'200732', u'x': u'208047', u'nodeId': u'210', u'nodeName': u'End of Corridor', u'linkTo': u'208'}, {u'y': u'201646', u'x': u'203475', u'nodeId': u'211', u'nodeName': u'Glass Door', u'linkTo': u'206, 212'}, {u'y': u'201829', u'x': u'203780', u'nodeId': u'212', u'nodeName': u'Wooden Door', u'linkTo': u'211, 213'}, {u'y': u'202012', u'x': u'204146', u'nodeId': u'213', u'nodeName': u'Another Door', u'linkTo': u'212, 214'}, {u'y': u'202317', u'x': u'204329', u'nodeId': u'214', u'nodeName': u'Stairwell', u'linkTo': u'213, 215'}, {u'y': u'202744', u'x': u'203841', u'nodeId': u'215', u'nodeName': u'Halfway', u'linkTo': u'214, 216'}, {u'y': u'202622', u'x': u'203719', u'nodeId': u'216', u'nodeName': u'TO 2-3-11', u'linkTo': u'215, 311'}, {u'y': u'202927', u'x': u'201159', u'nodeId': u'217', u'nodeName': u'P17', u'linkTo': u'201, 202, 218'}, {u'y': u'202805', u'x': u'200915', u'nodeId': u'218', u'nodeName': u"Bimlesh's Office", u'linkTo': u'217'}, {u'y': u'201464', u'x': u'202622', u'nodeId': u'219', u'nodeName': u'P19', u'linkTo': u'205, 206, 220'}, {u'y': u'201342', u'x': u'202378', u'nodeId': u'220', u'nodeName': u"Damith's Office", u'linkTo': u'219'}, {u'y': u'304024', u'x': u'300061', u'nodeName': u'TO 1-3-18', u'nodeId': u'301', u'linkTo': u'316'}, {u'y': u'301098', u'x': u'302988', u'nodeName': u'P2', u'nodeId': u'302', u'linkTo': u'303, 307, 314'}, {u'y': u'300732', u'x': u'303353', u'nodeName': u'P3', u'nodeId': u'303', u'linkTo': u'302, 304'}, {u'y': u'300732', u'x': u'303902', u'nodeName': u'P4', u'nodeId': u'304', u'linkTo': u'303, 305, 312'}, {u'y': u'300976', u'x': u'303902', u'nodeName': u'Discussion Room 7', u'nodeId': u'305', u'linkTo': u'304'}, {u'y': u'300732', u'x': u'308047', u'nodeName': u'End of Corridor', u'nodeId': u'306', u'linkTo': u'312'}, {u'y': u'301646', u'x': u'303475', u'nodeName': u'Glass Door', u'nodeId': u'307', u'linkTo': u'302, 308'}, {u'y': u'301829', u'x': u'303780', u'nodeName': u'Wooden Door', u'nodeId': u'308', u'linkTo': u'307, 309'}, {u'y': u'302012', u'x': u'304146', u'nodeName': u'Another Door', u'nodeId': u'309', u'linkTo': u'308, 310'}, {u'y': u'302134', u'x': u'304207', u'nodeName': u'Stairwell', u'nodeId': u'310', u'linkTo': u'309, 311'}, {u'y': u'302622', u'x': u'303719', u'nodeName': u'TO 2-2-16', u'nodeId': u'311', u'linkTo': u'216, 310'}, {u'y': u'300732', u'x': u'304085', u'nodeName': u'P12', u'nodeId': u'312', u'linkTo': u'304, 306, 313'}, {u'y': u'300976', u'x': u'304085', u'nodeName': u'Discussion Room 8', u'nodeId': u'313', u'linkTo': u'312'}, {u'y': u'301951', u'x': u'302134', u'nodeName': u'P14', u'nodeId': u'314', u'linkTo': u'302, 315, 316'}, {u'y': u'302012', u'x': u'302317', u'nodeName': u"Henry's Room", u'nodeId': u'315', u'linkTo': u'314'}, {u'y': u'302500', u'x': u'301524', u'nodeName': u'Mysterious Pt', u'nodeId': u'316', u'linkTo': u'301, 314'}]})

		request_info = json.dumps({"info": {"northAt": "305"}, "map": [{"y": "102436", "x": "100000", "nodeId": "101", "nodeName": "TO LT15", "linkTo": "102"}, {"y": "102436", "x": "102152", "nodeId": "102", "nodeName": "P2", "linkTo": "101, 103, 104"}, {"y": "100731", "x": "102152", "nodeId": "103", "nodeName": "Linkway", "linkTo": "102"}, {"y": "102436", "x": "102883", "nodeId": "104", "nodeName": "P4", "linkTo": "102, 105, 106, 107"}, {"y": "101787", "x": "102883", "nodeId": "105", "nodeName": "P5", "linkTo": "104, 108"}, {"y": "102924", "x": "102883", "nodeId": "106", "nodeName": "Seminar Room 6", "linkTo": "104"}, {"y": "102436", "x": "103776", "nodeId": "107", "nodeName": "Lobby ", "linkTo": "104"}, {"y": "101787", "x": "103330", "nodeId": "108", "nodeName": "P8", "linkTo": "105, 109, 110"}, {"y": "100934", "x": "103330", "nodeId": "109", "nodeName": "Seminar Room 2", "linkTo": "108"}, {"y": "101787", "x": "103776", "nodeId": "110", "nodeName": "P10", "linkTo": "108, 111"}, {"y": "101787", "x": "105603", "nodeId": "111", "nodeName": "Student Area", "linkTo": "110, 112, 113, 114"}, {"y": "102924", "x": "105603", "nodeId": "112", "nodeName": "Seminar Room 1", "linkTo": "111"}, {"y": "100609", "x": "105603", "nodeId": "113", "nodeName": "P13", "linkTo": "111, 136"}, {"y": "101787", "x": "107065", "nodeId": "114", "nodeName": "P14", "linkTo": "111, 115, 137"}, {"y": "102802", "x": "107065", "nodeId": "115", "nodeName": "P15", "linkTo": "114, 132"}, {"y": "100731", "x": "107065", "nodeId": "116", "nodeName": "P16", "linkTo": "118, 137"}, {"y": "102802", "x": "109014", "nodeId": "117", "nodeName": "P17", "linkTo": "139, 119, 121"}, {"y": "100731", "x": "108283", "nodeId": "118", "nodeName": "P18", "linkTo": "116, 120, 122"}, {"y": "102193", "x": "109014", "nodeId": "119", "nodeName": "Executive Classroom", "linkTo": "117"}, {"y": "101056", "x": "108283", "nodeId": "120", "nodeName": "Tutorial Room 11", "linkTo": "118"}, {"y": "102802", "x": "109460", "nodeId": "121", "nodeName": "P21", "linkTo": "117, 123, 124"}, {"y": "100731", "x": "109744", "nodeId": "122", "nodeName": "P22", "linkTo": "118, 125, 134"}, {"y": "103248", "x": "109460", "nodeId": "123", "nodeName": "Seminar Room 9", "linkTo": "121"}, {"y": "102802", "x": "111003", "nodeId": "124", "nodeName": "P24", "linkTo": "121, 127, 128"}, {"y": "101056", "x": "109744", "nodeId": "125", "nodeName": "NUS Hacker's Room", "linkTo": "122"}, {"y": "100691", "x": "111003", "nodeId": "126", "nodeName": "P26", "linkTo": "134, 128, 129"}, {"y": "103248", "x": "111003", "nodeId": "127", "nodeName": "Seminar Room 11", "linkTo": "124"}, {"y": "101259", "x": "111003", "nodeId": "128", "nodeName": "P28", "linkTo": "124, 126, 130"}, {"y": "100691", "x": "111571", "nodeId": "129", "nodeName": "P29", "linkTo": "126, 131"}, {"y": "100731", "x": "112180", "nodeId": "130", "nodeName": "TO Canteen", "linkTo": "128"}, {"y": "100406", "x": "111815", "nodeId": "131", "nodeName": "TO 2-2-1", "linkTo": "129, 201"}, {"y": "102802", "x": "107552", "nodeId": "132", "nodeName": "P32", "linkTo": "115, 133, 139"}, {"y": "103086", "x": "107552", "nodeId": "133", "nodeName": "Seminar Room 7", "linkTo": "132"}, {"y": "100731", "x": "110272", "nodeId": "134", "nodeName": "P34", "linkTo": "122, 126, 135"}, {"y": "100447", "x": "110272", "nodeId": "135", "nodeName": "Tutorial Room 5", "linkTo": "134"}, {"y": "100609", "x": "104263", "nodeId": "136", "nodeName": "Cerebro", "linkTo": "113"}, {"y": "101543", "x": "107065", "nodeId": "137", "nodeName": "P37", "linkTo": "114, 116, 138"}, {"y": "101543", "x": "107552", "nodeId": "138", "nodeName": "SR3 Front", "linkTo": "137"}, {"y": "102802", "x": "108811", "nodeId": "139", "nodeName": "P39", "linkTo": "117, 132, 140"}, {"y": "102436", "x": "108811", "nodeId": "140", "nodeName": "SR3 Back", "linkTo": "139"}, {"y": "204024", "x": "200061", "nodeId": "201", "nodeName": "TO 1-2-31", "linkTo": "131, 217"}, {"y": "202561", "x": "201585", "nodeId": "202", "nodeName": "P2", "linkTo": "203, 205, 217"}, {"y": "202378", "x": "201342", "nodeId": "203", "nodeName": "Uncle Soo's Office", "linkTo": "202"}, {"y": "202317", "x": "202134", "nodeId": "204", "nodeName": "Colin's Office", "linkTo": "205"}, {"y": "202195", "x": "201951", "nodeId": "205", "nodeName": "P5", "linkTo": "202, 204, 219"}, {"y": "201098", "x": "202988", "nodeId": "206", "nodeName": "P6", "linkTo": "207, 211, 219"}, {"y": "200732", "x": "203353", "nodeId": "207", "nodeName": "P7", "linkTo": "206, 208"}, {"y": "200732", "x": "204085", "nodeId": "208", "nodeName": "P8", "linkTo": "207, 209, 210"}, {"y": "200976", "x": "204085", "nodeId": "209", "nodeName": "Discussion Room 6", "linkTo": "208"}, {"y": "200732", "x": "208047", "nodeId": "210", "nodeName": "End of Corridor", "linkTo": "208"}, {"y": "201646", "x": "203475", "nodeId": "211", "nodeName": "Glass Door", "linkTo": "206, 212"}, {"y": "201829", "x": "203780", "nodeId": "212", "nodeName": "Wooden Door", "linkTo": "211, 213"}, {"y": "202012", "x": "204146", "nodeId": "213", "nodeName": "Another Door", "linkTo": "212, 214"}, {"y": "202317", "x": "204329", "nodeId": "214", "nodeName": "Stairwell", "linkTo": "213, 215"}, {"y": "202744", "x": "203841", "nodeId": "215", "nodeName": "Halfway", "linkTo": "214, 216"}, {"y": "202622", "x": "203719", "nodeId": "216", "nodeName": "TO 2-3-11", "linkTo": "215, 311"}, {"y": "202927", "x": "201159", "nodeId": "217", "nodeName": "P17", "linkTo": "201, 202, 218"}, {"y": "202805", "x": "200915", "nodeId": "218", "nodeName": "Bimlesh's Office", "linkTo": "217"}, {"y": "201464", "x": "202622", "nodeId": "219", "nodeName": "P19", "linkTo": "205, 206, 220"}, {"y": "201342", "x": "202378", "nodeId": "220", "nodeName": "Damith's Office", "linkTo": "219"}, {"y": "304024", "x": "300061", "nodeName": "TO 1-3-18", "nodeId": "301", "linkTo": "316"}, {"y": "301098", "x": "302988", "nodeName": "P2", "nodeId": "302", "linkTo": "303, 307, 314"}, {"y": "300732", "x": "303353", "nodeName": "P3", "nodeId": "303", "linkTo": "302, 304"}, {"y": "300732", "x": "303902", "nodeName": "P4", "nodeId": "304", "linkTo": "303, 305, 312"}, {"y": "300976", "x": "303902", "nodeName": "Discussion Room 7", "nodeId": "305", "linkTo": "304"}, {"y": "300732", "x": "308047", "nodeName": "End of Corridor", "nodeId": "306", "linkTo": "312"}, {"y": "301646", "x": "303475", "nodeName": "Glass Door", "nodeId": "307", "linkTo": "302, 308"}, {"y": "301829", "x": "303780", "nodeName": "Wooden Door", "nodeId": "308", "linkTo": "307, 309"}, {"y": "302012", "x": "304146", "nodeName": "Another Door", "nodeId": "309", "linkTo": "308, 310"}, {"y": "302134", "x": "304207", "nodeName": "Stairwell", "nodeId": "310", "linkTo": "309, 311"}, {"y": "302622", "x": "303719", "nodeName": "TO 2-2-16", "nodeId": "311", "linkTo": "216, 310"}, {"y": "300732", "x": "304085", "nodeName": "P12", "nodeId": "312", "linkTo": "304, 306, 313"}, {"y": "300976", "x": "304085", "nodeName": "Discussion Room 8", "nodeId": "313", "linkTo": "312"}, {"y": "301951", "x": "302134", "nodeName": "P14", "nodeId": "314", "linkTo": "302, 315, 316"}, {"y": "302012", "x": "302317", "nodeName": "Henry's Room", "nodeId": "315", "linkTo": "314"}, {"y": "302500", "x": "301524", "nodeName": "Mysterious Pt", "nodeId": "316", "linkTo": "301, 314"}]})

		try:
			json_request_info = json.loads(request_info)
		except:
			print '[PATH FINDER] Error >> PathFinder::__update_node_info: JSON could not be decoded.'
			raise ValueError()

		if json_request_info['info'] is None:
			print '[PATH FINDER] Error >> PathFinder::__update_node_info: JSON is empty.'
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
			'y': int(node['y'])
			# 'wifi': []
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

		self.__adjacency_matrix = [[-1 for row in range(400)] for col in range(400)]

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
		visited = [False] * (400 + 1)
		# distance = [0 for i in range(self.__num_node + 1)]
		predecesor = [-1 for i in range(400)]

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
	def test_visit():
		print 'testing::test_visit(): started visit test'

		pf = PathFinder()

		source = 101
		target = 316

		pf.update_coordinate(0, 0, 0)
		pf.update_source_and_target(source, target)

		shortest_path = pf._PathFinder__shortest_path

		for i in range(source, target + 1):
			if (i <= 100) or (i >= 141 and i <= 200) or (i >= 221 and i <= 300) or (i >= 317):
				continue

			reached, node_reached = pf.update_coordinate(pf._PathFinder__node_info[i]['x'], pf._PathFinder__node_info[i]['y'], 0)
			if reached:
				if node_reached not in shortest_path:
					print 'Error'
					print 'source' + str(source)
					print 'target' + str(target)
					print 'node reached: ' + str(node_reached)
					print 'shortest path: ' + str(shortest_path)

		print 'testing::test_visit(): completed visit test'

	def test_angle():
		print 'testing::test_angle(): started angle test'

		pf = PathFinder()

		source = 101
		target = 102

		pf.update_coordinate(0, 0, 0)
		pf.update_source_and_target(source, target)
		sign_x = [0, 1, 1, 1, 0, -1, -1, -1]
		sign_y = [1, 1, 0, -1, -1, -1, 0, 1]

		for i in range(0, 8):
			x_coordinate = pf._PathFinder__node_info[source]['x'] + (500 * sign_x[i])
			y_coordinate = pf._PathFinder__node_info[source]['y'] + (500 * sign_y[i])
			angle_of_user_from_north = 0
			expected_angle = pf._PathFinder__convert_angle_to_convention((360 - pf._PathFinder__angle_of_north) + 180 + (i * 45))

			for j in range(0, 8):
				pf.update_coordinate(x_coordinate, y_coordinate, angle_of_user_from_north + (j * 45))

				if pf._PathFinder__instruction[0]['angle'] != pf._PathFinder__convert_angle_to_convention(expected_angle - (j * 45)):
					print 'Error'
					print 'user x: ' + str(x_coordinate)
					print 'user y: ' + str(y_coordinate)
					print 'user angle from north: ' + str(pf._PathFinder__convert_angle_to_convention(angle_of_user_from_north))
					print 'next x: ' + str(pf._PathFinder__node_info[source]['x'])
					print 'next y: ' + str(pf._PathFinder__node_info[source]['y'])
					print 'next angle: ' + str(pf._PathFinder__instruction[0]['angle'])
					print 'expected angle: ' + str(pf._PathFinder__convert_angle_to_convention(expected_angle))

		print 'testing::test_angle(): completed angle test'

	def test_instruction():
		print 'testing::test_instruction(): started instruction test'

		pf = PathFinder()

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

	def test_update():
		print 'testing::test_update(): started update test'

		pf = PathFinder()

		source = 101
		target = 101

		pf.update_coordinate(pf._PathFinder__node_info[101]['x'], pf._PathFinder__node_info[101]['y'], 0)
		pf.update_source_and_target(source, target)

		pf.update_coordinate(pf._PathFinder__node_info[101]['x'], pf._PathFinder__node_info[101]['y'], 0)

		instruction = pf._PathFinder__instruction

		if len(instruction) != 0:
			print 'Error'
			print 'instruction'

		print 'testing::test_update(): completed update test'
	
	""" uncomment any of these tests to run tests """

	test_visit()
	test_angle()
	test_instruction()
	test_update()
