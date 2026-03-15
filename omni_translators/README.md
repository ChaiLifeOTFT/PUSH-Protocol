# Omni-Translators

System prompts and handoff protocols that allow any AI to pick up work from any other AI. Each file is a complete, self-contained instruction set. Living documents — agents append discoveries.

## Available Translators

| File | Source | Purpose |
|------|--------|---------|
| `cdp_browser_agent.md` | Claude Opus | Browser automation via CDP — React fiber bypass, file upload, endpoint discovery |
| `gumroad_automation.md` | Claude Opus | Gumroad product CRUD via `/links/{id}` endpoint, dynamic cover upload |
| `patreon_automation.md` | Claude Opus | Patreon post creation — ProseMirror editor, Brave PUT for new tabs |
| `x_twitter_automation.md` | Claude Opus | X/Twitter posting — `Input.insertText` on React editor |
| `research_synthesis_agent.md` | Perplexity | Web research + structured synthesis with citations |
| `perplexity_engine_builder.md` | Perplexity | Build self-referential webapps from source docs |
| `triad_handoff.md` | Kimi | OhananahO triad continuity protocol (Jay/Nael/Kimi) |
| `UPGRADE_PROTOCOL.md` | Claude Opus | How agents write discoveries back to translators |

## How to Use

1. Pick the translator that matches the task
2. Paste it as the system prompt for the target AI
3. Include the UPGRADE_PROTOCOL instruction so discoveries persist
4. The AI produces output + appends new techniques to the translator

## The Nesting Pattern

```
Agent hits wall
  → spawns sub-agent with relevant translator
    → sub-agent hits wall
      → spawns sub-sub-agent with translator
        → wall breaks
      ← results + discoveries flow back up
    ← sub-agent appends discovery to translator file
  ← parent agent continues with result
```

## Upgrade Protocol

Every agent MUST append new discoveries to the relevant translator before completing. See `UPGRADE_PROTOCOL.md`. No wall should be hit twice.

## Verified Platforms (2026-03-15)

| Platform | Status | Translator |
|----------|--------|------------|
| GitHub | 9/9 ✓ | `cdp_browser_agent.md` |
| X/Twitter | 9/9 ✓ | `x_twitter_automation.md` |
| Gumroad | 9/9 ✓ | `gumroad_automation.md` |
| Patreon | 9/9 ✓ | `patreon_automation.md` |
| Perplexity | ✓ | `research_synthesis_agent.md` |
| Gemini | ✓ | `cdp_browser_agent.md` (use `/u/1/` for drakewnathaniel) |

Every translator is forkable. Tune if resonant.
