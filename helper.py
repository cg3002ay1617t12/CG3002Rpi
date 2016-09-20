import math

def get_detailed_path(start, end, path, distance, node_info):
	if path == [-1] or distance == [-1]:
		return "Path does not exist"

	for i, value in enumerate(path):
		path[i] -= 1

	detailed_path = ""

	detailed_path += "Total distance: " + str(distance[end - 1]) + "\n"

	for i, node in enumerate(path):
		if i == len(path) - 1:
			detailed_path += "<" + str(node + 1) + ":" + str(node_info[node]['name']) + ">"
		else:
			weight, angle = get_edge_info(path[i], path[i + 1], node_info)
			detailed_path += "<" + str(node + 1) + ":" + str(node_info[node]['name']) + "> --(" + str(weight) + ")--(" + str(angle) + ")--" + "> "

	return detailed_path

def get_edge_info(first_index, second_index, node_info):
	first_x = node_info[first_index]['x']
	first_y = node_info[first_index]['y']

	second_x = node_info[second_index]['x']
	second_y = node_info[second_index]['y']

	delta_x = first_x - second_x
	delta_y = first_y - second_y

	weight = int(math.sqrt(delta_x * delta_x + delta_y * delta_y))

	angle = math.degrees(math.atan2(delta_y, delta_x))

	angle = 360 - angle # Make clock wise

	angle += 90 # Calibrate angle

	if angle > 360: # Make sure all angle below 360
		angle -= 360

	return weight, angle
