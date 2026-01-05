from ds.core import HashTable

h = HashTable()
h.insert("Johar Town", {"id": 114})
print(f"Lookup 'Johar Town': {h.lookup('Johar Town')}")
print(f"Lookup 'johar town': {h.lookup('johar town')}")
print(f"Lookup 'johar town ': {h.lookup('johar town ')}")
