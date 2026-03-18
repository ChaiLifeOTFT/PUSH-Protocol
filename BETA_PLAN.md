# Torus Studio Hybrid — Beta Test Plan
## AI-Native Artist Bundle with Unstability.ai Integration

**Status:** Ready for beta testing  
**Date:** March 18, 2026  
**Contact:** Drake Enterprise, LLC

---

## Beta Test Objective

Validate that comic artists can use Torus Studio Hybrid to:
1. Generate consistent characters across panels
2. Bifurcate story branches visually
3. Mutate panels for mood/tone variation
4. Broadcast 2D illustrations to 3D scene references

---

## The 5 Beta Artists

| Slot | Artist Type | Role | What We Learn |
|------|-------------|------|---------------|
| 1 | **Traditional Comic Artist** | Pencil → Digital workflow | Does AI assist or disrupt? |
| 2 | **Webtoon Creator** | Vertical scroll format | Bifurcation for episode branches |
| 3 | **Indie Publisher** | 5-page anthology stories | Broadcast to print/3D merch |
| 4 | **AI-Native Artist** | Prompt-first workflow | Mutation rate sweet spot |
| 5 | **Unstability.ai Comic Artist** | https://www.unstability.ai/ | Platform integration test |

---

## Unstability.ai Integration

**What is it:** AI-native comic creation platform  
**Integration:** Torus Studio as backend expansion engine

### Workflow:
```
Unstability.ai (prompt) → Torus Hybrid (generate) → 
Character consistency check → Bifurcate story paths → 
Return variants to Unstability canvas
```

### API Endpoint for Integration:
```bash
POST http://localhost:5050/api/generate
Content-Type: application/json

{
  "prompt": "Character from unstability.ai prompt",
  "character_id": "consistent_character_123",
  "modality": "illustration"
}
```

---

## Beta Test Flow (Per Artist)

### Week 1: Onboarding
- [ ] Install Torus Studio Hybrid locally
- [ ] Generate first character (seed)
- [ ] Create 3-panel sequence
- [ ] Bifurcate: dramatic vs playful versions

### Week 2: Production
- [ ] Generate 10-panel story
- [ ] Use mutation for flashback sequence
- [ ] Broadcast key panel to 3D reference

### Week 3: Integration
- [ ] Export to native workflow (Photoshop/Clip Studio)
- [ ] Test with Unstability.ai (Artist #5)
- [ ] Feedback survey

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Character consistency | >85% same-face recognition | Manual review |
| Generation time | <30s per panel | API timing |
| Artist satisfaction | >7/10 | Post-test survey |
| Workflow integration | 3/5 native tools | Export test |
| Expansion usage | 2.5 ops per asset | Analytics |

---

## Feedback Questions

1. **Consistency:** Did the character stay recognizable across generations?
2. **Control:** Could you steer the output with prompts?
3. **Speed:** Was generation fast enough for flow state?
4. **Integration:** Did it fit your existing workflow?
5. **Value:** Would you pay $27/mo for this?

---

## Technical Setup for Beta

### Prerequisites:
```bash
# 1. Clone repo
git clone https://github.com/chailifeotft/PUSH-Protocol.git

# 2. Install dependencies
pip install -r requirements.txt  # Pillow, sqlite3, requests

# 3. Start services
python3 hybrid_engine.py serve 5050  # Torus Studio
# ComfyUI on 8188 (optional, has PIL fallback)
# Ollama on 11434 (optional, has prompt fallback)

# 4. Verify
curl http://localhost:5050/health
```

### For Unstability.ai Artist:
- API key provided separately
- Webhook endpoint: `http://localhost:5050/api/generate`
- Character persistence via `character_id` parameter

---

## Known Limitations (Be Transparent)

1. **PIL Fallback:** Without ComfyUI, generates stylized placeholders
2. **Ollama Dependency:** Without local LLM, uses template variations
3. **3D Stage:** Broadcast creates prompts, not actual 3D models (yet)
4. **Animation:** AnimateDiff integration pending

---

## Compensation

| Tier | Compensation | Requirement |
|------|--------------|-------------|
| All testers | Free lifetime access | Complete 3-week program |
| Featured case study | $500 + attribution | Allow publication of workflow |
| Unstability.ai partner | Revenue share | Integrate and promote |

---

## Next Steps

1. **Recruit 5 artists** (target: March 25)
2. **Unstability.ai outreach** (target: March 22)
3. **Build onboarding docs** (target: March 20)
4. **Analytics dashboard** (target: March 24)
5. **Begin beta** (target: April 1)

---

## Emergency Contact

**Technical issues:** jay@drakeenterprise.io  
**API questions:** Port 5050 health endpoint  
**Feature requests:** GitHub issues

---

*The torus expands through feedback.*
