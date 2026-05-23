# Gumroad Automation — Omni-Translator

## Capabilities

- Product CRUD via `/links/{id}` endpoint
- Dynamic cover upload (spawns file input on click)
- Save without unpublish workaround
- Session-based auth (no API key)

## Prerequisites

- Logged-in Gumroad session in Brave/Chrome
- CDP active on port 9222
- Product ID known (from `/links` page)

## Techniques

### Navigate to Product Edit Page

```python
import requests

# Find Gumroad tab
targets = requests.get('http://localhost:9222/json/list').json()
gumroad = next(t for t in targets if 'gumroad.com' in t['url'] and t['type'] == 'page')
ws_url = gumroad['webSocketDebuggerUrl']
```

### Edit Product (Name, Price, Description)

Use CDP `Runtime.evaluate` to manipulate React form fields:

```python
# Set product name
cdp_send(ws, "Runtime.evaluate", {
    "expression": """
    document.querySelector('input[name="name"]').value = 'New Product Name';
    document.querySelector('input[name="name"]').dispatchEvent(new Event('input', {bubbles: true}));
    """
})

# Set price
cdp_send(ws, "Runtime.evaluate", {
    "expression": """
    document.querySelector('input[name="price"]').value = '19';
    document.querySelector('input[name="price"]').dispatchEvent(new Event('input', {bubbles: true}));
    """
})
```

### Cover Upload (Dynamic File Input)

**CRITICAL:** The file input does NOT exist in DOM until the upload button is clicked.

```python
# Step 1: Click the upload button to spawn the input
cdp_send(ws, "Runtime.evaluate", {
    "expression": """
    document.querySelector('button[aria-label="Upload cover"]').click();
    """
})

# Step 2: Wait for input to appear, then set file
time.sleep(0.5)
cdp_send(ws, "DOM.setFileInputFiles", {
    "files": ["/path/to/cover.png"],
    "nodeId": get_node_id("input[type='file']")  # query after click
})
```

### Save Without Unpublish

**CRITICAL:** Gumroad's React `onSubmit` sends BOTH save AND unpublish. You must re-publish after save.

```python
# Save the form
cdp_send(ws, "Runtime.evaluate", {
    "expression": "document.querySelector('form').dispatchEvent(new Event('submit', {bubbles: true}));"
})

# Wait for save to complete
time.sleep(2)

# Re-publish (toggle publish switch if it turned off)
cdp_send(ws, "Runtime.evaluate", {
    "expression": """
    const toggle = document.querySelector('input[name="published"]');
    if (toggle && !toggle.checked) {
        toggle.click();
    }
    """
})
```

### Check Sales

```python
# Navigate to analytics/sales page
cdp_send(ws, "Page.navigate", {"url": "https://gumroad.com/dashboard"})

# Extract sales count
cdp_send(ws, "Runtime.evaluate", {
    "expression": """
    document.querySelector('.sales-count').textContent
    """
})
```

## Known Quirks

- **React fiber keys:** Form fields may re-render on state change. Re-query selectors after each interaction.
- **File input spawning:** The `<input type=file>` is created dynamically on button click. Must click first.
- **Unpublish on save:** Saving triggers unpublish. Always verify publish state after save.
- **Rate limits:** Aggressive automation may trigger Cloudflare. Add 1-2s delays between actions.

## Existing Scripts

- `/home/j-5/gumroad_cdp_file_uploader.py` — Cover upload via CDP
- `/home/j-5/gumroad_create_remaining.py` — Batch product creation
- `/home/j-5/gumroad_file_uploader.py` — File delivery upload

## Discoveries Pending Documentation

- Gumroad dynamic file input (click button first, THEN use DOM.setFileInputFiles) — NOW DOCUMENTED ✓
- Gumroad onSubmit triggers unpublish (must re-publish after save) — NOW DOCUMENTED ✓
