#!/usr/bin/env python3
"""
High-Availability AWS Auto Scaling Web Application
Exposes instance telemetry via IMDSv2, health check endpoint for ALB,
and CPU load generator to trigger CloudWatch Auto Scaling alarms.
"""

import os
import time
import socket
import threading
import psutil
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
request_count = 0
stress_active = False

def get_ec2_metadata():
    """Retrieve EC2 instance metadata securely using IMDSv2."""
    metadata = {
        "instance_id": "local-dev-instance",
        "availability_zone": "local-az",
        "private_ip": socket.gethostbyname(socket.gethostname()),
        "architecture": os.uname().machine if hasattr(os, "uname") else "x86_64",
        "is_ec2": False
    }
    
    try:
        # Step 1: Obtain IMDSv2 session token (TTL 60s)
        token_res = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
            timeout=1
        )
        if token_res.status_code == 200:
            token = token_res.text
            headers = {"X-aws-ec2-metadata-token": token}
            
            # Step 2: Fetch instance id and availability zone
            iid_res = requests.get("http://169.254.169.254/latest/meta-data/instance-id", headers=headers, timeout=1)
            az_res = requests.get("http://169.254.169.254/latest/meta-data/placement/availability-zone", headers=headers, timeout=1)
            ip_res = requests.get("http://169.254.169.254/latest/meta-data/local-ipv4", headers=headers, timeout=1)
            
            if iid_res.status_code == 200:
                metadata["instance_id"] = iid_res.text
                metadata["is_ec2"] = True
            if az_res.status_code == 200:
                metadata["availability_zone"] = az_res.text
            if ip_res.status_code == 200:
                metadata["private_ip"] = ip_res.text
    except Exception:
        # Fallback when running outside EC2 environment
        pass
        
    return metadata

@app.route("/")
def home():
    global request_count
    request_count += 1
    
    meta = get_ec2_metadata()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory_info = psutil.virtual_memory()
    
    return render_template(
        "index.html",
        metadata=meta,
        cpu_percent=cpu_percent,
        memory_percent=memory_info.percent,
        request_count=request_count,
        stress_active=stress_active
    )

@app.route("/health")
def health():
    """Application Load Balancer health check endpoint."""
    return jsonify({
        "status": "healthy",
        "uptime": time.time(),
        "instance_id": get_ec2_metadata().get("instance_id")
    }), 200

def cpu_burner(duration_seconds):
    global stress_active
    stress_active = True
    stop_time = time.time() + duration_seconds
    while time.time() < stop_time:
        _ = 999999 * 999999
    stress_active = False

@app.route("/stress", methods=["POST", "GET"])
def trigger_stress():
    """Triggers CPU load to validate CloudWatch Alarms & Auto Scaling scale-out."""
    global stress_active
    duration = int(request.args.get("duration", 60))
    threads_count = int(request.args.get("threads", psutil.cpu_count() or 2))
    
    if not stress_active:
        for _ in range(threads_count):
            t = threading.Thread(target=cpu_burner, args=(duration,))
            t.daemon = True
            t.start()
        msg = f"Started CPU stress test across {threads_count} threads for {duration} seconds."
    else:
        msg = "Stress test is already active on this instance."
        
    return jsonify({
        "message": msg,
        "stress_active": True,
        "duration": duration,
        "instance_id": get_ec2_metadata().get("instance_id")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
