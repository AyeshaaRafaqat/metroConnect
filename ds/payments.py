from ds.core import AVLTree, MinHeap, Stack, Queue, LinkedList

class TCash:
    def __init__(self, balance=500.0):
        self.balance = balance
        self.history = LinkedList()  # Custom Linked List
    
    def calculate_fare(self, path, graph):
        """Path-Level Fare Calculation (Fixes per-edge overbilling)"""
        if not path or len(path) < 2: return 0, []
        
        # 1. Segment the path into continuous mode legs
        legs = []
        if len(path) > 1:
            current_leg = {"type": None, "nodes": [path[0]], "dist": 0}
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                # Find edge type and distance
                edge_type = "walk"
                dist = 0
                for neighbor_id, t, d, typ in graph.adj.get(u, []):
                    if neighbor_id == v:
                        edge_type = typ
                        dist = d
                        break
                
                if edge_type == current_leg["type"]:
                    current_leg["nodes"].append(v)
                    current_leg["dist"] += dist
                else:
                    if current_leg["type"] is not None:
                        legs.append(current_leg)
                    current_leg = {"type": edge_type, "nodes": [u, v], "dist": dist}
            legs.append(current_leg)

        # 2. Apply rules to each leg
        total_fare = 0
        breakdown = []
        feeder_count = 0
        
        for leg in legs:
            typ = leg["type"]
            d = leg["dist"]
            start_node = leg["nodes"][0]
            end_node = leg["nodes"][-1]
            leg_name = f"{graph.id_to_name.get(start_node)} to {graph.id_to_name.get(end_node)}"
            
            leg_cost = 0
            if typ == "orange":
                # Official Orange Line Slabs (Applied once per leg)
                if d <= 4: leg_cost = 25
                elif d <= 8: leg_cost = 30
                elif d <= 12: leg_cost = 35
                elif d <= 16: leg_cost = 40
                else: leg_cost = 45
            elif typ == "metro":
                leg_cost = 30 # Flat per entry
            elif typ == "speedo":
                feeder_count += 1
                if feeder_count == 1: leg_cost = 20
                elif feeder_count <= 3: leg_cost = 5
                else: 
                    leg_cost = 20
                    feeder_count = 1 # Reset cycle
            
            total_fare += leg_cost
            breakdown.append((f"{typ.upper()}: {leg_name}", leg_cost))
                
        return total_fare, breakdown
    
    def pay(self, amount, route_name):
        if self.balance < amount:
            return False, "Insufficient balance"
        self.balance -= amount
        self.history.append(f"[Deduction] PKR {amount} for commute: {route_name}")
        return True, f"Success. Balance: {self.balance:.1f}PKR"
