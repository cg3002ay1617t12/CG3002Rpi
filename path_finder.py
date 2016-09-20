from parser import get_node_info, get_adjacency_list
import heapq, math

class PathFinder(object):
  def __init__(self):
    self.node_info = get_node_info()
    self.map = get_adjacency_list(self.node_info)

  def get_shortest_path(self, start_index, end_index, adjacency_matrix=None):
    if adjacency_matrix is None:
      adjacency_matrix = self.map

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
  
  def get_detailed_path(self, start, end, path, distance, node_info=None):
    if node_info is None:
      node_info = self.node_info
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

  def get_edge_info(self, first_index, second_index, node_info=None):
    if node_info is None:
      node_info = self.node_info

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

def test():
  PathFinder = PathFinder()
  print str(PathFinder.node_info) + "\n"
  print str(PathFinder.map) + "\n"

  start = 1
  end = 9

  shortest_path, distance = PathFinder.get_shortest_path(start, end)
  print str(shortest_path) + "\n"
  print str(distance) + "\n"

  detailed_path = PathFinder.get_detailed_path(start, end, shortest_path, distance)
  print str(detailed_path) + "\n"
  
if __name__ == "__main__":
  test()