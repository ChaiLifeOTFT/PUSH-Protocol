"""
Torus Core — Universal Expanding Torus Framework (Python)
Drake Enterprise, LLC

A generic, device-agnostic toroidal architecture where:
- Nodes exist on a manifold, not in a pipeline
- Every output becomes a new input (expansion, not repetition)
- Identity/consistency persists across all transformations
- The torus expands through its outputs — each cycle adds surface area

This is the pattern. Plug in any domain: creative tools, AI agents,
data processing, game engines, IoT networks, cognitive architectures.

Usage:
    from torus_core import Torus

    t = Torus()
    seed = t.seed("my_concept", mode="alpha", data={"key": "value"})
    transformed = t.transform(seed.id, target_mode="beta")
    expanded = t.expand(seed.id, strategy="bifurcate")
    lineage = t.lineage(seed.id)
    t.snapshot()  # persist state
"""

from __future__ import annotations

import json
import math
import time
import uuid
import hashlib
import sqlite3
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import (
    Any, Callable, Dict, List, Optional, Set, Tuple, Union
)
from collections import defaultdict
from pathlib import Path


# ─────────────────────────────────────────────────
# ENUMS & CONSTANTS
# ─────────────────────────────────────────────────

class ExpansionStrategy(Enum):
    """How a node expands the torus surface area."""
    BIFURCATE = "bifurcate"       # Split into two divergent children
    BROADCAST = "broadcast"       # Clone across all modes
    RECOMBINE = "recombine"       # Merge with another node
    DEEPEN = "deepen"             # Increase fidelity/resolution in same mode
    AMPLIFY = "amplify"           # Boost potential, widen influence radius
    BRIDGE = "bridge"             # Create cross-modal shortcut
    MUTATE = "mutate"             # Random perturbation within coherence bounds


class NodeState(Enum):
    """Lifecycle states of a torus node."""
    SEED = "seed"
    ACTIVE = "active"
    TRANSFORMING = "transforming"
    EXPANDED = "expanded"
    DORMANT = "dormant"
    ARCHIVED = "archived"


# Physics constants (tunable per-application)
DEFAULT_COHERENCE_THRESHOLD = 0.3
DEFAULT_POTENTIAL_DECAY = 0.7
DEFAULT_RADIUS_GROWTH = 0.5
DEFAULT_MAX_GENERATION = 1000
DEFAULT_ENTROPY_RATE = 0.01


# ─────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────

@dataclass
class TorusNode:
    """A single node on the torus manifold."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    mode: str = ""                      # Which modality/domain this node lives in
    state: str = NodeState.SEED.value
    data: Dict[str, Any] = field(default_factory=dict)
    essence: str = ""                   # Identity fingerprint (persists across transforms)
    potential: float = 1.0              # Energy available for expansion
    coherence: float = 1.0             # Alignment with torus identity
    generation: int = 0                 # How many expansions deep
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    lineage_path: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TorusNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TorusEdge:
    """A connection between two nodes — the topology of the torus."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_id: str = ""
    target_id: str = ""
    edge_type: str = "transform"  # transform | expand | bridge | recombine
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TorusEdge":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TorusMetrics:
    """Current state of the torus manifold."""
    total_nodes: int = 0
    total_edges: int = 0
    major_radius: float = 1.0          # Overall size of the torus
    minor_radius: float = 0.5          # Tube thickness
    surface_area: float = 0.0          # Computed: (2π)² × R × r
    volume: float = 0.0                # Computed: 2π² × R × r²
    mean_coherence: float = 1.0
    mean_potential: float = 1.0
    max_generation: int = 0
    modes: List[str] = field(default_factory=list)
    expansion_count: int = 0
    transform_count: int = 0

    def compute_geometry(self):
        """Recalculate torus geometry from radii."""
        self.surface_area = (2 * math.pi) ** 2 * self.major_radius * self.minor_radius
        self.volume = 2 * (math.pi ** 2) * self.major_radius * (self.minor_radius ** 2)


# ─────────────────────────────────────────────────
# CONSISTENCY ENGINE
# ─────────────────────────────────────────────────

class ConsistencyEngine:
    """
    Maintains identity across all transformations.
    Essence = fingerprint that persists regardless of mode.
    """

    @staticmethod
    def compute_essence(data: Dict[str, Any], mode: str, parent_essence: str = "") -> str:
        """Generate an identity fingerprint from data + lineage."""
        raw = json.dumps(data, sort_keys=True, default=str) + mode + parent_essence
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def coherence_between(node_a: TorusNode, node_b: TorusNode) -> float:
        """Measure identity coherence between two nodes (0.0–1.0)."""
        if not node_a.essence or not node_b.essence:
            return 0.0
        # Shared prefix length as fraction of max possible
        shared = 0
        for ca, cb in zip(node_a.essence, node_b.essence):
            if ca == cb:
                shared += 1
            else:
                break
        return shared / max(len(node_a.essence), len(node_b.essence), 1)

    @staticmethod
    def is_coherent(node: TorusNode, threshold: float = DEFAULT_COHERENCE_THRESHOLD) -> bool:
        """Check if a node's coherence is above the survival threshold."""
        return node.coherence >= threshold

    @staticmethod
    def decay_potential(potential: float, decay_rate: float = DEFAULT_POTENTIAL_DECAY) -> float:
        """Apply energy conservation after expansion."""
        return max(0.0, potential * decay_rate)

    @staticmethod
    def inherit_essence(parent: TorusNode, child_data: Dict[str, Any], child_mode: str) -> str:
        """Child inherits identity from parent, mutated by its own data."""
        return ConsistencyEngine.compute_essence(child_data, child_mode, parent.essence)


# ─────────────────────────────────────────────────
# PERSISTENCE (SQLite — works everywhere)
# ─────────────────────────────────────────────────

class TorusMemory:
    """
    Project memory as a graph database.
    Tracks lineage, modality bridges, and torus geometry over time.
    SQLite backend — portable, zero-dependency.
    """

    def __init__(self, db_path: str = "torus.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                mode TEXT,
                state TEXT,
                data TEXT,
                essence TEXT,
                potential REAL,
                coherence REAL,
                generation INTEGER,
                parent_id TEXT,
                children_ids TEXT,
                lineage_path TEXT,
                created_at REAL,
                updated_at REAL,
                tags TEXT,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT,
                target_id TEXT,
                edge_type TEXT,
                weight REAL,
                metadata TEXT,
                created_at REAL
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                metrics TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_nodes_mode ON nodes(mode);
            CREATE INDEX IF NOT EXISTS idx_nodes_state ON nodes(state);
            CREATE INDEX IF NOT EXISTS idx_nodes_essence ON nodes(essence);
            CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);
            CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);
        """)
        self.conn.commit()

    def save_node(self, node: TorusNode):
        d = node.to_dict()
        d["data"] = json.dumps(d["data"])
        d["children_ids"] = json.dumps(d["children_ids"])
        d["lineage_path"] = json.dumps(d["lineage_path"])
        d["tags"] = json.dumps(d["tags"])
        d["metadata"] = json.dumps(d["metadata"])
        self.conn.execute(
            """INSERT OR REPLACE INTO nodes
               (id, mode, state, data, essence, potential, coherence, generation,
                parent_id, children_ids, lineage_path, created_at, updated_at, tags, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            tuple(d[k] for k in [
                "id", "mode", "state", "data", "essence", "potential", "coherence",
                "generation", "parent_id", "children_ids", "lineage_path",
                "created_at", "updated_at", "tags", "metadata"
            ])
        )
        self.conn.commit()

    def load_node(self, node_id: str) -> Optional[TorusNode]:
        row = self.conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["data"] = json.loads(d["data"])
        d["children_ids"] = json.loads(d["children_ids"])
        d["lineage_path"] = json.loads(d["lineage_path"])
        d["tags"] = json.loads(d["tags"])
        d["metadata"] = json.loads(d["metadata"])
        return TorusNode.from_dict(d)

    def save_edge(self, edge: TorusEdge):
        d = edge.to_dict()
        d["metadata"] = json.dumps(d["metadata"])
        self.conn.execute(
            """INSERT OR REPLACE INTO edges
               (id, source_id, target_id, edge_type, weight, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            tuple(d[k] for k in [
                "id", "source_id", "target_id", "edge_type", "weight", "metadata", "created_at"
            ])
        )
        self.conn.commit()

    def get_children(self, node_id: str) -> List[TorusNode]:
        rows = self.conn.execute(
            "SELECT * FROM nodes WHERE parent_id = ?", (node_id,)
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["data"] = json.loads(d["data"])
            d["children_ids"] = json.loads(d["children_ids"])
            d["lineage_path"] = json.loads(d["lineage_path"])
            d["tags"] = json.loads(d["tags"])
            d["metadata"] = json.loads(d["metadata"])
            results.append(TorusNode.from_dict(d))
        return results

    def get_nodes_by_mode(self, mode: str) -> List[TorusNode]:
        rows = self.conn.execute(
            "SELECT * FROM nodes WHERE mode = ?", (mode,)
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["data"] = json.loads(d["data"])
            d["children_ids"] = json.loads(d["children_ids"])
            d["lineage_path"] = json.loads(d["lineage_path"])
            d["tags"] = json.loads(d["tags"])
            d["metadata"] = json.loads(d["metadata"])
            results.append(TorusNode.from_dict(d))
        return results

    def get_nodes_by_essence(self, essence: str) -> List[TorusNode]:
        rows = self.conn.execute(
            "SELECT * FROM nodes WHERE essence = ?", (essence,)
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["data"] = json.loads(d["data"])
            d["children_ids"] = json.loads(d["children_ids"])
            d["lineage_path"] = json.loads(d["lineage_path"])
            d["tags"] = json.loads(d["tags"])
            d["metadata"] = json.loads(d["metadata"])
            results.append(TorusNode.from_dict(d))
        return results

    def get_all_nodes(self) -> List[TorusNode]:
        rows = self.conn.execute("SELECT * FROM nodes").fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["data"] = json.loads(d["data"])
            d["children_ids"] = json.loads(d["children_ids"])
            d["lineage_path"] = json.loads(d["lineage_path"])
            d["tags"] = json.loads(d["tags"])
            d["metadata"] = json.loads(d["metadata"])
            results.append(TorusNode.from_dict(d))
        return results

    def get_edges_from(self, node_id: str) -> List[TorusEdge]:
        rows = self.conn.execute(
            "SELECT * FROM edges WHERE source_id = ?", (node_id,)
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["metadata"] = json.loads(d["metadata"])
            results.append(TorusEdge.from_dict(d))
        return results

    def get_edges_to(self, node_id: str) -> List[TorusEdge]:
        rows = self.conn.execute(
            "SELECT * FROM edges WHERE target_id = ?", (node_id,)
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["metadata"] = json.loads(d["metadata"])
            results.append(TorusEdge.from_dict(d))
        return results

    def save_snapshot(self, metrics: TorusMetrics):
        self.conn.execute(
            "INSERT INTO snapshots (timestamp, metrics) VALUES (?, ?)",
            (time.time(), json.dumps(asdict(metrics)))
        )
        self.conn.commit()

    def get_snapshots(self, limit: int = 100) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{"id": r["id"], "timestamp": r["timestamp"],
                 "metrics": json.loads(r["metrics"])} for r in rows]

    def node_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    def edge_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    def close(self):
        self.conn.close()


# ─────────────────────────────────────────────────
# MODE REGISTRY
# ─────────────────────────────────────────────────

class ModeRegistry:
    """
    Registers available modes (modalities/domains).
    Each mode can have:
    - transform_fn: how to convert data entering this mode
    - validate_fn: whether data is valid for this mode
    - metadata: arbitrary config
    """

    def __init__(self):
        self._modes: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        transform_fn: Optional[Callable] = None,
        validate_fn: Optional[Callable] = None,
        metadata: Optional[Dict] = None,
    ):
        self._modes[name] = {
            "transform_fn": transform_fn or (lambda data, **kw: data),
            "validate_fn": validate_fn or (lambda data: True),
            "metadata": metadata or {},
        }

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self._modes.get(name)

    def list_modes(self) -> List[str]:
        return list(self._modes.keys())

    def has_mode(self, name: str) -> bool:
        return name in self._modes


# ─────────────────────────────────────────────────
# EXPANSION ENGINE
# ─────────────────────────────────────────────────

class ExpansionEngine:
    """
    The expansion engine — how the torus grows.
    Every output becomes a new entry point, increasing surface area.
    """

    def __init__(
        self,
        consistency: ConsistencyEngine,
        memory: TorusMemory,
        mode_registry: ModeRegistry,
        coherence_threshold: float = DEFAULT_COHERENCE_THRESHOLD,
        potential_decay: float = DEFAULT_POTENTIAL_DECAY,
        radius_growth: float = DEFAULT_RADIUS_GROWTH,
    ):
        self.consistency = consistency
        self.memory = memory
        self.modes = mode_registry
        self.coherence_threshold = coherence_threshold
        self.potential_decay = potential_decay
        self.radius_growth = radius_growth

    def _make_child(
        self, parent: TorusNode, data: Dict, mode: str, edge_type: str, tags: List[str] = None
    ) -> Tuple[TorusNode, TorusEdge]:
        """Create a child node from a parent, maintaining lineage."""
        child = TorusNode(
            mode=mode,
            state=NodeState.ACTIVE.value,
            data=data,
            essence=self.consistency.inherit_essence(parent, data, mode),
            potential=self.consistency.decay_potential(parent.potential, self.potential_decay),
            coherence=max(0.0, parent.coherence - DEFAULT_ENTROPY_RATE),
            generation=parent.generation + 1,
            parent_id=parent.id,
            lineage_path=parent.lineage_path + [parent.id],
            tags=tags or parent.tags.copy(),
        )
        edge = TorusEdge(
            source_id=parent.id,
            target_id=child.id,
            edge_type=edge_type,
            weight=child.coherence,
        )
        # Update parent
        parent.children_ids.append(child.id)
        parent.state = NodeState.EXPANDED.value
        parent.updated_at = time.time()
        return child, edge

    def bifurcate(self, node: TorusNode) -> List[Tuple[TorusNode, TorusEdge]]:
        """Split a node into two divergent children in the same mode."""
        results = []
        for i, suffix in enumerate(["_alpha", "_beta"]):
            child_data = {**node.data, "_branch": suffix, "_bifurcation_index": i}
            child, edge = self._make_child(node, child_data, node.mode, "bifurcate")
            child.tags = node.tags + [f"bifurcation{suffix}"]
            results.append((child, edge))
        return results

    def broadcast(self, node: TorusNode) -> List[Tuple[TorusNode, TorusEdge]]:
        """Clone a node across all registered modes."""
        results = []
        for mode_name in self.modes.list_modes():
            if mode_name == node.mode:
                continue
            mode_cfg = self.modes.get(mode_name)
            if mode_cfg and mode_cfg["validate_fn"](node.data):
                transformed_data = mode_cfg["transform_fn"](node.data, source_mode=node.mode)
                child, edge = self._make_child(node, transformed_data, mode_name, "broadcast")
                results.append((child, edge))
        return results

    def recombine(self, node_a: TorusNode, node_b: TorusNode) -> Tuple[TorusNode, List[TorusEdge]]:
        """Merge two nodes into a recombined child."""
        merged_data = {**node_a.data, **node_b.data, "_recombined_from": [node_a.id, node_b.id]}
        # Child uses the mode of whichever parent has higher coherence
        target_mode = node_a.mode if node_a.coherence >= node_b.coherence else node_b.mode
        child = TorusNode(
            mode=target_mode,
            state=NodeState.ACTIVE.value,
            data=merged_data,
            essence=self.consistency.compute_essence(
                merged_data, target_mode, node_a.essence + node_b.essence
            ),
            potential=(node_a.potential + node_b.potential) * self.potential_decay,
            coherence=(node_a.coherence + node_b.coherence) / 2,
            generation=max(node_a.generation, node_b.generation) + 1,
            parent_id=node_a.id,  # Primary parent
            lineage_path=node_a.lineage_path + [node_a.id],
            tags=list(set(node_a.tags + node_b.tags)),
        )
        edges = [
            TorusEdge(source_id=node_a.id, target_id=child.id, edge_type="recombine"),
            TorusEdge(source_id=node_b.id, target_id=child.id, edge_type="recombine"),
        ]
        node_a.children_ids.append(child.id)
        node_b.children_ids.append(child.id)
        return child, edges

    def deepen(self, node: TorusNode, depth_data: Optional[Dict] = None) -> Tuple[TorusNode, TorusEdge]:
        """Increase fidelity/resolution in the same mode."""
        child_data = {**node.data, "_depth_level": node.generation + 1}
        if depth_data:
            child_data.update(depth_data)
        child, edge = self._make_child(node, child_data, node.mode, "deepen")
        child.potential = node.potential * 0.9  # Deepening is cheaper than branching
        return child, edge

    def amplify(self, node: TorusNode, factor: float = 1.5) -> TorusNode:
        """Boost a node's potential and coherence (in-place)."""
        node.potential = min(node.potential * factor, 10.0)
        node.coherence = min(node.coherence * 1.1, 1.0)
        node.updated_at = time.time()
        node.tags.append("amplified")
        return node

    def bridge(self, node: TorusNode, target_mode: str) -> Tuple[TorusNode, TorusEdge]:
        """Create a cross-modal shortcut."""
        mode_cfg = self.modes.get(target_mode)
        if mode_cfg:
            bridged_data = mode_cfg["transform_fn"](node.data, source_mode=node.mode)
        else:
            bridged_data = node.data.copy()
        child, edge = self._make_child(node, bridged_data, target_mode, "bridge")
        child.tags.append("bridged")
        return child, edge

    def mutate(self, node: TorusNode, mutation_fn: Optional[Callable] = None) -> Tuple[TorusNode, TorusEdge]:
        """Random perturbation within coherence bounds."""
        if mutation_fn:
            mutated_data = mutation_fn(node.data.copy())
        else:
            mutated_data = {**node.data, "_mutated": True, "_mutation_seed": uuid.uuid4().hex[:8]}
        child, edge = self._make_child(node, mutated_data, node.mode, "mutate")
        child.coherence = max(0.0, child.coherence - DEFAULT_ENTROPY_RATE * 2)  # Mutations cost coherence
        return child, edge


# ─────────────────────────────────────────────────
# HOOKS / MIDDLEWARE
# ─────────────────────────────────────────────────

class HookRegistry:
    """
    Event hooks for extensibility.
    Register callbacks for: on_seed, on_transform, on_expand, on_persist, on_snapshot.
    """

    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)

    def register(self, event: str, fn: Callable):
        self._hooks[event].append(fn)

    def fire(self, event: str, **kwargs):
        for fn in self._hooks.get(event, []):
            fn(**kwargs)


# ─────────────────────────────────────────────────
# THE TORUS — Main Interface
# ─────────────────────────────────────────────────

class Torus:
    """
    The Torus.

    A universal expanding manifold where:
    - seed() creates entry points in any mode
    - transform() flows between modes (toroidal topology)
    - expand() grows the surface area (bifurcate, broadcast, recombine, etc.)
    - lineage() traces full genealogy of any node
    - snapshot() persists the manifold state
    - metrics() returns current geometry

    The torus expands through its outputs.
    """

    def __init__(
        self,
        db_path: str = "torus.db",
        coherence_threshold: float = DEFAULT_COHERENCE_THRESHOLD,
        potential_decay: float = DEFAULT_POTENTIAL_DECAY,
        radius_growth: float = DEFAULT_RADIUS_GROWTH,
    ):
        self.memory = TorusMemory(db_path)
        self.consistency = ConsistencyEngine()
        self.modes = ModeRegistry()
        self.hooks = HookRegistry()
        self.expansion = ExpansionEngine(
            consistency=self.consistency,
            memory=self.memory,
            mode_registry=self.modes,
            coherence_threshold=coherence_threshold,
            potential_decay=potential_decay,
            radius_growth=radius_growth,
        )
        self._metrics = TorusMetrics()
        self._coherence_threshold = coherence_threshold
        self._radius_growth = radius_growth

        # Register default modes (override or extend for your domain)
        self.modes.register("default")

    # ── Mode Management ──────────────────────────

    def register_mode(
        self,
        name: str,
        transform_fn: Optional[Callable] = None,
        validate_fn: Optional[Callable] = None,
        metadata: Optional[Dict] = None,
    ) -> "Torus":
        """Register a new modality on the torus. Returns self for chaining."""
        self.modes.register(name, transform_fn, validate_fn, metadata)
        return self

    # ── Core Operations ──────────────────────────

    def seed(
        self,
        intent: str,
        mode: str = "default",
        data: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> TorusNode:
        """
        Create an entry point on the torus.
        Drop in with text, data, or any representation.
        """
        if not self.modes.has_mode(mode):
            self.modes.register(mode)  # Auto-register unknown modes

        node_data = data or {}
        node_data["_intent"] = intent

        node = TorusNode(
            mode=mode,
            state=NodeState.ACTIVE.value,
            data=node_data,
            essence=self.consistency.compute_essence(node_data, mode),
            tags=tags or [],
        )

        self.memory.save_node(node)
        self._update_metrics_after_add()
        self.hooks.fire("on_seed", node=node)
        return node

    def transform(
        self,
        node_id: str,
        target_mode: str,
        transform_data: Optional[Dict] = None,
    ) -> Optional[TorusNode]:
        """
        Flow a node to a different mode on the torus.
        The identity persists; the representation changes.
        """
        source = self.memory.load_node(node_id)
        if not source:
            return None

        if not self.modes.has_mode(target_mode):
            self.modes.register(target_mode)

        mode_cfg = self.modes.get(target_mode)
        if mode_cfg:
            new_data = mode_cfg["transform_fn"](source.data.copy(), source_mode=source.mode)
        else:
            new_data = source.data.copy()

        if transform_data:
            new_data.update(transform_data)

        child = TorusNode(
            mode=target_mode,
            state=NodeState.ACTIVE.value,
            data=new_data,
            essence=self.consistency.inherit_essence(source, new_data, target_mode),
            potential=self.consistency.decay_potential(source.potential),
            coherence=source.coherence,
            generation=source.generation + 1,
            parent_id=source.id,
            lineage_path=source.lineage_path + [source.id],
            tags=source.tags.copy(),
        )

        edge = TorusEdge(
            source_id=source.id,
            target_id=child.id,
            edge_type="transform",
            weight=child.coherence,
        )

        source.children_ids.append(child.id)
        source.state = NodeState.EXPANDED.value
        source.updated_at = time.time()

        self.memory.save_node(source)
        self.memory.save_node(child)
        self.memory.save_edge(edge)
        self._update_metrics_after_add()
        self._metrics.transform_count += 1
        self.hooks.fire("on_transform", source=source, target=child, edge=edge)
        return child

    def expand(
        self,
        node_id: str,
        strategy: Union[str, ExpansionStrategy] = ExpansionStrategy.BIFURCATE,
        target_node_id: Optional[str] = None,
        target_mode: Optional[str] = None,
        depth_data: Optional[Dict] = None,
        mutation_fn: Optional[Callable] = None,
        amplify_factor: float = 1.5,
    ) -> List[TorusNode]:
        """
        Expand the torus through a node.
        Every expansion increases surface area.
        Returns list of new nodes created.
        """
        if isinstance(strategy, str):
            strategy = ExpansionStrategy(strategy)

        node = self.memory.load_node(node_id)
        if not node:
            return []

        if not self.consistency.is_coherent(node, self._coherence_threshold):
            return []  # Below coherence threshold — node cannot expand

        results: List[TorusNode] = []
        edges: List[TorusEdge] = []

        if strategy == ExpansionStrategy.BIFURCATE:
            for child, edge in self.expansion.bifurcate(node):
                results.append(child)
                edges.append(edge)

        elif strategy == ExpansionStrategy.BROADCAST:
            for child, edge in self.expansion.broadcast(node):
                results.append(child)
                edges.append(edge)

        elif strategy == ExpansionStrategy.RECOMBINE:
            if not target_node_id:
                return []
            target = self.memory.load_node(target_node_id)
            if not target:
                return []
            child, edge_list = self.expansion.recombine(node, target)
            results.append(child)
            edges.extend(edge_list)
            self.memory.save_node(target)

        elif strategy == ExpansionStrategy.DEEPEN:
            child, edge = self.expansion.deepen(node, depth_data)
            results.append(child)
            edges.append(edge)

        elif strategy == ExpansionStrategy.AMPLIFY:
            amplified = self.expansion.amplify(node, amplify_factor)
            self.memory.save_node(amplified)
            self.hooks.fire("on_expand", parent=node, children=[amplified], strategy=strategy)
            return [amplified]

        elif strategy == ExpansionStrategy.BRIDGE:
            if not target_mode:
                return []
            child, edge = self.expansion.bridge(node, target_mode)
            results.append(child)
            edges.append(edge)

        elif strategy == ExpansionStrategy.MUTATE:
            child, edge = self.expansion.mutate(node, mutation_fn)
            results.append(child)
            edges.append(edge)

        # Persist all new nodes and edges
        self.memory.save_node(node)  # Parent was updated
        for child in results:
            self.memory.save_node(child)
        for edge in edges:
            self.memory.save_edge(edge)

        # Grow the torus
        self._metrics.major_radius += self._radius_growth * len(results)
        self._metrics.minor_radius += self._radius_growth * 0.3 * len(results)
        self._metrics.expansion_count += 1
        self._update_metrics_after_add()

        self.hooks.fire("on_expand", parent=node, children=results, strategy=strategy)
        return results

    # ── Query Operations ─────────────────────────

    def get(self, node_id: str) -> Optional[TorusNode]:
        """Retrieve a single node."""
        return self.memory.load_node(node_id)

    def lineage(self, node_id: str) -> List[TorusNode]:
        """Trace the full ancestry of a node back to its seed."""
        node = self.memory.load_node(node_id)
        if not node:
            return []
        chain = []
        for ancestor_id in node.lineage_path:
            ancestor = self.memory.load_node(ancestor_id)
            if ancestor:
                chain.append(ancestor)
        chain.append(node)
        return chain

    def descendants(self, node_id: str, max_depth: int = 10) -> List[TorusNode]:
        """Get all descendants of a node up to max_depth."""
        result = []
        queue = [(node_id, 0)]
        visited = set()
        while queue:
            nid, depth = queue.pop(0)
            if nid in visited or depth > max_depth:
                continue
            visited.add(nid)
            children = self.memory.get_children(nid)
            for child in children:
                result.append(child)
                queue.append((child.id, depth + 1))
        return result

    def find_by_mode(self, mode: str) -> List[TorusNode]:
        """Get all nodes in a given mode."""
        return self.memory.get_nodes_by_mode(mode)

    def find_by_essence(self, essence: str) -> List[TorusNode]:
        """Find all nodes sharing an identity fingerprint."""
        return self.memory.get_nodes_by_essence(essence)

    def all_nodes(self) -> List[TorusNode]:
        """Get every node on the torus."""
        return self.memory.get_all_nodes()

    def edges_from(self, node_id: str) -> List[TorusEdge]:
        """Get all outbound edges from a node."""
        return self.memory.get_edges_from(node_id)

    def edges_to(self, node_id: str) -> List[TorusEdge]:
        """Get all inbound edges to a node."""
        return self.memory.get_edges_to(node_id)

    # ── Metrics & State ──────────────────────────

    def metrics(self) -> TorusMetrics:
        """Get current torus geometry and statistics."""
        self._update_metrics_after_add()
        return self._metrics

    def snapshot(self) -> TorusMetrics:
        """Persist current metrics as a point-in-time snapshot."""
        m = self.metrics()
        self.memory.save_snapshot(m)
        self.hooks.fire("on_snapshot", metrics=m)
        return m

    def history(self, limit: int = 100) -> List[Dict]:
        """Retrieve snapshot history."""
        return self.memory.get_snapshots(limit)

    def _update_metrics_after_add(self):
        """Recalculate aggregate metrics."""
        all_nodes = self.memory.get_all_nodes()
        self._metrics.total_nodes = len(all_nodes)
        self._metrics.total_edges = self.memory.edge_count()
        if all_nodes:
            self._metrics.mean_coherence = sum(n.coherence for n in all_nodes) / len(all_nodes)
            self._metrics.mean_potential = sum(n.potential for n in all_nodes) / len(all_nodes)
            self._metrics.max_generation = max(n.generation for n in all_nodes)
            self._metrics.modes = list(set(n.mode for n in all_nodes))
        self._metrics.compute_geometry()

    # ── Lifecycle ─────────────────────────────────

    def close(self):
        """Close the database connection."""
        self.memory.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        m = self.metrics()
        return (
            f"Torus(nodes={m.total_nodes}, edges={m.total_edges}, "
            f"R={m.major_radius:.2f}, r={m.minor_radius:.2f}, "
            f"area={m.surface_area:.2f}, modes={m.modes})"
        )


# ─────────────────────────────────────────────────
# CONVENIENCE: Quick Torus with pre-wired modes
# ─────────────────────────────────────────────────

def create_torus(
    db_path: str = "torus.db",
    modes: Optional[Dict[str, Dict]] = None,
    **kwargs,
) -> Torus:
    """
    Factory function. Pass modes as:
        {
            "illustration": {"transform_fn": ..., "validate_fn": ...},
            "animation": {"transform_fn": ..., "validate_fn": ...},
        }
    Or just pass mode names and defaults will be used.
    """
    t = Torus(db_path=db_path, **kwargs)
    if modes:
        for name, cfg in modes.items():
            t.register_mode(
                name,
                transform_fn=cfg.get("transform_fn"),
                validate_fn=cfg.get("validate_fn"),
                metadata=cfg.get("metadata"),
            )
    return t


# ─────────────────────────────────────────────────
# CLI DEMO (if run directly)
# ─────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("  TORUS CORE — Universal Expanding Torus Framework")
    print("  Drake Enterprise, LLC")
    print("=" * 60)

    # Create a torus with three modes (like the Artist Bundle)
    db = os.path.join(tempfile.gettempdir(), "torus_demo.db")
    t = create_torus(
        db_path=db,
        modes={
            "illustration": {"metadata": {"description": "2D static art"}},
            "animation": {"metadata": {"description": "2D motion"}},
            "stage_3d": {"metadata": {"description": "3D posing/scene"}},
        }
    )

    # Seed: drop in with intent
    print("\n[SEED] Creating entry point...")
    character = t.seed(
        "cyberpunk warrior with neon katana",
        mode="illustration",
        data={"style": "anime", "palette": "neon_dark"},
        tags=["protagonist", "cyberpunk"],
    )
    print(f"  Created: {character.id} in mode={character.mode}")
    print(f"  Essence: {character.essence}")

    # Transform: flow to animation
    print("\n[TRANSFORM] Illustration → Animation...")
    anim = t.transform(character.id, "animation", {"fps": 24, "duration": 3.0})
    print(f"  Created: {anim.id} in mode={anim.mode}")
    print(f"  Essence: {anim.essence}")
    print(f"  Coherence with parent: {t.consistency.coherence_between(character, anim):.3f}")

    # Transform: animation → 3D
    print("\n[TRANSFORM] Animation → 3D Stage...")
    model = t.transform(anim.id, "stage_3d", {"mesh_resolution": "high"})
    print(f"  Created: {model.id} in mode={model.mode}")

    # Expand: bifurcate the character
    print("\n[EXPAND:BIFURCATE] Splitting character into two variants...")
    variants = t.expand(character.id, "bifurcate")
    for v in variants:
        print(f"  Variant: {v.id} | generation={v.generation} | potential={v.potential:.3f}")

    # Expand: broadcast across all modes
    print("\n[EXPAND:BROADCAST] Broadcasting 3D model to all modes...")
    broadcasts = t.expand(model.id, "broadcast")
    for b in broadcasts:
        print(f"  Broadcast: {b.id} → mode={b.mode}")

    # Expand: bridge (cross-modal shortcut)
    print("\n[EXPAND:BRIDGE] Creating shortcut from illustration to 3D...")
    bridges = t.expand(character.id, "bridge", target_mode="stage_3d")
    for b in bridges:
        print(f"  Bridge: {b.id} → mode={b.mode}")

    # Lineage
    print("\n[LINEAGE] Tracing 3D model's ancestry...")
    chain = t.lineage(model.id)
    for i, n in enumerate(chain):
        prefix = "  " + ("└─" if i == len(chain) - 1 else "├─")
        print(f"{prefix} [{n.mode}] {n.id} (gen={n.generation})")

    # Descendants
    print("\n[DESCENDANTS] All descendants of original character...")
    desc = t.descendants(character.id)
    for d in desc:
        print(f"  {d.id} | mode={d.mode} | gen={d.generation} | state={d.state}")

    # Metrics
    print("\n[METRICS] Current torus geometry:")
    m = t.snapshot()
    print(f"  Nodes: {m.total_nodes}")
    print(f"  Edges: {m.total_edges}")
    print(f"  Major radius (R): {m.major_radius:.2f}")
    print(f"  Minor radius (r): {m.minor_radius:.2f}")
    print(f"  Surface area: {m.surface_area:.2f}")
    print(f"  Volume: {m.volume:.2f}")
    print(f"  Mean coherence: {m.mean_coherence:.3f}")
    print(f"  Max generation: {m.max_generation}")
    print(f"  Modes: {m.modes}")
    print(f"  Expansions: {m.expansion_count}")
    print(f"  Transforms: {m.transform_count}")

    print(f"\n  {t}")

    t.close()
    print("\n[DONE] Torus expanding through its outputs.")
