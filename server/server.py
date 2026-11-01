import logging
from flask import Flask, request

app = Flask(__name__)

# Configure logging to print directly to stdout for Kubernetes logs
logging.basicConfig(level=logging.INFO)


@app.route("/")
def hello():
    # Logs the client's internal IP address
    app.logger.info(
        f"Received request from client IP: {request.remote_addr}"
    )
    return "Hello from the Kubernetes Server!", 200


if __name__ == "__main__":
    # Listen on all interfaces (0.0.0.0) inside the container on port 8080
    app.run(host="0.0.0.0", port=8080)