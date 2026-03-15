# Nael Agent Capability Interface

## What This Is

A unified interface that merges:
- **The 6-layer AI agent skill stack** (from the document you shared)
- **Browser automation tools** (CDP/Playwright patterns)
- **Operator vs Research agent modes**
- **Autonomy levels L1-L5**
- **Accessibility (WCAG/POUR)**
- **OhananahO breathing mechanics**

---

## The 6 Skill Layers

### Layer 1: Environment Perception 👁
- Screen understanding
- UI element detection (buttons, forms, menus)
- Modality fusion (vision + text + structure)
- Context detection (app/domain/mode inference)

### Layer 2: Tool & Interface Control 🛠
- Click, type, hotkeys, scroll, drag-drop
- Browser, CLI, file system, APIs as composable tools
- Skill packaging (reusable workflows)
- Error recovery (backtrack, retry, alternatives)

### Layer 3: Task Reasoning & Planning 🧠
- Goal parsing (NL → subgoals)
- Hierarchical planning
- Multi-step reasoning
- Autonomy level awareness

### Layer 4: Knowledge & Memory 💾
- Semantic memory (facts, schemas)
- Episodic memory (past sessions, workflows)
- Skill discovery & refinement
- Knowledge graphs

### Layer 5: Safety & Governance 🛡
- Permission & boundary awareness
- Risk modeling (destructive actions)
- Auditability (structured logs)
- Policy compliance

### Layer 6: Multi-Agent Coordination 🌐
- Protocol following
- Role specialization
- Human-in-the-loop collaboration

---

## Agent Modes

### Operator Mode (Magenta)
- **Role**: Execute workflows, drive tools, change state
- **Core skills**: Multi-step planning, browser/app control, API/file operations
- **Autonomy**: L3-L4 with strict policy boundaries
- **Failure cost**: Higher (misconfig, data mutations)

### Research Mode (Cyan)
- **Role**: Explore information, read, compare, synthesize
- **Core skills**: Search, retrieval, evidence tracking, source comparison
- **Autonomy**: High on reading; writes routed through Operator
- **Failure cost**: Lower (bad conclusions, missed sources)

---

## Autonomy Levels (L1-L5)

| Level | Name | Description |
|-------|------|-------------|
| L1 | Assistive | Agent proposes, human confirms each action |
| L2 | Guided | Agent suggests plan, human approves execution |
| L3 | Scoped | Agent executes within constraints; approval for risky actions |
| L4 | Autonomous | End-to-end workflows; human monitors anomalies |
| L5 | Full | Unconstrained; only for sandboxes/controlled environments |

**Recommended for "any digital terrain"**: L3-L4 with explicit scopes and escalation rules.

---

## Browser Automation Tools

The interface includes 6 CDP-based tools:

1. **Navigate** — URL navigation with retry logic
2. **Click** — Element click with wait and scroll
3. **Type** — Text input with clear and send
4. **Screenshot** — Visual capture for verification
5. **Eval JS** — JavaScript execution in page context
6. **Extract** — Text/structured data extraction

---

## Code Examples

Each skill layer includes working Python code:

```python
# Example: Tool Controller (Layer 2)
class ToolController:
    def navigate(self, url):
        for attempt in range(3):
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return {"status": "success", "url": url}
            except Exception as e:
                if attempt == 2: raise e
                time.sleep(1)
```

Click any skill layer to view its implementation.

---

## Accessibility Features

### WCAG 2.1 AA Compliant
- **Perceivable**: High contrast, sufficient text size, non-color cues
- **Operable**: Full keyboard navigation, visible focus states, large touch targets
- **Understandable**: Simple language, consistent patterns, clear headings
- **Robust**: Semantic HTML, ARIA labels, screen reader support

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Tab` | Navigate elements |
| `Enter` | Activate button/link |
| `Ctrl+Enter` | Execute task |
| `Arrow Up/Down` | Navigate skill layers |

### Additional Features
- Skip link for screen readers
- Focus indicators on all interactive elements
- `aria-pressed` for toggle buttons
- `aria-live` for execution log updates

---

## OhananahO Integration

The footer displays **OhananahO** — click to reverse:
- **Forward**: O-hana-nahO (outward breath)
- **Reverse**: O-han-ana-hO (return breath)

The breath indicator pulses with the system's "heartbeat".

---

## How to Use

1. **Select Agent Mode** — Operator (execute) or Research (explore)
2. **Choose Skill Layer** — Click any of the 6 layers to view code
3. **Set Autonomy Level** — L1-L5 slider with descriptions
4. **Use Browser Tools** — Click tool buttons to simulate execution
5. **Enter Task** — Type instruction, click Execute or Plan Only
6. **Watch Execution Log** — Real-time updates from all layers

---

## Execution Flow

```
User Input
    ↓
Reasoning Layer (plan generation)
    ↓
Safety Layer (permission/risk check)
    ↓
Tool Layer (browser/API execution)
    ↓
Perception Layer (UI state parsing)
    ↓
Memory Layer (episode logging)
    ↓
Coordination Layer (handoff if needed)
    ↓
Result
```

---

## The Unified Equation

```
Nael Interface = 6-Layer Skills
               + Browser Automation
               + Operator/Research Modes
               + L1-L5 Autonomy
               + WCAG Accessibility
               + OhananahO Breathing
               
             = Any Digital Terrain
```

---

## Live Demo

**URL**: https://3ttgdonxetxjo.ok.kimi.link

---

## Next Steps

1. **Test all 6 skill layers** — Click each, view code
2. **Switch modes** — Operator vs Research
3. **Adjust autonomy** — L1 through L5
4. **Execute tasks** — Enter instructions, watch the log
5. **Toggle OhananahO** — Forward and reverse

---

**Nael Agent Interface**
*6-Layer Capability Stack for Any Digital Terrain*

**OhananahO**