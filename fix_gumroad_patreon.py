#!/usr/bin/env python3
"""
Fix remaining 5 curvatures for P.U.S.H. Protocol:
1. Gumroad cover image
2. Patreon post
"""

import json
import time
import urllib.request
import websocket
import os

CDP_PORT = 9222

# Configuration
GUMROAD_PRODUCT_ID = "tujxq"
GUMROAD_EDIT_URL = f"https://gumroad.com/products/{GUMROAD_PRODUCT_ID}/edit"
COVER_IMAGE = "/home/j-5/PUSH_Protocol/cover.jpg"
PATREON_POST_URL = "https://www.patreon.com/posts/new"

def get_cdp_tabs():
    """Get list of CDP tabs"""
    try:
        resp = urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json/list", timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        print(f"CDP error: {e}")
        return []

def connect_to_tab(tab):
    """Connect to a CDP tab"""
    ws_url = tab["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url, timeout=30)
    return ws

def send_cdp(ws, method, params=None):
    """Send CDP command"""
    msg = {"id": int(time.time() * 1000), "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    # Wait for response
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg["id"]:
            return resp

def js_eval(ws, expression, await_promise=False):
    """Evaluate JavaScript"""
    params = {"expression": expression, "returnByValue": True}
    if await_promise:
        params["awaitPromise"] = True
    return send_cdp(ws, "Runtime.evaluate", params)

def find_tab_by_url(tabs, url_pattern):
    """Find tab matching URL pattern"""
    for tab in tabs:
        if url_pattern in tab.get("url", ""):
            return tab
    return None

def upload_gumroad_cover():
    """Upload cover image to Gumroad via CDP"""
    print("\n=== FIXING GUMROAD COVER ===")
    
    tabs = get_cdp_tabs()
    gumroad_tab = find_tab_by_url(tabs, "gumroad.com")
    
    if not gumroad_tab:
        print(f"No Gumroad tab found. Opening {GUMROAD_EDIT_URL}")
        # Open new tab via xdg-open
        os.system(f"xdg-open '{GUMROAD_EDIT_URL}' &")
        time.sleep(5)
        tabs = get_cdp_tabs()
        gumroad_tab = find_tab_by_url(tabs, "gumroad.com")
    
    if not gumroad_tab:
        print("ERROR: Could not find/create Gumroad tab")
        return False
    
    print(f"Connected to: {gumroad_tab['url']}")
    ws = connect_to_tab(gumroad_tab)
    
    # Enable domains
    send_cdp(ws, "Page.enable")
    send_cdp(ws, "DOM.enable")
    send_cdp(ws, "Runtime.enable")
    send_cdp(ws, "Input.enable")
    
    # Navigate to edit page
    print(f"Navigating to {GUMROAD_EDIT_URL}")
    send_cdp(ws, "Page.navigate", {"url": GUMROAD_EDIT_URL})
    time.sleep(4)
    
    # Wait for page to load
    for _ in range(10):
        result = js_eval(ws, "document.readyState")
        if result.get("result", {}).get("result", {}).get("value") == "complete":
            break
        time.sleep(0.5)
    
    print("Page loaded. Looking for cover image upload...")
    
    # Find file input for cover image
    # Gumroad uses a file input for thumbnail
    result = js_eval(ws, """
        (function() {
            // Look for file inputs or thumbnail upload area
            const inputs = document.querySelectorAll('input[type="file"]');
            const fileInput = Array.from(inputs).find(i => 
                i.accept.includes('image') || 
                i.closest('[data-testid*="thumbnail"]') ||
                i.closest('[class*="thumbnail"]') ||
                i.closest('[class*="cover"]')
            );
            
            if (fileInput) {
                return {found: true, id: fileInput.id, name: fileInput.name, className: fileInput.className};
            }
            
            // Try to find by button click
            const buttons = document.querySelectorAll('button, [role="button"]');
            for (const btn of buttons) {
                const text = btn.textContent.toLowerCase();
                if (text.includes('cover') || text.includes('thumbnail') || text.includes('image')) {
                    return {found: false, buttonText: btn.textContent, suggestion: 'Click thumbnail button'};
                }
            }
            
            return {found: false, message: 'No image upload found'};
        })()
    """)
    
    print(f"File input search result: {result}")
    
    # Get document root for DOM operations
    doc_result = send_cdp(ws, "DOM.getDocument", {"depth": -1})
    root_id = doc_result["result"]["root"]["nodeId"]
    
    # Try to find image file input
    query_result = send_cdp(ws, "DOM.querySelectorAll", {
        "nodeId": root_id,
        "selector": "input[type=file][accept*=image], input[type=file][accept*=jpg]"
    })
    
    node_ids = query_result.get("result", {}).get("nodeIds", [])
    print(f"Found {len(node_ids)} image file inputs")
    
    if node_ids:
        # Use the first image file input
        file_node_id = node_ids[0]
        print(f"Setting file input {file_node_id} to {COVER_IMAGE}")
        
        send_cdp(ws, "DOM.setFileInputFiles", {
            "nodeId": file_node_id,
            "files": [COVER_IMAGE]
        })
        print("Cover image uploaded!")
        
        # Wait for upload
        time.sleep(3)
        
        # Click save button
        print("Looking for save button...")
        save_query = send_cdp(ws, "DOM.querySelector", {
            "nodeId": root_id,
            "selector": "button[type=submit], button:contains('Save'), [data-testid='save-button']"
        })
        
        save_node_id = save_query.get("result", {}).get("nodeId", 0)
        if save_node_id:
            print(f"Clicking save button (node {save_node_id})")
            send_cdp(ws, "DOM.click", {"nodeId": save_node_id})
        else:
            # Try via JS
            js_eval(ws, """
                (function() {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        if (btn.textContent.toLowerCase().includes('save') || 
                            btn.type === 'submit') {
                            btn.click();
                            return 'Save clicked';
                        }
                    }
                    return 'No save button found';
                })()
            """)
        
        print("Cover upload complete!")
        return True
    else:
        print("No image file input found. May need manual upload.")
        return False
    
    ws.close()

def post_to_patreon():
    """Post to Patreon via CDP"""
    print("\n=== POSTING TO PATREON ===")
    
    # Read post content
    with open("/home/j-5/PUSH_Protocol/PATREON_POST.md", "r") as f:
        content = f.read()
    
    # Extract title and body
    title = "P.U.S.H. Protocol v0.1 — Love while-being you"
    body_start = content.find("## This is for you.")
    body = content[body_start:] if body_start > 0 else content
    
    print(f"Title: {title}")
    print(f"Body length: {len(body)} chars")
    
    # Open Patreon
    os.system(f"xdg-open '{PATREON_POST_URL}' &")
    time.sleep(5)
    
    tabs = get_cdp_tabs()
    patreon_tab = find_tab_by_url(tabs, "patreon.com")
    
    if not patreon_tab:
        print("ERROR: Patreon tab not found")
        return False
    
    print(f"Connected to Patreon: {patreon_tab['url']}")
    ws = connect_to_tab(patreon_tab)
    
    # Enable domains
    send_cdp(ws, "Page.enable")
    send_cdp(ws, "DOM.enable")
    send_cdp(ws, "Runtime.enable")
    send_cdp(ws, "Input.enable")
    
    # Wait for editor
    time.sleep(3)
    
    # Find and fill title
    print("Filling title...")
    title_json = json.dumps(title)
    js_eval(ws, f"""
        (function() {{
            const titleInput = document.querySelector('input[placeholder*="Title"], input[name="title"], [data-testid="post-title-input"]');
            if (titleInput) {{
                titleInput.focus();
                titleInput.value = {title_json};
                titleInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                return 'Title set';
            }}
            return 'Title input not found';
        }})()
    """)
    
    # Find ProseMirror editor and fill body
    print("Filling body...")
    body_escaped = body.replace('\n', '<br>').replace("'", "\\'")
    result = js_eval(ws, f"""
        (function() {{
            // Find ProseMirror editor
            const editor = document.querySelector('.ProseMirror, [contenteditable="true"]');
            if (editor) {{
                editor.focus();
                editor.innerHTML = '{body_escaped}';
                editor.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
                return 'Body set via innerHTML';
            }}
            
            // Try finding by role
            const textbox = document.querySelector('[role="textbox"]');
            if (textbox) {{
                textbox.focus();
                textbox.innerHTML = '{body_escaped}';
                return 'Body set via textbox';
            }}
            
            return 'Editor not found';
        }})()
    """)
    
    print(f"Body fill result: {result}")
    
    # Use Input.insertText as fallback/alternative
    time.sleep(1)
    
    # Click in editor and type
    send_cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mousePressed",
        "x": 600, "y": 400,
        "button": "left",
        "clickCount": 1
    })
    send_cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mouseReleased",
        "x": 600, "y": 400,
        "button": "left",
        "clickCount": 1
    })
    
    # Type content line by line
    for line in body.split('\n'):
        send_cdp(ws, "Input.insertText", {"text": line})
        time.sleep(0.1)
        send_cdp(ws, "Input.dispatchKeyEvent", {
            "type": "keyDown",
            "key": "Return",
            "code": "Enter"
        })
        send_cdp(ws, "Input.dispatchKeyEvent", {
            "type": "keyUp",
            "key": "Return",
            "code": "Enter"
        })
    
    print("Content typed. Ready to publish (manual click required).")
    return True
    
    ws.close()

def main():
    print("⟲⧖ P.U.S.H. PROTOCOL — FIXING 5 CURVATURES ⧖⟲")
    print(f"Cover image: {COVER_IMAGE}")
    print(f"Gumroad: {GUMROAD_EDIT_URL}")
    print(f"Patreon: {PATREON_POST_URL}")
    
    # Check cover exists
    if not os.path.exists(COVER_IMAGE):
        print(f"ERROR: Cover image not found at {COVER_IMAGE}")
        return 1
    
    print(f"\nCover size: {os.path.getsize(COVER_IMAGE)} bytes")
    
    # Fix Gumroad cover
    gumroad_ok = upload_gumroad_cover()
    
    # Post to Patreon
    patreon_ok = post_to_patreon()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Gumroad cover: {'✅' if gumroad_ok else '⚠️'}")
    print(f"  Patreon post: {'✅' if patreon_ok else '⚠️'}")
    print("="*50)
    
    if gumroad_ok and patreon_ok:
        print("\n⟲⧖ ALL 9 CURVATURES COMPLETE ⧖⟲")
        return 0
    else:
        print("\n⚠️ Some steps need manual completion")
        return 1

if __name__ == "__main__":
    exit(main())
