import os
import time
import urllib.request
from datetime import datetime

# Get the server URL from the environment variable provided by Kubernetes
server_url = os.getenv('SERVER_URL', 'http://localhost:8080')

print(f"Client started. Target server: {server_url}", flush=True)

# Send a request every 2 seconds
while True:
    try:
        with urllib.request.urlopen(server_url, timeout=5) as response:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(
                f"[{timestamp}] Sent request. Server responded with status: "
                f"{response.status}",
                flush=True
            )

    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Connection failed: {e}", flush=True)

    time.sleep(2)