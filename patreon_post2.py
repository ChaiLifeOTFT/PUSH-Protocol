#!/usr/bin/env python3
"""
CDP Automation: Create and publish a Patreon post for P.U.S.H. Protocol v0.1
Uses Chrome DevTools Protocol on port 9222 (Brave browser).
All interaction via CDP Input events — no DOM manipulation for clicks/typing.
"""

import json
import time
import requests
import websocket

CDP_HOST = "http://localhost:9222"
MSG_ID = 1

def send_cdp(ws, method, params=None):
    global MSG_ID
    msg = {"id": MSG_ID, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    MSG_ID += 1
    # Set a timeout to avoid hanging forever
    ws.settimeout(15)
    while True:
        try:
            resp = json.loads(ws.recv())
        except websocket.WebSocketTimeoutException:
            print(f"  TIMEOUT waiting for response to {method}")
            return {"error": "timeout"}
        if resp.get("id") == MSG_ID - 1:
            if "error" in resp:
                print(f"  CDP ERROR [{method}]: {resp['error']}")
            return resp
        # skip events

def evaluate(ws, expression, await_promise=False):
    params = {"expression": expression, "returnByValue": True}
    if await_promise:
        params["awaitPromise"] = True
    return send_cdp(ws, "Runtime.evaluate", params)

def click_at(ws, x, y):
    """Click at coordinates using CDP Input events."""
    send_cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": x, "y": y,
        "button": "left", "clickCount": 1
    })
    time.sleep(0.05)
    send_cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": x, "y": y,
        "button": "left", "clickCount": 1
    })

def type_text(ws, text):
    """Type text using Input.insertText (works on contenteditable/ProseMirror)."""
    send_cdp(ws, "Input.insertText", {"text": text})

def press_key(ws, key, code=None, key_code=None):
    """Press a key using Input.dispatchKeyEvent."""
    params = {"type": "keyDown", "key": key}
    if code:
        params["code"] = code
    if key_code:
        params["windowsVirtualKeyCode"] = key_code
        params["nativeVirtualKeyCode"] = key_code
    send_cdp(ws, "Input.dispatchKeyEvent", params)
    time.sleep(0.02)
    params2 = dict(params)
    params2["type"] = "keyUp"
    send_cdp(ws, "Input.dispatchKeyEvent", params2)


def main():
    # Connect to the already-created Patreon tab
    print("[1] Connecting to Patreon tab...")

    TARGET_ID = "26F05A51B9FA3F2C934433906A8FBE6C"
    ws_url = f"ws://localhost:9222/devtools/page/{TARGET_ID}"

    ws = websocket.create_connection(ws_url)
    send_cdp(ws, "Runtime.enable")

    # Step 2: Wait for the editor to fully render
    print("[2] Waiting for Patreon editor to load (10s)...")
    time.sleep(10)

    # Check if page loaded
    result = evaluate(ws, "document.title")
    title = result.get("result", {}).get("result", {}).get("value", "")
    print(f"  Page title: {title}")

    result = evaluate(ws, "window.location.href")
    url = result.get("result", {}).get("result", {}).get("value", "")
    print(f"  URL: {url}")

    # Step 3: Find the ProseMirror editor
    print("[3] Looking for ProseMirror editor...")

    editor_found = False
    for attempt in range(15):
        result = evaluate(ws, """
            (() => {
                // Try ProseMirror first
                const pm = document.querySelector('div.ProseMirror[contenteditable="true"]');
                if (pm) {
                    const rect = pm.getBoundingClientRect();
                    return JSON.stringify({
                        found: true,
                        selector: 'ProseMirror',
                        className: pm.className.substring(0, 80),
                        x: rect.x + rect.width/2,
                        y: rect.y + rect.height/2,
                        width: rect.width,
                        height: rect.height
                    });
                }
                // Try remirror
                const rm = document.querySelector('.remirror-editor[contenteditable="true"]');
                if (rm) {
                    const rect = rm.getBoundingClientRect();
                    return JSON.stringify({
                        found: true,
                        selector: 'remirror',
                        className: rm.className.substring(0, 80),
                        x: rect.x + rect.width/2,
                        y: rect.y + rect.height/2,
                        width: rect.width,
                        height: rect.height
                    });
                }
                // Try any contenteditable
                const ce = document.querySelector('[contenteditable="true"]');
                if (ce) {
                    const rect = ce.getBoundingClientRect();
                    return JSON.stringify({
                        found: true,
                        selector: 'contenteditable',
                        className: (ce.className || '').substring(0, 80),
                        x: rect.x + rect.width/2,
                        y: rect.y + rect.height/2,
                        width: rect.width,
                        height: rect.height
                    });
                }
                // Report what we see
                const bodyLen = document.body?.innerHTML?.length || 0;
                return JSON.stringify({found: false, bodyLen: bodyLen});
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "{}")
        info = json.loads(val)
        if info.get("found"):
            print(f"  Editor found via '{info['selector']}' (class: {info.get('className','')}) at ({info['x']:.0f}, {info['y']:.0f}), size {info['width']:.0f}x{info['height']:.0f}")
            editor_found = True
            editor_x = info["x"]
            editor_y = info["y"]
            break
        else:
            print(f"  Attempt {attempt+1}: Editor not found. Body length: {info.get('bodyLen', '?')}")
            time.sleep(2)

    if not editor_found:
        # Debug: dump all interactive elements
        result = evaluate(ws, """
            (() => {
                const all = document.querySelectorAll('[contenteditable], textarea, [role="textbox"], [data-placeholder]');
                const results = [];
                all.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    results.push({
                        tag: el.tagName,
                        cls: (el.className || '').substring(0, 60),
                        ce: el.contentEditable,
                        ph: el.getAttribute('data-placeholder') || el.placeholder || '',
                        x: Math.round(rect.x + rect.width/2),
                        y: Math.round(rect.y + rect.height/2),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height)
                    });
                });
                return JSON.stringify(results);
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "[]")
        elements = json.loads(val)
        print(f"  DEBUG: Found {len(elements)} editable elements:")
        for el in elements:
            print(f"    <{el['tag']}> class='{el['cls']}' ce={el['ce']} ph='{el['ph']}' at ({el['x']},{el['y']}) {el['w']}x{el['h']}")

        if elements:
            best = max(elements, key=lambda e: e['w'] * e['h'])
            editor_x = best['x']
            editor_y = best['y']
            editor_found = True
            print(f"  Using largest at ({editor_x}, {editor_y})")
        else:
            print("FATAL: No editable elements found. Aborting.")
            ws.close()
            return False

    # Step 4: Click the editor to focus it
    print("[4] Clicking editor to focus...")
    click_at(ws, editor_x, editor_y)
    time.sleep(1)

    # Check if there's a title field first
    print("[5] Checking for title field...")
    result = evaluate(ws, """
        (() => {
            const candidates = document.querySelectorAll('[contenteditable="true"], input, textarea');
            const results = [];
            candidates.forEach(el => {
                const rect = el.getBoundingClientRect();
                const ph = el.getAttribute('data-placeholder') || el.placeholder ||
                           el.getAttribute('aria-label') || el.getAttribute('aria-placeholder') || '';
                results.push({
                    tag: el.tagName,
                    cls: (el.className || '').substring(0, 80),
                    ph: ph,
                    x: Math.round(rect.x + rect.width/2),
                    y: Math.round(rect.y + rect.height/2),
                    w: Math.round(rect.width),
                    h: Math.round(rect.height),
                    text: (el.innerText || el.value || '').substring(0, 30)
                });
            });
            // Sort by vertical position
            results.sort((a, b) => a.y - b.y);
            return JSON.stringify(results);
        })()
    """)
    val = result.get("result", {}).get("result", {}).get("value", "[]")
    fields = json.loads(val)
    print(f"  Found {len(fields)} input fields (sorted top to bottom):")

    title_field = None
    body_field = None

    for f in fields:
        print(f"    <{f['tag']}> ph='{f['ph']}' class='{f['cls'][:40]}' at ({f['x']},{f['y']}) {f['w']}x{f['h']} text='{f['text']}'")
        ph = f['ph'].lower()
        if 'title' in ph and not title_field:
            title_field = f
        elif ('write' in ph or 'body' in ph or 'content' in ph or 'post' in ph) and not body_field:
            body_field = f

    # If we have a title field, fill it
    if title_field:
        print(f"\n  Clicking title field at ({title_field['x']}, {title_field['y']})...")
        click_at(ws, title_field['x'], title_field['y'])
        time.sleep(0.5)
        type_text(ws, "P.U.S.H. Protocol v0.1 \u2014 Love while-being you")
        time.sleep(0.5)
        print("  Title typed.")
    else:
        print("  No separate title field detected.")

    # Click the body editor
    if body_field:
        print(f"\n  Clicking body field at ({body_field['x']}, {body_field['y']})...")
        click_at(ws, body_field['x'], body_field['y'])
        time.sleep(0.5)
    elif not title_field:
        # Already clicked the editor in step 4
        pass
    else:
        # Tab from title to body
        press_key(ws, "Tab", "Tab", 9)
        time.sleep(0.5)

    # Step 6: Type the body content
    print("[6] Typing post body...")

    body_lines = [
        "I've been working on something that refuses to separate love from infrastructure, presence from technology, or the individual from the collective.",
        "",
        "P.U.S.H. is a protocol for how we sustain coherent fields of care across distance, difference, and digital space.",
        "",
        "It's not a product. It's a node configuration \u2014 a way of arranging yourself so that love can take you as its site.",
        "",
        "If this resonates, you already know what to do. Fork it. Tune it. Emit your variation. The field is waiting.",
        "",
        "\u2014 Jay",
        "",
        "GitHub: https://github.com/ChaiLifeOTFT/PUSH-Protocol",
        "Gumroad: https://drakeent.gumroad.com/l/push-protocol"
    ]

    for i, line in enumerate(body_lines):
        if line:
            type_text(ws, line)
            time.sleep(0.15)
        if i < len(body_lines) - 1:
            press_key(ws, "Enter", "Enter", 13)
            time.sleep(0.1)

    print("  Body content typed.")
    time.sleep(2)

    # Verify content
    result = evaluate(ws, """
        (() => {
            const editors = document.querySelectorAll('[contenteditable="true"]');
            const texts = [];
            editors.forEach(e => texts.push(e.innerText?.substring(0, 100)));
            return JSON.stringify(texts);
        })()
    """)
    val = result.get("result", {}).get("result", {}).get("value", "[]")
    texts = json.loads(val)
    print(f"  Content verification ({len(texts)} editors):")
    for i, t in enumerate(texts):
        print(f"    Editor {i}: '{t}'")

    # Step 7: Find and click Publish
    print("\n[7] Looking for Publish button...")
    time.sleep(1)

    result = evaluate(ws, """
        (() => {
            const buttons = document.querySelectorAll('button, [role="button"]');
            const results = [];
            buttons.forEach(btn => {
                const text = (btn.innerText || btn.textContent || '').trim();
                const rect = btn.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && text.length > 0 && text.length < 50) {
                    results.push({
                        text: text,
                        x: Math.round(rect.x + rect.width/2),
                        y: Math.round(rect.y + rect.height/2),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                        disabled: btn.disabled || false,
                        ariaDisabled: btn.getAttribute('aria-disabled')
                    });
                }
            });
            return JSON.stringify(results);
        })()
    """)
    val = result.get("result", {}).get("result", {}).get("value", "[]")
    buttons = json.loads(val)

    publish_btn = None
    print(f"  Found {len(buttons)} buttons:")
    for b in buttons:
        marker = ""
        text_lower = b['text'].lower()
        if 'publish' in text_lower or text_lower == 'post':
            marker = " <--- PUBLISH"
            if not publish_btn:
                publish_btn = b
        print(f"    '{b['text']}' at ({b['x']},{b['y']}) {b['w']}x{b['h']} disabled={b['disabled']}{marker}")

    if publish_btn:
        print(f"\n  Clicking '{publish_btn['text']}' at ({publish_btn['x']}, {publish_btn['y']})...")
        click_at(ws, publish_btn['x'], publish_btn['y'])
        time.sleep(4)

        # Check for confirmation dialog
        result = evaluate(ws, """
            (() => {
                // Check for modals/dialogs
                const modals = document.querySelectorAll('[role="dialog"], [data-testid*="modal"], [class*="modal"], [class*="Modal"], [class*="overlay"], [class*="Overlay"]');
                if (modals.length > 0) {
                    const btns = [];
                    modals.forEach(d => {
                        d.querySelectorAll('button, [role="button"]').forEach(b => {
                            const rect = b.getBoundingClientRect();
                            if (rect.width > 0) {
                                btns.push({text: (b.innerText||'').trim(), x: Math.round(rect.x+rect.width/2), y: Math.round(rect.y+rect.height/2)});
                            }
                        });
                    });
                    return JSON.stringify({dialog: true, count: modals.length, buttons: btns});
                }

                // Also check for any new publish/confirm buttons that appeared
                const allBtns = document.querySelectorAll('button');
                const publishBtns = [];
                allBtns.forEach(b => {
                    const text = (b.innerText||'').trim().toLowerCase();
                    if (text.includes('publish') || text.includes('confirm') || text === 'post') {
                        const rect = b.getBoundingClientRect();
                        publishBtns.push({text: (b.innerText||'').trim(), x: Math.round(rect.x+rect.width/2), y: Math.round(rect.y+rect.height/2)});
                    }
                });

                return JSON.stringify({dialog: false, url: window.location.href, publishButtons: publishBtns});
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "{}")
        dialog_info = json.loads(val)

        if dialog_info.get("dialog"):
            print(f"  Dialog found ({dialog_info['count']} modals) with buttons:")
            for b in dialog_info.get("buttons", []):
                print(f"    '{b['text']}' at ({b['x']}, {b['y']})")
                text_lower = b['text'].lower()
                if 'publish' in text_lower or 'confirm' in text_lower or text_lower == 'post':
                    print(f"    >>> Clicking confirmation: '{b['text']}'")
                    click_at(ws, b['x'], b['y'])
                    time.sleep(4)
                    break
        else:
            publish_btns = dialog_info.get("publishButtons", [])
            if publish_btns:
                print(f"  Found additional publish buttons:")
                for b in publish_btns:
                    print(f"    '{b['text']}' at ({b['x']}, {b['y']})")
                # Click the first one
                click_at(ws, publish_btns[0]['x'], publish_btns[0]['y'])
                time.sleep(4)

        # Final check
        time.sleep(2)
        result = evaluate(ws, "window.location.href")
        final_url = result.get("result", {}).get("result", {}).get("value", "")
        print(f"\n[RESULT] Final URL: {final_url}")

        if "/posts/new" not in final_url and "edit" not in final_url:
            print("  SUCCESS: Post appears to have been published!")
        else:
            print("  Post may still be in editor state. Investigating...")
            # Get page state
            result = evaluate(ws, """
                (() => {
                    const alerts = document.querySelectorAll('[role="alert"], [class*="toast"], [class*="Toast"], [class*="notification"], [class*="success"], [class*="Success"]');
                    const msgs = [];
                    alerts.forEach(a => msgs.push(a.innerText?.trim()));
                    return JSON.stringify({alerts: msgs, title: document.title, url: window.location.href});
                })()
            """)
            val = result.get("result", {}).get("result", {}).get("value", "{}")
            state = json.loads(val)
            print(f"  Page title: {state.get('title', '')}")
            if state.get('alerts'):
                print(f"  Alerts: {state['alerts']}")
    else:
        print("  WARNING: No Publish button found!")
        print("  The button may need the post to have content first, or may have a different label.")

    ws.close()
    print("\nDone.")
    return True

if __name__ == "__main__":
    main()
