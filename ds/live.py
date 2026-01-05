import random
from datetime import datetime, timedelta
from ds.core import AVLTree, MinHeap, Stack, Queue, LinkedList

class LiveUpdates:
    def __init__(self):
        self.avl_store = AVLTree()
        self.avl_root = None
        self.alert_history = Stack()
        self.upcoming_queue = Queue()
        self.priority_alerts = MinHeap()
        
        # Pre-generate some logical fake data
        self._seed_mock_data()

    def _seed_mock_data(self):
        """Simulates a real-time system state using DSA"""
        messages = [
            (1, "Slight signal delay (Standard)"),
            (0, "CRITICAL: Power outage reported"),
            (2, "High passenger volume (Expect delays)"),
            (1, "Cleaning in progress"),
            (1, "Escalator maintenance")
        ]
        
        # Seed various stations with random states (IDs 1-120)
        for _ in range(30):
            s_id = random.randint(1, 120)
            priority, msg = random.choice(messages)
            
            # Store in AVL Tree for indexed lookup
            self.avl_root = self.avl_store.insert(self.avl_root, s_id, {"msg": msg, "lvl": priority})
            
            # If critical, add to Priority Queue
            if priority == 0:
                self.priority_alerts.push(0, f"Node {s_id}: {msg}")

    def get_path_alerts(self, path, id_map):
        """
         Complex alert filtering.
        1. Uses Priority Queue (Min-Heap) for system-wide CRITICAL alerts.
        2. Uses AVL Tree (Balanced BST) for O(log N) per-node path filtering.
        3. Uses Stack for history tracking.
        """
        journey_alerts = []
        
        # 1. Global Priority Alerts (System Wide)
        while self.priority_alerts.heap:
            prio, msg = self.priority_alerts.pop()
            journey_alerts.append(f"🚩 GLOBAL: {msg}")
            self.alert_history.push(msg) # Track in Stack

        if not path:
            return journey_alerts + ["🔎 Enter a route to see relevant service alerts."]

        # 2. Path-Specific Alerts (AVL Search)
        for stop_id in path:
            node = self.avl_store.search(self.avl_root, stop_id)
            if node:
                s_name = id_map.get(stop_id, (f"Node {stop_id}",))[0]
                lvl_icon = "🛑" if node.value["lvl"] == 0 else "⚠️" 
                alert_text = f"{lvl_icon} {s_name}: {node.value['msg']}"
                journey_alerts.append(alert_text)
                self.alert_history.push(alert_text) # Track in Stack
                
        if len(journey_alerts) == 0:
            return ["✅ All stations in your journey are reporting normal operations."]
            
        return journey_alerts

    def get_eta(self, stop_id, line_type):
        base_time = datetime.now() + timedelta(minutes=5)
        delay = random.randint(0, 3)
        eta_time = base_time + timedelta(minutes=delay)
        return eta_time.strftime("%H:%M")
