# 🚆 MetroConnect PRO: Intelligent City Transit & Safety Engine

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Premium_Rounded-gold.svg)](#-premium-high-fidelity-ui)
[![DSA](https://img.shields.io/badge/DSA-Advanced_Graphs-green.svg)](#-core-engineering--dsa)

**MetroConnect PRO** is a state-of-the-art urban transit management system designed to optimize commuting in high-density cities like Lahore. Moving beyond simple routing, it leverages high-level engineering and advanced Data Structures to provide a "Decision Engine" for modern commuters.

---

## 🚀 Key Innovation: Tri-Modal Route Optimization
Unlike standard apps that give a single path, MetroConnect PRO executes **three distinct graph objectives** simultaneously to empower user choice:

1.  **⚡ Flash Route (Time Optimized)**: Uses **Dijkstra's Algorithm** with time weights to find the absolute quickest path.
2.  **💰 Budget Route (Cost Optimized)**: Dijkstra's logic weighted by distance/fare, finding the most economical way to travel.
3.  **🧘 Relax Route (Transfer Optimized)**: A specialized **BFS (Breadth-First Search)** that minimizes switches between lines, prioritizing passenger comfort.

---

## 💎 Premium High-Fidelity UI
The application features a **bespoke design system** built from scratch in Tkinter:
*   **High-Precision Rounded UI**: A custom-engineered geometry engine for smooth, anti-aliased container corners (25px radius).
*   **Glassmorphism Effects**: Integration of Windows Acrylic/Mica effects for a deep, professional desktop aesthetic.
*   **Dynamic Data Visualization**: Real-time Leaflet.js map generation for high-impact journey walkthroughs.

---

## 🧠 Core Engineering & DSA
This project serves as a showcase for advanced Data Structures and Algorithms:

| Module | Data Structure | Algorithm / Logic |
| :--- | :--- | :--- |
| **Routing Engine** | **Graph (Adjacency List)** | Dijkstra's with Min-Heap ($O(E \log V)$) |
| **Safety Command** | **General Tree** | Hierarchy management and Tree Traversal |
| **Nearest Assistance** | **Graph** | BFS for absolute nearest service point |
| **Live Alerting** | **AVL Tree** | $O(\log N)$ station-specific predictive filtering |
| **Alert Priority** | **Min-Heap (Priority Queue)** | Ensures "Critical" alerts always surface first |
| **Community Feed** | **Linked List** | Prepend logic for $O(1)$ post additions |
| **Analytics/Undo** | **Stack** | LIFO buffer for password reverts and journey tracking |

---

## 🌱 Eco-Impact & Sustainability
MetroConnect PRO includes a built-in **Carbon Footprint Calculator**. It analyzes the total distance of every public transit route versus private car travel, providing users with a "Green Impact" score to encourage sustainable city commuting.

---

## 🛡️ City Safety Command
A dedicated security module that allows users to:
*   Visualize the **City Security Hierarchy** managed via a General Tree structure.
*   Trigger an **Emergency BFS Pulse** that scans the urban graph to find the nearest security post relative to the user's current train stop.

---

## 🛠️ How to Launch
1.  **Ensure Python 3.8+** is installed on your Windows environment.
2.  **Clone the Repo**: `git clone https://github.com/AyeshaaRafaqat/metroConnectF.git`
3.  **Run**: `python main.py`
4.  **Audio**: Use the **Journey Narrative** controls to hear your route plan read out by the intelligent audio engine.

---
Developed by **Ayeshaa Rafaqat** for the **Advanced Data Structures & Engineering Evaluation**.
