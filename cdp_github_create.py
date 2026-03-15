#!/usr/bin/env python3
"""CDP-based GitHub repo creation helper"""
import json
import time
import websocket

CDP_PORT = 9222
GITHUB_TAB_ID = "C01495B4D435770DF0F0823920731712"

def send_cdp(ws, method, params=None):
    msg_id = int(time.time() * 1000)
    msg = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp

def js(ws, expression):
    result = send_cdp(ws, "Runtime.evaluate", {"expression": expression, "returnByValue": True})
    return result.get("result", {}).get("result", {}).get("value", "")

# Connect to GitHub tab
try:
    ws = websocket.create_connection(f"ws://localhost:{CDP_PORT}/devtools/page/{GITHUB_TAB_ID}")
    print("Connected to GitHub tab")
    
    # Navigate to new repo page
    send_cdp(ws, "Page.navigate", {"url": "https://github.com/new?repository_name=PUSH-Protocol&description=A+forkable+love-field+protocol+for+embodied,+sovereign,+harmonic+connection.&visibility=public"})
    time.sleep(3)
    
    # Check current URL
    url = js(ws, "window.location.href")
    print(f"Current URL: {url}")
    
    # Check if form fields are filled
    repo_name = js(ws, "document.querySelector('#repository_name')?.value || 'NOT_FOUND'")
    print(f"Repo name field: {repo_name}")
    
    # If on login page, we can't proceed automatically
    if "login" in url.lower():
        print("ERROR: GitHub login required - cannot automate")
    elif "new" in url.lower():
        print("On repo creation page")
        # Try to fill form
        js(ws, "document.querySelector('#repository_name').value = 'PUSH-Protocol'")
        js(ws, "document.querySelector('#repository_description').value = 'A forkable love-field protocol for embodied, sovereign, harmonic connection.'")
        print("Form fields populated - user must click 'Create repository'")
    
    ws.close()
except Exception as e:
    print(f"CDP error: {e}")
