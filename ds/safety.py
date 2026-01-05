from ds.core import Queue, GeneralTree

class SafetyManager:
    def __init__(self):
        # DSA: General Tree to represent security hierarchy
        self.hierarchy = GeneralTree("City Safety Command")
        police = self.hierarchy.add_child(self.hierarchy.root, "Punjab Police")
        self.hierarchy.add_child(police, "Model Town Sector")
        self.hierarchy.add_child(police, "Gulberg Sector")
        self.hierarchy.add_child(police, "Johar Town Sector")
        
        rescue = self.hierarchy.add_child(self.hierarchy.root, "Rescue 1122")
        self.hierarchy.add_child(rescue, "Central Response Unit")
        
        # Safe Points: {node_id: name}
        self.safe_points = {
            1: "Civil Secretariat Security",
            15: "Kalma Chowk Police Post",
            28: "Ali Town Checkpoint",
            44: "Railway Station Police",
            116: "Gulberg Security Hub"
        }

    def find_nearest_safe_point(self, current_node_id, graph):
        """
        DSA: Breadth-First Search (BFS)
        Finds the shortest number of hops to a safety point.
        """
        if current_node_id in self.safe_points:
            return current_node_id, 0
            
        visited = {current_node_id}
        queue = Queue()
        queue.enqueue((current_node_id, 0))
        
        while queue.items:
            u, dist = queue.dequeue()
            
            for v, _, _, _ in graph.get_neighbors(u):
                if v not in visited:
                    if v in self.safe_points:
                        return v, dist + 1
                    visited.add(v)
                    queue.enqueue((v, dist + 1))
        return None, float('inf')

    def get_security_hierarchy(self):
        """Returns the hierarchy as a formatted string for the UI"""
        res = []
        def traverse(node, level):
            res.append("  " * level + "• " + node.data)
            for child in node.children:
                traverse(child, level + 1)
        traverse(self.hierarchy.root, 0)
        return "\n".join(res)

    def get_safety_brief(self):
        """Returns a high-level summary of city safety from the hierarchy tree."""
        root = self.hierarchy.root
        units = len(root.children)
        total_sectors = sum(len(child.children) for child in root.children)
        return f"🔒 STATUS: {units} major command units (Police & Rescue) are overseeing {total_sectors} active city sectors."
