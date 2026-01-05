import json
import os
from datetime import datetime
from ds.core import Stack, HashTable, MaxHeap

class AnalyticsManager:
    def __init__(self, storage_file="data/journeys.json"):
        self.storage_file = storage_file
        self.user_journeys = {} # {username: Stack of journeys}
        self.undo_stack = Stack() # Global undo stack for current session actions
        self._ensure_storage()
        self._load_journeys()

    def _ensure_storage(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.storage_file) or os.path.getsize(self.storage_file) < 5:
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
            self._populate_dummy_journeys()

    def _populate_dummy_journeys(self):
        dummy = {
            "admin": [
                {"from": "Ali Town", "to": "Anarkali", "fare": 40, "timestamp": "2026-01-01 10:00:00"},
                {"from": "Ali Town", "to": "Anarkali", "fare": 40, "timestamp": "2026-01-02 11:30:00"},
                {"from": "Anarkali", "to": "Dera Gujran", "fare": 60, "timestamp": "2026-01-03 09:15:00"},
                {"from": "Shahdara", "to": "Gajjumata", "fare": 30, "timestamp": "2026-01-04 08:00:00"}
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(dummy, f, indent=2)

    def _load_journeys(self):
        with open(self.storage_file, 'r') as f:
            try:
                data = json.load(f)
            except:
                data = {}
            for username, journeys in data.items():
                s = Stack()
                # Journeys in JSON are [oldest...newest]
                for j in journeys:
                    s.push(j)
                self.user_journeys[username.lower()] = s

    def _save_journeys(self):
        data = {}
        for username, s in self.user_journeys.items():
            data[username] = s.items
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def log_journey(self, username, source, destination, fare):
        username = username.lower()
        if username not in self.user_journeys:
            self.user_journeys[username] = Stack()
        
        journey = {
            "from": source,
            "to": destination,
            "fare": fare,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.user_journeys[username].push(journey)
        self._save_journeys()

    def get_history(self, username):
        username = username.lower()
        if username not in self.user_journeys or not self.user_journeys[username].items:
            # First-time user: Give some dummy history for better UX
            self.log_journey(username, "Ali Town", "Anarkali", 40)
            self.log_journey(username, "Ali Town", "Anarkali", 40)
            self.log_journey(username, "Gajjumata", "Shahdara", 30)
            
        # Return as list, newest first
        return list(reversed(self.user_journeys[username].items))

    def get_top_routes(self, username, limit=5):
        username = username.lower()
        if username not in self.user_journeys:
            return []
        
        # 1. Use HashTable to count frequencies
        counts = HashTable(size=50)
        # Route key = "Source -> Destination"
        for j in self.user_journeys[username].items:
            route = f"{j['from']} ➔ {j['to']}"
            current_count = counts.lookup(route) or 0
            counts.insert(route, current_count + 1)
            
        # 2. Use MaxHeap to extract top N
        heap = MaxHeap()
        # Collect all unique routes from HashTable chaining table
        seen = set()
        for bucket in counts.table:
            for route, count in bucket:
                if route not in seen:
                    heap.push(count, route)
                    seen.add(route)
        
        top_routes = []
        for _ in range(limit):
            top = heap.pop()
            if top:
                top_routes.append({"route": top[1], "count": top[0]})
            else:
                break
        return top_routes

    def push_undo(self, action_type, data):
        """Action types: 'password_change', etc."""
        self.undo_stack.push({"type": action_type, "data": data})

    def pop_undo(self):
        return self.undo_stack.pop()
