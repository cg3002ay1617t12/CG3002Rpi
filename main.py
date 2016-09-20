from parser import get_node_info, get_adjacency_list
from path_finder import get_shortest_path
from helper import get_detailed_path

node_info = get_node_info()

print str(node_info) + "\n"

adjacency_matrix = get_adjacency_list(node_info)

print str(adjacency_matrix) + "\n"

start = 1
end = 9

shortest_path, distance = get_shortest_path(adjacency_matrix, start, end)

print str(shortest_path) + "\n"
print str(distance) + "\n"

detailed_path = get_detailed_path(start, end, shortest_path, distance, node_info)

print str(detailed_path) + "\n"