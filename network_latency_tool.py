import scapy.all as scapy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import time
import threading
from geopy.geocoders import Nominatim
import folium
from folium.plugins import HeatMap
import webbrowser
import json
import csv
import os
from datetime import datetime

class NetworkLatencyTool:
    def __init__(self, root):  # Fixed from _init_ to __init__
        self.root = root
        self.root.title("Advanced Network Latency Measurement Tool")
        self.root.geometry("1200x800")
        
        # Initialize data storage
        self.latency_data = {}
        self.historical_data = []
        self.geolocator = Nominatim(user_agent="network_latency_tool")
        
        # Create GUI elements
        self.create_gui()
        
    def create_gui(self):
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.tab4 = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab1, text="Latency Measurement")
        self.notebook.add(self.tab2, text="Historical Data")
        self.notebook.add(self.tab3, text="Geographical View")
        self.notebook.add(self.tab4, text="Settings")
        
        # Tab 1: Latency Measurement
        self.create_tab1()
        
        # Tab 2: Historical Data
        self.create_tab2()
        
        # Tab 3: Geographical View
        self.create_tab3()
        
        # Tab 4: Settings
        self.create_tab4()
        
    def create_tab1(self):
        # Create frame for input
        input_frame = ttk.LabelFrame(self.tab1, text="Measurement Settings")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # IP addresses input
        ttk.Label(input_frame, text="IP Addresses (comma separated):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ip_entry = ttk.Entry(input_frame, width=50)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ip_entry.insert(0, "8.8.8.8, 1.1.1.1, 208.67.222.222")
        
        # Number of pings
        ttk.Label(input_frame, text="Number of Pings:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ping_entry = ttk.Entry(input_frame, width=10)
        self.ping_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.ping_entry.insert(0, "5")  # Reduced default number of pings
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Measurement", command=self.start_measurement)
        self.start_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Data", command=self.export_data).pack(side=tk.LEFT, padx=5)
        
        # Create frame for results
        results_frame = ttk.LabelFrame(self.tab1, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for results table
        columns = ("IP", "Average Latency", "Min Latency", "Max Latency", "Packet Loss")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)
            
        self.results_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Create frame for charts
        charts_frame = ttk.LabelFrame(self.tab1, text="Visualization")
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create figure and canvas for plotting
        self.fig1, self.ax1 = plt.subplots(figsize=(6, 3))
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=charts_frame)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def create_tab2(self):
        # Historical data view
        history_frame = ttk.Frame(self.tab2)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for historical data
        columns = ("Timestamp", "IPs Tested", "Avg Latency", "Packet Loss")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
            
        self.history_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Button frame
        button_frame = ttk.Frame(self.tab2)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="View Details", command=self.view_historical_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export History", command=self.export_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
    
    def create_tab3(self):
        # Geographical view
        geo_frame = ttk.Frame(self.tab3)
        geo_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions frame
        instructions_frame = ttk.LabelFrame(geo_frame, text="Instructions")
        instructions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        instructions_text = ttk.Label(instructions_frame, 
            text="1. First, run a latency measurement from the 'Latency Measurement' tab\n"
                 "2. Then click 'Generate Map' below to visualize the measured data on a world map\n"
                 "3. The map will show actual measured latency with color-coded markers:\n"
                 "   • Green: Low latency (< 50ms)\n"
                 "   • Orange: Medium latency (50-100ms)\n"
                 "   • Red: High latency (> 100ms)",
            justify=tk.LEFT)
        instructions_text.pack(padx=10, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(geo_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Generate Map from Measured Data", command=self.generate_map).pack(pady=5)
        
        # Map frame
        map_frame = ttk.LabelFrame(geo_frame, text="Map View")
        map_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.map_label = ttk.Label(map_frame, 
            text="Run a latency measurement first, then click 'Generate Map' to visualize your results",
            wraplength=500)
        self.map_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def create_tab4(self):
        # Settings tab
        settings_frame = ttk.Frame(self.tab4)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings
        general_frame = ttk.LabelFrame(settings_frame, text="General Settings")
        general_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Default Number of Pings:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.default_pings = ttk.Entry(general_frame, width=10)
        self.default_pings.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.default_pings.insert(0, "5")  # Reduced default number
        
        ttk.Label(general_frame, text="Ping Timeout (seconds):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ping_timeout = ttk.Entry(general_frame, width=10)
        self.ping_timeout.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.ping_timeout.insert(0, "2")
        
        # Advanced settings
        advanced_frame = ttk.LabelFrame(settings_frame, text="Advanced Settings")
        advanced_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(advanced_frame, text="Data Storage Location:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.storage_path = ttk.Entry(advanced_frame, width=50)
        self.storage_path.grid(row=0, column=1, padx=5, pady=5)
        self.storage_path.insert(0, os.path.join(os.getcwd(), "latency_data"))
        
        ttk.Button(advanced_frame, text="Browse", command=self.browse_storage_path).grid(row=0, column=2, padx=5, pady=5)
        
        # Save settings button
        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).pack(pady=10)
    
    def measure_latency(self, ip_address, num_pings=10):
        # This method is now only used for individual measurements, not from the UI
        # The main measurement functionality has been moved to the start_measurement method
        latencies = []
        for _ in range(num_pings):
            packet = scapy.IP(dst=ip_address)/scapy.ICMP()
            start_time = time.time()
            reply = scapy.sr1(packet, timeout=2, verbose=0)
            end_time = time.time()
            
            if reply:
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                latencies.append(latency)
            else:
                latencies.append(None)  # No response
            
            time.sleep(0.2)  # Reduced wait time between pings
        
        return latencies
    
    def start_measurement(self):
        # Get input values
        ip_addresses = [ip.strip() for ip in self.ip_entry.get().split(",")]
        try:
            num_pings = int(self.ping_entry.get())
            if num_pings <= 0:
                messagebox.showerror("Input Error", "Number of pings must be a positive integer.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Number of pings must be a valid integer.")
            return
            
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Create and configure progress bar
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Measurement Progress")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)  # Set as transient to main window
        progress_window.grab_set()  # Make window modal
        
        ttk.Label(progress_window, text="Measuring latency...").pack(pady=10)
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        status_label = ttk.Label(progress_window, text="Initializing...")
        status_label.pack(pady=5)
        
        # Disable the start button to prevent multiple clicks
        self.start_button.configure(state="disabled")
        
        # Function to run in background thread
        def background_task():
            self.latency_data = {}
            total_pings = len(ip_addresses) * num_pings
            current_ping = 0
            
            # Measure latency for each IP
            for i, ip in enumerate(ip_addresses):
                # Update status
                self.root.after(0, lambda ip=ip: status_label.config(text=f"Testing {ip}..."))
                
                latencies = []
                for j in range(num_pings):
                    # Update progress
                    current_ping += 1
                    progress_percent = (current_ping / total_pings) * 100
                    self.root.after(0, lambda p=progress_percent: progress_var.set(p))
                    
                    # Measure single ping
                    packet = scapy.IP(dst=ip)/scapy.ICMP()
                    start_time = time.time()
                    reply = scapy.sr1(packet, timeout=2, verbose=0)
                    end_time = time.time()
                    
                    if reply:
                        latency = (end_time - start_time) * 1000  # Convert to milliseconds
                        latencies.append(latency)
                    else:
                        latencies.append(None)  # No response
                    
                    time.sleep(0.2)  # Reduced wait time between pings
                
                # Calculate statistics
                valid_latencies = [lat for lat in latencies if lat is not None]
                avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else 0
                min_latency = min(valid_latencies) if valid_latencies else 0
                max_latency = max(valid_latencies) if valid_latencies else 0
                packet_loss = (1 - len(valid_latencies)/num_pings) * 100
                
                # Store data for visualization
                self.latency_data[ip] = {
                    "latencies": latencies,
                    "avg": avg_latency,
                    "min": min_latency,
                    "max": max_latency,
                    "packet_loss": packet_loss
                }
            
            # When all measurements are complete, update UI in main thread
            self.root.after(0, complete_measurements)
        
        # Function to update UI after measurements are complete
        def complete_measurements():
            # Close progress window
            progress_window.destroy()
            
            # Update results table
            for ip, data in self.latency_data.items():
                self.results_tree.insert("", tk.END, values=(
                    ip,
                    f"{data['avg']:.2f} ms",
                    f"{data['min']:.2f} ms",
                    f"{data['max']:.2f} ms",
                    f"{data['packet_loss']:.1f}%"
                ))
            
            # Update chart
            self.update_chart()
            
            # Add to historical data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.historical_data.append({
                "timestamp": timestamp,
                "data": self.latency_data.copy()
            })
            
            # Update historical data view
            self.update_historical_view()
            
            # Re-enable the start button
            self.start_button.configure(state="normal")
            
            messagebox.showinfo("Measurement Complete", "Latency measurement completed successfully!")
        
        # Start the background thread
        thread = threading.Thread(target=background_task)
        thread.daemon = True  # Thread will exit when main program exits
        thread.start()
    
    def update_chart(self):
        # Clear previous plot
        self.ax1.clear()
        
        # Plot latency for each IP
        for ip, data in self.latency_data.items():
            latencies = data["latencies"]
            x = list(range(1, len(latencies)+1))
            y = [lat if lat is not None else 0 for lat in latencies]
            
            self.ax1.plot(x, y, marker='o', label=ip)
        
        # Configure plot
        self.ax1.set_title("Latency Measurements")
        self.ax1.set_xlabel("Ping Number")
        self.ax1.set_ylabel("Latency (ms)")
        self.ax1.legend()
        self.ax1.grid(True)
        
        # Redraw canvas
        self.canvas1.draw()
    
    def update_historical_view(self):
        # Clear previous entries
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Add historical data
        for entry in self.historical_data:
            timestamp = entry["timestamp"]
            data = entry["data"]
            ips = ", ".join(list(data.keys()))
            
            # Calculate average of averages
            avg_latencies = [d["avg"] for d in data.values()]
            overall_avg = sum(avg_latencies) / len(avg_latencies) if avg_latencies else 0
            
            # Calculate average packet loss
            packet_losses = [d["packet_loss"] for d in data.values()]
            overall_loss = sum(packet_losses) / len(packet_losses) if packet_losses else 0
            
            self.history_tree.insert("", tk.END, values=(
                timestamp,
                ips,
                f"{overall_avg:.2f} ms",
                f"{overall_loss:.1f}%"
            ))
    
    def view_historical_details(self):
        # Get selected item
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a historical record to view details.")
            return
        
        # Get index of selected item
        index = self.history_tree.index(selected[0])
        
        # Get data for selected item
        entry = self.historical_data[index]
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Details for {entry['timestamp']}")
        details_window.geometry("600x400")
        
        # Create treeview for details
        columns = ("IP", "Average Latency", "Min Latency", "Max Latency", "Packet Loss")
        details_tree = ttk.Treeview(details_window, columns=columns, show="headings")
        
        for col in columns:
            details_tree.heading(col, text=col)
            details_tree.column(col, width=100)
        
        details_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add data to treeview
        for ip, data in entry["data"].items():
            details_tree.insert("", tk.END, values=(
                ip,
                f"{data['avg']:.2f} ms",
                f"{data['min']:.2f} ms",
                f"{data['max']:.2f} ms",
                f"{data['packet_loss']:.1f}%"
            ))
    
    def clear_data(self):
        # Clear results table
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Clear latency data
        self.latency_data = {}
        
        # Clear chart
        self.ax1.clear()
        self.canvas1.draw()
    
    def clear_history(self):
        # Confirm with user
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all historical data?"):
            self.historical_data = []
            self.update_historical_view()
    
    def generate_map(self):
        # Check if we have latency data to map
        if not self.latency_data:
            messagebox.showwarning("No Data", "Please run a latency measurement first before generating the map.")
            return
        
        # Get IP addresses from latency data
        ip_addresses = list(self.latency_data.keys())
        
        # Create a map centered at a default location (world view)
        try:
            m = folium.Map(location=[20, 0], zoom_start=2)
            
            # Create list for heatmap data
            heat_data = []
            
            # Process each IP address
            for ip in ip_addresses:
                try:
                    # Try to get hostname/location info for the IP
                    import socket
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = ip
                    
                    # Try to geocode the hostname or use a geolocation API for the IP
                    # For DNS servers and well-known IPs, manually map some common ones
                    location_map = {
                        "8.8.8.8": ("Mountain View, CA, USA", 37.4056, -122.0775),  # Google DNS
                        "8.8.4.4": ("Mountain View, CA, USA", 37.4056, -122.0775),  # Google DNS
                        "1.1.1.1": ("San Francisco, CA, USA", 37.7749, -122.4194),  # Cloudflare DNS
                        "1.0.0.1": ("San Francisco, CA, USA", 37.7749, -122.4194),  # Cloudflare DNS
                        "208.67.222.222": ("San Francisco, CA, USA", 37.7749, -122.4194),  # OpenDNS
                        "208.67.220.220": ("San Francisco, CA, USA", 37.7749, -122.4194),  # OpenDNS
                    }
                    
                    if ip in location_map:
                        loc_name, lat, lon = location_map[ip]
                        location = type('obj', (object,), {'latitude': lat, 'longitude': lon})()
                    else:
                        # Try to geocode the hostname
                        location = self.geolocator.geocode(hostname)
                        loc_name = hostname
                    
                    if location:
                        # Get actual measured latency data
                        data = self.latency_data[ip]
                        avg_latency = data['avg']
                        min_latency = data['min']
                        max_latency = data['max']
                        packet_loss = data['packet_loss']
                        
                        # Determine marker color based on latency
                        if avg_latency < 50:
                            color = 'green'
                        elif avg_latency < 100:
                            color = 'orange'
                        else:
                            color = 'red'
                        
                        # Create popup with real data
                        popup_html = f"""
                        <b>{loc_name}</b><br>
                        IP: {ip}<br>
                        Avg Latency: {avg_latency:.2f} ms<br>
                        Min: {min_latency:.2f} ms<br>
                        Max: {max_latency:.2f} ms<br>
                        Packet Loss: {packet_loss:.1f}%
                        """
                        
                        # Add marker with actual latency data
                        folium.Marker(
                            [location.latitude, location.longitude],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{ip} - {avg_latency:.2f} ms",
                            icon=folium.Icon(color=color, icon='info-sign')
                        ).add_to(m)
                        
                        # Add to heatmap data (latitude, longitude, intensity based on latency)
                        heat_data.append([location.latitude, location.longitude, avg_latency / 10])
                    
                except Exception as e:
                    print(f"Could not process location for {ip}: {str(e)}")
                    continue
            
            # Add heatmap layer if we have data
            if heat_data:
                HeatMap(heat_data, radius=25, blur=35, max_zoom=13).add_to(m)
            
            # Save map to HTML file
            map_file = os.path.join(os.getcwd(), "latency_map.html")
            m.save(map_file)
            
            # Open in browser
            webbrowser.open(f"file://{map_file}")
            
            self.map_label.config(text=f"Map created with real latency data and opened in browser.\nFile saved to: {map_file}")
            
        except Exception as e:
            messagebox.showerror("Map Generation Error", f"Error generating map: {str(e)}")
    
    def browse_storage_path(self):
        # Open directory browser
        directory = tk.filedialog.askdirectory()
        if directory:
            self.storage_path.delete(0, tk.END)
            self.storage_path.insert(0, directory)
    
    def save_settings(self):
        # Save settings
        settings = {
            "default_pings": self.default_pings.get(),
            "ping_timeout": self.ping_timeout.get(),
            "storage_path": self.storage_path.get()
        }
        
        # Create settings directory if it doesn't exist
        os.makedirs("settings", exist_ok=True)
        
        # Save settings to file
        with open(os.path.join("settings", "settings.json"), 'w') as f:
            json.dump(settings, f, indent=4)
        
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
    
    def export_data(self):
        # Ask for file format
        file_format = simpledialog.askstring("Export Data", "Enter file format (csv/json):", initialvalue="csv")
        
        if file_format and file_format.lower() == "csv":
            # Export to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"latency_data_{timestamp}.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["IP", "Average Latency (ms)", "Min Latency (ms)", "Max Latency (ms)", "Packet Loss (%)"])
                
                # Write data
                for ip, data in self.latency_data.items():
                    writer.writerow([
                        ip,
                        f"{data['avg']:.2f}",
                        f"{data['min']:.2f}",
                        f"{data['max']:.2f}",
                        f"{data['packet_loss']:.1f}"
                    ])
            
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
        
        elif file_format and file_format.lower() == "json":
            # Export to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"latency_data_{timestamp}.json"
            
            with open(filename, 'w') as jsonfile:
                json.dump(self.latency_data, jsonfile, indent=4)
            
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
        
        else:
            messagebox.showerror("Export Error", "Invalid file format. Please enter 'csv' or 'json'.")
    
    def export_history(self):
        # Ask for file format
        file_format = simpledialog.askstring("Export History", "Enter file format (csv/json):", initialvalue="json")
        
        if file_format and file_format.lower() == "csv":
            # Export to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"latency_history_{timestamp}.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Timestamp", "IP", "Average Latency (ms)", "Min Latency (ms)", "Max Latency (ms)", "Packet Loss (%)"])
                
                # Write data
                for entry in self.historical_data:
                    timestamp = entry["timestamp"]
                    for ip, data in entry["data"].items():
                        writer.writerow([
                            timestamp,
                            ip,
                            f"{data['avg']:.2f}",
                            f"{data['min']:.2f}",
                            f"{data['max']:.2f}",
                            f"{data['packet_loss']:.1f}"
                        ])
            
            messagebox.showinfo("Export Complete", f"Historical data exported to {filename}")
        
        elif file_format and file_format.lower() == "json":
            # Export to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"latency_history_{timestamp}.json"
            
            with open(filename, 'w') as jsonfile:
                json.dump(self.historical_data, jsonfile, indent=4)
            
            messagebox.showinfo("Export Complete", f"Historical data exported to {filename}")
        
        else:
            messagebox.showerror("Export Error", "Invalid file format. Please enter 'csv' or 'json'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkLatencyTool(root)
    root.mainloop()