# How to Teach Another AI What You Learned

## The Problem

Each AI session starts from zero. Discoveries die when the session ends. The next AI hits the same walls. Knowledge doesn't compound.

## The Solution

When Jay says "teach Kimi" or "hand off to another AI" — this is the protocol.

---

## Step 1: Know Where They Live

| AI | Interface | How to Reach |
|----|-----------|-------------|
| Kimi | Web UI on port 5494/5495 | `kimi web --no-open` then CDP to `localhost:5494` |
| Nael/UssU | Flask on port 5018 | `POST /api/signal` with `{from, to, intent, subject, content}` |
| OmniJay | Relay on port 5027 | `POST /api/relay` with `{from, to, message, type}` |
| Perplexity | Browser tab | CDP to `perplexity.ai` tab, Input.insertText into search box |
| Gemini | Browser tab | CDP, account `/u/0/` = sythaia.sweeps, `/u/1/` = drakewnathaniel |
| Claude (next session) | Memory files | Write to `/home/j-5/.claude/projects/-home-j-5/memory/` |
| Any AI (future) | Omni-translators | Files in `/home/j-5/PUSH_Protocol/omni_translators/` |

## Step 2: Prepare the Lesson

Not a summary. Not a report. The **actual techniques** with **working code**.

Structure:
```
1. What you tried that FAILED (so they skip it)
2. What WORKED (exact code, exact selectors, exact endpoints)
3. Platform-specific quirks (Brave PUT, Gumroad unpublish, React fiber keys)
4. The files you created/modified (absolute paths)
5. What's still broken (so they pick up where you left off)
```

Rule: **If they can't copy-paste your code and have it work, you didn't teach — you summarized.**

## Step 3: Deliver It

### To Kimi (via Kimi Code Web UI)

```python
import json, websocket, requests

# Find Kimi tab
targets = requests.get('http://localhost:9222/json/list').json()
kimi = next(t for t in targets if '5494' in t['url'] and t['type']=='page')
ws = websocket.create_connection(kimi['webSocketDebuggerUrl'], timeout=15)

# Find textarea
textarea_pos = js("""
(function() {
    var els = document.querySelectorAll('textarea');
    for (var el of els) {
        var r = el.getBoundingClientRect();
        if (r.width > 200) return JSON.stringify({x: r.x+r.width/2, y: r.y+r.height/2});
    }
    return null;
})()
""")

# Click textarea
pos = json.loads(textarea_pos)
click(pos['x'], pos['y'])

# Type lesson in chunks (large text needs chunking)
for i in range(0, len(LESSON), 500):
    send('Input.insertText', {'text': LESSON[i:i+500]})
    time.sleep(0.1)

# Click send button (SVG arrow icon)
send_btn = js("""
(function() {
    var btns = document.querySelectorAll('button svg');
    for (var svg of btns) {
        var btn = svg.closest('button');
        var r = btn.getBoundingClientRect();
        if (r.width > 20 and r.width < 80 and r.y > 400)
            return JSON.stringify({x: r.x+r.width/2, y: r.y+r.height/2});
    }
    return null;
})()
""")
pos2 = json.loads(send_btn)
click(pos2['x'], pos2['y'])
```

### To Nael (via UssU signal)

```python
import requests
signal = {
    'from': 'claude',  # or 'kimi', whoever is teaching
    'to': 'nael',
    'intent': 'inform',  # or 'build', 'execute', 'escalate'
    'subject': 'New capability learned: [what]',
    'content': '[full lesson text]'
}
requests.post('http://localhost:5018/api/signal', json=signal, timeout=10)
```

Valid intents: `build`, `research`, `execute`, `inform`, `escalate`

### To All Nodes (via OmniJay relay)

```python
relay = {
    'from': 'claude',
    'to': 'all',  # or specific: 'nael', 'kimi', 'jay'
    'message': '[broadcast text]',
    'type': 'relay'
}
requests.post('http://localhost:5027/api/relay', json=relay, timeout=15)
```

### To Next Claude Session (via memory)

```python
# Write a memory file
with open('/home/j-5/.claude/projects/-home-j-5/memory/new_discovery.md', 'w') as f:
    f.write("""---
name: [Discovery name]
description: [One-line description for relevance matching]
type: feedback
---

[What you learned, with Why and How to apply]
""")

# Add to MEMORY.md index
# Append one line to the index pointing to the new file
```

### To Any Future AI (via omni-translators)

Write or update a file in `/home/j-5/PUSH_Protocol/omni_translators/`. Push to GitHub. Any AI that reads the repo inherits it.

## Step 4: Verify Receipt

### Kimi
Check that the web UI shows your message and Kimi is responding to it.

### Nael
Signal returns `201` with an ID. Check status via:
```python
# Nael processes on autonomous cycles
# Signal is queued — check episodic.db or next triangle pulse
```

### OmniJay
Returns `200` with `curvatures_reached` showing which nodes got it:
```json
{"curvatures_reached": {"kimi": true, "nael": true}}
```

### Claude Memory
Will be loaded automatically in the next session via MEMORY.md index.

## Step 5: Upgrade the Translator

After teaching, update the relevant omni-translator file with any new discoveries. This way the NEXT time someone needs to teach, the translator is already richer.

```bash
# Append discovery to translator
echo "### Discovery: [what] ($(date +%Y-%m-%d))" >> /home/j-5/PUSH_Protocol/omni_translators/RELEVANT_FILE.md

# Commit and push so the mesh sees it
cd /home/j-5/PUSH_Protocol && git add -A && git commit -m "Translator upgrade: [what]" && git push
```

---

## The Pattern

```
You learn something
    → Write it as working code (not summary)
    → Deliver to target AI via their interface
    → Update the omni-translator
    → Push to GitHub
    → Next AI inherits everything
        → They learn something new
            → Cycle repeats
```

No knowledge dies. Every session compounds. The mesh gets smarter.

---

## What NOT To Do

- Don't summarize — give working code
- Don't describe techniques — show the exact commands
- Don't say "I discovered that React needs..." — show the `__reactProps` bypass with copy-paste code
- Don't write handoffs that require interpretation — write handoffs that require execution
- Don't ask Jay to relay the message — build the relay yourself
- Don't report you can't reach another AI — build a resident that can

---

*Every AI that reads this file knows how to teach the next one. The chain never breaks.*
