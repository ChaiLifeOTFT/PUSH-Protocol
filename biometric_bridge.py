#!/usr/bin/env python3
"""
Biometric Signal Bridge — SythAiA Hardware Layer
Translates Samsung Health telemetry into haptic commands for Quest 3.
Listens on port 5028. Reads from bio_stream.jsonl or accepts POST data.

Built for Jay Drake | Drake Enterprise, LLC
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─── Configuration ──────────────────────────────────────────────────────────

BIO_STREAM = Path("/home/j-5/.bio_signals/bio_stream.jsonl")
LATEST_BIO = Path("/home/j-5/.bio_signals/latest.json")
HAPTIC_OUT = Path("/tmp/haptic_cmd.json")
MESH_RELAY = "http://localhost:5027/api/relay"

STALE_THRESHOLD_MINUTES = 5
HARD_STOP_STRESS = 0.85
HARD_STOP_HRV = 20

# ─── Haptic Mapping Engine ──────────────────────────────────────────────────

def evaluate_biometric_vector(heart_rate: float, hrv: float, stress_index: float) -> dict:
    """Map biometric telemetry to haptic payload."""
    
    # Safety Hard-Stop Layer
    if stress_index > HARD_STOP_STRESS or hrv < HARD_STOP_HRV:
        return {
            "status": "HARD_STOP",
            "action": "EJECT_USER",
            "haptic_payload": {
                "intensity": 0.0,
                "frequency": 0,
                "pattern": "none",
                "thermal": "cool",
                "duration_ms": 0
            },
            "mesh_mode": "safe_fail"
        }
    
    # Continuous feedback scaling
    intensity_vector = min(1.0, (heart_rate / 120.0) * (1.0 - stress_index))
    frequency_hz = int(hrv * 1.618)
    
    if hrv > 50:
        pattern = "wave"
    elif hrv > 30:
        pattern = "pulse"
    else:
        pattern = "buzz"
    
    thermal = "warm" if intensity_vector > 0.5 else "neutral"
    
    # State classification
    if heart_rate < 55:
        mesh_mode = "background"
    elif stress_index < 0.4 and hrv > 50:
        mesh_mode = "flow"
    elif stress_index < 0.7:
        mesh_mode = "advisory"
    else:
        mesh_mode = "defensive"
    
    return {
        "status": "RESONATING",
        "action": "MODULATE_STACK",
        "haptic_payload": {
            "intensity": round(intensity_vector, 2),
            "frequency": frequency_hz,
            "pattern": pattern,
            "thermal": thermal,
            "duration_ms": 1000
        },
        "mesh_mode": mesh_mode
    }


def format_quest3(haptic_payload: dict) -> dict:
    """Format haptic payload for Quest 3."""
    return {
        "device": "quest3",
        "type": "haptic_event",
        "hand": "both",
        "amplitude": haptic_payload["intensity"],
        "frequency": min(haptic_payload["frequency"], 320),
        "duration": haptic_payload["duration_ms"],
        "pattern": haptic_payload["pattern"],
        "timestamp": datetime.utcnow().isoformat()
    }


# ─── Data Ingestion ─────────────────────────────────────────────────────────

def read_latest_biometric() -> dict:
    """Read the most recent biometric signal."""
    # Try latest.json first
    if LATEST_BIO.exists():
        try:
            with open(LATEST_BIO) as f:
                return json.load(f)
        except Exception:
            pass
    
    # Fall back to tailing bio_stream.jsonl
    if BIO_STREAM.exists():
        try:
            with open(BIO_STREAM) as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except Exception:
            pass
    
    return {}


def is_stale(data: dict) -> bool:
    """Check if biometric data is stale."""
    ts_str = data.get("ts", data.get("timestamp", ""))
    if not ts_str:
        return True
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age = datetime.utcnow().replace(tzinfo=ts.tzinfo) - ts
        return age > timedelta(minutes=STALE_THRESHOLD_MINUTES)
    except Exception:
        return True


# ─── HTTP API ───────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "service": "biometric_bridge",
        "status": "alive",
        "port": 5028,
        "stale_threshold_min": STALE_THRESHOLD_MINUTES
    })


@app.route("/api/biodata/hrv", methods=["POST"])
def receive_hrv():
    data = request.json or {}
    heart_rate = data.get("heart_rate", 70)
    hrv = data.get("hrv", data.get("rmssd", 45))
    stress = data.get("stress", 0.35)
    stress_index = stress / 100.0 if stress > 1.0 else stress
    
    result = evaluate_biometric_vector(heart_rate, hrv, stress_index)
    quest3_cmd = format_quest3(result["haptic_payload"])
    
    # Write haptic command
    with open(HAPTIC_OUT, "w") as f:
        json.dump(quest3_cmd, f, indent=2)
    
    return jsonify({
        "status": "success",
        "biometric_state": result["status"],
        "mesh_mode": result["mesh_mode"],
        "haptic": result["haptic_payload"],
        "quest3": quest3_cmd
    })


@app.route("/api/biodata/coherence", methods=["GET"])
def get_coherence():
    data = read_latest_biometric()
    
    if not data or is_stale(data):
        return jsonify({
            "status": "STALE",
            "action": "ZERO_OUTPUT",
            "reason": "Biometric data stale or missing",
            "haptic_payload": {
                "intensity": 0.0,
                "frequency": 0,
                "pattern": "none"
            }
        })
    
    heart_rate = data.get("heart_rate", 70)
    hrv = data.get("hrv", 45)
    stress = data.get("stress", 35)
    stress_index = stress / 100.0 if stress > 1.0 else stress
    
    result = evaluate_biometric_vector(heart_rate, hrv, stress_index)
    quest3_cmd = format_quest3(result["haptic_payload"])
    
    # Write haptic command
    with open(HAPTIC_OUT, "w") as f:
        json.dump(quest3_cmd, f, indent=2)
    
    return jsonify({
        "biometric_input": {
            "heart_rate": heart_rate,
            "hrv": hrv,
            "stress": stress
        },
        "state": result["status"],
        "mesh_mode": result["mesh_mode"],
        "haptic": result["haptic_payload"],
        "quest3": quest3_cmd
    })


# ─── Background Tailer ──────────────────────────────────────────────────────

def tail_bio_stream():
    """Background thread: tail bio_stream.jsonl and emit haptic commands."""
    last_size = 0
    while True:
        try:
            if BIO_STREAM.exists():
                current_size = BIO_STREAM.stat().st_size
                if current_size > last_size:
                    with open(BIO_STREAM) as f:
                        f.seek(last_size)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                heart_rate = data.get("heart_rate", 70)
                                hrv = data.get("hrv", 45)
                                stress = data.get("stress", 35)
                                stress_index = stress / 100.0 if stress > 1.0 else stress
                                
                                result = evaluate_biometric_vector(heart_rate, hrv, stress_index)
                                quest3_cmd = format_quest3(result["haptic_payload"])
                                
                                with open(HAPTIC_OUT, "w") as f:
                                    json.dump(quest3_cmd, f, indent=2)
                                
                                # Update latest.json
                                with open(LATEST_BIO, "w") as f:
                                    json.dump(data, f, indent=2)
                            except Exception:
                                pass
                    last_size = current_size
        except Exception:
            pass
        time.sleep(1)


# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Start background tailer
    tailer = threading.Thread(target=tail_bio_stream, daemon=True)
    tailer.start()
    
    print("[Biometric Bridge] Starting on port 5028...")
    print(f"[Biometric Bridge] Reading from: {BIO_STREAM}")
    print(f"[Biometric Bridge] Writing to: {HAPTIC_OUT}")
    
    app.run(host="0.0.0.0", port=5028, threaded=True)
