import heapq

def get_shortest_path(adjacency_matrix, start_index, end_index):
	start_index -= 1
	end_index -= 1

	if start_index < 0 or end_index < 0 or start_index >= len(adjacency_matrix) or end_index >= len(adjacency_matrix):
		return [-1], [-1]

	priority_queue = []
	visited = [False] * len(adjacency_matrix)
	distance = [0 for i in range(len(adjacency_matrix))]
	predecesor = [-1 for i in range(len(adjacency_matrix))]

	init_index = start_index
	init_weight = 0
	init_predecesor = -1
	init_tuple = (init_weight, init_index, init_predecesor)

	heapq.heappush(priority_queue, init_tuple)

	while priority_queue:
		pop_tuple = heapq.heappop(priority_queue)
		pop_index = pop_tuple[0]
		pop_weight = pop_tuple[1]
		pop_predecesor = pop_tuple[2]

		if not visited[pop_index]:
			visited[pop_index] = True
			distance[pop_index] = pop_weight
			predecesor[pop_index] = pop_predecesor

			# Since execution speed is not in question, don't have ot include
			# if pop_index == end_index:
			#   break

			for neighbour_index, neighbour_weight in enumerate(adjacency_matrix[pop_index]):
				if neighbour_weight != -1 and not visited[neighbour_index]:
					push_index = neighbour_index
					push_weight = pop_weight + neighbour_weight
					push_predecesor = pop_index
					push_tuple = (push_index, push_weight, push_predecesor)

					heapq.heappush(priority_queue, push_tuple)

	shortest_path = []

	while 1:
		shortest_path.append(end_index + 1)
		if end_index == start_index:
			break
		end_index = predecesor[end_index]

	shortest_path.reverse()

	return shortest_path, distance
