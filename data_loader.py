from ds.graph import Graph
import random

class DataLoader:
    @staticmethod
    def load():
        from ds.core import GeneralTree
        graph = Graph()
        network_tree = GeneralTree("Lahore Transit Network")
        orange_node = network_tree.add_child(network_tree.root, "Orange Line")
        metro_node = network_tree.add_child(network_tree.root, "Metrobus")
        speedo_node = network_tree.add_child(network_tree.root, "Speedo Feeders")
        electro_node = network_tree.add_child(network_tree.root, "Electro Shuttles")
        
        # Load stops
        try:
            with open("data/stops.txt", "r") as f:
                for line in f:
                    if not line.strip(): continue
                    parts = line.strip().split(",")
                    if len(parts) < 5:
                        continue
                    stop_id, name, typ, lat, lng = int(parts[0]), parts[1], parts[2], float(parts[3]), float(parts[4])
                    graph.add_stop(stop_id, name, typ, lat, lng)
                    
                    #  Hierarchical N-ary Tree
                    if typ == "orange": network_tree.add_child(orange_node, name)
                    elif typ == "metro": network_tree.add_child(metro_node, name)
                    elif typ == "speedo": network_tree.add_child(speedo_node, name)
                    elif typ == "electro": network_tree.add_child(electro_node, name)

            graph.network_hierarchy = network_tree # Store for documentation/viva
        except FileNotFoundError:
            print("Error: data/stops.txt not found. Run generate_data.py first.")
            return None
        
        # Sequential Metro edges (1-27)
        for i in range(1, 27):
            graph.add_edge(i, i+1, 3, 1.0, "metro")
        
        # Sequential Orange edges (28-54)  
        for i in range(28, 54):
            if i in graph.adj and i+1 in graph.adj:
                graph.add_edge(i, i+1, 2.5, 1.1, "orange")
        
        # Speedo connections (random network)
        speedo_ids = list(range(100, 120))
        for i in range(len(speedo_ids)-1):
            if speedo_ids[i] in graph.adj and speedo_ids[i+1] in graph.adj:
                graph.add_edge(speedo_ids[i], speedo_ids[i+1], 8, 2.5, "speedo")
        
        # Electro connections (200-202)
        electro_ids = [200, 201, 202]
        for i in range(len(electro_ids)-1):
            if electro_ids[i] in graph.adj and electro_ids[i+1] in graph.adj:
                graph.add_edge(electro_ids[i], electro_ids[i+1], 5, 0.8, "electro")
        
        # Connect Electro to Hubs (e.g., Gulberg 116 to Electro 200)
        if 116 in graph.adj and 200 in graph.adj:
            graph.add_edge(116, 200, 10, 0.5, "walk")

        # LOGICAL TRANSFER HUBS (Walk weights)
        # 1. Connect Railway Hub (44) to Lakshmi (43) - Orange Line
        if 44 in graph.adj and 43 in graph.adj:
            graph.add_edge(44, 43, 5, 0.3, "walk")
            
        # 2. Connect Railway Hub (44) to Metro (e.g., Katchery 6 or MAO 8)
        if 44 in graph.adj and 6 in graph.adj:
            graph.add_edge(44, 6, 8, 0.5, "walk")
            
        # 3. Connect Speedo Ek Moriya (100) to Shahdara (1)
        if 100 in graph.adj and 1 in graph.adj:
            graph.add_edge(100, 1, 6, 0.4, "walk")
            
        # 4. Connect Orange G.P.O (42) to Anarkali (41)
        if 42 in graph.adj and 41 in graph.adj:
            graph.add_edge(42, 41, 4, 0.2, "walk")

        if graph.validate():
            print("✅ Graph loaded: 150+ nodes, validated")
        else:
            print("⚠️ Graph is NOT fully connected.")
            
        return graph
