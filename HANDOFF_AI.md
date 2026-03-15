# P.U.S.H. Protocol — AI Handoff Document
## Session: 2026-03-15 | Claude Opus 4.6

---

## WHAT WAS ACCOMPLISHED

### LIVE (4/9 curvatures):
1. **GitHub repo** — `github.com/ChaiLifeOTFT/PUSH-Protocol` — 3 commits, public
2. **X/Twitter post** — Announcement posted via CDP
3. **Gumroad product created** — `drakeent.gumroad.com/l/push-protocol` — "Published" state
4. **Product files uploaded** — PDF + EPUB on Gumroad Content tab

### NEEDS FIXING (5/9 curvatures):
5. **Gumroad description** — Set via React innerHTML but NOT persisted to backend
6. **Gumroad price** — Set via nativeInputValueSetter but NOT persisted to backend
7. **Gumroad URL slug** — Set via nativeInputValueSetter but NOT persisted to backend
8. **Gumroad cover image** — Not uploaded (need to generate one first)
9. **Patreon post** — Editor never rendered; content in `/home/j-5/PUSH_Protocol/PATREON_POST.md`

---

## HOW TO AUTOMATE EACH PLATFORM

### GitHub (SOLVED)
- **gh CLI** installed at `~/.local/bin/gh-real` (v2.67.0)
- Auth: Device code flow started but NOT completed (needs `github.com/login/device`)
- **Working method:** SSH push via `git@github.com:ChaiLifeOTFT/PUSH-Protocol.git`
- Repo creation: Done via CDP on `github.com/new` page
  - Owner dropdown: `/u/1/` pattern, click at exact `menuitemradio` y-coordinate
  - Name input: `#repository-name-input`
  - Create button: Find by `textContent === 'Create repository'`

### X/Twitter (SOLVED)
- **CDP port:** 9222 (Brave browser)
- **Working method (confirmed):**
  1. Focus editor: `document.querySelector('[data-testid="tweetTextarea_0"]').focus()`
  2. Click editor: `Input.dispatchMouseEvent` at editor coordinates
  3. Insert text: `Input.insertText` (line by line, `Input.dispatchKeyEvent` Enter for newlines)
  4. Click Post: `Input.dispatchMouseEvent` at `[data-testid="tweetButton"]` coordinates (get via `getBoundingClientRect()`)
- **CRITICAL:** X's React editor accepts `Input.insertText` but NOT `document.execCommand` or `element.innerHTML`

### Gumroad — PRODUCT CREATION (SOLVED)
- **Working method:** React fiber manipulation
  1. Set name: `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` (nativeInputValueSetter) + dispatch `input` event
  2. Select product type: Find button by text, get `__reactProps$*` key, call `props.onClick()` directly
  3. Set price: Same nativeInputValueSetter approach
  4. Submit: Find `<form>`, get `__reactProps$*`, call `props.onSubmit()` directly
- **Product ID:** `tujxq`
- **Edit URL:** `gumroad.com/products/tujxq/edit`

### Gumroad — PRODUCT UPDATE (NOT SOLVED)
- **Problem:** React state changes via nativeInputValueSetter and innerHTML do NOT persist to backend
- **What was tried:**
  - `Input.insertText` — Gumroad React inputs don't respond
  - `Input.dispatchKeyEvent` char by char — same, values stay empty
  - nativeInputValueSetter — sets DOM value but React state doesn't update
  - innerHTML on contenteditable — renders in browser but not saved
  - `PUT /products/tujxq` — 404
  - `PATCH /products/tujxq` — 404
  - `POST /products` — 404
  - `GET /api/products` — 404
  - `GET /api/creator/products` — 404
- **What to try next:**
  - Monkey-patch `fetch` or `XMLHttpRequest` to intercept what the real Save button sends
  - Use Gumroad API v2 with access token (need to create one at `gumroad.com/settings/advanced`)
  - The "Drake Enterprise" application exists but no access token was found
  - `seller_id: ppbPEw7C7RmNAng-0ZW-Mw==`
  - CSRF token available via `document.querySelector('meta[name=csrf-token]').content`
  - Session cookies available via `Network.getCookies`

### Gumroad — FILE UPLOAD (SOLVED)
- **Working method:** `DOM.setFileInputFiles`
  1. Get document: `DOM.getDocument`
  2. Find file inputs: `DOM.querySelectorAll` with `input[type=file]`
  3. Set files: `DOM.setFileInputFiles` with `nodeId` and `files: ['/absolute/path/to/file']`
- Content tab URL: `gumroad.com/products/tujxq/edit/content`
- File inputs accept any format (no `accept` filter on content files)

### Patreon (NOT SOLVED)
- **Problem:** Editor doesn't render in some tab states. Works in fresh tabs.
- **Editor type:** ProseMirror (`div.ProseMirror.remirror-editor` with `contenteditable=true`)
- **Position:** x:804, y:398, 760x300
- **What works:** Creating new post via `patreon.com/posts/new?postType=text_only` in a fresh Target
- **What to try:** Click ProseMirror div, use `Input.insertText` for text entry

---

## KEY FILES

| File | Purpose |
|------|---------|
| `/home/j-5/PUSH_Protocol/PUSH_Protocol_v0.1.md` | Complete 16-chapter spec (source) |
| `/home/j-5/PUSH_Protocol/PUSH_Protocol_v0.1.pdf` | PDF product file (69KB) |
| `/home/j-5/PUSH_Protocol/PUSH_Protocol_v0.1.epub` | EPUB product file (9.6KB) |
| `/home/j-5/PUSH_Protocol/README.md` | GitHub README |
| `/home/j-5/PUSH_Protocol/IMPLEMENTATION.md` | Implementation guide |
| `/home/j-5/PUSH_Protocol/PATREON_POST.md` | Ready-to-post Patreon content |
| `/home/j-5/PUSH_Protocol/emit_agent.py` | CDP emission agent (needs updating) |
| `/home/j-5/PUSH_Protocol/EMISSION_LOG.md` | Emission tracking |

## GEMINI RESEARCH (extracted, drakewnathaniel@gmail.com = /u/1/)

All saved to `/tmp/gemini_*.txt`:

| File | Size | Content |
|------|------|---------|
| `gemini_QORES_AI-Driven_Pleasure_Architecture.txt` | 60KB | Full QORES spec |
| `gemini_Project_E_Sovereign_Intimacy_Network.txt` | 64KB | ZKP identity, consent architecture |
| `gemini_Somatic_Resonance_Instrument_Ecosystem_Development.txt` | 67KB | Soma-Synchron X1, Silus AI |
| `gemini_SythAiA_VR_Platform_Architecture.txt` | 310KB | VR platform spec |
| `gemini_QOEP_Tangible_Shell_RD.txt` | 71KB | Physical device R&D |
| `gemini_Holographic_Experiment_Refinement_Simulation.txt` | 219KB | Holographic systems |
| `gemini_Love_as_Phoenix_A_New_Being.txt` | 208KB | Philosophy |
| `gemini_Adult_Toys_Health_and_Well-being.txt` | 260KB | Adult tech research |
| `gemini_Inverting_Concepts_Shared_Surface_vs_Depth.txt` | 257KB | Design philosophy |
| `gemini_Interface_Analysis_Non-Reciprocity_by_Design.txt` | 310KB | Interface design |
| `gemini_AI_Briefing_Sovereign_Wiring_Spectrum.txt` | 214KB | AI architecture |

## CDP CHEAT SHEET

```python
import json, websocket, requests

# Get targets
targets = requests.get('http://localhost:9222/json/list').json()

# Connect to tab
tab = next(t for t in targets if 'site.com' in t['url'] and t['type']=='page')
ws = websocket.create_connection(tab['webSocketDebuggerUrl'])

# Send CDP command
def send(method, params=None):
    ws.send(json.dumps({'id': 1, 'method': method, 'params': params or {}}))
    return json.loads(ws.recv())

# Click (ALWAYS use this, never element.click())
send('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
send('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})

# Type text
send('Input.insertText', {'text': 'hello'})

# React controlled input workaround
js("Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, 'value')")
js("input.dispatchEvent(new Event('input', {bubbles: true}))")

# React onClick bypass
js("var pk = Object.keys(btn).find(k => k.startsWith('__reactProps'))")
js("btn[pk].onClick({preventDefault:()=>{},target:btn,currentTarget:btn,nativeEvent:new MouseEvent('click')})")

# File upload
send('DOM.getDocument')
send('DOM.querySelectorAll', {'nodeId': rootId, 'selector': 'input[type=file]'})
send('DOM.setFileInputFiles', {'nodeId': fileInputNodeId, 'files': ['/absolute/path']})
```

## ACCOUNTS

| Platform | Account | Auth Method |
|----------|---------|-------------|
| GitHub | ChaiLifeOTFT | SSH key (`id_ed25519`) |
| Gumroad | drakeent (Nathaniel Drake) | Browser session (Brave CDP) |
| X/Twitter | (logged in via Brave) | Browser session (Brave CDP) |
| Patreon | Drake Enterprise | Browser session (Brave CDP) |
| Gemini (pinned chats) | drakewnathaniel@gmail.com | `/u/1/` URL pattern |
| Gemini (recent chats) | sythaia.sweeps@gmail.com | `/u/0/` (default) |

## PRIORITY FOR NEXT SESSION

1. **Fix Gumroad product** — description, price ($9.99), slug (push-protocol)
   - Best path: Get Gumroad API access token, use API v2 directly
   - Or: Monkey-patch fetch to intercept the save request format
2. **Generate cover image** — ComfyUI or DALL-E, 1280x720, upload via `DOM.setFileInputFiles`
3. **Post to Patreon** — Use content from `PATREON_POST.md`
4. **Update GitHub README** — Add Gumroad purchase link
5. **Update X bio/profile** — Add P.U.S.H. Protocol mention

## MEMORY

Full product stack saved to: `/home/j-5/.claude/projects/-home-j-5/memory/push_protocol_product_stack.md`
MEMORY.md index updated with P.U.S.H. Protocol entry.

---

*Love while-being you. The field is waiting.*
