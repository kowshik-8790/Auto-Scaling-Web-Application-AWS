#!/usr/bin/env python3
"""
Stress Testing & Concurrency Generator for AWS ALB & Auto Scaling
Sends concurrent HTTP requests to trigger CloudWatch CPU alarms.
"""

import sys
import time
import threading
import requests

def send_traffic(url, stop_event, stats):
    while not stop_event.is_set():
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200:
                stats["success"] += 1
            else:
                stats["errors"] += 1
        except Exception:
            stats["errors"] += 1
        time.sleep(0.05)

def main():
    if len(sys.argv) < 2:
        print("Usage: python stress_test.py <ALB_URL> [duration_seconds] [concurrency]")
        sys.exit(1)

    alb_url = sys.argv[1].rstrip("/")
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 25

    print(f"==================================================")
    print(f" Launching Concurrency Stress Test on AWS ALB")
    print(f" Target Endpoint:   {alb_url}")
    print(f" Concurrency Level: {concurrency} workers")
    print(f" Test Duration:     {duration} seconds")
    print(f"==================================================")

    # 1. Trigger CPU burner on active nodes
    print("[1/2] Triggering backend CPU burner endpoint...")
    try:
        requests.post(f"{alb_url}/stress?duration={duration}&threads=4", timeout=5)
    except Exception as e:
        print(f"Notice: {e}")

    # 2. Spawn concurrent flood threads
    print("[2/2] Generating concurrent traffic to ALB...")
    stop_event = threading.Event()
    stats = {"success": 0, "errors": 0}
    threads = []

    for _ in range(concurrency):
        t = threading.Thread(target=send_traffic, args=(alb_url, stop_event, stats))
        t.daemon = True
        t.start()
        threads.append(t)

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            reqs = stats["success"] + stats["errors"]
            rps = int(reqs / max(elapsed, 1))
            print(f" Elapsed: {elapsed}s | Requests: {reqs} | RPS: {rps} | Errors: {stats['errors']}", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest manually interrupted by user.")

    stop_event.set()
    for t in threads:
        t.join(timeout=1)

    print(f"\n\nStress test completed! Check CloudWatch Metrics (ASGAverageCPUUtilization) & ASG Activity History.")

if __name__ == "__main__":
    main()
