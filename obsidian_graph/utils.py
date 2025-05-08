from collections import deque


def bfs_upto_levels(graph, start_node, max_levels):
    ## BFS search for context
    visited = set()
    queue = deque([(start_node, 0)])  # (node, current_level)
    result = []

    while queue:
        node, level = queue.popleft()
        if level > max_levels:
            break

        if node not in visited:
            visited.add(node)
            result.append((node, level))

            for neighbor in graph.neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, level + 1))

    return result
