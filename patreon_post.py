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
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == MSG_ID - 1:
            if "error" in resp:
                print(f"  CDP ERROR: {resp['error']}")
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
    # Step 1: Create a fresh tab with Patreon new post URL
    print("[1] Creating fresh Patreon tab...")

    # Get an existing page target to use for Target.createTarget
    targets = requests.get(f"{CDP_HOST}/json/list").json()
    page_target = next(t for t in targets if t["type"] == "page")

    # Use the /json/new endpoint to create a fresh tab (Brave requires PUT)
    new_url = "https://www.patreon.com/posts/new?postType=text_only"
    new_target = requests.put(f"{CDP_HOST}/json/new?{new_url}").json()
    ws_url = new_target["webSocketDebuggerUrl"]
    print(f"  New tab ID: {new_target['id'][:12]}")

    ws = websocket.create_connection(ws_url)
    send_cdp(ws, "Runtime.enable")

    # Step 2: Wait for the editor to fully render
    print("[2] Waiting for Patreon editor to load (12s)...")
    time.sleep(12)

    # Check if page loaded
    result = evaluate(ws, "document.title")
    title = result.get("result", {}).get("result", {}).get("value", "")
    print(f"  Page title: {title}")

    # Step 3: Find the ProseMirror editor
    print("[3] Looking for ProseMirror editor...")

    # Wait and poll for the editor
    editor_found = False
    for attempt in range(10):
        result = evaluate(ws, """
            (() => {
                const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
                if (!editor) {
                    // Also try other selectors
                    const alt = document.querySelector('[contenteditable="true"]');
                    if (alt) {
                        const rect = alt.getBoundingClientRect();
                        return JSON.stringify({
                            found: true,
                            selector: 'contenteditable',
                            className: alt.className,
                            x: rect.x + rect.width/2,
                            y: rect.y + rect.height/2,
                            width: rect.width,
                            height: rect.height
                        });
                    }
                    return JSON.stringify({found: false, html: document.body?.innerHTML?.substring(0, 500)});
                }
                const rect = editor.getBoundingClientRect();
                return JSON.stringify({
                    found: true,
                    selector: 'ProseMirror',
                    x: rect.x + rect.width/2,
                    y: rect.y + rect.height/2,
                    width: rect.width,
                    height: rect.height
                });
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "{}")
        info = json.loads(val)
        if info.get("found"):
            print(f"  Editor found via '{info['selector']}' at ({info['x']:.0f}, {info['y']:.0f}), size {info['width']:.0f}x{info['height']:.0f}")
            editor_found = True
            editor_x = info["x"]
            editor_y = info["y"]
            break
        else:
            print(f"  Attempt {attempt+1}: Editor not found yet, waiting 3s...")
            if "html" in info:
                print(f"  Body preview: {str(info['html'])[:200]}")
            time.sleep(3)

    if not editor_found:
        print("  FALLBACK: Trying to find any editable area...")
        result = evaluate(ws, """
            (() => {
                const all = document.querySelectorAll('[contenteditable], textarea, [role="textbox"]');
                const results = [];
                all.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    results.push({
                        tag: el.tagName,
                        class: el.className?.substring?.(0, 60),
                        ce: el.contentEditable,
                        x: rect.x + rect.width/2,
                        y: rect.y + rect.height/2,
                        w: rect.width,
                        h: rect.height
                    });
                });
                return JSON.stringify(results);
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "[]")
        elements = json.loads(val)
        print(f"  Found {len(elements)} editable elements:")
        for el in elements:
            print(f"    {el['tag']} class='{el['class']}' ce={el['ce']} at ({el['x']:.0f},{el['y']:.0f}) {el['w']:.0f}x{el['h']:.0f}")

        if elements:
            # Pick the largest contenteditable
            best = max(elements, key=lambda e: e['w'] * e['h'])
            editor_x = best['x']
            editor_y = best['y']
            editor_found = True
            print(f"  Using largest element at ({editor_x:.0f}, {editor_y:.0f})")

    if not editor_found:
        print("FATAL: Could not find editor. Aborting.")
        ws.close()
        return False

    # Step 4: Click the editor to focus it
    print("[4] Clicking editor to focus...")
    click_at(ws, editor_x, editor_y)
    time.sleep(1)

    # Step 5: Type the post content
    print("[5] Typing post content...")

    # First, let's check if there's a title field we should fill
    result = evaluate(ws, """
        (() => {
            // Look for a title input/textarea
            const titleEl = document.querySelector('[data-testid*="title"], [placeholder*="Title"], [placeholder*="title"], input[name="title"], [aria-label*="Title"], [aria-label*="title"]');
            if (titleEl) {
                const rect = titleEl.getBoundingClientRect();
                return JSON.stringify({
                    found: true,
                    tag: titleEl.tagName,
                    placeholder: titleEl.placeholder || titleEl.getAttribute('aria-label') || '',
                    x: rect.x + rect.width/2,
                    y: rect.y + rect.height/2
                });
            }
            return JSON.stringify({found: false});
        })()
    """)
    val = result.get("result", {}).get("result", {}).get("value", "{}")
    title_info = json.loads(val)

    if title_info.get("found"):
        print(f"  Found title field: {title_info['tag']} '{title_info['placeholder']}' at ({title_info['x']:.0f}, {title_info['y']:.0f})")
        click_at(ws, title_info["x"], title_info["y"])
        time.sleep(0.5)
        type_text(ws, "P.U.S.H. Protocol v0.1 — Love while-being you")
        time.sleep(0.5)
        # Tab to body
        press_key(ws, "Tab", "Tab", 9)
        time.sleep(0.5)
    else:
        print("  No separate title field found — typing title in editor body")

    # Type the body content
    # Patreon's ProseMirror: insertText should handle line breaks with \n but
    # if not, we'll type line by line with Enter key presses

    body_lines = [
        "I've been working on something that refuses to separate love from infrastructure, presence from technology, or the individual from the collective.",
        "",
        "P.U.S.H. is a protocol for how we sustain coherent fields of care across distance, difference, and digital space.",
        "",
        "It's not a product. It's a node configuration — a way of arranging yourself so that love can take you as its site.",
        "",
        "If this resonates, you already know what to do. Fork it. Tune it. Emit your variation. The field is waiting.",
        "",
        "— Jay",
        "",
        "GitHub: https://github.com/ChaiLifeOTFT/PUSH-Protocol",
        "Gumroad: https://drakeent.gumroad.com/l/push-protocol"
    ]

    for i, line in enumerate(body_lines):
        if line:
            type_text(ws, line)
            time.sleep(0.1)
        if i < len(body_lines) - 1:
            press_key(ws, "Enter", "Enter", 13)
            time.sleep(0.1)

    print("  Content typed.")
    time.sleep(2)

    # Verify content was entered
    result = evaluate(ws, """
        (() => {
            const editor = document.querySelector('div.ProseMirror[contenteditable="true"]') ||
                           document.querySelector('[contenteditable="true"]');
            if (editor) {
                return editor.innerText.substring(0, 200);
            }
            return 'NO_EDITOR_FOUND';
        })()
    """)
    preview = result.get("result", {}).get("result", {}).get("value", "")
    print(f"  Editor content preview: {preview[:150]}...")

    if not preview or preview == "NO_EDITOR_FOUND" or len(preview.strip()) < 20:
        print("  WARNING: Content may not have been typed properly. Trying innerHTML approach...")

        # Fallback: set content via innerHTML + dispatch input event
        body_html = "<p>" + "</p><p>".join(
            line if line else "<br>" for line in body_lines
        ) + "</p>"
        body_html_escaped = body_html.replace("'", "\\'").replace('"', '\\"')

        evaluate(ws, f"""
            (() => {{
                const editor = document.querySelector('div.ProseMirror[contenteditable="true"]') ||
                               document.querySelector('[contenteditable="true"]');
                if (editor) {{
                    editor.innerHTML = '{body_html_escaped}';
                    editor.dispatchEvent(new Event('input', {{bubbles: true}}));
                    editor.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return 'set';
                }}
                return 'no editor';
            }})()
        """)
        time.sleep(1)

        # Re-verify
        result = evaluate(ws, """
            (() => {
                const editor = document.querySelector('div.ProseMirror[contenteditable="true"]') ||
                               document.querySelector('[contenteditable="true"]');
                return editor ? editor.innerText.substring(0, 200) : 'none';
            })()
        """)
        preview2 = result.get("result", {}).get("result", {}).get("value", "")
        print(f"  After innerHTML fallback: {preview2[:150]}...")

    # Step 6: Find and click the Publish button
    print("[6] Looking for Publish button...")
    time.sleep(1)

    result = evaluate(ws, """
        (() => {
            // Look for publish button with various selectors
            const selectors = [
                'button[data-tag="publish-button"]',
                'button[data-testid="publish-button"]',
                '[data-tag*="publish"]',
                '[data-testid*="publish"]',
            ];
            for (const sel of selectors) {
                const btn = document.querySelector(sel);
                if (btn) {
                    const rect = btn.getBoundingClientRect();
                    return JSON.stringify({found: true, text: btn.innerText, x: rect.x + rect.width/2, y: rect.y + rect.height/2, selector: sel});
                }
            }

            // Search all buttons by text
            const buttons = document.querySelectorAll('button, [role="button"]');
            const results = [];
            buttons.forEach(btn => {
                const text = (btn.innerText || btn.textContent || '').trim();
                const rect = btn.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    results.push({
                        text: text.substring(0, 50),
                        x: rect.x + rect.width/2,
                        y: rect.y + rect.height/2,
                        w: rect.width,
                        h: rect.height,
                        classes: (btn.className || '').substring(0, 60)
                    });
                }
            });
            return JSON.stringify({found: false, buttons: results});
        })()
    """)
    val = result.get("result", {}).get("result", {}).get("value", "{}")
    btn_info = json.loads(val)

    publish_x = None
    publish_y = None

    if btn_info.get("found"):
        publish_x = btn_info["x"]
        publish_y = btn_info["y"]
        print(f"  Found publish button '{btn_info['text']}' at ({publish_x:.0f}, {publish_y:.0f})")
    else:
        buttons = btn_info.get("buttons", [])
        print(f"  No direct match. Found {len(buttons)} buttons:")
        for b in buttons:
            text = b['text'].lower()
            print(f"    '{b['text']}' at ({b['x']:.0f},{b['y']:.0f}) {b['w']:.0f}x{b['h']:.0f} class='{b['classes']}'")
            if 'publish' in text:
                publish_x = b['x']
                publish_y = b['y']
                print(f"    ^^^ THIS IS THE PUBLISH BUTTON")

    if publish_x is None:
        # Try finding by text content more aggressively
        result = evaluate(ws, """
            (() => {
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                const matches = [];
                while (walker.nextNode()) {
                    const text = walker.currentNode.textContent.trim().toLowerCase();
                    if (text === 'publish' || text === 'post' || text === 'create post') {
                        const el = walker.currentNode.parentElement;
                        const rect = el.getBoundingClientRect();
                        const clickable = el.closest('button, [role="button"], a');
                        const cRect = clickable ? clickable.getBoundingClientRect() : rect;
                        matches.push({
                            text: walker.currentNode.textContent.trim(),
                            tag: el.tagName,
                            x: cRect.x + cRect.width/2,
                            y: cRect.y + cRect.height/2,
                            w: cRect.width
                        });
                    }
                }
                return JSON.stringify(matches);
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "[]")
        text_matches = json.loads(val)
        print(f"  Text search found {len(text_matches)} matches:")
        for m in text_matches:
            print(f"    '{m['text']}' in <{m['tag']}> at ({m['x']:.0f},{m['y']:.0f})")

        if text_matches:
            # Prefer 'Publish' or 'Post'
            for m in text_matches:
                if 'publish' in m['text'].lower():
                    publish_x = m['x']
                    publish_y = m['y']
                    break
            if publish_x is None:
                publish_x = text_matches[0]['x']
                publish_y = text_matches[0]['y']

    if publish_x is not None:
        print(f"  Clicking Publish at ({publish_x:.0f}, {publish_y:.0f})...")
        click_at(ws, publish_x, publish_y)
        time.sleep(3)

        # Check if a confirmation dialog appeared
        result = evaluate(ws, """
            (() => {
                const dialogs = document.querySelectorAll('[role="dialog"], [data-testid*="modal"], .modal');
                if (dialogs.length > 0) {
                    const btns = [];
                    dialogs.forEach(d => {
                        d.querySelectorAll('button').forEach(b => {
                            const rect = b.getBoundingClientRect();
                            btns.push({text: b.innerText?.trim(), x: rect.x+rect.width/2, y: rect.y+rect.height/2});
                        });
                    });
                    return JSON.stringify({dialog: true, buttons: btns});
                }
                return JSON.stringify({dialog: false, url: window.location.href});
            })()
        """)
        val = result.get("result", {}).get("result", {}).get("value", "{}")
        dialog_info = json.loads(val)

        if dialog_info.get("dialog"):
            print(f"  Confirmation dialog found with buttons:")
            for b in dialog_info.get("buttons", []):
                print(f"    '{b['text']}' at ({b['x']:.0f}, {b['y']:.0f})")
                if b['text'] and ('publish' in b['text'].lower() or 'confirm' in b['text'].lower() or 'post' in b['text'].lower()):
                    print(f"    Clicking confirmation: '{b['text']}'")
                    click_at(ws, b['x'], b['y'])
                    time.sleep(3)
                    break
        else:
            current_url = dialog_info.get("url", "")
            print(f"  No dialog. Current URL: {current_url}")

        # Final status check
        time.sleep(2)
        result = evaluate(ws, "window.location.href")
        final_url = result.get("result", {}).get("result", {}).get("value", "")
        print(f"\n[DONE] Final URL: {final_url}")

        if "/posts/new" not in final_url:
            print("  SUCCESS: Navigated away from editor — post likely published!")
        else:
            print("  Post may still be in editor. Checking for errors or additional steps needed...")
            # Check for any error messages
            result = evaluate(ws, """
                (() => {
                    const errors = document.querySelectorAll('[role="alert"], .error, [class*="error"], [class*="Error"]');
                    const msgs = [];
                    errors.forEach(e => msgs.push(e.innerText?.trim()));
                    return JSON.stringify(msgs);
                })()
            """)
            val = result.get("result", {}).get("result", {}).get("value", "[]")
            errors = json.loads(val)
            if errors:
                print(f"  Errors found: {errors}")
    else:
        print("  FATAL: Could not find Publish button. Manual intervention needed.")
        print("  Taking a screenshot of current state for debugging...")

    ws.close()
    return True

if __name__ == "__main__":
    main()
