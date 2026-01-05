import json
import os
from ds.core import HashTable

class AuthManager:
    def __init__(self, storage_file="data/users.json"):
        self.storage_file = storage_file
        self.user_table = HashTable(size=101) # Hash Table for O(1) lookups
        self._ensure_storage()
        self._load_users()

    def _ensure_storage(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)

    def _load_users(self):
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
            for username, info in data.items():
                self.user_table.insert(username, info)

    def register(self, username, password, name, email, phone):
        if self.user_table.lookup(username):
            return False, "User already exists"
        
        user_data = {
            "password": password,
            "name": name,
            "email": email,
            "phone": phone
        }
        self.user_table.insert(username, user_data)
        
        # Update persistence
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
        data[username.lower()] = user_data
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True, "Registration successful"

    def login(self, username, password):
        user_info = self.user_table.lookup(username)
        if user_info and user_info.get("password") == password:
            return True, "Login successful"
        return False, "Invalid username or password"

    def update_password(self, username, new_password):
        username = username.lower()
        user_info = self.user_table.lookup(username)
        if not user_info:
            return False, "User not found"
        
        user_info["password"] = new_password
        self.user_table.insert(username, user_info)
        
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
        data[username] = user_info
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True, "Password updated successfully"
