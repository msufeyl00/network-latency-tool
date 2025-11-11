from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import scapy.all as scapy
import time
import json
import os
from datetime import datetime
import folium
from folium.plugins import HeatMap
import socket
import threading
import struct
import platform
import subprocess

# Add TCP ping function as fallback
def tcp_ping(host, port=80, timeout=2):
    """TCP ping as fallback when ICMP is not available"""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        end_time = time.time()
        return (end_time - start_time) * 1000  # Convert to ms
    except:
        return None

# Traceroute function
def traceroute(destination, max_hops=30, timeout=2):
    """Perform traceroute to destination"""
    hops = []
    dest_ip = socket.gethostbyname(destination)
    
    for ttl in range(1, max_hops + 1):
        try:
            # Create ICMP packet with specific TTL
            packet = scapy.IP(dst=dest_ip, ttl=ttl) / scapy.ICMP()
            start_time = time.time()
            reply = scapy.sr1(packet, timeout=timeout, verbose=0)
            end_time = time.time()
            
            if reply is None:
                hops.append({
                    'hop': ttl,
                    'ip': '*',
                    'hostname': '*',
                    'latency': None
                })
            else:
                latency = (end_time - start_time) * 1000
                try:
                    hostname = socket.gethostbyaddr(reply.src)[0]
                except:
                    hostname = reply.src
                
                hops.append({
                    'hop': ttl,
                    'ip': reply.src,
                    'hostname': hostname,
                    'latency': latency
                })
                
                # Check if we reached destination
                if reply.src == dest_ip:
                    break
        except Exception as e:
            print(f"Traceroute error at hop {ttl}: {str(e)}")
            hops.append({
                'hop': ttl,
                'ip': '*',
                'hostname': '*',
                'latency': None
            })
    
    return hops

# Network diagnostics
def get_network_info(ip):
    """Get detailed network information about an IP"""
    info = {
        'ip': ip,
        'hostname': None,
        'reverse_dns': None,
        'is_reachable': False,
        'open_ports': [],
        'ttl': None,
        'protocol': None
    }
    
    try:
        # Get hostname
        info['hostname'] = socket.gethostbyname(ip)
        
        # Reverse DNS lookup
        try:
            info['reverse_dns'] = socket.gethostbyaddr(ip)[0]
        except:
            pass
        
        # Check common ports
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 8080]
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    info['open_ports'].append(port)
            except:
                pass
        
        # Simple reachability test
        try:
            packet = scapy.IP(dst=ip) / scapy.ICMP()
            reply = scapy.sr1(packet, timeout=2, verbose=0)
            if reply:
                info['is_reachable'] = True
                info['ttl'] = reply.ttl if hasattr(reply, 'ttl') else None
        except:
            pass
            
    except Exception as e:
        print(f"Network info error for {ip}: {str(e)}")
    
    return info

# Calculate network statistics
def calculate_jitter(latencies):
    """Calculate jitter (variation in latency)"""
    if len(latencies) < 2:
        return 0
    
    differences = []
    for i in range(1, len(latencies)):
        if latencies[i] is not None and latencies[i-1] is not None:
            differences.append(abs(latencies[i] - latencies[i-1]))
    
    return sum(differences) / len(differences) if differences else 0

def calculate_throughput_estimate(latency, packet_size=64):
    """Estimate throughput based on latency (simplified)"""
    if latency == 0:
        return 0
    # Simplified bandwidth estimation
    # BDP (Bandwidth-Delay Product) estimation
    rtt = latency / 1000  # Convert to seconds
    if rtt == 0:
        return 0
    # Assume TCP window size of 64KB
    estimated_bandwidth = (65536 * 8) / rtt  # bits per second
    return estimated_bandwidth / 1_000_000  # Convert to Mbps

# Check if we have raw socket privileges
def check_raw_socket_privileges():
    """Check if we can create raw sockets (need admin/root)"""
    try:
        # Try to create a raw socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        test_socket.close()
        return True
    except PermissionError:
        return False
    except:
        return False

has_admin = check_raw_socket_privileges()
print(f"{'✓' if has_admin else '✗'} Running with {'administrator' if has_admin else 'normal'} privileges")
if not has_admin:
    print("⚠ WARNING: No admin privileges detected. Using TCP ping fallback (port 80/443).")
    print("  For true ICMP ping, restart as Administrator (Windows) or with sudo (Linux/Mac)")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Data storage
latency_data = {}
historical_data = []
settings = {
    "default_pings": 5,
    "ping_timeout": 2,
    "storage_path": os.path.join(os.getcwd(), "latency_data")
}

# Load settings if they exist
if os.path.exists("settings.json"):
    with open("settings.json", 'r') as f:
        settings = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_historical_data')
def get_historical_data():
    return jsonify(historical_data)

@app.route('/get_current_data')
def get_current_data():
    return jsonify(latency_data)

@app.route('/get_settings')
def get_settings():
    return jsonify(settings)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    global settings
    settings = request.json
    
    # Save to file
    with open("settings.json", 'w') as f:
        json.dump(settings, f, indent=4)
    
    return jsonify({"status": "success", "message": "Settings saved successfully"})

@app.route('/clear_data', methods=['POST'])
def clear_data():
    global latency_data
    latency_data = {}
    return jsonify({"status": "success", "message": "Data cleared"})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    global historical_data
    historical_data = []
    return jsonify({"status": "success", "message": "History cleared"})

@app.route('/export_data/<format>')
def export_data(format):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'csv':
        import csv
        filename = f"latency_data_{timestamp}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["IP", "Average Latency (ms)", "Min Latency (ms)", "Max Latency (ms)", "Packet Loss (%)"])
            
            for ip, data in latency_data.items():
                writer.writerow([
                    ip,
                    f"{data['avg']:.2f}",
                    f"{data['min']:.2f}",
                    f"{data['max']:.2f}",
                    f"{data['packet_loss']:.1f}"
                ])
        
        return send_file(filepath, as_attachment=True)
    
    elif format == 'json':
        filename = f"latency_data_{timestamp}.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w') as jsonfile:
            json.dump(latency_data, jsonfile, indent=4)
        
        return send_file(filepath, as_attachment=True)
    
    return jsonify({"status": "error", "message": "Invalid format"})

@app.route('/export_history/<format>')
def export_history(format):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'csv':
        import csv
        filename = f"latency_history_{timestamp}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "IP", "Average Latency (ms)", "Min Latency (ms)", "Max Latency (ms)", "Packet Loss (%)"])
            
            for entry in historical_data:
                ts = entry["timestamp"]
                for ip, data in entry["data"].items():
                    writer.writerow([
                        ts,
                        ip,
                        f"{data['avg']:.2f}",
                        f"{data['min']:.2f}",
                        f"{data['max']:.2f}",
                        f"{data['packet_loss']:.1f}"
                    ])
        
        return send_file(filepath, as_attachment=True)
    
    elif format == 'json':
        filename = f"latency_history_{timestamp}.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w') as jsonfile:
            json.dump(historical_data, jsonfile, indent=4)
        
        return send_file(filepath, as_attachment=True)
    
    return jsonify({"status": "error", "message": "Invalid format"})

@app.route('/generate_map')
def generate_map():
    if not latency_data:
        return jsonify({"status": "error", "message": "No latency data available. Please run a measurement first."})
    
    try:
        # Create a map centered at a default location (world view)
        m = folium.Map(location=[20, 0], zoom_start=2)
        
        # Create list for heatmap data
        heat_data = []
        
        # Location mapping for common IPs
        location_map = {
            "8.8.8.8": ("Mountain View, CA, USA", 37.4056, -122.0775),
            "8.8.4.4": ("Mountain View, CA, USA", 37.4056, -122.0775),
            "1.1.1.1": ("San Francisco, CA, USA", 37.7749, -122.4194),
            "1.0.0.1": ("San Francisco, CA, USA", 37.7749, -122.4194),
            "208.67.222.222": ("San Francisco, CA, USA", 37.7749, -122.4194),
            "208.67.220.220": ("San Francisco, CA, USA", 37.7749, -122.4194),
        }
        
        # Process each IP address
        for ip in latency_data.keys():
            try:
                if ip in location_map:
                    loc_name, lat, lon = location_map[ip]
                else:
                    # Try to get hostname
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                        loc_name = hostname
                    except:
                        loc_name = ip
                    
                    # Default coordinates (can be enhanced with IP geolocation API)
                    lat, lon = 0, 0
                
                if lat != 0 or lon != 0:  # Only add if we have valid coordinates
                    # Get actual measured latency data
                    data = latency_data[ip]
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
                        [lat, lon],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=f"{ip} - {avg_latency:.2f} ms",
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(m)
                    
                    # Add to heatmap data
                    heat_data.append([lat, lon, avg_latency / 10])
            
            except Exception as e:
                print(f"Could not process location for {ip}: {str(e)}")
                continue
        
        # Add heatmap layer if we have data
        if heat_data:
            HeatMap(heat_data, radius=25, blur=35, max_zoom=13).add_to(m)
        
        # Save map to HTML file
        map_file = os.path.join(os.getcwd(), "static", "latency_map.html")
        os.makedirs(os.path.dirname(map_file), exist_ok=True)
        m.save(map_file)
        
        return jsonify({"status": "success", "message": "Map generated successfully", "map_url": "/static/latency_map.html"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error generating map: {str(e)}"})

@app.route('/traceroute/<destination>')
def trace_route(destination):
    """Perform traceroute to destination"""
    try:
        if not has_admin:
            return jsonify({
                "status": "error",
                "message": "Traceroute requires administrator privileges"
            })
        
        hops = traceroute(destination)
        return jsonify({
            "status": "success",
            "destination": destination,
            "hops": hops
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Traceroute failed: {str(e)}"
        })

@app.route('/network_info/<ip>')
def network_info(ip):
    """Get detailed network information about an IP"""
    try:
        info = get_network_info(ip)
        return jsonify({
            "status": "success",
            "info": info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get network info: {str(e)}"
        })

@app.route('/bandwidth_test')
def bandwidth_test():
    """Simple bandwidth estimation based on latency measurements"""
    if not latency_data:
        return jsonify({"status": "error", "message": "No latency data available"})
    
    results = {}
    for ip, data in latency_data.items():
        results[ip] = {
            "estimated_bandwidth_mbps": data.get('throughput_estimate', 0),
            "avg_latency_ms": data['avg'],
            "jitter_ms": data.get('jitter', 0)
        }
    
    return jsonify({
        "status": "success",
        "results": results
    })

@socketio.on('start_measurement')
def handle_measurement(data):
    global latency_data, historical_data
    
    ip_addresses = [ip.strip() for ip in data['ip_addresses'].split(',')]
    num_pings = int(data['num_pings'])
    
    latency_data = {}
    total_pings = len(ip_addresses) * num_pings
    current_ping = 0
    
    try:
        # Measure latency for each IP
        for ip in ip_addresses:
            emit('progress', {
                'status': f'Testing {ip}...',
                'progress': (current_ping / total_pings) * 100
            })
            
            latencies = []
            for j in range(num_pings):
                current_ping += 1
                
                try:
                    if has_admin:
                        # Use ICMP ping (requires admin)
                        packet = scapy.IP(dst=ip)/scapy.ICMP()
                        start_time = time.time()
                        reply = scapy.sr1(packet, timeout=2, verbose=0, retry=0)
                        end_time = time.time()
                        
                        if reply:
                            latency = (end_time - start_time) * 1000
                            latencies.append(latency)
                        else:
                            latencies.append(None)
                    else:
                        # Fallback to TCP ping (doesn't require admin)
                        # Try port 80 first, then 443 if that fails
                        latency = tcp_ping(ip, port=80, timeout=2)
                        if latency is None:
                            latency = tcp_ping(ip, port=443, timeout=2)
                        latencies.append(latency)
                
                except Exception as e:
                    print(f"Error pinging {ip}: {str(e)}")
                    latencies.append(None)
                
                # Send progress update
                emit('progress', {
                    'status': f'Testing {ip}... ({j+1}/{num_pings})',
                    'progress': (current_ping / total_pings) * 100
                })
                
                time.sleep(0.1)  # Reduced delay
            
            # Calculate statistics (including networking concepts)
            valid_latencies = [lat for lat in latencies if lat is not None]
            avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else 0
            min_latency = min(valid_latencies) if valid_latencies else 0
            max_latency = max(valid_latencies) if valid_latencies else 0
            packet_loss = (1 - len(valid_latencies)/num_pings) * 100 if num_pings > 0 else 100
            
            # Advanced networking metrics
            jitter = calculate_jitter(valid_latencies)
            throughput_estimate = calculate_throughput_estimate(avg_latency)
            
            # Calculate RTT statistics
            if valid_latencies:
                import statistics
                std_dev = statistics.stdev(valid_latencies) if len(valid_latencies) > 1 else 0
            else:
                std_dev = 0
            
            latency_data[ip] = {
                "latencies": latencies,
                "avg": avg_latency,
                "min": min_latency,
                "max": max_latency,
                "packet_loss": packet_loss,
                "jitter": jitter,  # Network jitter
                "std_dev": std_dev,  # Standard deviation
                "throughput_estimate": throughput_estimate,  # Estimated bandwidth (Mbps)
                "protocol": "ICMP" if has_admin else "TCP"  # Protocol used
            }
        
        # Add to historical data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        historical_data.append({
            "timestamp": timestamp,
            "data": latency_data.copy()
        })
        
        # Send completion message
        emit('measurement_complete', {
            'status': 'success',
            'data': latency_data
        })
        
    except Exception as e:
        print(f"Measurement error: {str(e)}")
        emit('measurement_complete', {
            'status': 'error',
            'message': f'Error during measurement: {str(e)}',
            'data': latency_data
        })

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
