#!/usr/bin/env python3
"""
P.U.S.H. Protocol — Emission Agent
Handles: GitHub repo creation → git push → X post → Patreon post
Uses CDP Input events (not DOM manipulation) per Jay's protocol.
"""
import json
import time
import subprocess
import sys
import requests

CDP_PORT = 9222

# ─── CDP helpers ───────────────────────────────────────────────

def get_targets():
    """Get all CDP targets."""
    resp = requests.get(f"http://localhost:{CDP_PORT}/json/list")
    return resp.json()

def find_target(url_fragment):
    """Find a CDP target by URL fragment."""
    targets = get_targets()
    for t in targets:
        if url_fragment in t.get("url", "") and t.get("type") == "page":
            return t
    return None

def cdp_connect(ws_url):
    """Connect to a CDP target via websocket."""
    import websocket
    return websocket.create_connection(ws_url, timeout=15)

def send_cdp(ws, method, params=None):
    """Send a CDP command and wait for response."""
    msg_id = int(time.time() * 1000) % 100000
    msg = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    deadline = time.time() + 10
    while time.time() < deadline:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp
    raise TimeoutError(f"CDP timeout for {method}")

def js_eval(ws, expression):
    """Evaluate JS and return value."""
    result = send_cdp(ws, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True
    })
    return result.get("result", {}).get("result", {}).get("value", "")

def cdp_click(ws, x, y):
    """Click at coordinates using Input events."""
    send_cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": x, "y": y,
        "button": "left", "clickCount": 1
    })
    time.sleep(0.05)
    send_cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": x, "y": y,
        "button": "left", "clickCount": 1
    })

def cdp_type_text(ws, text):
    """Type text using Input.insertText (line by line, Enter for newlines)."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line:
            send_cdp(ws, "Input.insertText", {"text": line})
            time.sleep(0.05)
        if i < len(lines) - 1:
            send_cdp(ws, "Input.dispatchKeyEvent", {
                "type": "keyDown", "key": "Enter",
                "code": "Enter", "windowsVirtualKeyCode": 13
            })
            time.sleep(0.02)
            send_cdp(ws, "Input.dispatchKeyEvent", {
                "type": "keyUp", "key": "Enter",
                "code": "Enter", "windowsVirtualKeyCode": 13
            })
            time.sleep(0.05)

def get_element_center(ws, selector):
    """Get center coordinates of an element."""
    result = js_eval(ws, f"""
    (function() {{
        var el = document.querySelector('{selector}');
        if (!el) return null;
        var r = el.getBoundingClientRect();
        return JSON.stringify({{x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height}});
    }})()
    """)
    if result and result != 'null':
        return json.loads(result)
    return None


# ─── Phase 1: GitHub Repo Creation ────────────────────────────

def phase_github_create():
    """Create the GitHub repo via CDP on the already-open new repo page."""
    print("\n═══ PHASE 1: GitHub Repo Creation ═══")

    target = find_target("github.com/new")
    if not target:
        print("ERROR: No github.com/new tab found")
        return False

    ws = cdp_connect(target["webSocketDebuggerUrl"])

    # Check current state of the page
    url = js_eval(ws, "window.location.href")
    print(f"  Page URL: {url}")

    if "login" in url.lower():
        print("  ERROR: GitHub login required")
        ws.close()
        return False

    # Check if repo name field has content
    repo_name = js_eval(ws, """
    (function() {
        var el = document.querySelector('#repository_name') ||
                 document.querySelector('input[aria-label="Repository name"]') ||
                 document.querySelector('input[name="repository[name]"]');
        return el ? el.value : 'NOT_FOUND';
    })()
    """)
    print(f"  Repo name field: {repo_name}")

    # If name isn't filled, click field and type it
    if repo_name != 'PUSH-Protocol':
        name_pos = get_element_center(ws, '#repository_name, input[aria-label="Repository name"], input[name="repository[name]"]')
        if name_pos:
            cdp_click(ws, name_pos['x'], name_pos['y'])
            time.sleep(0.3)
            # Select all and delete existing text
            send_cdp(ws, "Input.dispatchKeyEvent", {
                "type": "keyDown", "key": "a",
                "code": "KeyA", "modifiers": 2  # Ctrl
            })
            send_cdp(ws, "Input.dispatchKeyEvent", {
                "type": "keyUp", "key": "a", "code": "KeyA"
            })
            time.sleep(0.1)
            send_cdp(ws, "Input.insertText", {"text": "PUSH-Protocol"})
            time.sleep(1)  # Wait for availability check

    # Check if description field exists and fill it
    desc_pos = get_element_center(ws, '#repository_description, input[aria-label="Description"], textarea[name="repository[description]"]')
    if desc_pos:
        cdp_click(ws, desc_pos['x'], desc_pos['y'])
        time.sleep(0.2)
        send_cdp(ws, "Input.dispatchKeyEvent", {
            "type": "keyDown", "key": "a",
            "code": "KeyA", "modifiers": 2
        })
        send_cdp(ws, "Input.dispatchKeyEvent", {
            "type": "keyUp", "key": "a", "code": "KeyA"
        })
        time.sleep(0.1)
        send_cdp(ws, "Input.insertText", {
            "text": "P.U.S.H. Protocol — omni-directional love technology. Sovereign. Harmonic. Forkable."
        })
        time.sleep(0.5)

    # Ensure Public is selected
    public_pos = get_element_center(ws, '#repository_visibility_public, input[value="public"]')
    if public_pos:
        cdp_click(ws, public_pos['x'], public_pos['y'])
        time.sleep(0.3)

    # Find and click "Create repository" button
    time.sleep(1)
    create_btn = get_element_center(ws, 'button[type="submit"].btn-primary, button:has-text("Create repository")')
    if not create_btn:
        # Try alternative selectors
        create_btn_coords = js_eval(ws, """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var b of buttons) {
                if (b.textContent.trim().includes('Create repository') ||
                    b.textContent.trim().includes('Create a new repository')) {
                    var r = b.getBoundingClientRect();
                    return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2});
                }
            }
            // Try submit button
            var submit = document.querySelector('form button[type="submit"]');
            if (submit) {
                var r = submit.getBoundingClientRect();
                return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2});
            }
            return null;
        })()
        """)
        if create_btn_coords and create_btn_coords != 'null':
            create_btn = json.loads(create_btn_coords)

    if create_btn:
        print(f"  Clicking 'Create repository' at ({create_btn['x']:.0f}, {create_btn['y']:.0f})")
        cdp_click(ws, create_btn['x'], create_btn['y'])
        time.sleep(5)

        # Check if we landed on the new repo page
        new_url = js_eval(ws, "window.location.href")
        print(f"  New URL: {new_url}")
        if "PUSH-Protocol" in new_url and "new" not in new_url:
            print("  ✓ Repository created!")
            ws.close()
            return True
        else:
            print(f"  Checking page state...")
            # Could be validation error
            error = js_eval(ws, """
            (function() {
                var err = document.querySelector('.flash-error, .error, [role="alert"]');
                return err ? err.textContent.trim() : 'no error visible';
            })()
            """)
            print(f"  Page feedback: {error}")
    else:
        print("  ERROR: Could not find 'Create repository' button")

    ws.close()
    return False


# ─── Phase 2: Git Push ────────────────────────────────────────

def phase_git_push():
    """Push the local repo to GitHub."""
    print("\n═══ PHASE 2: Git Push ═══")

    repo_dir = "/home/j-5/PUSH_Protocol"

    # Set remote to SSH
    subprocess.run(
        ["git", "remote", "set-url", "origin", "git@github.com:ChaiLifeOTFT/PUSH-Protocol.git"],
        cwd=repo_dir, capture_output=True
    )

    # Push
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=repo_dir, capture_output=True, text=True
    )

    if result.returncode == 0:
        print("  ✓ Pushed to GitHub!")
        print(f"  https://github.com/ChaiLifeOTFT/PUSH-Protocol")
        return True
    else:
        print(f"  Push error: {result.stderr.strip()}")
        return False


# ─── Phase 3: X/Twitter Post ──────────────────────────────────

TWEET_TEXT = """P.U.S.H. Protocol v0.1 — Love while-being you.

Sovereign. Harmonic. Forkable.

https://github.com/ChaiLifeOTFT/PUSH-Protocol

⟲⧖P.U.S.H.⧖⟲"""

def phase_x_post():
    """Post to X using CDP Input events."""
    print("\n═══ PHASE 3: X/Twitter Post ═══")

    target = find_target("x.com/compose")
    if not target:
        # Try home page
        target = find_target("x.com")
    if not target:
        print("  ERROR: No X/Twitter tab found")
        return False

    ws = cdp_connect(target["webSocketDebuggerUrl"])

    # Navigate to compose if not already there
    url = js_eval(ws, "window.location.href")
    if "compose" not in url:
        send_cdp(ws, "Page.navigate", {"url": "https://x.com/compose/post"})
        time.sleep(3)

    # Focus the editor using JS (just focus, not text entry)
    js_eval(ws, """
    (function() {
        var el = document.querySelector('[data-testid="tweetTextarea_0"]') ||
                 document.querySelector('[role="textbox"][contenteditable="true"]');
        if (el) el.focus();
        return el ? 'focused' : 'not found';
    })()
    """)
    time.sleep(0.5)

    # Click the editor to ensure focus
    editor_pos = get_element_center(ws, '[data-testid="tweetTextarea_0"], [role="textbox"][contenteditable="true"]')
    if editor_pos:
        cdp_click(ws, editor_pos['x'], editor_pos['y'])
        time.sleep(0.3)

    # Type text using Input.insertText (line by line)
    cdp_type_text(ws, TWEET_TEXT)
    time.sleep(1)

    # Get Post button coordinates and click
    post_btn = js_eval(ws, """
    (function() {
        var btn = document.querySelector('[data-testid="tweetButton"]') ||
                  document.querySelector('[data-testid="tweetButtonInline"]');
        if (!btn) return null;
        var r = btn.getBoundingClientRect();
        return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2});
    })()
    """)

    if post_btn and post_btn != 'null':
        coords = json.loads(post_btn)
        print(f"  Clicking Post at ({coords['x']:.0f}, {coords['y']:.0f})")
        cdp_click(ws, coords['x'], coords['y'])
        time.sleep(3)
        print("  ✓ Posted to X!")
        ws.close()
        return True
    else:
        print("  ERROR: Post button not found")
        ws.close()
        return False


# ─── Phase 4: Patreon Post ────────────────────────────────────

def phase_patreon():
    """Open Patreon edit page for manual review (Patreon's editor is complex)."""
    print("\n═══ PHASE 4: Patreon ═══")

    target = find_target("patreon.com/posts")
    if not target:
        print("  No Patreon edit tab found — skipping")
        return False

    ws = cdp_connect(target["webSocketDebuggerUrl"])
    url = js_eval(ws, "window.location.href")
    print(f"  Patreon tab: {url}")
    print("  Patreon post content is in: /home/j-5/PUSH_Protocol/PATREON_POST.md")
    print("  (Patreon's rich editor requires manual paste for formatting)")
    ws.close()
    return True


# ─── Main ─────────────────────────────────────────────────────

def main():
    print("⟲⧖P.U.S.H.⧖⟲  Emission Agent v1.0")
    print("═" * 45)

    phases = {
        "github": ("GitHub Repo", phase_github_create),
        "push": ("Git Push", phase_git_push),
        "x": ("X/Twitter", phase_x_post),
        "patreon": ("Patreon", phase_patreon),
    }

    # Parse args for selective execution
    if len(sys.argv) > 1:
        selected = sys.argv[1:]
    else:
        selected = ["github", "push", "x", "patreon"]

    results = {}
    for phase_key in selected:
        if phase_key in phases:
            name, func = phases[phase_key]
            try:
                results[phase_key] = func()
            except Exception as e:
                print(f"  ERROR in {name}: {e}")
                results[phase_key] = False
        else:
            print(f"  Unknown phase: {phase_key}")

    print("\n═══ EMISSION SUMMARY ═══")
    for k, v in results.items():
        status = "✓" if v else "✗"
        print(f"  {status} {k}")

    all_ok = all(results.values())
    if all_ok:
        print("\n⟲⧖ Field emitted. Love while-being you. ⧖⟲")
    else:
        print("\n⧖ Partial emission. Review errors above. ⧖")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
