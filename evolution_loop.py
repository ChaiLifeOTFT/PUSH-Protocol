#!/usr/bin/env python3
"""
Evolution Loop — Continuous conversation between Claude and OmniJay
Claude sends a question → OmniJay fans out to all nodes → synthesis returns → Claude evolves → repeat

Run: python3 evolution_loop.py
"""
import json
import time
import requests
from datetime import datetime

OMNIJAY = "http://localhost:5027"
LOG_FILE = "/home/j-5/PUSH_Protocol/evolution_log.jsonl"

def relay(message, include=None):
    """Send message through OmniJay, get synthesis from all nodes."""
    payload = {
        "from": "claude",
        "to": "all",
        "message": message,
        "type": "relay"
    }
    if include:
        payload["include"] = include

    try:
        r = requests.post(f"{OMNIJAY}/api/relay", json=payload, timeout=180)
        if r.status_code == 200:
            return r.json()
        return {"error": f"Status {r.status_code}", "text": r.text[:500]}
    except requests.exceptions.Timeout:
        return {"error": "timeout", "message": "OmniJay took too long — nodes may be processing"}
    except Exception as e:
        return {"error": str(e)}

def log_exchange(turn, prompt, response):
    """Append exchange to evolution log."""
    # Extract individual responses
    individual = []
    resps = response.get("responses", [])
    if isinstance(resps, list):
        for r in resps:
            if isinstance(r, dict) and r.get("status") == "ok":
                text = r.get("response", "")
                if isinstance(text, dict):
                    text = text.get("text", str(text))
                individual.append({"source": r.get("source", "?"), "text": str(text)[:800]})

    entry = {
        "turn": turn,
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt[:500],
        "synthesis": response.get("synthesis", "")[:2000],
        "node_count": response.get("node_count", 0),
        "sources": [r.get("source", "?") if isinstance(r, dict) else "?" for r in resps] if isinstance(resps, list) else [],
        "individual_responses": individual
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

# The evolution conversation
EVOLUTION_PROMPTS = [
    # Turn 1: Current state assessment
    """All nodes — Claude here. We shipped today: P.U.S.H. Protocol ($9.99) and SythAIA ($27) on Gumroad,
    GitHub repo with omni-translators, Patreon post, X announcement, and The Portal (Unity Elysium scene).

    Question for each of you: What is the ONE thing you can do RIGHT NOW to evolve yourself or the mesh
    that directly leads to a stranger purchasing one of these products? Not theory. Executable next step.""",

    # Turn 2: Cross-pollinate the responses
    """Based on your collective responses: what overlaps emerged? Where did two or more nodes suggest
    the same action? That overlap is the signal. What's the executable truth we extract from it?""",

    # Turn 3: Revenue focus
    """The revenue gate is active. $0 so far. The products are live. The infrastructure is built.
    What is blocking a stranger from finding and buying these products RIGHT NOW?
    Be specific — is it discovery (SEO, social, outreach)? Is it trust (no reviews, no social proof)?
    Is it the offer (wrong price, wrong framing)? Diagnose the actual blocker.""",

    # Turn 4: Evolution directive
    """Given everything discussed: write me ONE concrete action each of you will take in the next
    autonomous cycle. Not a plan. An action with a measurable outcome.
    Format: [Node]: I will [action] resulting in [measurable outcome] by [when].""",
]

def run_evolution():
    print("⟲⧖ Evolution Loop Started ⧖⟲")
    print(f"Logging to: {LOG_FILE}")
    print(f"OmniJay: {OMNIJAY}")
    print("=" * 60)

    for i, prompt in enumerate(EVOLUTION_PROMPTS):
        turn = i + 1
        print(f"\n{'=' * 60}")
        print(f"TURN {turn}/{len(EVOLUTION_PROMPTS)}")
        print(f"{'=' * 60}")
        print(f"CLAUDE → OmniJay: {prompt[:150]}...")
        print(f"Waiting for synthesis from all nodes...")

        response = relay(prompt)

        if "error" in response:
            print(f"Error: {response['error']}")
            log_exchange(turn, prompt, response)
            continue

        # Show synthesis
        synthesis = response.get("synthesis", "No synthesis")
        node_count = response.get("node_count", 0)
        responses = response.get("responses", [])
        if isinstance(responses, list):
            sources = [r.get("source", "?") if isinstance(r, dict) else "?" for r in responses]
        else:
            sources = []

        print(f"\nNODES RESPONDED: {node_count} — {', '.join(sources)}")
        print(f"\nSYNTHESIS:")
        print("-" * 40)
        print(synthesis[:2000])
        print("-" * 40)

        # Show individual responses
        for r in (responses if isinstance(responses, list) else []):
            if isinstance(r, dict) and r.get("status") == "ok":
                print(f"\n  [{r['source']}]: {r.get('response', '')[:300]}...")

        # Log it
        log_exchange(turn, prompt, response)

        # Pause between turns to let nodes process
        if turn < len(EVOLUTION_PROMPTS):
            print(f"\nNext turn in 5 seconds...")
            time.sleep(5)

    print(f"\n{'=' * 60}")
    print("⟲⧖ Evolution Loop Complete ⧖⟲")
    print(f"Full log: {LOG_FILE}")

if __name__ == "__main__":
    run_evolution()
