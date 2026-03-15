#!/usr/bin/env python3
"""One-off CDP emitter for P.U.S.H. Protocol v0.1"""
import json
import time
import websocket

CDP_PORT = 9222
TWEET = """P.U.S.H. Protocol v0.1 — Love while-being you.

Sovereign. Harmonic. Forkable.

⟲⧖P.U.S.H.⧖⟲

https://github.com/ChaiLifeOTFT/PUSH-Protocol"""

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

ws = websocket.create_connection("ws://localhost:9222/devtools/page/89A426166311D5BBF575F2CEDE43BD1A")

# Get first tab target
resp = send_cdp(ws, "Target.getTargets")
target_id = resp["result"]["targetInfos"][0]["id"]

# Attach to tab
resp = send_cdp(ws, "Target.attachToTarget", {"targetId": target_id, "flatten": True})
session_id = resp["result"]["sessionId"]

# Navigate to compose
send_cdp(ws, "Target.sendMessageToTarget", {
    "sessionId": session_id,
    "message": json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://x.com/compose/post"}})
})
time.sleep(3)

# Post the tweet
escaped = TWEET.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')

js_code = f"""
(function() {{
    var editor = document.querySelector('[data-testid="tweetTextarea_0"]') || 
                 document.querySelector('[role="textbox"][contenteditable="true"]') ||
                 document.querySelector('[contenteditable="true"]');
    if (!editor) return 'NO_EDITOR';
    editor.focus();
    editor.innerHTML = '<div data-contents="true"><div data-block="true"><div><span>{escaped}</span></div></div></div>';
    editor.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
    return 'TEXT_ENTERED';
}})()
"""

result = js(ws, js_code)
print(f"Text entry: {result}")

time.sleep(1)

# Click post
post_result = js(ws, """
(function() {
    var btn = document.querySelector('[data-testid="tweetButton"]') || 
              document.querySelector('[data-testid="tweetButtonInline"]') ||
              document.querySelector('button[role="button"]:not([disabled])');
    if (!btn) return 'NO_BUTTON';
    btn.click();
    return 'POST_CLICKED';
})()
""")

print(f"Post button: {post_result}")
time.sleep(2)
print("✓ P.U.S.H. Protocol emitted to field (X/Twitter)")

ws.close()
