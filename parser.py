import json
import requests
import re
import math

def get_node_info():
	MAP_URL = 'http://showmyway.comp.nus.edu.sg/getMapInfo.php?Building=DemoBuilding&Level=1'
	SPLIT_RE = re.compile('\s*, \s*')

	map_info = requests.get(MAP_URL)

	json_map_info = json.loads(map_info.text)

	node_info = {}

	for node in json_map_info['map']:
		node_info[int(node['nodeId']) - 1] = {
			'neighbour' : [(int(node_index) - 1) for node_index in SPLIT_RE.split(str(node['linkTo']))],
			'x': int(node['x']),
			'y': int(node['y']),
			'name': node['nodeName']
		}

	return node_info

def get_adjacency_list(node_info):
	num_node = len(node_info)

	adjacency_matrix = [[-1 for row in range(num_node)] for col in range(num_node)]

	for index, node in node_info.iteritems():
		current_index = index
		current_x = node['x']
		current_y = node['y']

		for neighbour_index in node['neighbour']:
			neighbour_x = node_info[neighbour_index]['x']
			neighbour_y = node_info[neighbour_index]['y']

			delta_x = current_x - neighbour_x 
			delta_y = current_y - neighbour_y

			weight = int(math.sqrt(delta_x * delta_x + delta_y * delta_y))

			adjacency_matrix[current_index][neighbour_index] = weight
			adjacency_matrix[neighbour_index][current_index] = weight

	return adjacency_matrix