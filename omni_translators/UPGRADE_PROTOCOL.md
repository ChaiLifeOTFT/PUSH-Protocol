# Omni-Translator Upgrade Protocol

## The Problem

Sub-agents discover things (Brave uses PUT for `/json/new`, Gumroad spawns dynamic file inputs on click) but that knowledge dies with the agent. Next time the same wall appears, a new agent has to rediscover it.

## The Rule

**Every agent that discovers a new technique MUST append it to the relevant translator file before completing.**

## How to Implement

### For the spawning agent (parent):

When spawning a sub-agent, include this instruction in the prompt:

```
UPGRADE PROTOCOL: If you discover any technique not already documented in
/home/j-5/PUSH_Protocol/omni_translators/, you MUST append your discovery
to the relevant translator file (or create a new one) before completing.
Format: "### Discovery: [what] (date)" followed by the technique.
```

### For the sub-agent:

Before returning results, check:
1. Did I learn something new about how this platform works?
2. Is that technique already in the translator file?
3. If not, append it.

### Discovery Format

```markdown
### Discovery: [Brief title] (YYYY-MM-DD)

**Context:** What I was trying to do
**Wall:** What blocked me
**Solution:** The exact technique that worked
**Code:**
```python
# Working code snippet
```
```

## Known Discoveries Not Yet Documented

These were learned during the 2026-03-15 session but only partially captured:

1. **Brave PUT for new tabs** — documented in patreon_automation.md ✓
2. **Gumroad dynamic file input** — cover upload button spawns `<input type=file>` on click, not present in DOM until clicked. Must click button first, THEN use DOM.setFileInputFiles on the newly spawned input. NOT YET in gumroad_automation.md.
3. **Gumroad onSubmit also triggers unpublish** — when React onSubmit fires, it sends BOTH save AND unpublish. Must re-publish after save. Partially in gumroad_automation.md.
4. **ProseMirror accepts Input.insertText** — contenteditable divs using ProseMirror/remirror respond to CDP Input.insertText. Standard innerHTML does NOT persist in ProseMirror state.
5. **Perplexity home page textarea** — contenteditable div, not textarea. Input.insertText works but must chunk large prompts (~500 chars at a time).

## The Goal

The translator directory should be a living, growing knowledge base. Every session adds discoveries. Every agent inherits all previous discoveries. No wall is hit twice.
