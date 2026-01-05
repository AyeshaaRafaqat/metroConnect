import tkinter as tk
from tkinter import ttk, messagebox
from data_loader import DataLoader
from ds.algorithms import dijkstra, bfs_min_transfers, find_nearest_station, bfs_get_alternatives, find_k_nearest_stations, calculate_walking_time
from ds.graph import Graph, SessionGraph
from ds.payments import TCash
from ds.live import LiveUpdates
from ds.auth import AuthManager
from ds.feed import FeedManager
from ds.analytics import AnalyticsManager
from ds.safety import SafetyManager
import random
import webbrowser
import urllib.parse
import os
import urllib.request
from pathlib import Path
import subprocess
import ctypes
import json

class RoundedFrame(tk.Canvas):
    """Logic: Simulates a rounded container using Canvas for premium UI."""
    def __init__(self, parent, bg, border_color, radius=25, **kwargs):
        super().__init__(parent, bg=parent['bg'], highlightthickness=0, **kwargs)
        self.radius = radius
        self.fill_color = bg
        self.border_color = border_color
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self.radius
        if w <= 2*r or h <= 2*r: return 
        o = 2 # offset to avoid edge cut
        
        # Exact 90-degree arcs for perfect corners
        self.create_arc(o, o, r*2+o, r*2+o, start=90, extent=90, fill=self.fill_color, outline=self.border_color, width=2)
        self.create_arc(w-r*2-o, o, w-o, r*2+o, start=0, extent=90, fill=self.fill_color, outline=self.border_color, width=2)
        self.create_arc(w-r*2-o, h-r*2-o, w-o, h-o, start=270, extent=90, fill=self.fill_color, outline=self.border_color, width=2)
        self.create_arc(0+o, h-r*2-o, r*2+o, h-o, start=180, extent=90, fill=self.fill_color, outline=self.border_color, width=2)
        
        # Solid core fills
        self.create_rectangle(r+o, o, w-r-o, h-o, fill=self.fill_color, outline="")
        self.create_rectangle(o, r+o, w-o, h-r-o, fill=self.fill_color, outline="")
        
        # Sharp border lines
        self.create_line(r+o, o, w-r-o, o, fill=self.border_color, width=2)
        self.create_line(r+o, h-o, w-r-o, h-o, fill=self.border_color, width=2)
        self.create_line(o, r+o, o, h-r-o, fill=self.border_color, width=2)
        self.create_line(w-o, r+o, w-o, h-r-o, fill=self.border_color, width=2)

class MetroConnect:
    THEMES = {
        "Dark Mode": {"bg": "#0f172a", "fg": "#f1f5f9", "accent": "#3b82f6", "sub": "#1e293b", "text_bg": "#1e293b"},
        "Onyx Grey": {"bg": "#000000", "fg": "#ffffff", "accent": "#4b5563", "sub": "#1a1a1a", "text_bg": "#000000"}
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MetroConnect PRO")
        self.root.state('zoomed') # Full screen for 14" and 16" laptops
        
        # Initialize Core Systems
        self.graph = DataLoader.load()
        self.tcash = TCash(balance=500.0)
        self.live_system = LiveUpdates()
        self.auth_system = AuthManager()
        self.feed_system = FeedManager()
        self.analytics_system = AnalyticsManager()
        self.safety_system = SafetyManager()
        self.current_theme = "Dark Mode"
        self.current_user = None
        
        # State
        self.id_to_name_map = {}
        self.current_route_data = [] # Stores current path nodes
        self.custom_locations = {}   # Logic: Name -> (lat, lon) for user-friendly routing
        self.start_coords = None     # Internal tracking
        self.end_coords = None       # Internal tracking
        self._build_id_map()
        
        # Apply Styles for Notebook and Tabs to match Dark Mode
        self.style = ttk.Style()
        self.setup_styles()
        
        # Apply Windows Blur Effect (Acrylic) for Premium Look
        self.apply_blur_effect()
        
        self.setup_auth_screen()

    def apply_blur_effect(self):
        """Logic: Uses ctypes to inject Windows Acrylic/Mica effects."""
        try:
            from ctypes import windll, c_int, byref, sizeof, Structure

            class ACCENT_POLICY(Structure):
                _fields_ = [('AccentState', c_int), ('AccentFlags', c_int), ('GradientColor', c_int), ('AnimationId', c_int)]

            class WINDOWCOMPOSITIONATTRIBDATA(Structure):
                _fields_ = [('Attribute', c_int), ('Data', ctypes.POINTER(ACCENT_POLICY)), ('SizeOfData', c_int)]

            hwnd = windll.user32.GetParent(self.root.winfo_id())
            accent = ACCENT_POLICY()
            accent.AccentState = 3 # 3: Blur, 4: Acrylic
            
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19
            data.SizeOfData = sizeof(accent)
            data.Data = ctypes.pointer(accent)
            
            windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))
        except:
            pass
    
    def setup_styles(self):
        theme = self.THEMES[self.current_theme]
        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=theme["sub"], foreground=theme["fg"], padding=[15, 8], font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab", background=[("selected", theme["accent"])], foreground=[("selected", "white")])
        self.style.configure("TLabel", background=theme["sub"], foreground=theme["fg"])
        self.style.configure("TFrame", background=theme["bg"])
        
        # Rounded-like button simulation
        self.style.configure("Rounded.TButton", padding=10, relief="flat", background=theme["accent"])

    def _build_id_map(self):
        for bucket in self.graph.stops.table:
            for name, details in bucket:
                self.id_to_name_map[details["id"]] = (name, details["type"], details["lat"], details["lng"])

    def setup_auth_screen(self):
        theme = self.THEMES[self.current_theme]
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=theme["bg"])
        main_container = tk.Frame(self.root, bg=theme["bg"])
        main_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Rounded Auth Box
        self.auth_bg = RoundedFrame(main_container, bg=theme["sub"], border_color=theme["accent"], width=650, height=550)
        self.auth_bg.pack(pady=20)
        
        container = tk.Frame(self.auth_bg, bg=theme["sub"])
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # 1. App Name
        tk.Label(container, text="METRO CONNECT PRO", font=("Helvetica", 40, "bold"), 
                 bg=theme["sub"], fg=theme["accent"]).pack(pady=(0, 10))
        
        # 2. Tagline
        tk.Label(container, text="Your Ultimate Urban Transit Companion for Lahore City", 
                 font=("Arial", 14), bg=theme["sub"], fg="gray").pack(pady=(0, 40))
        
        # 3. Initial Options
        self.auth_box = tk.Frame(container, bg=theme["bg"])
        self.auth_box.pack()
        
        btn_style = {"font": ("Arial", 14, "bold"), "fg": "white", "padx": 50, "pady": 15, "borderwidth": 0, "cursor": "hand2"}
        
        tk.Button(self.auth_box, text="SIGN IN", bg=theme["accent"], 
                  command=lambda: self.show_auth_fields("login"), **btn_style).pack(side="left", padx=10)
        
        tk.Button(self.auth_box, text="CREATE ACCOUNT", bg="#10b981", 
                  command=lambda: self.show_auth_fields("signup"), **btn_style).pack(side="left", padx=10)

    def show_auth_fields(self, mode):
        # Clear the initial buttons
        for widget in self.auth_box.winfo_children():
            widget.destroy()
            
        theme = self.THEMES[self.current_theme]
        self.auth_box.configure(bg=theme["sub"], padx=60, pady=40)
        
        title = "SECURE LOGIN" if mode == "login" else "CREATE ACCOUNT"
        tk.Label(self.auth_box, text=title, font=("Arial", 16, "bold"), 
                 bg=theme["sub"], fg="white").pack(pady=(0, 25))
        
        entry_style = {"font": ("Arial", 12), "bg": theme["bg"], "fg": "white", "borderwidth": 0, "insertbackground": "white"}
        
        # New Registration Fields
        if mode == "signup":
            tk.Label(self.auth_box, text="FULL NAME", bg=theme["sub"], fg=theme["accent"], font=("Arial", 8, "bold")).pack(anchor="w")
            self.name_entry = tk.Entry(self.auth_box, width=40, **entry_style)
            self.name_entry.pack(pady=(2, 12))
            
            tk.Label(self.auth_box, text="EMAIL ADDRESS", bg=theme["sub"], fg=theme["accent"], font=("Arial", 8, "bold")).pack(anchor="w")
            self.email_entry = tk.Entry(self.auth_box, width=40, **entry_style)
            self.email_entry.pack(pady=(2, 12))
            
            tk.Label(self.auth_box, text="PHONE NUMBER", bg=theme["sub"], fg=theme["accent"], font=("Arial", 8, "bold")).pack(anchor="w")
            self.phone_entry = tk.Entry(self.auth_box, width=40, **entry_style)
            self.phone_entry.pack(pady=(2, 12))

        tk.Label(self.auth_box, text="USERNAME", bg=theme["sub"], fg=theme["accent"], font=("Arial", 8, "bold")).pack(anchor="w")
        self.user_entry = tk.Entry(self.auth_box, width=40, **entry_style)
        self.user_entry.pack(pady=(2, 12))
        
        tk.Label(self.auth_box, text="PASSWORD", bg=theme["sub"], fg=theme["accent"], font=("Arial", 8, "bold")).pack(anchor="w")
        self.pass_entry = tk.Entry(self.auth_box, width=40, **entry_style, show="*")
        self.pass_entry.pack(pady=(2, 25))
        
        cmd = self.handle_login if mode == "login" else self.handle_register
        btn_txt = "ACCESS HUB" if mode == "login" else "REGISTER"
        btn_clr = theme["accent"] if mode == "login" else "#10b981"
        
        tk.Button(self.auth_box, text=btn_txt, bg=btn_clr, fg="white", font=("Arial", 12, "bold"),
                  padx=40, pady=12, borderwidth=0, cursor="hand2", command=cmd).pack(fill="x")
        
        # Auth Navigation Links
        toggle_msg = "New member? Create Account" if mode == "login" else "Already have an account? Sign In"
        toggle_mode = "signup" if mode == "login" else "login"
        tk.Button(self.auth_box, text=toggle_msg, bg=theme["sub"], fg=theme["accent"], 
                  font=("Arial", 10, "underline"), borderwidth=0, cursor="hand2",
                  command=lambda: self.show_auth_fields(toggle_mode)).pack(pady=(15, 0))

        tk.Button(self.auth_box, text="← BACK TO MAIN MENU", bg=theme["sub"], fg="gray", font=("Arial", 9),
                  borderwidth=0, cursor="hand2", command=self.setup_auth_screen).pack(pady=(10, 0))

    def handle_login(self):
        u, p = self.user_entry.get(), self.pass_entry.get()
        if not u or not p:
            messagebox.showwarning("Auth", "Please enter all fields")
            return
            
        success, msg = self.auth_system.login(u, p)
        if success:
            self.current_user = u
            self.setup_ui()
            self.update_live()
        else:
            messagebox.showerror("Auth Error", msg)

    def handle_register(self):
        u = self.user_entry.get()
        p = self.pass_entry.get()
        name = self.name_entry.get()
        email = self.email_entry.get()
        phone = self.phone_entry.get()
        
        if not all([u, p, name, email, phone]):
            messagebox.showwarning("Auth", "All fields are required for professional registration")
            return
            
        success, msg = self.auth_system.register(u, p, name, email, phone)
        if success:
            messagebox.showinfo("Auth", "Account Created! You can now Sign In.")
            self.setup_auth_screen() # Go back to landing to sign in
        else:
            messagebox.showerror("Auth Error", msg)

    def setup_ui(self):
        style_colors = self.THEMES[self.current_theme]
        self.setup_styles() # Refresh styles
        
        # Clear root if re-rendering for theme
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.configure(bg=style_colors["bg"])
        
        # HEADER
        header = tk.Frame(self.root, bg=style_colors["bg"], height=70)
        header.pack(fill="x")
        
        title_lbl = tk.Label(header, text="MetroConnect", bg=style_colors["bg"], fg=style_colors["fg"], 
                            font=("Helvetica", 24, "bold"))
        title_lbl.pack(pady=15, side="left", padx=30)
        
        theme_ctrl = tk.Frame(header, bg=style_colors["bg"])
        theme_ctrl.pack(side="right", padx=20)
        
        tk.Button(theme_ctrl, text="🌗 TOGGLE THEME", font=("Arial", 10, "bold"),
                  command=self.toggle_theme,
                  bg=style_colors["accent"], fg="white", borderwidth=0, padx=15, pady=8).pack()

        # MAIN NOTEBOOK
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # TAB 1: ROUTE PLANNER
        self.route_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.route_frame, text=" 📍 Route Planner ")
        self.setup_route_planner()
        
        # TAB 2: LIVE UPDATES
        self.live_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.live_frame, text=" 🔄 Live Updates ")
        self.setup_live_updates()
        
        # TAB 3: T-CASH WALLET
        self.wallet_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.wallet_frame, text=" 💳 T-Cash Wallet ")
        self.setup_wallet()
        
        # TAB 4: NETWORK MAP
        self.map_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.map_frame, text=" 🗺️ Network Map ")
        self.setup_map()
        
        # TAB 5: COMMUNITY HUB
        self.community_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.community_frame, text=" 💬 Community Hub ")
        self.setup_community_hub()
        
        # TAB 6: PROFILE & ANALYTICS
        self.profile_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.profile_frame, text=" 👤 Profile & Analytics ")
        self.setup_profile_tab()

        # TAB 7: SAFETY HUB (New DSA Feature)
        self.safety_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.safety_frame, text=" 🛡️ Safety Hub ")
        self.setup_safety_hub()

        # TAB 8: CONTACT US
        self.contact_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.contact_frame, text=" 📞 Contact Us ")
        self.setup_contact_tab()

        # TAB 9: ABOUT US (Layman's Guide)
        self.about_frame = tk.Frame(self.notebook, bg=style_colors["bg"])
        self.notebook.add(self.about_frame, text=" ✨ About Us ")
        self.setup_about_tab()

    def setup_route_planner(self):
        theme = self.THEMES[self.current_theme]
        # Search Container (Rounded)
        self.search_rounded = RoundedFrame(self.route_frame, bg=theme["sub"], border_color=theme["accent"], height=160)
        self.search_rounded.pack(fill="x", padx=20, pady=10)
        
        search_container = tk.Frame(self.search_rounded, bg=theme["sub"])
        search_container.place(relx=0.01, rely=0.1, relwidth=0.98, relheight=0.8)
        
        # From/To Selectors
        inputs_frame = tk.Frame(search_container, bg=theme["sub"])
        inputs_frame.pack(side="left", padx=20)
        
        tk.Label(inputs_frame, text="Origin Stop", bg=theme["sub"], fg=theme["fg"], font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.from_combo = ttk.Combobox(inputs_frame, width=35)
        self.from_combo.grid(row=1, column=0, padx=5, pady=5)
        
        from_loc_btns = tk.Frame(inputs_frame, bg=theme["sub"])
        from_loc_btns.grid(row=2, column=0, sticky="w", padx=5)
        tk.Button(from_loc_btns, text="📍 Current", font=("Arial", 8), command=lambda: self.use_current_location("start")).pack(side="left", padx=2)
        tk.Button(from_loc_btns, text="⌨️ Manual", font=("Arial", 8), command=lambda: self.enter_manual_coords("start")).pack(side="left", padx=2)

        tk.Label(inputs_frame, text="Destination Stop", bg=theme["sub"], fg=theme["fg"], font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
        self.to_combo = ttk.Combobox(inputs_frame, width=35)
        self.to_combo.grid(row=1, column=1, padx=5, pady=5)

        to_loc_btns = tk.Frame(inputs_frame, bg=theme["sub"])
        to_loc_btns.grid(row=2, column=1, sticky="w", padx=5)
        tk.Button(to_loc_btns, text="📍 Current", font=("Arial", 8), command=lambda: self.use_current_location("end")).pack(side="left", padx=2)
        tk.Button(to_loc_btns, text="⌨️ Manual", font=("Arial", 8), command=lambda: self.enter_manual_coords("end")).pack(side="left", padx=2)
        
        # Search Button (Full width in its container since filters are gone)
        btn_search = tk.Button(search_container, text="🚀 FIND BEST ROUTE", bg=theme["accent"], fg="white", 
                             font=("Arial", 12, "bold"), padx=40, pady=12, borderwidth=0, command=self.search_route)
        btn_search.pack(side="right", padx=20)
        
        # Populate
        self.refresh_combo_values()
        
        # Results Container (Rounded & Premium)
        self.res_rounded = RoundedFrame(self.route_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.res_rounded.pack(fill="both", expand=True, padx=20, pady=10)
        
        res_frame = tk.Frame(self.res_rounded, bg=theme["bg"])
        res_frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # Top Map Button
        self.btn_viz_map = tk.Button(res_frame, text="🗺️ VIEW INTERACTIVE JOURNEY MAP", 
                                    bg="#059669", fg="white", font=("Arial", 11, "bold"),
                                    command=self.generate_interactive_map, borderwidth=0, pady=12)
        self.btn_viz_map.pack(fill="x", pady=(0, 15))

        # Main Content (Narrative Left | Itinerary Right)
        content_frame = tk.Frame(res_frame, bg=theme["bg"])
        content_frame.pack(fill="both", expand=True)

        # LEFT: Narrative & Voice
        self.left_col_rounded = RoundedFrame(content_frame, bg=theme["sub"], border_color=theme["sub"], radius=20)
        self.left_col_rounded.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        left_col = tk.Frame(self.left_col_rounded, bg=theme["sub"])
        left_col.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)
        
        tk.Label(left_col, text="🔊 JOURNEY NARRATIVE", bg=theme["sub"], fg=theme["accent"], font=("Arial", 10, "bold")).pack(anchor="w")
        
        # Narrative with Scrollbar
        nar_container = tk.Frame(left_col, bg=theme["sub"])
        nar_container.pack(fill="both", expand=True, pady=5)

        self.narrative_text = tk.Text(nar_container, bg=theme["sub"], fg=theme["fg"], font=("Helvetica", 11),
                                     borderwidth=0, height=10, wrap="word")
        sb_nar = tk.Scrollbar(nar_container, command=self.narrative_text.yview)
        self.narrative_text.configure(yscrollcommand=sb_nar.set)
        sb_nar.pack(side="right", fill="y")
        self.narrative_text.pack(side="left", fill="both", expand=True)
        
        # Voice Controls Row
        voice_frame = tk.Frame(left_col, bg=theme["sub"])
        voice_frame.pack(fill="x", pady=10)
        
        tk.Button(voice_frame, text="▶ START AUDIO", bg="#10b981", fg="white", font=("Arial", 9, "bold"),
                  command=self.listen_to_plan, borderwidth=0, padx=10, pady=8).pack(side="left", expand=True, fill="x", padx=2)
        
        tk.Button(voice_frame, text="⏹ STOP AUDIO", bg="#ef4444", fg="white", font=("Arial", 9, "bold"),
                  command=self.stop_listening, borderwidth=0, padx=10, pady=8).pack(side="left", expand=True, fill="x", padx=2)

        # RIGHT: Itinerary
        self.right_col_rounded = RoundedFrame(content_frame, bg=theme["text_bg"], border_color=theme["sub"], radius=20)
        self.right_col_rounded.pack(side="left", fill="both", expand=True)
        
        right_col = tk.Frame(self.right_col_rounded, bg=theme["text_bg"])
        right_col.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)
        
        tk.Label(right_col, text="📋 STEP-BY-STEP", bg=theme["text_bg"], fg=theme["accent"], font=("Arial", 10, "bold")).pack(anchor="w")
        
        # Itinerary with Scrollbar (Cleaned up)
        iti_container = tk.Frame(right_col, bg=theme["text_bg"])
        iti_container.pack(fill="both", expand=True, pady=10)
        
        self.results_text = tk.Text(iti_container, bg=theme["text_bg"], fg=theme["fg"], 
                                   font=("Consolas", 11), borderwidth=0,
                                   insertbackground="white", wrap="word")
        sb = tk.Scrollbar(iti_container, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.results_text.pack(side="left", fill="both", expand=True)

        self.current_route_data = [] 
        self.last_summary_text = ""

    def listen_to_plan(self):
        if not self.last_summary_text: return
        self.stop_listening() 
        
        try:
            clean_txt = self.last_summary_text.replace('"', '').replace("'", "").replace("\n", " ").replace("`", "")
            # Cross-platform safe flag for hiding console windows (Windows only)
            no_window = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            cmd = f'powershell -WindowStyle Hidden -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean_txt}\')"'
            self.speech_process = subprocess.Popen(cmd, creationflags=no_window)
        except:
            pass

    def stop_listening(self):
        if hasattr(self, 'speech_process') and self.speech_process:
            try:
                no_window = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                # Kill the specific process tree 
                subprocess.run(["taskkill", "/PID", str(self.speech_process.pid), "/F", "/T"], 
                               creationflags=no_window, capture_output=True)
                self.speech_process = None
            except:
                pass

    def generate_interactive_map(self):
        """Generates a real interactive map using Leaflet.js (No library needed)"""
        if not self.current_route_data:
            messagebox.showwarning("No Route", "Please search for a route first!")
            return
            
        points = []
        first_lat, first_lng = None, None
        for i, stop_id in enumerate(self.current_route_data):
            name, _, lat, lng = self.id_to_name_map[stop_id]
            points.append(f"[{lat}, {lng}, '{name}']")
            if i == 0:
                first_lat, first_lng = lat, lng
            
        # Create a beautiful HTML file with Leaflet
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MetroConnect Journey Planner</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <style>
                #map {{ height: 100vh; width: 100%; }}
                body {{ margin: 0; padding: 0; background: #0f172a; }}
                .info {{ padding: 10px; background: rgba(15, 23, 42, 0.9); color: white; border-radius: 5px; border: 1px solid #3b82f6; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{first_lat}, {first_lng}], 13);
                
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; OpenStreetMap contributors'
                }}).addTo(map);

                var stops = [{", ".join(points)}];
                var latlngs = stops.map(s => [s[0], s[1]]);
                
                // Draw Path
                var polyline = L.polyline(latlngs, {{
                    color: '#34d399', 
                    weight: 6, 
                    opacity: 0.9,
                    lineJoin: 'round'
                }}).addTo(map);

                // Add Markers with CSS circles (No broken images)
                stops.forEach((s, i) => {{
                    var color = i === 0 ? '#10b981' : (i === stops.length - 1 ? '#ef4444' : '#3b82f6');
                    var size = i === 0 || i === stops.length - 1 ? 15 : 10;
                    
                    var icon = L.divIcon({{
                        className: 'custom-div-icon',
                        html: `<div style="background-color:${{color}}; width:${{size}}px; height:${{size}}px; border-radius:50%; border:2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>`,
                        iconSize: [size, size],
                        iconAnchor: [size/2, size/2]
                    }});

                    L.marker([s[0], s[1]], {{icon: icon}})
                        .bindPopup(`<b>Stop ${{i+1}}: ${{s[2]}}</b>`)
                        .addTo(map);
                }});

                map.fitBounds(polyline.getBounds());
            </script>
        </body>
        </html>
        """
        
        path = os.path.abspath("route_map.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        webbrowser.open(Path(path).as_uri())

    def setup_live_updates(self):
        theme = self.THEMES[self.current_theme]
        # Rounded Container for Live Updates
        self.live_rounded = RoundedFrame(self.live_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.live_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Frame(self.live_rounded, bg=theme["bg"])
        container.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        tk.Label(container, text="🔔 SERVICE ALERTS & ETA", font=("Arial", 18, "bold"), 
                 bg=theme["bg"], fg=theme["accent"]).pack(anchor="w", pady=(20, 10), padx=20)
        
        self.live_listbox = tk.Listbox(container, font=("Arial", 11), height=15, 
                                      bg=theme["sub"], fg=theme["fg"], borderwidth=0, highlightthickness=0)
        self.live_listbox.pack(fill="both", expand=True, pady=20, padx=20)
        
        tk.Button(container, text="🔄 REFRESH STATUS", bg=theme["accent"], fg="white", 
                 font=("Arial", 9, "bold"), command=self.update_live, padx=20, pady=10, borderwidth=0).pack(anchor="e", padx=20, pady=(0, 20))

    def setup_wallet(self):
        theme = self.THEMES[self.current_theme]
        self.wallet_rounded = RoundedFrame(self.wallet_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.wallet_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Frame(self.wallet_rounded, bg=theme["bg"])
        container.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # 💳 PREMIUM VIRTUAL CARD
        self.card_rounded = RoundedFrame(container, bg=theme["sub"], border_color=theme["accent"], radius=20, height=200)
        self.card_rounded.pack(fill="x", padx=100, pady=30)
        
        card = tk.Frame(self.card_rounded, bg=theme["sub"])
        card.place(relx=0.05, rely=0.1, relwidth=0.9, relheight=0.8)
        
        tk.Label(card, text="💳 T-CASH VIRTUAL CARD", bg=theme["sub"], fg=theme["accent"], font=("Arial", 10, "bold")).pack(anchor="w")
        self.balance_lbl = tk.Label(card, text=f"PKR {self.tcash.balance:.2f}", bg=theme["sub"], fg="white", 
                                   font=("Arial", 32, "bold"))
        self.balance_lbl.pack(pady=10)
        
        tk.Label(card, text="ACTIVE TRANSIT PASS", bg=theme["sub"], fg="gray", font=("Arial", 9)).pack(anchor="e")
        
        # Actions
        actions = tk.Frame(container, bg=theme["bg"])
        actions.pack(fill="x", padx=100)
        tk.Button(actions, text="➕ TOP UP WALLET", bg="#10b981", fg="white", font=("Arial", 10, "bold"), 
                 padx=20, pady=12, borderwidth=0, command=self.top_up).pack(side="left")
        
        # Transaction History (Rounded list)
        tk.Label(container, text="🕒 RECENT ACTIVITY", font=("Arial", 12, "bold"), 
                 bg=theme["bg"], fg=theme["accent"]).pack(anchor="w", pady=(30, 10), padx=100)
        
        self.hist_rounded = RoundedFrame(container, bg=theme["sub"], border_color=theme["sub"], radius=15)
        self.hist_rounded.pack(fill="both", expand=True, padx=100, pady=(0, 30))
        
        self.history_list = tk.Listbox(self.hist_rounded, font=("Arial", 10),
                                      bg=theme["sub"], fg=theme["fg"], borderwidth=0, highlightthickness=0)
        self.history_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.update_wallet_ui()


    def setup_map(self):
        theme = self.THEMES[self.current_theme]
        # Rounded Wrapper for Network Map
        self.map_rounded = RoundedFrame(self.map_frame, bg="#111827", border_color=theme["accent"], radius=25)
        self.map_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        wrapper = tk.Frame(self.map_rounded, bg="#111827")
        wrapper.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # Guide Panel (Left Side)
        guide = tk.Frame(wrapper, bg="#111827", width=250, padx=20, pady=20)
        guide.pack(side="left", fill="y")
        guide.pack_propagate(False)
        
        tk.Label(guide, text="🗺️ NETWORK GUIDE", font=("Arial", 12, "bold"), fg="#3b82f6", bg="#111827").pack(anchor="w", pady=(0,10))
        
        tips = [
            "🖱️ Click any node to see station name",
            "🚀 Set Origin/Destination directly",
            "🟡 Yellow path = Current Route",
            "📏 Scale: Accurate LHR Topology"
        ]
        for tip in tips:
            tk.Label(guide, text=tip, fg="gray", bg="#111827", font=("Arial", 9), wraplength=200, justify="left").pack(anchor="w", pady=5)
        
        # Legend
        tk.Label(guide, text="\n🚦 LINE LEGEND", font=("Arial", 10, "bold"), fg="white", bg="#111827").pack(anchor="w", pady=(20,5))
        legend_data = [("Orange Line", "#ea580c"), ("Metrobus", "#3b82f6"), ("Speedo/Feeder", "#22c55e"), ("Inter-hub Walk", "gray")]
        for text, color in legend_data:
            row = tk.Frame(guide, bg="#111827")
            row.pack(anchor="w", pady=2)
            tk.Canvas(row, width=15, height=15, bg=color, highlightthickness=0).pack(side="left", padx=(0,10))
            tk.Label(row, text=text, fg="white", bg="#111827", font=("Arial", 9)).pack(side="left")

        # Canvas (Right Side)
        self.canvas = tk.Canvas(wrapper, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)
        
        # Add Click Interaction 
        self.canvas.bind("<Button-1>", self.on_map_click)
        
        self.root.update_idletasks()
        self._draw_network_map()

    def on_map_click(self, event):
        """Interactive Station Identification and Selection"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Coordinate Space (Match Drawing)
        valid_stops = {sid: info for sid, info in self.id_to_name_map.items() if info[2] > 1.0 and info[3] > 1.0}
        lats = [v[2] for v in valid_stops.values()]
        lngs = [v[3] for v in valid_stops.values()]
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        lat_range = max(max_lat - min_lat, 0.0001)
        lng_range = max(max_lng - min_lng, 0.0001)
        
        padding = 60
        best_dist = 20 # Click tolerance px
        selected_stop = None

        for sid, info in valid_stops.items():
            # Scale Stop to Canvas
            cy = h - padding - ((info[2] - min_lat) / lat_range * (h - (padding*2)))
            cx = padding + ((info[3] - min_lng) / lng_range * (w - (padding*2)))
            
            dist = ((cx - event.x)**2 + (cy - event.y)**2)**0.5
            if dist < best_dist:
                best_dist = dist
                selected_stop = (sid, info[0])

        if selected_stop:
            sid, s_name = selected_stop
            # Show a custom popup for selection
            choice = messagebox.askquestion("Station Selection", f"Station: {s_name}\n\nSet as STARTING point?")
            if choice == 'yes':
                self.start_coords = None # Reset dynamic coords if selecting real station
                self.from_combo.set(s_name)
                self.notebook.select(0)
            else:
                choice2 = messagebox.askquestion("Station Selection", f"Set {s_name} as DESTINATION?")
                if choice2 == 'yes':
                    self.end_coords = None
                    self.to_combo.set(s_name)
                    self.notebook.select(0)
        else:
            # Logic: Handle click as Dynamic Location (Non-Station)
            padding = 60
            user_lat = min_lat + ((h - padding - event.y) / (h - (padding*2))) * lat_range
            user_lng = min_lng + ((event.x - padding) / (w - (padding*2))) * lng_range
            
            if 0 < event.x < w and 0 < event.y < h:
                # Ask for a professional name for this point
                from tkinter import simpledialog
                p_name = simpledialog.askstring("Custom Location", "Enter a name for this location (e.g. Home, Office):")
                if not p_name: 
                    p_name = f"Location @ {user_lat:.2f}, {user_lng:.2f}"
                
                self.custom_locations[p_name] = (user_lat, user_lng)
                self.refresh_combo_values()
                
                choice = messagebox.askquestion("Route Setup", f"Set '{p_name}' as start point?")
                if choice == 'yes':
                    self.from_combo.set(p_name)
                    self.notebook.select(0)
                else:
                    self.to_combo.set(p_name)
                    self.notebook.select(0)

    def _draw_network_map(self, path=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100: w = 800
        if h < 100: h = 600
        
        # Filter stops with valid coordinates
        valid_stops = {sid: info for sid, info in self.id_to_name_map.items() if info[2] > 1.0 and info[3] > 1.0}
        if not valid_stops: return

        lats = [v[2] for v in valid_stops.values()]
        lngs = [v[3] for v in valid_stops.values()]
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        lat_range = max(max_lat - min_lat, 0.0001)
        lng_range = max(max_lng - min_lng, 0.0001)

        def scale(lat, lng):
            padding = 60
            y = h - padding - ((lat - min_lat) / lat_range * (h - (padding*2)))
            x = padding + ((lng - min_lng) / lng_range * (w - (padding*2)))
            return x, y

        # Colors & Drawing
        colors = {"metro": "#3b82f6", "orange": "#ea580c", "speedo": "#22c55e", "walk": "#4b5563"}
        
        # 1. Draw Edges First
        drawn_edges = set()
        for u_id in self.graph.adj:
            if u_id not in valid_stops: continue
            u_pos = scale(valid_stops[u_id][2], valid_stops[u_id][3])
            
            for v_id, _, _, typ in self.graph.adj[u_id]:
                if v_id not in valid_stops: continue
                edge_key = tuple(sorted((u_id, v_id)))
                if edge_key not in drawn_edges:
                    v_pos = scale(valid_stops[v_id][2], valid_stops[v_id][3])
                    is_on_path = path and u_id in path and v_id in path and abs(path.index(u_id) - path.index(v_id)) == 1
                    
                    self.canvas.create_line(u_pos[0], u_pos[1], v_pos[0], v_pos[1], 
                                          fill="yellow" if is_on_path else colors.get(typ, "gray"), 
                                          width=5 if is_on_path else 2)
                    drawn_edges.add(edge_key)

        # 2. Draw Nodes
        for stop_id, info in valid_stops.items():
            x, y = scale(info[2], info[3])
            is_on_path = path and stop_id in path
            r = 6 if is_on_path else 3
            clr = "yellow" if is_on_path else colors.get(info[1], "white")
            
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=clr, outline="white", width=1)
            
            if is_on_path and (stop_id == path[0] or stop_id == path[-1]):
                self.canvas.create_text(x, y-15, text=info[0], fill="white", font=("Arial", 8, "bold"), anchor="s")

    def toggle_theme(self):
        self.current_theme = "Onyx Grey" if self.current_theme == "Dark Mode" else "Dark Mode"
        self.setup_ui()
        if self.current_route_data:
            self._draw_network_map(path=self.current_route_data)

    def update_live(self):
        self.live_listbox.delete(0, tk.END)
        #  Filter alerts using AVL Search on current path
        alerts = self.live_system.get_path_alerts(self.current_route_data, self.id_to_name_map)
        
        for a in alerts:
            self.live_listbox.insert(tk.END, a)
            self.live_listbox.insert(tk.END, "") # spacing

    def update_wallet_ui(self):
        self.balance_lbl.config(text=f"PKR {self.tcash.balance:.2f}")
        self.history_list.delete(0, tk.END)
        #  Traverse Custom Linked List
        curr = self.tcash.history.head
        while curr:
            self.history_list.insert(0, curr.data) # Insert at top for LIFO feel
            curr = curr.next

    def top_up(self):
        self.tcash.balance += 500
        self.update_wallet_ui()
        messagebox.showinfo("Wallet", "Success! PKR 500 added to your T-Cash account.")

    def refresh_combo_values(self):
        station_names = sorted([x[0] for x in self.id_to_name_map.values()])
        custom_names = sorted(list(self.custom_locations.keys()))
        all_options = custom_names + station_names
        self.from_combo['values'] = all_options
        self.to_combo['values'] = all_options

    def use_current_location(self, target):
        if messagebox.askyesno("Location", "Allow MetroConnect to access your current location?"):
            # Simulated GPS for Model Town/GULBERG area
            lat, lon = (31.481, 74.321) 
            loc_name = "My Current Location"
            self.custom_locations[loc_name] = (lat, lon)
            self.refresh_combo_values()
            
            if target == "start":
                self.from_combo.set(loc_name)
            else:
                self.to_combo.set(loc_name)

    def enter_manual_coords(self, target):
        popup = tk.Toplevel(self.root)
        popup.title("Add Custom Place")
        popup.geometry("350x250")
        
        tk.Label(popup, text="Place Name (e.g. My School):").pack(pady=2)
        name_e = tk.Entry(popup)
        name_e.pack()
        
        tk.Label(popup, text="Latitude:").pack(pady=2)
        lat_e = tk.Entry(popup)
        lat_e.pack()
        
        tk.Label(popup, text="Longitude:").pack(pady=2)
        lon_e = tk.Entry(popup)
        lon_e.pack()

        def save():
            try:
                name = name_e.get()
                lat, lon = float(lat_e.get()), float(lon_e.get())
                self.custom_locations[name] = (lat, lon)
                self.refresh_combo_values()
                if target == "start":
                    self.from_combo.set(name)
                else:
                    self.to_combo.set(name)
                popup.destroy()
            except:
                messagebox.showerror("Error", "Invalid coordinates!")
        tk.Button(popup, text="Save & Use", command=save, bg="#10b981", fg="white").pack(pady=10)

    def search_route(self):
        # Robust Input Handling: Strip whitespace to prevent lookup failures
        start_name = self.from_combo.get().strip()
        end_name = self.to_combo.get().strip()
        
        # 🧪 DSA INTEGRATION: Session Graph & Augmentation
        session_graph = self.graph 
        
        # Case-Insensitive Station Lookup
        start_stop = self.graph.stops.lookup(start_name)
        end_stop = self.graph.stops.lookup(end_name)
        
        s_id = start_stop["id"] if start_stop else None
        e_id = end_stop["id"] if end_stop else None
        
        # Case-Insensitive Custom Locations Lookup
        def get_custom_coords(name):
            if name in self.custom_locations:
                return self.custom_locations[name]
            # Fallback search regardless of casing
            for k, v in self.custom_locations.items():
                if k.lower() == name.lower():
                    return v
            return None

        s_coords = get_custom_coords(start_name)
        e_coords = get_custom_coords(end_name)

        # Logic: If we have custom coords, use session graph
        use_session = False
        if s_coords or e_coords:
            session_graph = SessionGraph(self.graph)
            use_session = True
            
            # Add Temporary Start Node
            if s_coords:
                lat, lon = s_coords
                s_id = 99999 # Reserved Temp ID
                session_graph.add_stop(s_id, start_name, "walk", lat, lon)
                nearestPorts = find_k_nearest_stations(lat, lon, self.graph, k=3)
                for nid, nname, dist in nearestPorts:
                    w_time = calculate_walking_time(dist)
                    session_graph.add_temp_edge(s_id, nid, w_time, dist, "walk")
                self.id_to_name_map[s_id] = (start_name, "walk", lat, lon)
            
            # Add Temporary End Node
            if e_coords:
                lat, lon = e_coords
                e_id = 99998 # Reserved Temp ID
                session_graph.add_stop(e_id, end_name, "walk", lat, lon)
                nearestPorts = find_k_nearest_stations(lat, lon, self.graph, k=3)
                for nid, nname, dist in nearestPorts:
                    w_time = calculate_walking_time(dist)
                    session_graph.add_temp_edge(e_id, nid, w_time, dist, "walk")
                self.id_to_name_map[e_id] = (end_name, "walk", lat, lon)

        if s_id is None or e_id is None:
            messagebox.showerror("Error", "Please select stations or set custom locations.")
            return

        # 🧪 SMART TRI-MODAL OPTIMIZATION (Feature to stand out)
        # Run 3 different graph algorithms to suggest the 'Intelligence' factor
        fastest = dijkstra(session_graph, s_id, e_id, "time")
        budget = dijkstra(session_graph, s_id, e_id, "dist") # Budget path based on distance
        
        # Main result for narrative
        result = fastest 
        if not result["path"]:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "❌ No route found. Please check connectivity.")
            return

        # FARE CALCULATION
        real_fare, breakdown = self.tcash.calculate_fare(result["path"], session_graph)
        pay_ok, pay_msg = self.tcash.pay(real_fare, f"{start_name} to {end_name}")
        
        # COMPARISON INSIGHT (WOW FACTOR)
        budget_fare, _ = self.tcash.calculate_fare(budget["path"], session_graph)
        theme = self.THEMES[self.current_theme]
        
        if budget_fare < real_fare and budget["path"] != result["path"]:
            savings = real_fare - budget_fare
            insight = f"💡 BUDGET SAVER: You can save PKR {savings} by taking an alternative path.\n"
        else:
            insight = "⭐ OPTIMIZED: This is the absolute fastest and cheapest route available.\n"

        # 🛡️ SAFETY ANALYSIS
        safe_node, hops = self.safety_system.find_nearest_safe_point(s_id, session_graph)
        if safe_node:
            safe_name = self.safety_system.safe_points.get(safe_node, "Security Hub")
            self.safe_status.config(text=f"✅ SAFE ESCORT FOUND\nYour nearest security point is {safe_name} ({hops} connections away).", fg="#10b981")
        else:
            self.safe_status.config(text="⚠️ SECURITY ALERT\nNo immediate safe escort found within the local sector.", fg="#ef4444")
        
        # 2. CALCULATE METRICS (Clean Path Traversal)
        total_time = 0
        total_dist = 0
        path = result["path"]
        
        prev_mode = None
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            found = False
            # Check Session Graph for neighbors
            for v_id, t, d, typ in session_graph.get_neighbors(u):
                if v_id == v:
                    total_dist += d
                    total_time += t
                    if prev_mode and typ != prev_mode:
                        total_time += 5 
                    prev_mode = typ
                    found = True
                    break
        
        self.update_wallet_ui()
        
        # 3. USER-FRIENDLY ITINERARY
        self.results_text.delete(1.0, tk.END)
        self.results_text.tag_configure("insight", foreground=theme["accent"], font=("Arial", 10, "bold"))
        self.results_text.insert(tk.END, "─" * 40 + "\n")
        self.results_text.insert(tk.END, insight, "insight")
        self.results_text.insert(tk.END, "─" * 40 + "\n\n")

        self.results_text.insert(tk.END, f"🚩 JOURNEY FROM {start_name.upper()}\n")
        self.results_text.insert(tk.END, f"🏁 TO {end_name.upper()}\n")
        self.results_text.insert(tk.END, "─" * 40 + "\n\n")
        
        for i, stop_id in enumerate(path):
            s_name, s_typ, _, _ = self.id_to_name_map[stop_id]
            icon = "🟠" if s_typ == "orange" else "🔵" if s_typ == "metro" else "🚶" if s_typ == "walk" else "⚡" if s_typ == "electro" else "🚌"
            
            if i == 0:
                self.results_text.insert(tk.END, f"⭐ START: {s_name}\n")
            elif i == len(path)-1:
                self.results_text.insert(tk.END, f"📍 ARRIVE: {s_name}\n")
            else:
                self.results_text.insert(tk.END, f"  {icon} {s_name}\n")
            
            if i < len(path)-1:
                self.results_text.insert(tk.END, "    │\n")

        # 4. NARRATIVE SUMMARY (Ultra-Detailed Project Flow)
        summary = f"Route optimization complete. Your journey from {start_name} to {end_name} "
        summary += f"will take approximately {int(total_time)} minutes for the {total_dist:.1f} KM distance. "
        summary += f"The total cost is PKR {real_fare}."

        # 🌿 ECO-IMPACT (The STAND OUT Feature)
        co2_saved = total_dist * 0.12 * 0.7 
        carbon_phrase = f"🌱 ECO-IMPACT: You saved {co2_saved:.2f} KG of CO2 by using public transport!"

        narrative = f"{carbon_phrase}\n\n📜 STEP-BY-STEP COMMUTE GUIDE:\n"
        last_service = None
        
        for i, (leg_info, cost) in enumerate(breakdown):
            try:
                mode_raw, details = leg_info.split(": ")
                mode = mode_raw.lower()
                origin_leg, dest_leg = details.split(" to ")
                
                # Logic: Service naming for Suggestions
                service = "Orange Line Train" if "orange" in mode else "Metrobus" if "metro" in mode else "Speedo Shuttle" if "speedo" in mode else "Electro Premium" if "electro" in mode else "Walk"
                
                if i == 0:
                    phrase = f"• First, board the {service} at {origin_leg}."
                elif service != last_service:
                    phrase = f"• At {origin_leg}, please get off and switch to the {service}."
                else:
                    phrase = f"• Continue on your {service} toward {dest_leg}."

                if "walk" in mode:
                    phrase = f"• Next, walk from {origin_leg} to reach {dest_leg}. (No Charge)"
                else:
                    phrase += f" Stay on board until you reach {dest_leg}. (PKR {cost})"
                
                narrative += phrase + "\n"
                last_service = service
            except Exception:
                narrative += f"• Segment: {leg_info} (PKR {cost})\n"
        
        narrative += f"\n🏁 Finally, arrive at your destination: {end_name}."
        narrative += "\n🛡️ SAFETY NOTICE: This route passes through guarded sectors. Emergency SOS is available in the Safety Hub."
        
        # Save for Audio
        self.last_summary_text = summary + ". " + narrative.replace("• ", "").replace("↳ ", "")
        
        self.narrative_text.config(state="normal")
        self.narrative_text.delete(1.0, tk.END)
        self.narrative_text.insert(tk.END, summary + "\n\n" + narrative)
        self.narrative_text.config(state="disabled")
        
        self.last_summary_text = summary + "\n" + narrative 
        self.current_route_data = path
        
        # 5. Draw on Main Map
        self._draw_network_map(path=path)
        
        # 6. Refresh Live Alerts for this path
        self.update_live()
        
        # 7. LOG JOURNEY FOR ANALYTICS
        self.analytics_system.log_journey(self.current_user, start_name, end_name, real_fare)

        # 🧪 DISCARD SESSION GRAPH & CLEANUP
        # Keep base graph immutable
        if use_session:
            self.id_to_name_map.pop(99999, None)
            self.id_to_name_map.pop(99998, None)
            del session_graph 

    def setup_community_hub(self):
        theme = self.THEMES[self.current_theme]
        self.comm_rounded = RoundedFrame(self.community_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.comm_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Frame(self.comm_rounded, bg=theme["bg"])
        container.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # Left Panel (Actions) - Rounded Sidebar
        self.side_rounded = RoundedFrame(container, bg=theme["sub"], border_color=theme["sub"], radius=20, width=320)
        self.side_rounded.pack(side="left", fill="y", padx=(20, 10), pady=20)
        self.side_rounded.pack_propagate(False)
        
        sidebar = tk.Frame(self.side_rounded, bg=theme["sub"])
        sidebar.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        tk.Label(sidebar, text=f"Welcome, {self.current_user}!", font=("Arial", 14, "bold"), 
                 bg=theme["sub"], fg=theme["accent"]).pack(anchor="w", pady=(0, 20))
        
        tk.Label(sidebar, text="Share your journey status or transit tips with the community.", 
                 fg="gray", bg=theme["sub"], font=("Arial", 9), wraplength=250).pack(anchor="w", pady=(0, 30))
        
        self.post_input = tk.Text(sidebar, font=("Arial", 11), height=5, bg=theme["bg"], 
                                 fg="white", borderwidth=0, padx=10, pady=10)
        self.post_input.pack(fill="x", pady=(0, 10))
        
        tk.Button(sidebar, text="POST TO FEED", bg=theme["accent"], fg="white", font=("Arial", 10, "bold"),
                  command=self.add_feed_post, pady=10).pack(fill="x")
        
        tk.Frame(sidebar, bg="gray", height=1).pack(fill="x", pady=30)
        
        tk.Button(sidebar, text="UPDATE SELECTED", bg="#10b981", fg="white", font=("Arial", 9),
                  command=self.update_feed_post).pack(fill="x", pady=5)
        
        tk.Button(sidebar, text="DELETE POST", bg="#ef4444", fg="white", font=("Arial", 9),
                  command=self.delete_feed_post).pack(fill="x", pady=5)

        # Right Panel (Feed Treeview)
        feed_area = tk.Frame(container, bg=theme["bg"])
        feed_area.pack(side="right", fill="both", expand=True)
        
        tk.Label(feed_area, text="Global Community Feed", font=("Arial", 16, "bold"), 
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w", pady=(0, 20))
        
        # Treeview for professional look
        style = ttk.Style()
        style.configure("Treeview", background=theme["sub"], foreground="white", fieldbackground=theme["sub"], rowheight=60)
        style.map("Treeview", background=[('selected', theme["accent"])])
        
        self.feed_tree = ttk.Treeview(feed_area, columns=("id", "author", "time", "message"), show="headings")
        self.feed_tree.heading("id", text="ID")
        self.feed_tree.heading("author", text="User")
        self.feed_tree.heading("time", text="Timestamp")
        self.feed_tree.heading("message", text="Community Message")
        self.feed_tree.column("id", width=40, anchor="center")
        self.feed_tree.column("author", width=100)
        self.feed_tree.column("time", width=140)
        self.feed_tree.column("message", width=450)
        self.feed_tree.pack(fill="both", expand=True)
        
        # BIND SELECTION: Auto-fill text box when a post is clicked
        self.feed_tree.bind("<<TreeviewSelect>>", self._on_post_selected)
        
        self.load_community_feed()

    def _on_post_selected(self, event):
        selected = self.feed_tree.selection()
        if not selected: return
        values = self.feed_tree.item(selected[0])["values"]
        # values: [id, author, time, message]
        msg = values[3]
        self.post_input.delete("1.0", tk.END)
        self.post_input.insert("1.0", msg)

    def load_community_feed(self):
        #  Traverse Linked List and render
        self.feed_tree.delete(*self.feed_tree.get_children())
        global_posts = self.feed_system.get_global_feed()
        for post in global_posts:
            self.feed_tree.insert("", "end", values=(post["id"], post["author"], post["timestamp"], post["msg"]))

    def add_feed_post(self):
        msg = self.post_input.get("1.0", "end-1c").strip()
        if not msg: return
        
        #  O(1) Prepend to Linked List
        self.feed_system.add_post(self.current_user, msg)
        self.post_input.delete("1.0", tk.END)
        self.load_community_feed()
        messagebox.showinfo("Feed", "Post added successfully!")

    def update_feed_post(self):
        selected = self.feed_tree.selection()
        if not selected:
            messagebox.showwarning("Feed", "Select a post to update")
            return
        
        values = self.feed_tree.item(selected[0])["values"]
        post_id, author = values[0], values[1]
        
        # PERMISSION CHECK
        if author.lower() != self.current_user.lower():
            messagebox.showerror("Permission Denied", "You can only edit your own posts.")
            return

        new_msg = self.post_input.get("1.0", "end-1c").strip()
        if not new_msg:
            messagebox.showwarning("Feed", "Enter new message in the text box above")
            return
        
        #  O(N) Traversal to find and update node
        if self.feed_system.update_post(self.current_user, post_id, new_msg):
            self.post_input.delete("1.0", tk.END)
            self.load_community_feed()
            messagebox.showinfo("Feed", "Post updated!")
        else:
            messagebox.showerror("Feed", "Failed to update post")

    def delete_feed_post(self):
        selected = self.feed_tree.selection()
        if not selected:
            messagebox.showwarning("Feed", "Select a post to delete")
            return
        
        values = self.feed_tree.item(selected[0])["values"]
        post_id, author = values[0], values[1]

        # PERMISSION CHECK
        if author.lower() != self.current_user.lower():
            messagebox.showerror("Permission Denied", "You can only delete your own posts.")
            return

        if messagebox.askyesno("Feed", "Are you sure you want to delete this post?"):
            #  O(N) Traversal to remove node from Linked List
            if self.feed_system.delete_post(self.current_user, post_id):
                self.load_community_feed()
                messagebox.showinfo("Feed", "Post deleted")

    def setup_profile_tab(self):
        theme = self.THEMES[self.current_theme]
        self.prof_rounded = RoundedFrame(self.profile_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.prof_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Frame(self.prof_rounded, bg=theme["bg"])
        container.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # 1. Sidebar (User Profile & Undo) - Rounded
        self.pside_rounded = RoundedFrame(container, bg=theme["sub"], border_color=theme["sub"], radius=20, width=320)
        self.pside_rounded.pack(side="left", fill="y", padx=(20, 10), pady=20)
        self.pside_rounded.pack_propagate(False)
        
        sidebar = tk.Frame(self.pside_rounded, bg=theme["sub"])
        sidebar.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        tk.Label(sidebar, text="ACCOUNT SETTINGS", font=("Arial", 12, "bold"), fg=theme["accent"], bg=theme["sub"]).pack(anchor="w", pady=(0, 20))
        
        tk.Label(sidebar, text="New Password", fg="gray", bg=theme["sub"]).pack(anchor="w")
        self.new_pass_entry = tk.Entry(sidebar, show="*", bg=theme["bg"], fg="white", borderwidth=0, font=("Arial", 11))
        self.new_pass_entry.pack(fill="x", pady=(5, 15))
        
        tk.Button(sidebar, text="CHANGE PASSWORD", bg=theme["accent"], fg="white", command=self.handle_change_password).pack(fill="x", pady=5)
        
        tk.Button(sidebar, text="⏪ UNDO PASSWORD CHANGE", bg="#4b5563", fg="white", command=self.handle_undo_password).pack(fill="x", pady=(20, 5))
        tk.Label(sidebar, text="Restore your previous login credentials", font=("Arial", 8), fg="gray", bg=theme["sub"]).pack()
        
        # 2. History Panel (Center)
        history_panel = tk.Frame(container, bg=theme["bg"])
        history_panel.pack(side="left", fill="both", expand=True, padx=10)
        
        tk.Label(history_panel, text="📜 JOURNEY HISTORY (Newest First)", font=("Arial", 12, "bold"), fg="white", bg=theme["bg"]).pack(anchor="w", pady=(0, 10))
        
        # Treeview for History (LIFO via Stack)
        self.history_tree = ttk.Treeview(history_panel, columns=("from", "to", "fare", "time"), show="headings", height=15)
        self.history_tree.heading("from", text="Origin")
        self.history_tree.heading("to", text="Destination")
        self.history_tree.heading("fare", text="Fare")
        self.history_tree.heading("time", text="Date/Time")
        self.history_tree.column("from", width=150)
        self.history_tree.column("to", width=150)
        self.history_tree.column("fare", width=70)
        self.history_tree.column("time", width=150)
        self.history_tree.pack(fill="both", expand=True)
        
        # 3. Analytics Panel (Right)
        analytics_panel = tk.Frame(container, bg=theme["sub"], width=350, padx=15, pady=15)
        analytics_panel.pack(side="right", fill="y", padx=(20, 0))
        analytics_panel.pack_propagate(False)
        
        tk.Label(analytics_panel, text="📊 MONTHLY ANALYTICS", font=("Arial", 12, "bold"), fg=theme["accent"], bg=theme["sub"]).pack(anchor="w", pady=(0, 10))
        tk.Label(analytics_panel, text="Top 5 Most Used Routes", font=("Arial", 10), fg="white", bg=theme["sub"]).pack(anchor="w", pady=(0, 5))
        
        self.analytics_display = tk.Text(analytics_panel, bg=theme["bg"], fg="#10b981", borderwidth=0, font=("Consolas", 10), padx=10, pady=10)
        self.analytics_display.pack(fill="both", expand=True)
        
        # Register tab switch event to refresh UI
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 5: # Profile Tab
            self.update_profile_ui()

    def update_profile_ui(self):
        # 1. Update History
        self.history_tree.delete(*self.history_tree.get_children())
        history = self.analytics_system.get_history(self.current_user)
        for j in history:
            self.history_tree.insert("", "end", values=(j["from"], j["to"], f"PKR {j['fare']}", j["timestamp"]))
            
        # 2. Update Analytics
        self.analytics_display.config(state="normal")
        self.analytics_display.delete(1.0, tk.END)
        top_routes = self.analytics_system.get_top_routes(self.current_user)
        if not top_routes:
            self.analytics_display.insert(tk.END, "No journey data available yet.\nStart traveling to see stats!")
        else:
            self.analytics_display.insert(tk.END, " RANK | COUNT | ROUTE\n")
            self.analytics_display.insert(tk.END, "-------------------------------------\n")
            for i, r in enumerate(top_routes, 1):
                self.analytics_display.insert(tk.END, f"  #{i}  |   {r['count']}   | {r['route']}\n")
        self.analytics_display.config(state="disabled")

    def handle_change_password(self):
        new_p = self.new_pass_entry.get()
        if not new_p: return
        
        # Push OLD password to undo buffer before changing
        user_info = self.auth_system.user_table.lookup(self.current_user)
        if user_info:
            old_p = user_info["password"]
            self.analytics_system.push_undo("password_change", {"old": old_p})
            
            if self.auth_system.update_password(self.current_user, new_p):
                messagebox.showinfo("Profile", "Password updated! You can undo this if needed.")
                self.new_pass_entry.delete(0, tk.END)
    
    def handle_undo_password(self):
        # Revert last change from undo buffer
        action = self.analytics_system.pop_undo()
        if not action or action["type"] != "password_change":
            messagebox.showwarning("Undo", "Nothing left to undo.")
            return
            
        old_p = action["data"]["old"]
        if self.auth_system.update_password(self.current_user, old_p):
            messagebox.showinfo("Undo", "Action reverted! Password restored.")

    def setup_safety_hub(self):
        theme = self.THEMES[self.current_theme]
        self.safety_rounded = RoundedFrame(self.safety_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.safety_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Frame(self.safety_rounded, bg=theme["bg"])
        container.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

        tk.Label(container, text="🛡️ CITY SAFETY COMMAND", font=("Helvetica", 24, "bold"), 
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=(20, 20))

        grid = tk.Frame(container, bg=theme["bg"])
        grid.pack(fill="both", expand=True, padx=20)

        # Left: Hierarchy (Rounded)
        self.h_rounded = RoundedFrame(grid, bg=theme["sub"], border_color=theme["sub"], radius=20)
        self.h_rounded.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        h_container = tk.Frame(self.h_rounded, bg=theme["sub"])
        h_container.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        tk.Label(h_container, text="LAHORE SECURITY NETWORK", bg=theme["sub"], fg=theme["accent"], font=("Arial", 12, "bold")).pack(anchor="w", pady=10)
        
        brief_lbl = tk.Label(h_container, text=self.safety_system.get_safety_brief(), bg=theme["sub"], fg="white", font=("Arial", 9, "italic"), wraplength=250, justify="left")
        brief_lbl.pack(fill="x", pady=5)
        
        h_text = tk.Text(h_container, bg=theme["sub"], fg="gray", font=("Consolas", 10), height=12, borderwidth=0)
        h_text.insert(tk.END, self.safety_system.get_security_hierarchy())
        h_text.config(state="disabled")
        h_text.pack(fill="both", expand=True, pady=10)

        # Right: Safe Points (Rounded) - UI Fix
        self.s_rounded = RoundedFrame(grid, bg=theme["sub"], border_color=theme["sub"], radius=20)
        self.s_rounded.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        s_container = tk.Frame(self.s_rounded, bg=theme["sub"])
        s_container.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        tk.Label(s_container, text="EMERGENCY ASSISTANCE", bg=theme["sub"], fg=theme["accent"], font=("Arial", 12, "bold")).pack(anchor="w")
        self.safe_status = tk.Label(s_container, text="Search for a route to see nearest safe points.", 
                                    bg=theme["sub"], fg="gray", wraplength=300, justify="left", pady=20)
        self.safe_status.pack(fill="x")
        
        tk.Button(s_container, text="🚨 EMERGENCY SOS", bg="#ef4444", fg="white", font=("Arial", 12, "bold"),
                  command=lambda: messagebox.showwarning("SOS", "Emergency services notified!"), 
                  padx=20, pady=15, borderwidth=0).pack(pady=20)

    def setup_contact_tab(self):
        theme = self.THEMES[self.current_theme]
        self.contact_rounded = RoundedFrame(self.contact_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.contact_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Frame(self.contact_rounded, bg=theme["bg"])
        container.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.8)

        tk.Label(container, text="📞 CONTACT METROCONNECT", font=("Helvetica", 24, "bold"), 
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=(0, 40))

        info = [
            ("Central Helpline", "1199"),
            ("Email Support", "support@metroconnect.pk"),
            ("Office Address", "Arfa Software Technology Park, Lahore"),
            ("Operating Hours", "06:00 AM - 11:59 PM")
        ]

        for label, val in info:
            row = tk.Frame(container, bg=theme["sub"], pady=10, padx=20)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, bg=theme["sub"], fg=theme["accent"], font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(row, text=val, bg=theme["sub"], fg=theme["fg"], font=("Arial", 10)).pack(side="right")

    def setup_about_tab(self):
        theme = self.THEMES[self.current_theme]
        # Rounded Container for About Us
        self.about_rounded = RoundedFrame(self.about_frame, bg=theme["bg"], border_color=theme["accent"], radius=25)
        self.about_rounded.pack(fill="both", expand=True, padx=20, pady=20)
        
        container = tk.Canvas(self.about_rounded, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.about_rounded, orient="vertical", command=container.yview)
        scroll_frame = tk.Frame(container, bg=theme["bg"])

        scroll_frame.bind(
            "<Configure>",
            lambda e: container.configure(scrollregion=container.bbox("all"))
        )

        container.create_window((0, 0), window=scroll_frame, anchor="nw", width=self.root.winfo_screenwidth() - 100)
        container.configure(yscrollcommand=scrollbar.set)

        container.pack(side="left", fill="both", expand=True, padx=40, pady=20)
        scrollbar.pack(side="right", fill="y")

        # TITLE
        tk.Label(scroll_frame, text="✨ OUR MISSION & VISION", font=("Helvetica", 28, "bold"), 
                 bg=theme["bg"], fg=theme["accent"]).pack(pady=(40, 10))
        tk.Label(scroll_frame, text="The Heart of MetroConnect PRO Engineering", 
                 font=("Arial", 12, "italic"), bg=theme["bg"], fg="gray").pack(pady=(0, 40))

        # SECTIONS (Simplified)
        sections = [
            ("🌟 Our Vision", "Our vision is to make Lahore a world-class smart city where no one has to wait for a bus or worry about navigation. We see a future where every 'Speedo', 'Metro', and 'Orange Train' is perfectly synced for you."),
            ("🚀 Our Mission", "We are on a mission to optimize urban travel. By using advanced engineering, we ensure that you spend less time in traffic and more time doing what you love.")
        ]

        for title, content in sections:
            # Rounded Block for each section with fixed height for better layout
            block_rounded = RoundedFrame(scroll_frame, bg=theme["sub"], border_color=theme["accent"], radius=20, height=180)
            block_rounded.pack(fill="x", pady=15, padx=60)
            block_rounded.pack_propagate(False) # Force the height
            
            # Use pack for internal contents for consistent vertical spacing
            block = tk.Frame(block_rounded, bg=theme["sub"], padx=25, pady=25)
            block.pack(fill="both", expand=True)
            
            tk.Label(block, text=title.strip(), font=("Arial", 20, "bold"), 
                     bg=theme["sub"], fg=theme["accent"]).pack(anchor="w")
            tk.Label(block, text=content, font=("Arial", 12), bg=theme["sub"], fg=theme["fg"], 
                     wraplength=700, justify="left").pack(anchor="w", pady=(10, 0))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MetroConnect()
    app.run()
