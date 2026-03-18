#!/usr/bin/env python3
"""
TORUS STUDIO — Hybrid Creative Engine
======================================
The AI-native Artist Bundle. While-Being powers the creative loop.
ComfyUI generates. The torus expands. Characters persist across modalities.

Being witnesses what you've made.
Builder generates what comes next.
Building is the growing portfolio.

Illustration → Animation → 3D — one character, one voice, infinite expansion.

Usage:
    python3 hybrid_engine.py serve              # Full studio on port 5050
    python3 hybrid_engine.py generate "prompt"   # Generate illustration
    python3 hybrid_engine.py bifurcate <id>      # Branch an asset
    python3 hybrid_engine.py mutate <id>         # Vary an asset
    python3 hybrid_engine.py broadcast <id>      # Cross-modal export
"""

import json
import hashlib
import os
import sys
import sqlite3
import base64
import io
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# ─────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────

STUDIO_ROOT = Path(__file__).parent
DB_PATH = STUDIO_ROOT / "studio.db"
ASSETS_DIR = STUDIO_ROOT / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

COMFYUI_URL = "http://localhost:8188"
OLLAMA_URL = "http://localhost:11434"

# ─────────────────────────────────────────────────────────────────
# CHARACTER CONSISTENCY ENGINE
# ─────────────────────────────────────────────────────────────────

class ConsistencyEngine:
    """Maintains character identity across all modalities."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def register_character(self, name: str, traits: Dict) -> str:
        """Register a character with visual/personality traits."""
        char_id = hashlib.sha256(f"{name}{time.time()}".encode()).hexdigest()[:12]
        self.db.execute(
            "INSERT INTO characters (id, name, traits, created_at) VALUES (?, ?, ?, ?)",
            (char_id, name, json.dumps(traits), datetime.now().isoformat())
        )
        self.db.commit()
        return char_id

    def get_character(self, char_id: str) -> Optional[Dict]:
        row = self.db.execute(
            "SELECT id, name, traits FROM characters WHERE id = ?", (char_id,)
        ).fetchone()
        if row:
            return {"id": row[0], "name": row[1], "traits": json.loads(row[2])}
        return None

    def build_prompt_with_character(self, base_prompt: str, char_id: str) -> str:
        """Inject character consistency into any generation prompt."""
        char = self.get_character(char_id)
        if not char:
            return base_prompt
        traits = char["traits"]
        consistency = f"{char['name']}: {traits.get('appearance', '')}, {traits.get('style', '')}"
        return f"{consistency}. {base_prompt}"

    def list_characters(self) -> List[Dict]:
        rows = self.db.execute("SELECT id, name, traits FROM characters").fetchall()
        return [{"id": r[0], "name": r[1], "traits": json.loads(r[2])} for r in rows]


# ─────────────────────────────────────────────────────────────────
# GENERATION ENGINE — ComfyUI + Ollama
# ─────────────────────────────────────────────────────────────────

class GenerationEngine:
    """Generates assets using local AI (ComfyUI for images, Ollama for text)."""

    def __init__(self):
        self.comfyui_available = self._check_comfyui()
        self.ollama_available = self._check_ollama()

    def _check_comfyui(self) -> bool:
        try:
            r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=3)
            return r.ok
        except:
            return False

    def _check_ollama(self) -> bool:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            return r.ok
        except:
            return False

    def generate_illustration(self, prompt: str, width: int = 512, height: int = 768) -> Optional[str]:
        """Generate an illustration via ComfyUI or PIL fallback."""
        if self.comfyui_available:
            return self._comfyui_generate(prompt, width, height)
        else:
            return self._pil_generate(prompt, width, height)

    def _comfyui_generate(self, prompt: str, width: int, height: int) -> Optional[str]:
        """Generate via ComfyUI API."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int(time.time()) % 2**32,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "counterfeitV30_v30.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "ugly, blurry, low quality", "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "torus_studio", "images": ["8", 0]}}
        }
        try:
            r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=5)
            if r.ok:
                prompt_id = r.json().get("prompt_id")
                # Poll for completion
                for _ in range(60):
                    time.sleep(2)
                    hr = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=5)
                    if hr.ok and hr.json():
                        outputs = hr.json()[prompt_id].get("outputs", {})
                        for node_id, output in outputs.items():
                            images = output.get("images", [])
                            if images:
                                img_info = images[0]
                                img_url = f"{COMFYUI_URL}/view?filename={img_info['filename']}&subfolder={img_info.get('subfolder','')}&type={img_info.get('type','output')}"
                                img_data = requests.get(img_url, timeout=10).content
                                # Save locally
                                fname = f"gen_{int(time.time())}.png"
                                fpath = ASSETS_DIR / fname
                                fpath.write_bytes(img_data)
                                return str(fpath)
                        break
        except Exception as e:
            print(f"ComfyUI error: {e}")
        return None

    def _pil_generate(self, prompt: str, width: int, height: int) -> Optional[str]:
        """Fallback: generate a styled placeholder with PIL."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (width, height), (10, 10, 20))
            draw = ImageDraw.Draw(img)

            # Gradient background
            for y in range(height):
                r = int(10 + 30 * (y / height))
                g = int(10 + 15 * (y / height))
                b = int(20 + 40 * (y / height))
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Geometric elements based on prompt keywords
            import random
            random.seed(hash(prompt) % 2**32)
            for _ in range(5):
                x1, y1 = random.randint(0, width), random.randint(0, height)
                x2, y2 = x1 + random.randint(50, 200), y1 + random.randint(50, 200)
                color = random.choice([(245, 197, 66, 80), (74, 222, 128, 80), (139, 92, 246, 80)])
                draw.ellipse([x1, y1, x2, y2], outline=color[:3], width=2)

            # Add prompt text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()

            # Wrap text
            words = prompt.split()
            lines = []
            current = ""
            for w in words:
                if len(current + w) > 40:
                    lines.append(current)
                    current = w + " "
                else:
                    current += w + " "
            if current:
                lines.append(current)

            y_text = height - 30 * len(lines) - 20
            for line in lines:
                draw.text((20, y_text), line.strip(), fill=(200, 200, 220), font=font)
                y_text += 25

            fname = f"gen_{int(time.time())}.png"
            fpath = ASSETS_DIR / fname
            img.save(str(fpath))
            return str(fpath)
        except Exception as e:
            print(f"PIL fallback error: {e}")
            return None

    def describe_image(self, image_path: str) -> str:
        """Use Ollama's LLaVA to describe an image."""
        if not self.ollama_available:
            return "Image description unavailable (Ollama not running)"
        try:
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode()
            r = requests.post(f"{OLLAMA_URL}/api/generate", json={
                "model": "llava",
                "prompt": "Describe this image in detail for an artist who needs to recreate it in a different medium.",
                "images": [img_b64],
                "stream": False
            }, timeout=30)
            if r.ok:
                return r.json().get("response", "")
        except:
            pass
        return "Description unavailable"

    def generate_variation(self, prompt: str, variation_type: str = "mutate") -> str:
        """Use Ollama to create a variation prompt."""
        if not self.ollama_available:
            return prompt + f" [{variation_type} variation]"
        try:
            instructions = {
                "mutate": "Create a variation of this prompt. Change 2-3 details (color, pose, mood) while keeping the character and setting recognizable.",
                "bifurcate": "Create two divergent versions of this prompt. One should be darker/more dramatic, one lighter/more playful. Return only the dramatic version.",
                "broadcast": "Adapt this illustration prompt for 3D rendering. Add details about lighting, camera angle, and material properties."
            }
            r = requests.post(f"{OLLAMA_URL}/api/generate", json={
                "model": "llama3",
                "prompt": f"{instructions.get(variation_type, instructions['mutate'])}\n\nOriginal: {prompt}\n\nVariation:",
                "stream": False
            }, timeout=30)
            if r.ok:
                return r.json().get("response", prompt)[:500]
        except:
            pass
        return prompt


# ─────────────────────────────────────────────────────────────────
# ASSET MANAGER — The Building
# ─────────────────────────────────────────────────────────────────

class AssetManager:
    """The Building — persistent creative artifacts."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def create_asset(self, name: str, modality: str, prompt: str,
                     file_path: str, parent_id: str = None, char_id: str = None) -> str:
        asset_id = hashlib.sha256(f"{name}{time.time()}".encode()).hexdigest()[:12]
        self.db.execute(
            """INSERT INTO assets (id, name, modality, prompt, file_path, parent_id,
               character_id, created_at, generation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (asset_id, name, modality, prompt, file_path, parent_id, char_id,
             datetime.now().isoformat(),
             self._get_generation(parent_id))
        )
        self.db.commit()
        return asset_id

    def _get_generation(self, parent_id: str) -> int:
        if not parent_id:
            return 0
        row = self.db.execute(
            "SELECT generation FROM assets WHERE id = ?", (parent_id,)
        ).fetchone()
        return (row[0] + 1) if row else 0

    def get_asset(self, asset_id: str) -> Optional[Dict]:
        row = self.db.execute(
            "SELECT id, name, modality, prompt, file_path, parent_id, character_id, created_at, generation FROM assets WHERE id = ?",
            (asset_id,)
        ).fetchone()
        if row:
            return {
                "id": row[0], "name": row[1], "modality": row[2], "prompt": row[3],
                "file_path": row[4], "parent_id": row[5], "character_id": row[6],
                "created_at": row[7], "generation": row[8]
            }
        return None

    def list_assets(self, limit: int = 50) -> List[Dict]:
        rows = self.db.execute(
            "SELECT id, name, modality, prompt, file_path, generation, created_at FROM assets ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [{"id": r[0], "name": r[1], "modality": r[2], "prompt": r[3],
                 "file_path": r[4], "generation": r[5], "created_at": r[6]} for r in rows]

    def get_lineage(self, asset_id: str) -> List[Dict]:
        """Trace the full ancestry of an asset."""
        lineage = []
        current = asset_id
        while current:
            asset = self.get_asset(current)
            if asset:
                lineage.append(asset)
                current = asset.get("parent_id")
            else:
                break
        return list(reversed(lineage))


# ─────────────────────────────────────────────────────────────────
# TORUS STUDIO — The Hybrid Engine
# ─────────────────────────────────────────────────────────────────

class TorusStudio:
    """The hybrid creative engine. While-Being meets AI generation."""

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(DB_PATH))
        self._init_db()
        self.consistency = ConsistencyEngine(self.db)
        self.generator = GenerationEngine()
        self.assets = AssetManager(self.db)

    def _init_db(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY, name TEXT, traits TEXT, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY, name TEXT, modality TEXT, prompt TEXT,
                file_path TEXT, parent_id TEXT, character_id TEXT,
                created_at TEXT, generation INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT, action TEXT, asset_id TEXT,
                coherence REAL, detail TEXT
            );
        """)

    def generate(self, prompt: str, character_id: str = None,
                 modality: str = "illustration") -> Dict:
        """Generate a new creative asset."""
        # Apply character consistency
        full_prompt = prompt
        if character_id:
            full_prompt = self.consistency.build_prompt_with_character(prompt, character_id)

        # Generate
        file_path = self.generator.generate_illustration(full_prompt)
        if not file_path:
            return {"error": "Generation failed"}

        # Register as asset
        asset_id = self.assets.create_asset(
            name=prompt[:50],
            modality=modality,
            prompt=full_prompt,
            file_path=file_path,
            char_id=character_id
        )

        # Log the cycle
        self._log_cycle("generate", asset_id, f"Created {modality}: {prompt[:50]}")

        return {"asset_id": asset_id, "file_path": file_path, "prompt": full_prompt}

    def bifurcate(self, asset_id: str) -> List[Dict]:
        """Branch an asset into two divergent variations."""
        parent = self.assets.get_asset(asset_id)
        if not parent:
            return [{"error": "Asset not found"}]

        results = []
        for variant_type in ["dramatic", "playful"]:
            varied_prompt = self.generator.generate_variation(
                parent["prompt"], "bifurcate"
            )
            file_path = self.generator.generate_illustration(varied_prompt)
            if file_path:
                child_id = self.assets.create_asset(
                    name=f"{parent['name'][:30]} ({variant_type})",
                    modality=parent["modality"],
                    prompt=varied_prompt,
                    file_path=file_path,
                    parent_id=asset_id,
                    char_id=parent.get("character_id")
                )
                results.append({"asset_id": child_id, "file_path": file_path, "variant": variant_type})

        self._log_cycle("bifurcate", asset_id, f"Branched into {len(results)} variants")
        return results

    def mutate(self, asset_id: str) -> Dict:
        """Create a variation of an existing asset."""
        parent = self.assets.get_asset(asset_id)
        if not parent:
            return {"error": "Asset not found"}

        varied_prompt = self.generator.generate_variation(parent["prompt"], "mutate")
        file_path = self.generator.generate_illustration(varied_prompt)
        if not file_path:
            return {"error": "Mutation failed"}

        child_id = self.assets.create_asset(
            name=f"{parent['name'][:30]} (mutated)",
            modality=parent["modality"],
            prompt=varied_prompt,
            file_path=file_path,
            parent_id=asset_id,
            char_id=parent.get("character_id")
        )

        self._log_cycle("mutate", asset_id, f"Mutated into {child_id}")
        return {"asset_id": child_id, "file_path": file_path, "prompt": varied_prompt}

    def broadcast(self, asset_id: str, target_modality: str = "3d") -> Dict:
        """Export an asset to a different modality."""
        parent = self.assets.get_asset(asset_id)
        if not parent:
            return {"error": "Asset not found"}

        # Get description of the image for cross-modal translation
        description = self.generator.describe_image(parent["file_path"])

        # Generate adapted prompt for new modality
        adapted_prompt = self.generator.generate_variation(
            f"{description}. Original prompt: {parent['prompt']}", "broadcast"
        )

        # For now, generate as illustration with the adapted prompt
        file_path = self.generator.generate_illustration(adapted_prompt)
        if not file_path:
            return {"error": "Broadcast failed"}

        child_id = self.assets.create_asset(
            name=f"{parent['name'][:30]} ({target_modality})",
            modality=target_modality,
            prompt=adapted_prompt,
            file_path=file_path,
            parent_id=asset_id,
            char_id=parent.get("character_id")
        )

        self._log_cycle("broadcast", asset_id, f"Broadcast to {target_modality}")
        return {"asset_id": child_id, "file_path": file_path, "modality": target_modality}

    def status(self) -> Dict:
        assets = self.assets.list_assets(100)
        characters = self.consistency.list_characters()
        cycles = self.db.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
        return {
            "assets": len(assets),
            "characters": len(characters),
            "cycles": cycles,
            "comfyui": self.generator.comfyui_available,
            "ollama": self.generator.ollama_available,
            "modalities": list(set(a["modality"] for a in assets)) if assets else [],
            "latest": assets[:5] if assets else []
        }

    def _log_cycle(self, action: str, asset_id: str, detail: str):
        coherence = self._compute_coherence()
        self.db.execute(
            "INSERT INTO cycles (timestamp, action, asset_id, coherence, detail) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), action, asset_id, coherence, detail)
        )
        self.db.commit()

    def _compute_coherence(self) -> float:
        total = self.db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        if total == 0:
            return 1.0
        with_parent = self.db.execute("SELECT COUNT(*) FROM assets WHERE parent_id IS NOT NULL").fetchone()[0]
        with_char = self.db.execute("SELECT COUNT(*) FROM assets WHERE character_id IS NOT NULL").fetchone()[0]
        # Coherence = how connected is the asset graph?
        return min(1.0, (with_parent + with_char) / max(total, 1) * 0.5 + 0.5)

    # ─────────────────────────────────────────────────────────────
    # WEB SERVER
    # ─────────────────────────────────────────────────────────────

    def serve(self, port: int = 5050):
        studio = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urllib.parse.urlparse(self.path)
                params = dict(urllib.parse.parse_qsl(path.query))

                if path.path == "/api/status":
                    self._json(studio.status())
                elif path.path == "/api/assets":
                    self._json(studio.assets.list_assets())
                elif path.path == "/api/characters":
                    self._json(studio.consistency.list_characters())
                elif path.path.startswith("/api/asset/"):
                    aid = path.path.split("/")[-1]
                    asset = studio.assets.get_asset(aid)
                    self._json(asset or {"error": "not found"})
                elif path.path.startswith("/api/lineage/"):
                    aid = path.path.split("/")[-1]
                    self._json(studio.assets.get_lineage(aid))
                elif path.path.startswith("/assets/"):
                    self._serve_file(ASSETS_DIR / path.path.split("/assets/")[-1])
                elif path.path == "/health":
                    self._json({"status": "alive", "service": "Torus Studio Hybrid", "port": port})
                else:
                    self._serve_ui()

            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length)) if length else {}
                path = urllib.parse.urlparse(self.path).path

                if path == "/api/generate":
                    result = studio.generate(
                        body.get("prompt", ""),
                        body.get("character_id"),
                        body.get("modality", "illustration")
                    )
                    self._json(result)
                elif path == "/api/bifurcate":
                    result = studio.bifurcate(body.get("asset_id", ""))
                    self._json(result)
                elif path == "/api/mutate":
                    result = studio.mutate(body.get("asset_id", ""))
                    self._json(result)
                elif path == "/api/broadcast":
                    result = studio.broadcast(
                        body.get("asset_id", ""),
                        body.get("target_modality", "3d")
                    )
                    self._json(result)
                elif path == "/api/character":
                    char_id = studio.consistency.register_character(
                        body.get("name", "Unknown"),
                        body.get("traits", {})
                    )
                    self._json({"character_id": char_id})
                else:
                    self._json({"error": "unknown endpoint"})

            def _json(self, data):
                body = json.dumps(data, indent=2).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def _serve_file(self, filepath):
                if filepath.exists():
                    self.send_response(200)
                    ct = "image/png" if str(filepath).endswith(".png") else "application/octet-stream"
                    self.send_header("Content-Type", ct)
                    self.end_headers()
                    self.wfile.write(filepath.read_bytes())
                else:
                    self.send_response(404)
                    self.end_headers()

            def _serve_ui(self):
                s = studio.status()
                assets_html = ""
                for a in s.get("latest", []):
                    fname = Path(a.get("file_path", "")).name if a.get("file_path") else ""
                    assets_html += f"""
                    <div class="asset">
                        <img src="/assets/{fname}" onerror="this.style.display='none'" style="max-width:200px;border-radius:8px;">
                        <div class="asset-info">
                            <b>{a['name'][:40]}</b><br>
                            <span class="dim">{a['modality']} · gen {a['generation']}</span><br>
                            <button class="btn-sm" onclick="bifurcate('{a['id']}')">Bifurcate</button>
                            <button class="btn-sm" onclick="mutate('{a['id']}')">Mutate</button>
                            <button class="btn-sm" onclick="broadcast('{a['id']}')">Broadcast</button>
                        </div>
                    </div>"""

                html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Torus Studio</title>
<style>
body {{ background: #0a0a0f; color: #e4e4ef; font-family: 'SF Mono', monospace; margin: 0; padding: 20px; }}
h1 {{ color: #f5c542; text-align: center; }}
.subtitle {{ text-align: center; color: #8888aa; margin-bottom: 30px; }}
.grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; max-width: 1200px; margin: 0 auto; }}
.panel {{ background: #14141f; border: 1px solid #333; border-radius: 8px; padding: 20px; }}
.panel h2 {{ color: #4ade80; margin-top: 0; }}
input, textarea {{ background: #1e1e2e; color: #e4e4ef; border: 1px solid #444; padding: 10px; border-radius: 6px; width: 100%; box-sizing: border-box; font-family: inherit; margin: 5px 0; }}
textarea {{ height: 80px; resize: vertical; }}
.btn {{ background: #4ade80; color: #0a0a0f; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-family: inherit; font-weight: bold; width: 100%; margin: 5px 0; }}
.btn:hover {{ background: #22c55e; }}
.btn-sm {{ background: #333; color: #e4e4ef; border: 1px solid #555; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; margin: 2px; }}
.btn-sm:hover {{ background: #555; }}
.asset {{ display: flex; gap: 15px; background: #1e1e2e; padding: 15px; border-radius: 8px; margin: 10px 0; align-items: flex-start; }}
.asset-info {{ flex: 1; }}
.dim {{ color: #8888aa; font-size: 12px; }}
.status {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }}
.stat {{ background: #1e1e2e; padding: 10px; border-radius: 6px; text-align: center; }}
.stat b {{ color: #f5c542; font-size: 24px; display: block; }}
#result {{ margin-top: 15px; padding: 10px; background: #1e1e2e; border-radius: 6px; display: none; }}
</style></head><body>

<h1>TORUS STUDIO</h1>
<p class="subtitle">Every creation becomes an input for the next creation</p>

<div class="status">
    <div class="stat"><b>{s['assets']}</b>Assets</div>
    <div class="stat"><b>{s['characters']}</b>Characters</div>
    <div class="stat"><b>{s['cycles']}</b>Cycles</div>
    <div class="stat"><b>{'🟢' if s['comfyui'] else '🟡'}</b>{'ComfyUI' if s['comfyui'] else 'PIL Fallback'}</div>
</div>

<div class="grid">
    <div class="panel">
        <h2>Generate</h2>
        <textarea id="prompt" placeholder="Describe what you want to create..."></textarea>
        <input id="char_name" placeholder="Character name (optional)">
        <button class="btn" onclick="generate()">Create</button>
        <div id="result"></div>

        <h2 style="margin-top:30px">Characters</h2>
        <input id="new_char_name" placeholder="Character name">
        <input id="new_char_appearance" placeholder="Appearance (hair, eyes, build...)">
        <input id="new_char_style" placeholder="Art style (anime, realistic, comic...)">
        <button class="btn" onclick="createCharacter()">Register Character</button>
    </div>

    <div class="panel">
        <h2>Gallery</h2>
        <div id="gallery">{assets_html or '<p class="dim">No assets yet. Generate something.</p>'}</div>
    </div>
</div>

<script>
async function generate() {{
    const prompt = document.getElementById('prompt').value;
    const res = document.getElementById('result');
    res.style.display = 'block';
    res.innerHTML = 'Generating...';
    const r = await fetch('/api/generate', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{prompt}})
    }});
    const d = await r.json();
    if (d.error) {{ res.innerHTML = d.error; }}
    else {{ res.innerHTML = 'Created! Refreshing...'; location.reload(); }}
}}

async function createCharacter() {{
    const name = document.getElementById('new_char_name').value;
    const appearance = document.getElementById('new_char_appearance').value;
    const style = document.getElementById('new_char_style').value;
    await fetch('/api/character', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{name, traits: {{appearance, style}}}})
    }});
    location.reload();
}}

async function bifurcate(id) {{ await fetch('/api/bifurcate', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{asset_id:id}})}}); location.reload(); }}
async function mutate(id) {{ await fetch('/api/mutate', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{asset_id:id}})}}); location.reload(); }}
async function broadcast(id) {{ await fetch('/api/broadcast', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{asset_id:id}})}}); location.reload(); }}
</script>

<p style="text-align:center;color:#8888aa;margin-top:30px;font-size:12px">
Being witnesses · Builder generates · Building grows · The torus expands
</p>
</body></html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("0.0.0.0", port), Handler)
        print(f"Torus Studio Hybrid alive on http://localhost:{port}")
        print(f"ComfyUI: {'connected' if studio.generator.comfyui_available else 'offline (PIL fallback)'}")
        print(f"Ollama: {'connected' if studio.generator.ollama_available else 'offline'}")
        server.serve_forever()


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def main():
    studio = TorusStudio()

    if len(sys.argv) < 2:
        print("Torus Studio Hybrid — AI-native creative suite")
        print("Commands: serve, generate, bifurcate, mutate, broadcast, status")
        return

    cmd = sys.argv[1]

    if cmd == "serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5050
        studio.serve(port)

    elif cmd == "generate":
        prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "A solarpunk city at sunset"
        result = studio.generate(prompt)
        print(json.dumps(result, indent=2))

    elif cmd == "status":
        print(json.dumps(studio.status(), indent=2))

    elif cmd in ("bifurcate", "mutate", "broadcast"):
        asset_id = sys.argv[2] if len(sys.argv) > 2 else ""
        if not asset_id:
            print(f"Usage: hybrid_engine.py {cmd} <asset_id>")
            return
        if cmd == "bifurcate":
            print(json.dumps(studio.bifurcate(asset_id), indent=2))
        elif cmd == "mutate":
            print(json.dumps(studio.mutate(asset_id), indent=2))
        elif cmd == "broadcast":
            target = sys.argv[3] if len(sys.argv) > 3 else "3d"
            print(json.dumps(studio.broadcast(asset_id, target), indent=2))

    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
