# Network Latency Measurement Tool - Web Version

A modern web-based network latency measurement tool with real-time monitoring, visualization, and geographic mapping.

## Features

✨ **Real-time Latency Measurement**
- Measure ping latency to multiple IP addresses simultaneously
- Real-time progress tracking with WebSocket updates
- Color-coded status indicators (Green/Orange/Red)

📊 **Data Visualization**
- Interactive line charts showing latency trends
- Detailed statistics table with min/max/average values
- Packet loss tracking

🗺️ **Geographic Mapping**
- Interactive world map with latency markers
- Heat map visualization
- Color-coded markers based on latency performance

📈 **Historical Data**
- Track measurement history over time
- Export data in CSV or JSON format
- View detailed historical records

⚙️ **Customizable Settings**
- Configure default ping count
- Set ping timeout values
- Customize data storage location

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python app.py
```

3. **Open your browser:**
Navigate to `http://localhost:5000`

## Usage

### Running a Measurement

1. Go to the **Latency Measurement** tab
2. Enter IP addresses (comma-separated), e.g., `8.8.8.8, 1.1.1.1, 208.67.222.222`
3. Set the number of pings (default: 5)
4. Click **Start Measurement**
5. View results in the table and chart

### Viewing Geographic Data

1. First run a latency measurement
2. Go to the **Geographic View** tab
3. Click **Generate Map from Measured Data**
4. View the interactive map with color-coded markers:
   - 🟢 **Green**: Low latency (< 50ms)
   - 🟠 **Orange**: Medium latency (50-100ms)
   - 🔴 **Red**: High latency (> 100ms)

### Exporting Data

- Click **Export CSV** or **Export JSON** to download current measurement data
- Use the **Historical Data** tab to export all historical measurements

### Settings

Configure default values in the **Settings** tab:
- Default number of pings
- Ping timeout (seconds)
- Data storage location

## Technology Stack

- **Backend**: Flask, Flask-SocketIO
- **Frontend**: Bootstrap 5, Chart.js, Socket.IO
- **Network**: Scapy (ICMP ping)
- **Mapping**: Folium (Leaflet.js)

## Important Notes

⚠️ **Administrator/Root Privileges Required**
- Scapy requires elevated privileges to send ICMP packets
- On Windows: Run as Administrator
- On Linux/Mac: Use `sudo python app.py`

📍 **Geographic Data**
- The tool maps actual measured latency from YOUR location to target IPs
- Location data is based on known DNS server locations
- Add custom IP-to-location mappings in `app.py` if needed

🌐 **Network Requirements**
- Outbound ICMP (ping) traffic must be allowed
- Target hosts must respond to ICMP echo requests

## File Structure

```
CN/
├── app.py                          # Flask backend server
├── requirements.txt                # Python dependencies
├── templates/
│   └── index.html                  # Main HTML template
├── static/
│   ├── app.js                      # Frontend JavaScript
│   └── latency_map.html           # Generated map (created dynamically)
└── README.md                       # This file
```

## API Endpoints

- `GET /` - Main application
- `GET /get_historical_data` - Retrieve historical measurements
- `GET /get_current_data` - Get current measurement data
- `GET /get_settings` - Retrieve settings
- `POST /save_settings` - Save settings
- `POST /clear_data` - Clear current data
- `POST /clear_history` - Clear historical data
- `GET /export_data/<format>` - Export data (csv/json)
- `GET /export_history/<format>` - Export history (csv/json)
- `GET /generate_map` - Generate geographic map

## WebSocket Events

- `start_measurement` - Initiate latency measurement
- `progress` - Real-time measurement progress updates
- `measurement_complete` - Measurement finished

## License

MIT License

## Contributing

Feel free to submit issues or pull requests!
