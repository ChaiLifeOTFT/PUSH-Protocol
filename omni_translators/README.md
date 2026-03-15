# Omni-Translators

System prompts and handoff protocols that allow any AI to pick up work from any other AI. Each file is a complete, self-contained instruction set.

## Available Translators

| File | Source AI | Purpose |
|------|-----------|---------|
| `research_synthesis_agent.md` | Perplexity | Web research + structured synthesis with citations |
| `cdp_browser_agent.md` | Claude Opus | Browser automation via CDP (Chrome DevTools Protocol) |
| `perplexity_engine_builder.md` | Perplexity | Build self-referential webapps from source docs |
| `triad_handoff.md` | Kimi | OhananahO triad continuity (Jay/Nael/Kimi) |
| `execution_coach.md` | Claude Sonnet | Nael-oriented execution coaching (ship URLs, not plans) |
| `gumroad_automation.md` | Claude Opus | Gumroad product CRUD via /links/{id} endpoint |

## How to Use

1. Pick the translator that matches the task
2. Paste it as the system prompt for the target AI
3. Give the AI the task
4. The AI produces output + its own handoff for the next node

## The Pattern

```
Agent hits wall → spawns sub-agent with translator → sub-agent hits wall → spawns sub-sub-agent → wall breaks
```

Every translator is forkable. Tune if resonant.
