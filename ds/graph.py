from ds.core import HashTable, Queue

class Graph:
    def __init__(self):
        self.adj = {}  # {node_id: [(neighbor_id, time_min, dist_km, type), ...]}
        self.stops = HashTable()  # name → {"id": int, "type": str, "lat": float, "lng": float}
        self.id_to_name = {} # {id: name}
    
    def add_stop(self, stop_id, name, stop_type, lat, lng):
        self.stops.insert(name, {"id": stop_id, "type": stop_type, "lat": lat, "lng": lng})
        self.id_to_name[stop_id] = name
        if stop_id not in self.adj:
            self.adj[stop_id] = []
    
    def add_edge(self, from_id, to_id, time_min, dist_km, edge_type):
        self.adj[from_id].append((to_id, time_min, dist_km, edge_type))
        self.adj[to_id].append((from_id, time_min, dist_km, edge_type))  # Bidirectional
    
    def get_neighbors(self, node_id):
        return self.adj.get(node_id, [])
    
    def validate(self):
        # DFS check connectivity
        if not self.adj:
            return True
        visited = set()
        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for neighbor, _, _, _ in self.get_neighbors(node):
                dfs(neighbor)
        
        # Start DFS from the first available node
        start_node = next(iter(self.adj))
        dfs(start_node)
        return len(visited) == len(self.adj)

class SessionGraph(Graph):
    """
    Logic: Demonstrates 'Copy-on-Write' and 'Graph Augmentation'.
    This graph exists only in memory for a single calculation.
    """
    def __init__(self, base_graph):
        super().__init__()
        # Shallow copy the adj dictionary, but we will treat lists as immutable
        # If we add a neighbor to a base node, we must replace its list in self.adj
        self.adj = base_graph.adj.copy()
        
        # Share the ID map for existing nodes
        self.id_to_name = base_graph.id_to_name.copy()
        
        # Clone stops HashTable to allow temporary lookups
        # HashTable doesn't have a clone, so we manually re-insert
        self.stops = HashTable(size=base_graph.stops.size)
        for bucket in base_graph.stops.table:
            for name, data in bucket:
                self.stops.insert(name, data)

    def add_temp_edge(self, u, v, time, dist, edge_type):
        """Augments the graph with a temporary edge"""
        # Ensure u exists in our local adj
        if u not in self.adj:
            self.adj[u] = []
        else:
            # Clone the neighbor list for u to stay safe (Copy-on-Write)
            # Only if it hasn't been cloned yet in this session
            # We can check if it's the same object as base but that's complex
            # For simplicity in this demo, we just create a new list
            self.adj[u] = list(self.adj[u])
            
        self.adj[u].append((v, time, dist, edge_type))

        # Repeat for v (bidirectional)
        if v not in self.adj:
            self.adj[v] = []
        else:
            self.adj[v] = list(self.adj[v])
        self.adj[v].append((u, time, dist, edge_type))
