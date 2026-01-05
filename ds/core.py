class HashTable:
    def __init__(self, size=251):  # Prime for Lahore stops
        self.size = size
        self.table = [[] for _ in range(size)]  # Chaining
    
    def _hash(self, key):
        return hash(key.lower()) % self.size
    
    def insert(self, key, value):
        index = self._hash(key)
        for i, (k, v) in enumerate(self.table[index]):
            if k.lower() == key.lower():
                self.table[index][i] = (key, value)
                return
        self.table[index].append((key, value))
    
    def lookup(self, key):
        index = self._hash(key)
        for k, v in self.table[index]:
            if k.lower() == key.lower():
                return v
        return None

class MinHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, cost, node):
        self.heap.append((cost, node))
        self._bubble_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        min_val = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._bubble_down(0)
        return min_val
    
    def _bubble_up(self, i):
        parent = (i - 1) // 2
        if i > 0 and self.heap[i][0] < self.heap[parent][0]:
            self.heap[i], self.heap[parent] = self.heap[parent], self.heap[i]
            self._bubble_up(parent)
    
    def _bubble_down(self, i):
        smallest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]:
            smallest = left
        if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]:
            smallest = right
        
        if smallest != i:
            self.heap[i], self.heap[smallest] = self.heap[smallest], self.heap[i]
            self._bubble_down(smallest)

class Queue:
    def __init__(self):
        self.items = []
    def enqueue(self, item):
        self.items.append(item)
    def dequeue(self):
        return self.items.pop(0) if self.items else None

class Stack:
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)
    def pop(self):
        return self.items.pop() if self.items else None
    def peek(self):
        return self.items[-1] if self.items else None

class Node:
    """Linked List Node"""
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
    def prepend(self, data):
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last = self.head
        while last.next:
            last = last.next
        last.next = new_node
    
    def remove(self, key, value):
        """Removes node where data[key] == value"""
        curr = self.head
        prev = None
        while curr:
            if isinstance(curr.data, dict) and curr.data.get(key) == value:
                if prev:
                    prev.next = curr.next
                else:
                    self.head = curr.next
                return True
            prev = curr
            curr = curr.next
        return False

class AVLNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def get_height(self, node):
        return node.height if node else 0
    
    def get_balance(self, node):
        return self.get_height(node.left) - self.get_height(node.right) if node else 0

    def rotate_right(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        return x

    def rotate_left(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y

    def insert(self, root, key, value):
        if not root:
            return AVLNode(key, value)
        if key < root.key:
            root.left = self.insert(root.left, key, value)
        elif key > root.key:
            root.right = self.insert(root.right, key, value)
        else:
            root.value = value
            return root

        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        balance = self.get_balance(root)

        # Left Left
        if balance > 1 and key < root.left.key:
            return self.rotate_right(root)
        # Right Right
        if balance < -1 and key > root.right.key:
            return self.rotate_left(root)
        # Left Right
        if balance > 1 and key > root.left.key:
            root.left = self.rotate_left(root.left)
            return self.rotate_right(root)
        # Right Left
        if balance < -1 and key < root.right.key:
            root.right = self.rotate_right(root.right)
            return self.rotate_left(root)

        return root

    def search(self, root, key):
        if not root or root.key == key:
            return root
        if key < root.key:
            return self.search(root.left, key)
class GeneralTreeNode:
    def __init__(self, data):
        self.data = data
        self.children = []

class GeneralTree:
    def __init__(self, root_data):
        self.root = GeneralTreeNode(root_data)

    def add_child(self, parent_node, child_data):
        new_node = GeneralTreeNode(child_data)
        parent_node.children.append(new_node)
        return new_node

    def search(self, node, target):
        if node.data == target:
            return node
        for child in node.children:
            res = self.search(child, target)
            if res: return res
        return None

class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, val, data):
        self.heap.append((val, data))
        self._bubble_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap: return None
        if len(self.heap) == 1: return self.heap.pop()
        max_val = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._bubble_down(0)
        return max_val
    
    def _bubble_up(self, i):
        p = (i - 1) // 2
        if i > 0 and self.heap[i][0] > self.heap[p][0]:
            self.heap[i], self.heap[p] = self.heap[p], self.heap[i]
            self._bubble_up(p)
            
    def _bubble_down(self, i):
        largest = i
        l, r = 2*i + 1, 2*i + 2
        if l < len(self.heap) and self.heap[l][0] > self.heap[largest][0]: largest = l
        if r < len(self.heap) and self.heap[r][0] > self.heap[largest][0]: largest = r
        if largest != i:
            self.heap[i], self.heap[largest] = self.heap[largest], self.heap[i]
            self._bubble_down(largest)
