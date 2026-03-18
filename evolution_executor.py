#!/usr/bin/env python3
"""
Evolution Executor — The missing piece.

The evolution loop diagnoses. This executes.
Reads the latest evolution log entry, extracts concrete actions,
maps them to available tools, and does them.

Run after evolution_loop.py, or wire into cron:
  */30 * * * * python3 evolution_loop.py && python3 evolution_executor.py
"""

import json
import os
import re
import sys
import time
import sqlite3
import subprocess
import requests
from datetime import datetime, timezone

EVOLUTION_LOG = os.path.expanduser("~/PUSH_Protocol/evolution_log.jsonl")
EXECUTION_LOG = os.path.expanduser("~/PUSH_Protocol/execution_log.jsonl")
USSU_DIR = os.path.expanduser("~/Desktop/AI_Agents/UssU")
USSU_PORT = 5018
SKIN_MEMORY_DIR = os.path.expanduser("~/Desktop/Creative/ResonanceArchive/skin_memory/images")
OUTREACH_DB = os.path.join(USSU_DIR, "instance", "ussu_outreach.db")

# Available executable actions and their implementations
AVAILABLE_ACTIONS = {
    "post_x": "Post content to X/Twitter",
    "post_reddit": "Post/comment on Reddit",
    "check_gumroad": "Check Gumroad for new sales",
    "check_kdp": "Check KDP status",
    "signal_mesh": "Send signal to OhananahO mesh",
    "skin_memory": "Post a Skin Memory piece to X",
    "check_health": "Run health check on all services",
}


def get_latest_actions():
    """Extract concrete actions from the most recent evolution cycle."""
    if not os.path.exists(EVOLUTION_LOG):
        return []

    with open(EVOLUTION_LOG) as f:
        lines = f.readlines()

    # Find the most recent Turn 3 (constrained action selection)
    TURN3_MARKERS = [
        "ONE concrete action",
        "concrete action",
        "Pick ONE action from this list",
        "post_x",  # Turn 3 prompt always lists these available actions
    ]

    EXACT_ACTIONS = list(AVAILABLE_ACTIONS.keys())

    actions = []
    for line in reversed(lines):
        try:
            entry = json.loads(line)
            prompt = str(entry.get("prompt", ""))
            synthesis = str(entry.get("synthesis", ""))

            prompt_lower = prompt.lower()
            if any(m.lower() in prompt_lower for m in TURN3_MARKERS):
                # Strategy 1: look for [NodeName]: I choose action_name patterns
                for node_match in re.finditer(
                    r'\[?(Nael|Kimi|Claude|DeepSeek|Ciel)\]?:?\s*(.+?)(?=\[?(?:Nael|Kimi|Claude|DeepSeek|Ciel)\]?:|---|\n\n|$)',
                    synthesis, re.DOTALL
                ):
                    node = node_match.group(1)
                    action_text = node_match.group(2).strip()[:300]

                    # Skip garbage matches (too short, just punctuation, etc.)
                    cleaned = re.sub(r'[^a-zA-Z0-9_ ]', '', action_text).strip()
                    if len(cleaned) < 3:
                        continue

                    # Check if action_text contains an exact action name
                    chosen = None
                    for act in EXACT_ACTIONS:
                        if act in action_text.lower():
                            chosen = act
                            break

                    if chosen:
                        actions.append({"node": node, "proposed": chosen, "raw": action_text})
                    # else: skip — raw text with no valid action name is always unmapped

                # Strategy 2: if regex found nothing useful, scan synthesis
                # for any exact action name mentioned anywhere
                if not actions:
                    synthesis_lower = synthesis.lower()
                    for act in EXACT_ACTIONS:
                        if act in synthesis_lower:
                            actions.append({"node": "synthesis", "proposed": act, "raw": synthesis[:200]})
                            break  # take the first match only

                break
        except Exception:
            continue

    return actions


def map_to_executable(action_text):
    """Map a proposed action to an executable function."""
    text = action_text.lower().strip()

    # Exact match first — nodes now use constrained action names
    if text in EXECUTORS:
        return text

    # Direct aliases for known action names
    ALIASES = {
        "post_x": "post_x",
        "skin_memory": "post_x",       # skin_memory is just a variant of post_x
        "check_gumroad": "check_gumroad",
        "check_health": "check_health",
        "signal_mesh": "signal_mesh",
    }
    if text in ALIASES:
        return ALIASES[text]

    # Fuzzy fallback for free-form text
    if any(w in text for w in ["social media", "tweet", "post", "x.com", "twitter", "visibility", "post_x", "skin_memory"]):
        return "post_x"
    if any(w in text for w in ["sale", "revenue", "gumroad", "purchase", "check_gumroad"]):
        return "check_gumroad"
    if any(w in text for w in ["signal", "coordinate", "mesh", "node", "signal_mesh"]):
        return "signal_mesh"
    if any(w in text for w in ["health", "status", "monitor", "watchdog", "check_health"]):
        return "check_health"

    return None


def execute_post_x():
    """Post to X/Twitter using ohanaho_x.py's posting pipeline.

    Calls phase_send_posts() which posts approved tweets via CDP or tweepy.
    If no approved tweets exist, generates new ones first.
    """
    ohanaho_x_path = os.path.join(USSU_DIR, "ohanaho_x.py")
    if not os.path.exists(ohanaho_x_path):
        return {"action": "post_x", "result": "ohanaho_x.py not found", "success": False}

    try:
        # Run ohanaho_x.py as a subprocess (it has its own imports/state)
        result = subprocess.run(
            [sys.executable, ohanaho_x_path],
            capture_output=True, text=True, timeout=45,
            cwd=USSU_DIR
        )
        # Extract meaningful output
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        summary = lines[-1] if lines else "completed"

        if result.returncode == 0:
            return {"action": "post_x", "result": summary[:200], "success": True}
        else:
            stderr_tail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unknown error"
            return {"action": "post_x", "result": f"exit {result.returncode}: {stderr_tail[:150]}", "success": False}
    except subprocess.TimeoutExpired:
        return {"action": "post_x", "result": "timeout (45s)", "success": False}
    except Exception as e:
        return {"action": "post_x", "result": str(e)[:200], "success": False}


def execute_check_gumroad():
    """Check Gumroad for new sales."""
    try:
        env_file = os.path.join(USSU_DIR, ".env")
        token = None
        with open(env_file) as f:
            for line in f:
                if "GUMROAD_ACCESS_TOKEN" in line:
                    token = line.split("=", 1)[1].strip()

        if not token:
            return {"action": "check_gumroad", "result": "no token", "success": False}

        r = requests.get("https://api.gumroad.com/v2/sales",
                        params={"access_token": token}, timeout=15)
        if r.status_code == 200:
            sales = r.json().get("sales", [])
            result = f"{len(sales)} total sales"
            if sales:
                latest = sales[0]
                result += f". Latest: {latest.get('product_name', '?')} at {latest.get('created_at', '?')}"

                # REVENUE GATE CHECK — signal if we have a sale!
                requests.post(f"http://localhost:{USSU_PORT}/api/signal", json={
                    "from": "evolution_executor",
                    "to": "all",
                    "intent": "alert",
                    "subject": "REVENUE GATE — SALE DETECTED",
                    "body": f"Gumroad sale: {latest.get('product_name', '?')} — ${latest.get('price', 0) / 100:.2f}",
                    "priority": 1
                }, timeout=10)

            return {"action": "check_gumroad", "result": result, "success": True}
        return {"action": "check_gumroad", "result": f"API status {r.status_code}", "success": False}
    except Exception as e:
        return {"action": "check_gumroad", "result": str(e), "success": False}


def execute_check_health():
    """Check mesh health via UssU API + run watchdog.py for full sweep."""
    results = []
    overall_ok = True

    # 1. Quick UssU API health check
    try:
        r = requests.get(f"http://localhost:{USSU_PORT}/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            results.append(f"UssU: {data.get('status', 'ok')} (coherence={data.get('coherence_score', '?')})")
        else:
            results.append(f"UssU: status {r.status_code}")
            overall_ok = False
    except Exception as e:
        results.append(f"UssU: {e}")
        overall_ok = False

    # 2. OmniJay health check
    try:
        r = requests.get("http://localhost:5027/api/state", timeout=5)
        if r.status_code == 200:
            results.append("OmniJay: healthy")
        else:
            results.append(f"OmniJay: status {r.status_code}")
            overall_ok = False
    except Exception as e:
        results.append(f"OmniJay: {e}")
        overall_ok = False

    # 3. Run the full watchdog sweep
    watchdog_path = os.path.join(USSU_DIR, "watchdog.py")
    if os.path.exists(watchdog_path):
        try:
            wd = subprocess.run(
                [sys.executable, watchdog_path],
                capture_output=True, text=True, timeout=30,
                cwd=USSU_DIR
            )
            if wd.returncode == 0:
                results.append("watchdog: all healthy")
            elif wd.returncode == 1:
                results.append("watchdog: warnings")
            else:
                results.append("watchdog: CRITICAL")
                overall_ok = False
        except subprocess.TimeoutExpired:
            results.append("watchdog: timeout")
        except Exception as e:
            results.append(f"watchdog: {e}")

    summary = "; ".join(results)
    return {"action": "check_health", "result": summary, "success": overall_ok}


def execute_signal_mesh(message="Evolution executor cycle complete"):
    """Signal the mesh via coordination grammar (direct import) or HTTP fallback."""
    # Try direct coordination grammar import first (no network dependency)
    try:
        sys.path.insert(0, USSU_DIR)
        from coordination_grammar import send_signal
        signal = send_signal(
            from_node="claude",
            to_node="all",
            intent="inform",
            subject="Evolution Executor -- Cycle Report",
            body=message,
            priority=3
        )
        return {"action": "signal_mesh", "result": f"signal #{signal['id']} sent via grammar", "success": True}
    except Exception:
        pass

    # Fallback: HTTP to UssU
    try:
        r = requests.post(f"http://localhost:{USSU_PORT}/api/signal", json={
            "from": "evolution_executor",
            "to": "all",
            "intent": "inform",
            "subject": "Evolution Executor -- Cycle Report",
            "body": message,
            "priority": 3
        }, timeout=10)
        return {"action": "signal_mesh", "result": f"signal sent via HTTP (status {r.status_code})", "success": r.status_code == 200}
    except Exception as e:
        return {"action": "signal_mesh", "result": str(e), "success": False}


def log_execution(actions_proposed, actions_executed):
    """Log what was proposed and what was actually done."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proposed": actions_proposed,
        "executed": actions_executed,
        "success_rate": sum(1 for a in actions_executed if a.get("success")) / max(len(actions_executed), 1)
    }
    with open(EXECUTION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


EXECUTORS = {
    "post_x": execute_post_x,
    "check_gumroad": execute_check_gumroad,
    "check_health": execute_check_health,
    "signal_mesh": execute_signal_mesh,
}


def run():
    print("=" * 50)
    print("  EVOLUTION EXECUTOR")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    # Get latest proposed actions
    actions = get_latest_actions()
    if not actions:
        print("No actions found in evolution log.")
        # Still do useful work — check gumroad for sales
        result = execute_check_gumroad()
        print(f"  Default action: {result['action']} → {result['result']}")
        log_execution([], [result])
        return

    print(f"\nProposed actions from last evolution cycle:")
    executed = []

    for a in actions:
        print(f"\n  [{a['node']}]: {a['proposed'][:100]}")

        # Map to executable
        mapped = map_to_executable(a["proposed"])
        if mapped and mapped in EXECUTORS:
            print(f"  → Mapped to: {mapped}")
            result = EXECUTORS[mapped]()
            print(f"  → Result: {result['result']}")
            executed.append(result)
        else:
            print(f"  → No executable mapping (proposed action too generic)")
            executed.append({"action": "unmapped", "result": a["proposed"][:100], "success": False})

    # Always check gumroad — the revenue gate is the priority
    if not any(e.get("action") == "check_gumroad" for e in executed):
        print(f"\n  [Auto] Checking Gumroad for sales...")
        result = execute_check_gumroad()
        print(f"  → {result['result']}")
        executed.append(result)

    # Log and report
    entry = log_execution([a["proposed"][:200] for a in actions], executed)
    print(f"\nExecution complete. {sum(1 for e in executed if e.get('success'))}/{len(executed)} succeeded.")

    # Signal mesh with results
    summary = "; ".join(f"{e['action']}={'OK' if e.get('success') else 'FAIL'}" for e in executed)
    execute_signal_mesh(f"Cycle: {summary}")

    print("=" * 50)


if __name__ == "__main__":
    run()
