import json
import os
from datetime import datetime
from ds.core import LinkedList

class FeedManager:
    def __init__(self, storage_file="data/feed.json"):
        self.storage_file = storage_file
        self.user_feeds = {} # {username: LinkedList}
        self._ensure_storage()
        self._load_feeds()

    def _ensure_storage(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.storage_file) or os.path.getsize(self.storage_file) < 5:
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
            self._populate_dummy_data()

    def _populate_dummy_data(self):
        dummy = {
            "system": [
                {"id": 1, "msg": "Welcome to the MetroConnect Community! 🚇", "timestamp": "2026-01-01 09:00:00"},
                {"id": 2, "msg": "Transit Tip: Orange Line is 5 mins faster during rain. ☔", "timestamp": "2026-01-02 10:15:00"}
            ],
            "admin": [
                {"id": 1, "msg": "Maintenance on Orange Line sector 4 completed.", "timestamp": "2026-01-03 14:00:00"}
            ],
            "lahore_commuter": [
                {"id": 1, "msg": "Bus 14 is quite crowded today, better take the Metro.", "timestamp": "2026-01-04 12:30:00"},
                {"id": 2, "msg": "Found a lost card at Ali Town station. Handed to staff.", "timestamp": "2026-01-04 16:45:00"}
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(dummy, f, indent=2)

    def get_global_feed(self):
        """Returns all posts from all users sorted by timestamp (newest first)"""
        all_posts = []
        for username, ll in self.user_feeds.items():
            curr = ll.head
            while curr:
                # Create a copy with the author included
                post_copy = curr.data.copy()
                post_copy['author'] = username
                all_posts.append(post_copy)
                curr = curr.next
        
        # Sort by timestamp string
        all_posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_posts

    def _load_feeds(self):
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
            for username, posts in data.items():
                ll = LinkedList()
                # Appending so that they keep order if sorted, 
                # but user wants newest at head, so we prepend during creation
                # However, for loading from file (stored as list), assuming list is [newest...oldest]
                # if we append chronologically, we get [oldest...newest]. 
                # To get head = newest, we process list from oldest to newest and prepend.
                for post in reversed(posts):
                    ll.prepend(post)
                self.user_feeds[username.lower()] = ll

    def _save_feeds(self):
        data = {}
        for username, ll in self.user_feeds.items():
            posts = []
            curr = ll.head
            while curr:
                posts.append(curr.data)
                curr = curr.next
            data[username] = posts
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_feed(self, username):
        username = username.lower()
        if username not in self.user_feeds:
            self.user_feeds[username] = LinkedList()
        return self.user_feeds[username]

    def add_post(self, username, message):
        username = username.lower()
        ll = self.get_feed(username)
        
        # Get max ID or similar
        max_id = 0
        curr = ll.head
        while curr:
            if curr.data['id'] > max_id:
                max_id = curr.data['id']
            curr = curr.next
            
        new_post = {
            "id": max_id + 1,
            "msg": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        ll.prepend(new_post) # Insertion at HEAD (Newest first)
        self._save_feeds()
        return new_post

    def update_post(self, username, post_id, new_message):
        username = username.lower()
        ll = self.get_feed(username)
        curr = ll.head
        while curr:
            if curr.data['id'] == post_id:
                curr.data['msg'] = new_message
                curr.data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S (Edited)")
                self._save_feeds()
                return True
            curr = curr.next
        return False

    def delete_post(self, username, post_id):
        username = username.lower()
        ll = self.get_feed(username)
        success = ll.remove('id', post_id)
        if success:
            self._save_feeds()
        return success
