#!/usr/bin/env python3
"""Quick fix for Gumroad cover and Patreon"""
import json
import urllib.request
import subprocess
import os

CDP_PORT = 9222
COVER = "/home/j-5/PUSH_Protocol/cover.jpg"

def get_tabs():
    try:
        resp = urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json/list", timeout=5)
        return json.loads(resp.read())
    except:
        return []

def find_tab(tabs, pattern):
    for t in tabs:
        if pattern in t.get("url", ""):
            return t
    return None

# Get tabs
tabs = get_tabs()
gumroad = find_tab(tabs, "gumroad.com/products")
patreon = find_tab(tabs, "patreon.com")

print("⟲⧖ QUICK FIX ⧖⟲")
print(f"Cover: {COVER} ({os.path.getsize(COVER)} bytes)")
print(f"Gumroad tab: {gumroad['url'] if gumroad else 'Not found'}")
print(f"Patreon tab: {patreon['url'] if patreon else 'Not found'}")

# Open tabs if not found
if not gumroad:
    print("\nOpening Gumroad...")
    subprocess.Popen(["xdg-open", "https://gumroad.com/products/tujxq/edit"])

if not patreon:
    print("Opening Patreon...")
    subprocess.Popen(["xdg-open", "https://www.patreon.com/posts/new"])

print("""
╔══════════════════════════════════════════════════════════════╗
║  MANUAL STEPS (30 seconds each):                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. GUMROAD COVER:                                          ║
║     - Look for "Cover" or thumbnail upload area              ║
║     - Click "Add cover" or drag-drop:                       ║
║       /home/j-5/PUSH_Protocol/cover.jpg                     ║
║     - Click Save                                              ║
║                                                              ║
║  2. PATREON POST:                                           ║
║     - Title: P.U.S.H. Protocol v0.1 — Love while-being you  ║
║     - Copy content from:                                     ║
║       /home/j-5/PUSH_Protocol/PATREON_POST.md               ║
║     - Select tier: All patrons                               ║
║     - Click Publish                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

# Check current Gumroad state via API
print("\n=== GUMROAD API STATUS ===")
import os
token = os.environ.get("GUMROAD_ACCESS_TOKEN", "DBuKeGC1qau8vDHTXFoJ9qp-sCsGIWk1GLuhKOzV2xw")
try:
    resp = urllib.request.urlopen(
        f"https://api.gumroad.com/v2/products/tujxq?access_token={token}",
        timeout=10
    )
    data = json.loads(resp.read())
    p = data.get("product", {})
    print(f"Name: {p.get('name')}")
    print(f"Price: {p.get('formatted_price')}")
    print(f"Slug: {p.get('custom_permalink')}")
    print(f"Published: {p.get('published')}")
    print(f"Has Cover: {'✅' if p.get('thumbnail_url') else '❌'}")
    print(f"URL: {p.get('short_url')}")
except Exception as e:
    print(f"API error: {e}")

print("\n⟲⧖ Ready for manual completion ⧖⟲")
