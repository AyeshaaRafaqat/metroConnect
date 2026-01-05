from ds.graph import Graph
from ds.core import MinHeap, Queue

def dijkstra(graph: Graph, start_id: int, end_id: int, criteria="time") -> dict:
    """Min Time/Cost. Returns {'path': [ids], 'cost': float, 'type': str}"""
    distances = {node: float('inf') for node in graph.adj}
    previous = {}
    distances[start_id] = 0
    
    pq = MinHeap()
    pq.push(0, start_id)
    
    while pq.heap:
        pop_res = pq.pop()
        if pop_res is None:
            break
        current_dist, u = pop_res
        
        if u == end_id:
            break
        if current_dist > distances[u]:
            continue
            
        for v, time_min, dist_km, edge_type in graph.get_neighbors(u):
            # Weight is either time or distance
            weight = time_min if criteria == "time" else dist_km
            new_dist = distances[u] + weight
            
            if new_dist < distances[v]:
                distances[v] = new_dist
                previous[v] = u
                pq.push(new_dist, v)
    
    # Reconstruct path
    if end_id not in previous and start_id != end_id:
        return {"path": [], "cost": float('inf'), "error": "No path found"}
    
    path = []
    current = end_id
    while current != start_id:
        path.append(current)
        if current not in previous:
            break
        current = previous[current]
    path.append(start_id)
    path.reverse()
    
    total_cost = distances[end_id]
    return {
        "path": path,
        "cost": total_cost,
        "type": criteria
    }

def bfs_min_transfers(graph: Graph, start_id: int, end_id: int) -> dict:
    """Minimum transfers using BFS"""
    if start_id not in graph.adj or end_id not in graph.adj:
        return {"path": [], "transfers": float('inf')}
    
    transfers = {node: float('inf') for node in graph.adj}
    previous = {}
    transfers[start_id] = 0
    
    queue = Queue()
    queue.enqueue(start_id)
    
    while queue.items:
        u = queue.dequeue()
        if u == end_id:
            break
            
        for v, _, _, edge_type in graph.get_neighbors(u):
            if transfers[v] == float('inf'):
                transfers[v] = transfers[u] + (1 if edge_type != "walk" else 0)
                previous[v] = u
                queue.enqueue(v)
    
    # Reconstruct path
    path = []
    current = end_id
    while current is not None:
        path.append(current)
        current = previous.get(current)
        if current == start_id:
            path.append(start_id)
            break
    else:
        # Check if start and end are the same
        if start_id == end_id:
            return {"path": [start_id], "transfers": 0}
        return {"path": [], "transfers": float('inf')}
    
    path.reverse()
    return {
        "path": path,
        "transfers": transfers[end_id]
    }

import math

def get_distance(lat1, lng1, lat2, lng2):
    """
    Logic: Euclidean distance scaled to KM.
    1 Degree Lat/Lon is approx 111KM in regional context.
    Provides accurate weights for Dijkstra and Nearest Neighbor.
    """
    deg_dist = math.sqrt((lat1 - lat2)**2 + (lng1 - lng2)**2)
    return deg_dist * 111.0 # Convert to approx KM

def find_nearest_station(user_lat, user_lng, graph):
    """Snaps a coordinate to the closest graph node (Station)"""
    res = find_k_nearest_stations(user_lat, user_lng, graph, k=1)
    return res[0][0], res[0][1] if res else (None, None)

def find_k_nearest_stations(user_lat, user_lng, graph, k=3):
    """
    Logic: K-Nearest Neighbor Search (Minimization)
    Optimizes connectivity by providing multiple entry points to the network.
    """
    distances = []
    
    # Iterate through HashTable buckets
    for bucket in graph.stops.table:
        for name, details in bucket:
            dist = get_distance(user_lat, user_lng, details['lat'], details['lng'])
            distances.append((details['id'], name, dist))
            
    # Sort by distance and take Top K
    distances.sort(key=lambda x: x[2])
    return distances[:k]

def calculate_walking_time(dist_km):
    """
    Assumes average walking speed of 5 km/h.
    Time (min) = (Distance / 5) * 60
    """
    return (dist_km / 5.0) * 60.0 # Returns minutes

def bfs_get_alternatives(graph, start_node_id, max_hops=2):
    """
    Week 13 Concept: Level-Order discovery using BFS.
    Finds alternative stations within 'N' connections.
    """
    visited = {start_node_id}
    queue = Queue()
    queue.enqueue((start_node_id, 0))
    alternatives = []
    
    while queue.items:
        u, depth = queue.dequeue()
        if depth > 0: # Don't include the start node itself
            alternatives.append(u)
        
        if depth < max_hops:
            for v, _, _, _ in graph.get_neighbors(u):
                # Ensure neighbor ID exists in graph
                if v not in visited:
                    visited.add(v)
                    queue.enqueue((v, depth + 1))
    return alternatives
