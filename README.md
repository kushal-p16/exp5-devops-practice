# Experiment 5: Container Orchestration and Scaling with Kubernetes

## Aim

To deploy containerized applications on a Kubernetes cluster, configure
communication between client and server Pods, perform manual scaling,
and observe Kubernetes self-healing.

## 1. Prerequisites

Install and start:

-   Docker Desktop
-   Kubernetes enabled in Docker Desktop
-   `kubectl` command-line tool

Open Docker Desktop and wait until Kubernetes is running.

Verify the cluster:

``` bash
kubectl get nodes
kubectl cluster-info
```

The node should show `Ready`.

## 2. Create the project folders

Create the following folder structure:

``` text
Kubernetes-Experiment/
├── client/
│   ├── client.py
│   └── Dockerfile
├── server/
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
└── Kubernetes-app/
    ├── deployment.yaml
    ├── service.yaml
    └── client_deployment.yaml
```

## 3. Create the server application

Inside the `server` folder, create `server.py`:

``` python
import logging
from flask import Flask, request

app = Flask(__name__)

# Print application logs to the container's standard output.
logging.basicConfig(level=logging.INFO)


@app.route("/")
def hello():
    # Log the IP address of the client making the request.
    app.logger.info(
        f"Received request from client IP: {request.remote_addr}"
    )
    return "Hello from the Kubernetes Server!", 200


if __name__ == "__main__":
    # Listen on all network interfaces inside the container.
    app.run(host="0.0.0.0", port=8080)
```

Create `requirements.txt`:

``` text
flask==3.0.3
```

Create the server `Dockerfile`:

``` dockerfile
FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

CMD ["python", "server.py"]
```

## 4. Create the client application

Inside the `client` folder, create `client.py`:

``` python
import os
import time
import urllib.request
from datetime import datetime

# Read the server URL from the environment variable.
server_url = os.getenv("SERVER_URL", "http://localhost:8080")

print(f"Client started. Target server: {server_url}", flush=True)

# Send a request every two seconds.
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
```

Create the client `Dockerfile`:

``` dockerfile
FROM python:3.11-alpine

WORKDIR /app

COPY client.py .

CMD ["python", "client.py"]
```

## 5. Build the Docker images

Open a terminal in the `server` folder and build the server image:

``` bash
docker build -t my-server:latest .
```

Open a terminal in the `client` folder and build the client image:

``` bash
docker build -t my-client:latest .
```

Verify that both images exist:

``` bash
docker images
```

Confirm that `my-server:latest` and `my-client:latest` are listed. With
Docker Desktop Kubernetes, locally built images can be used when they
are available to the Kubernetes cluster and the manifests use the
matching image names.

## 6. Create the Kubernetes server Deployment

Inside `Kubernetes-app`, create `deployment.yaml`:

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: server-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: html-app
  template:
    metadata:
      labels:
        app: html-app
    spec:
      containers:
        - name: html-container
          image: my-server:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
```

This Deployment maintains two server Pods.

## 7. Create the Kubernetes Service

Create `service.yaml` in the same folder:

``` yaml
apiVersion: v1
kind: Service
metadata:
  name: html-service
spec:
  selector:
    app: html-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: NodePort
```

The Service selects Pods labelled `app: html-app`.

-   `port: 80` is the port exposed by the Service inside the cluster.
-   `targetPort: 8080` is the port on which the server application
    listens.
-   `type: NodePort` makes the Service available through a port on the
    Kubernetes node.

## 8. Create the client Deployment

Create `client_deployment.yaml`:

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-client
  template:
    metadata:
      labels:
        app: my-client
    spec:
      containers:
        - name: client
          image: my-client:latest
          imagePullPolicy: IfNotPresent
          env:
            - name: SERVER_URL
              value: "http://html-service:80"
```

The client uses the Kubernetes Service DNS name `html-service` and
connects to Service port `80`.

**Replica count:** `replicas: 1` creates one client Pod. To run multiple
client instances, change this value to the required number (for example,
`5`) before applying the manifest.

## 9. Apply the Kubernetes manifests

Open CMD or PowerShell in the `Kubernetes-app` folder and run:

``` bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f client_deployment.yaml
```

Check the deployments, Pods, and Service:

``` bash
kubectl get deployments
kubectl get pods
kubectl get services
```

Wait until the server Pods and client Pod show `Running`. The
Deployments should become `Available` or show the desired number of
ready replicas.

## 10. Verify client-server communication

Get the client Pod name:

``` bash
kubectl get pods
```

View the client logs:

``` bash
kubectl logs -f <client-pod-name>
```

Expected client output includes:

``` text
Client started. Target server: http://html-service:80
Sent request. Server responded with status: 200
Sent request. Server responded with status: 200
```

View the logs of a server Pod:

``` bash
kubectl logs -f <server-pod-name>
```

The server logs should show requests received from client Pod IP
addresses. HTTP status `200` indicates that the request was successful.

Press `Ctrl+C` to stop following the logs. This does not stop the Pods.

## 11. Access the application (optional)

Forward local port `8081` to Service port `80`:

``` bash
kubectl port-forward service/html-service 8081:80
```

Open this address in a browser:

``` text
http://localhost:8081
```

Expected response:

``` text
Hello from the Kubernetes Server!
```

Keep the port-forward terminal open while accessing the application.

## 12. Manual scaling

Scale the server Deployment from two Pods to five:

``` bash
kubectl scale deployment server-deployment --replicas=5
kubectl get pods
```

The Deployment should create additional server Pods.

Scale it back to two:

``` bash
kubectl scale deployment server-deployment --replicas=2
kubectl get pods
```

Kubernetes adjusts the number of Pods to match the requested replica
count.

> If you are following the first HTML application exercise instead of
> the client-server exercise, use its Deployment name `html-app` in the
> scale commands. Do not mix the two Deployment names.

## 13. Pod deletion and self-healing

List the Pods:

``` bash
kubectl get pods
```

Delete one server Pod by using its actual Pod name:

``` bash
kubectl delete pod <pod-name>
```

Watch the Pods:

``` bash
kubectl get pods -w
```

The Deployment controller should create a replacement Pod to maintain
the desired replica count. Press `Ctrl+C` to stop watching.

**Observation:** Deleting a Pod managed by a Deployment does not
permanently reduce the desired replica count. Kubernetes creates a
replacement Pod.

## 14. Remove the application

Delete the client Deployment, server Deployment, and Service:

``` bash
kubectl delete deployment client-deployment
kubectl delete deployment server-deployment
kubectl delete service html-service
```

Check that the resources have been removed:

``` bash
kubectl get deployments
kubectl get pods
kubectl get services
```

## 15. Re-create and run the application

If you deleted the Kubernetes resources and want to run the experiment
again:

1.  Confirm both Docker images are available:

    ``` bash
    docker images
    ```

2.  If an image is missing, rebuild it from its own folder:

    ``` bash
    # Run inside the server folder
    docker build -t my-server:latest .

    # Run inside the client folder
    docker build -t my-client:latest .
    ```

3.  Open a terminal in `Kubernetes-app`.

4.  Apply the manifests again:

    ``` bash
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
    kubectl apply -f client_deployment.yaml
    ```

5.  Verify the resources:

    ``` bash
    kubectl get deployments
    kubectl get pods
    kubectl get services
    ```

6.  Check client and server communication:

    ``` bash
    kubectl logs -f <client-pod-name>
    ```

## 16. Troubleshooting

### A Pod remains in `Pending`

Describe the Pod and inspect the Events section:

``` bash
kubectl describe pod <pod-name>
```

### A Pod shows `ImagePullBackOff` or `ErrImagePull`

Check the image names:

``` bash
docker images
```

Make sure the image name in the YAML matches the locally built image and
that the image is available to Docker Desktop Kubernetes.

### Client logs show connection failures

Check that the server Pods are running and that the Service exists:

``` bash
kubectl get pods
kubectl get services
kubectl describe service html-service
```

Confirm that the client Deployment contains:

``` yaml
env:
  - name: SERVER_URL
    value: "http://html-service:80"
```

The client must use Service port `80`, not the server container's `8080`
port. The Service forwards traffic from port `80` to target port `8080`.

## 17. Result

The server and client container images were created and deployed on
Kubernetes. The client communicated with the server through a Kubernetes
Service and received successful HTTP responses. Manual scaling and Pod
self-healing were demonstrated using Kubernetes Deployments.
