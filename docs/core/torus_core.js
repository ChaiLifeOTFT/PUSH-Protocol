/**
 * Torus Core — Universal Expanding Torus Framework (JavaScript)
 * Drake Enterprise, LLC
 *
 * Zero-dependency. Works in:
 * - Node.js (require/import)
 * - Browser (script tag or bundler)
 * - React Native / Electron / Deno
 *
 * The torus expands through its outputs.
 *
 * Usage:
 *   const { Torus } = require('./torus_core');
 *   // or: import { Torus } from './torus_core.js';
 *
 *   const t = new Torus();
 *   t.registerMode('illustration');
 *   t.registerMode('animation');
 *   t.registerMode('stage_3d');
 *
 *   const seed = t.seed('cyberpunk warrior', 'illustration', { style: 'anime' });
 *   const anim = t.transform(seed.id, 'animation', { fps: 24 });
 *   const variants = t.expand(seed.id, 'bifurcate');
 *   const lineage = t.lineage(anim.id);
 *   const metrics = t.metrics();
 */

// ─────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────

const EXPANSION_STRATEGIES = Object.freeze({
  BIFURCATE: 'bifurcate',
  BROADCAST: 'broadcast',
  RECOMBINE: 'recombine',
  DEEPEN: 'deepen',
  AMPLIFY: 'amplify',
  BRIDGE: 'bridge',
  MUTATE: 'mutate',
});

const NODE_STATES = Object.freeze({
  SEED: 'seed',
  ACTIVE: 'active',
  TRANSFORMING: 'transforming',
  EXPANDED: 'expanded',
  DORMANT: 'dormant',
  ARCHIVED: 'archived',
});

const DEFAULTS = Object.freeze({
  COHERENCE_THRESHOLD: 0.3,
  POTENTIAL_DECAY: 0.7,
  RADIUS_GROWTH: 0.5,
  ENTROPY_RATE: 0.01,
});

// ─────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────

function generateId() {
  // Crypto-quality in Node/browser, fallback to Math.random
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 12);
  }
  return Math.random().toString(36).slice(2, 14).padEnd(12, '0');
}

async function computeHash(str) {
  // Use SubtleCrypto if available (browser + Node 15+)
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
  }
  // Fallback: simple hash (not cryptographic, but deterministic)
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(16, '0').slice(0, 16);
}

function computeHashSync(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(16, '0').slice(0, 16);
}

function now() {
  return Date.now() / 1000;
}

// ─────────────────────────────────────────────────
// DATA MODELS
// ─────────────────────────────────────────────────

class TorusNode {
  constructor(opts = {}) {
    this.id = opts.id || generateId();
    this.mode = opts.mode || 'default';
    this.state = opts.state || NODE_STATES.SEED;
    this.data = opts.data || {};
    this.essence = opts.essence || '';
    this.potential = opts.potential ?? 1.0;
    this.coherence = opts.coherence ?? 1.0;
    this.generation = opts.generation ?? 0;
    this.parentId = opts.parentId || null;
    this.childrenIds = opts.childrenIds || [];
    this.lineagePath = opts.lineagePath || [];
    this.createdAt = opts.createdAt || now();
    this.updatedAt = opts.updatedAt || now();
    this.tags = opts.tags || [];
    this.metadata = opts.metadata || {};
  }

  toJSON() {
    return {
      id: this.id, mode: this.mode, state: this.state,
      data: this.data, essence: this.essence, potential: this.potential,
      coherence: this.coherence, generation: this.generation,
      parentId: this.parentId, childrenIds: this.childrenIds,
      lineagePath: this.lineagePath, createdAt: this.createdAt,
      updatedAt: this.updatedAt, tags: this.tags, metadata: this.metadata,
    };
  }

  static fromJSON(obj) {
    return new TorusNode(obj);
  }
}

class TorusEdge {
  constructor(opts = {}) {
    this.id = opts.id || generateId();
    this.sourceId = opts.sourceId || '';
    this.targetId = opts.targetId || '';
    this.edgeType = opts.edgeType || 'transform';
    this.weight = opts.weight ?? 1.0;
    this.metadata = opts.metadata || {};
    this.createdAt = opts.createdAt || now();
  }

  toJSON() {
    return {
      id: this.id, sourceId: this.sourceId, targetId: this.targetId,
      edgeType: this.edgeType, weight: this.weight,
      metadata: this.metadata, createdAt: this.createdAt,
    };
  }

  static fromJSON(obj) {
    return new TorusEdge(obj);
  }
}

// ─────────────────────────────────────────────────
// CONSISTENCY ENGINE
// ─────────────────────────────────────────────────

class ConsistencyEngine {
  computeEssence(data, mode, parentEssence = '') {
    const raw = JSON.stringify(data, Object.keys(data).sort()) + mode + parentEssence;
    return computeHashSync(raw);
  }

  inheritEssence(parent, childData, childMode) {
    return this.computeEssence(childData, childMode, parent.essence);
  }

  coherenceBetween(nodeA, nodeB) {
    if (!nodeA.essence || !nodeB.essence) return 0;
    let shared = 0;
    const minLen = Math.min(nodeA.essence.length, nodeB.essence.length);
    for (let i = 0; i < minLen; i++) {
      if (nodeA.essence[i] === nodeB.essence[i]) shared++;
      else break;
    }
    return shared / Math.max(nodeA.essence.length, nodeB.essence.length, 1);
  }

  isCoherent(node, threshold = DEFAULTS.COHERENCE_THRESHOLD) {
    return node.coherence >= threshold;
  }

  decayPotential(potential, decayRate = DEFAULTS.POTENTIAL_DECAY) {
    return Math.max(0, potential * decayRate);
  }
}

// ─────────────────────────────────────────────────
// IN-MEMORY STORE (Portable — swap for IndexedDB, SQLite, etc.)
// ─────────────────────────────────────────────────

class TorusMemory {
  constructor() {
    this.nodes = new Map();
    this.edges = new Map();
    this.snapshots = [];
  }

  saveNode(node) { this.nodes.set(node.id, node); }
  loadNode(id) { return this.nodes.get(id) || null; }
  saveEdge(edge) { this.edges.set(edge.id, edge); }

  getChildren(nodeId) {
    return Array.from(this.nodes.values()).filter(n => n.parentId === nodeId);
  }

  getNodesByMode(mode) {
    return Array.from(this.nodes.values()).filter(n => n.mode === mode);
  }

  getNodesByEssence(essence) {
    return Array.from(this.nodes.values()).filter(n => n.essence === essence);
  }

  getAllNodes() { return Array.from(this.nodes.values()); }

  getEdgesFrom(nodeId) {
    return Array.from(this.edges.values()).filter(e => e.sourceId === nodeId);
  }

  getEdgesTo(nodeId) {
    return Array.from(this.edges.values()).filter(e => e.targetId === nodeId);
  }

  saveSnapshot(metrics) {
    this.snapshots.push({ timestamp: now(), metrics: { ...metrics } });
  }

  getSnapshots(limit = 100) {
    return this.snapshots.slice(-limit);
  }

  nodeCount() { return this.nodes.size; }
  edgeCount() { return this.edges.size; }

  // Export/Import for persistence
  export() {
    return JSON.stringify({
      nodes: Array.from(this.nodes.values()).map(n => n.toJSON()),
      edges: Array.from(this.edges.values()).map(e => e.toJSON()),
      snapshots: this.snapshots,
    });
  }

  import(jsonStr) {
    const data = JSON.parse(jsonStr);
    this.nodes.clear();
    this.edges.clear();
    (data.nodes || []).forEach(n => this.nodes.set(n.id, TorusNode.fromJSON(n)));
    (data.edges || []).forEach(e => this.edges.set(e.id, TorusEdge.fromJSON(e)));
    this.snapshots = data.snapshots || [];
  }
}

// ─────────────────────────────────────────────────
// MODE REGISTRY
// ─────────────────────────────────────────────────

class ModeRegistry {
  constructor() {
    this._modes = new Map();
  }

  register(name, transformFn = null, validateFn = null, metadata = {}) {
    this._modes.set(name, {
      transformFn: transformFn || ((data) => ({ ...data })),
      validateFn: validateFn || (() => true),
      metadata,
    });
  }

  get(name) { return this._modes.get(name) || null; }
  listModes() { return Array.from(this._modes.keys()); }
  hasMode(name) { return this._modes.has(name); }
}

// ─────────────────────────────────────────────────
// EXPANSION ENGINE
// ─────────────────────────────────────────────────

class ExpansionEngine {
  constructor(consistency, memory, modes, opts = {}) {
    this.consistency = consistency;
    this.memory = memory;
    this.modes = modes;
    this.potentialDecay = opts.potentialDecay ?? DEFAULTS.POTENTIAL_DECAY;
  }

  _makeChild(parent, data, mode, edgeType, tags = null) {
    const child = new TorusNode({
      mode,
      state: NODE_STATES.ACTIVE,
      data,
      essence: this.consistency.inheritEssence(parent, data, mode),
      potential: this.consistency.decayPotential(parent.potential, this.potentialDecay),
      coherence: Math.max(0, parent.coherence - DEFAULTS.ENTROPY_RATE),
      generation: parent.generation + 1,
      parentId: parent.id,
      lineagePath: [...parent.lineagePath, parent.id],
      tags: tags || [...parent.tags],
    });
    const edge = new TorusEdge({
      sourceId: parent.id,
      targetId: child.id,
      edgeType,
      weight: child.coherence,
    });
    parent.childrenIds.push(child.id);
    parent.state = NODE_STATES.EXPANDED;
    parent.updatedAt = now();
    return { child, edge };
  }

  bifurcate(node) {
    return ['_alpha', '_beta'].map((suffix, i) => {
      const data = { ...node.data, _branch: suffix, _bifurcation_index: i };
      const tags = [...node.tags, `bifurcation${suffix}`];
      return this._makeChild(node, data, node.mode, 'bifurcate', tags);
    });
  }

  broadcast(node) {
    const results = [];
    for (const modeName of this.modes.listModes()) {
      if (modeName === node.mode) continue;
      const cfg = this.modes.get(modeName);
      if (cfg && cfg.validateFn(node.data)) {
        const transformed = cfg.transformFn(node.data, node.mode);
        results.push(this._makeChild(node, transformed, modeName, 'broadcast'));
      }
    }
    return results;
  }

  recombine(nodeA, nodeB) {
    const merged = { ...nodeA.data, ...nodeB.data, _recombined_from: [nodeA.id, nodeB.id] };
    const targetMode = nodeA.coherence >= nodeB.coherence ? nodeA.mode : nodeB.mode;
    const child = new TorusNode({
      mode: targetMode,
      state: NODE_STATES.ACTIVE,
      data: merged,
      essence: this.consistency.computeEssence(merged, targetMode, nodeA.essence + nodeB.essence),
      potential: (nodeA.potential + nodeB.potential) * this.potentialDecay,
      coherence: (nodeA.coherence + nodeB.coherence) / 2,
      generation: Math.max(nodeA.generation, nodeB.generation) + 1,
      parentId: nodeA.id,
      lineagePath: [...nodeA.lineagePath, nodeA.id],
      tags: [...new Set([...nodeA.tags, ...nodeB.tags])],
    });
    const edges = [
      new TorusEdge({ sourceId: nodeA.id, targetId: child.id, edgeType: 'recombine' }),
      new TorusEdge({ sourceId: nodeB.id, targetId: child.id, edgeType: 'recombine' }),
    ];
    nodeA.childrenIds.push(child.id);
    nodeB.childrenIds.push(child.id);
    return { child, edges };
  }

  deepen(node, depthData = {}) {
    const data = { ...node.data, _depth_level: node.generation + 1, ...depthData };
    const result = this._makeChild(node, data, node.mode, 'deepen');
    result.child.potential = node.potential * 0.9;
    return result;
  }

  amplify(node, factor = 1.5) {
    node.potential = Math.min(node.potential * factor, 10.0);
    node.coherence = Math.min(node.coherence * 1.1, 1.0);
    node.updatedAt = now();
    node.tags.push('amplified');
    return node;
  }

  bridge(node, targetMode) {
    const cfg = this.modes.get(targetMode);
    const data = cfg ? cfg.transformFn(node.data, node.mode) : { ...node.data };
    const result = this._makeChild(node, data, targetMode, 'bridge');
    result.child.tags.push('bridged');
    return result;
  }

  mutate(node, mutationFn = null) {
    const data = mutationFn
      ? mutationFn({ ...node.data })
      : { ...node.data, _mutated: true, _mutation_seed: generateId() };
    const result = this._makeChild(node, data, node.mode, 'mutate');
    result.child.coherence = Math.max(0, result.child.coherence - DEFAULTS.ENTROPY_RATE * 2);
    return result;
  }
}

// ─────────────────────────────────────────────────
// HOOKS
// ─────────────────────────────────────────────────

class HookRegistry {
  constructor() {
    this._hooks = {};
  }

  register(event, fn) {
    if (!this._hooks[event]) this._hooks[event] = [];
    this._hooks[event].push(fn);
  }

  fire(event, payload = {}) {
    (this._hooks[event] || []).forEach(fn => fn(payload));
  }
}

// ─────────────────────────────────────────────────
// THE TORUS
// ─────────────────────────────────────────────────

class Torus {
  constructor(opts = {}) {
    this.memory = new TorusMemory();
    this.consistency = new ConsistencyEngine();
    this.modes = new ModeRegistry();
    this.hooks = new HookRegistry();
    this.expansion = new ExpansionEngine(
      this.consistency, this.memory, this.modes,
      { potentialDecay: opts.potentialDecay ?? DEFAULTS.POTENTIAL_DECAY }
    );

    this._metrics = {
      totalNodes: 0, totalEdges: 0,
      majorRadius: 1.0, minorRadius: 0.5,
      surfaceArea: 0, volume: 0,
      meanCoherence: 1.0, meanPotential: 1.0,
      maxGeneration: 0, modes: [],
      expansionCount: 0, transformCount: 0,
    };

    this._coherenceThreshold = opts.coherenceThreshold ?? DEFAULTS.COHERENCE_THRESHOLD;
    this._radiusGrowth = opts.radiusGrowth ?? DEFAULTS.RADIUS_GROWTH;

    this.modes.register('default');
  }

  // ── Mode Management ──

  registerMode(name, transformFn = null, validateFn = null, metadata = {}) {
    this.modes.register(name, transformFn, validateFn, metadata);
    return this;
  }

  // ── Core Operations ──

  seed(intent, mode = 'default', data = {}, tags = []) {
    if (!this.modes.hasMode(mode)) this.modes.register(mode);

    const nodeData = { ...data, _intent: intent };
    const node = new TorusNode({
      mode,
      state: NODE_STATES.ACTIVE,
      data: nodeData,
      essence: this.consistency.computeEssence(nodeData, mode),
      tags: [...tags],
    });

    this.memory.saveNode(node);
    this._refreshMetrics();
    this.hooks.fire('on_seed', { node });
    return node;
  }

  transform(nodeId, targetMode, transformData = {}) {
    const source = this.memory.loadNode(nodeId);
    if (!source) return null;

    if (!this.modes.hasMode(targetMode)) this.modes.register(targetMode);

    const cfg = this.modes.get(targetMode);
    let newData = cfg ? cfg.transformFn(source.data, source.mode) : { ...source.data };
    Object.assign(newData, transformData);

    const child = new TorusNode({
      mode: targetMode,
      state: NODE_STATES.ACTIVE,
      data: newData,
      essence: this.consistency.inheritEssence(source, newData, targetMode),
      potential: this.consistency.decayPotential(source.potential),
      coherence: source.coherence,
      generation: source.generation + 1,
      parentId: source.id,
      lineagePath: [...source.lineagePath, source.id],
      tags: [...source.tags],
    });

    const edge = new TorusEdge({
      sourceId: source.id, targetId: child.id,
      edgeType: 'transform', weight: child.coherence,
    });

    source.childrenIds.push(child.id);
    source.state = NODE_STATES.EXPANDED;
    source.updatedAt = now();

    this.memory.saveNode(source);
    this.memory.saveNode(child);
    this.memory.saveEdge(edge);
    this._metrics.transformCount++;
    this._refreshMetrics();
    this.hooks.fire('on_transform', { source, target: child, edge });
    return child;
  }

  expand(nodeId, strategy = 'bifurcate', opts = {}) {
    const node = this.memory.loadNode(nodeId);
    if (!node) return [];
    if (!this.consistency.isCoherent(node, this._coherenceThreshold)) return [];

    let results = [];
    let edges = [];

    switch (strategy) {
      case EXPANSION_STRATEGIES.BIFURCATE: {
        for (const { child, edge } of this.expansion.bifurcate(node)) {
          results.push(child); edges.push(edge);
        }
        break;
      }
      case EXPANSION_STRATEGIES.BROADCAST: {
        for (const { child, edge } of this.expansion.broadcast(node)) {
          results.push(child); edges.push(edge);
        }
        break;
      }
      case EXPANSION_STRATEGIES.RECOMBINE: {
        if (!opts.targetNodeId) return [];
        const target = this.memory.loadNode(opts.targetNodeId);
        if (!target) return [];
        const { child, edges: eList } = this.expansion.recombine(node, target);
        results.push(child); edges.push(...eList);
        this.memory.saveNode(target);
        break;
      }
      case EXPANSION_STRATEGIES.DEEPEN: {
        const { child, edge } = this.expansion.deepen(node, opts.depthData);
        results.push(child); edges.push(edge);
        break;
      }
      case EXPANSION_STRATEGIES.AMPLIFY: {
        const amplified = this.expansion.amplify(node, opts.factor);
        this.memory.saveNode(amplified);
        this.hooks.fire('on_expand', { parent: node, children: [amplified], strategy });
        return [amplified];
      }
      case EXPANSION_STRATEGIES.BRIDGE: {
        if (!opts.targetMode) return [];
        const { child, edge } = this.expansion.bridge(node, opts.targetMode);
        results.push(child); edges.push(edge);
        break;
      }
      case EXPANSION_STRATEGIES.MUTATE: {
        const { child, edge } = this.expansion.mutate(node, opts.mutationFn);
        results.push(child); edges.push(edge);
        break;
      }
    }

    this.memory.saveNode(node);
    results.forEach(c => this.memory.saveNode(c));
    edges.forEach(e => this.memory.saveEdge(e));

    this._metrics.majorRadius += this._radiusGrowth * results.length;
    this._metrics.minorRadius += this._radiusGrowth * 0.3 * results.length;
    this._metrics.expansionCount++;
    this._refreshMetrics();
    this.hooks.fire('on_expand', { parent: node, children: results, strategy });
    return results;
  }

  // ── Query ──

  get(nodeId) { return this.memory.loadNode(nodeId); }

  lineage(nodeId) {
    const node = this.memory.loadNode(nodeId);
    if (!node) return [];
    const chain = node.lineagePath
      .map(id => this.memory.loadNode(id))
      .filter(Boolean);
    chain.push(node);
    return chain;
  }

  descendants(nodeId, maxDepth = 10) {
    const result = [];
    const queue = [{ id: nodeId, depth: 0 }];
    const visited = new Set();
    while (queue.length) {
      const { id, depth } = queue.shift();
      if (visited.has(id) || depth > maxDepth) continue;
      visited.add(id);
      const children = this.memory.getChildren(id);
      for (const child of children) {
        result.push(child);
        queue.push({ id: child.id, depth: depth + 1 });
      }
    }
    return result;
  }

  findByMode(mode) { return this.memory.getNodesByMode(mode); }
  findByEssence(essence) { return this.memory.getNodesByEssence(essence); }
  allNodes() { return this.memory.getAllNodes(); }
  edgesFrom(nodeId) { return this.memory.getEdgesFrom(nodeId); }
  edgesTo(nodeId) { return this.memory.getEdgesTo(nodeId); }

  // ── Metrics ──

  metrics() { this._refreshMetrics(); return { ...this._metrics }; }

  snapshot() {
    const m = this.metrics();
    this.memory.saveSnapshot(m);
    this.hooks.fire('on_snapshot', { metrics: m });
    return m;
  }

  history(limit = 100) { return this.memory.getSnapshots(limit); }

  _refreshMetrics() {
    const all = this.memory.getAllNodes();
    this._metrics.totalNodes = all.length;
    this._metrics.totalEdges = this.memory.edgeCount();
    if (all.length) {
      this._metrics.meanCoherence = all.reduce((s, n) => s + n.coherence, 0) / all.length;
      this._metrics.meanPotential = all.reduce((s, n) => s + n.potential, 0) / all.length;
      this._metrics.maxGeneration = Math.max(...all.map(n => n.generation));
      this._metrics.modes = [...new Set(all.map(n => n.mode))];
    }
    const R = this._metrics.majorRadius;
    const r = this._metrics.minorRadius;
    this._metrics.surfaceArea = Math.pow(2 * Math.PI, 2) * R * r;
    this._metrics.volume = 2 * Math.pow(Math.PI, 2) * R * r * r;
  }

  // ── Persistence ──

  export() { return this.memory.export(); }
  import(jsonStr) { this.memory.import(jsonStr); this._refreshMetrics(); }

  toString() {
    const m = this.metrics();
    return `Torus(nodes=${m.totalNodes}, edges=${m.totalEdges}, R=${m.majorRadius.toFixed(2)}, r=${m.minorRadius.toFixed(2)}, area=${m.surfaceArea.toFixed(2)}, modes=[${m.modes.join(',')}])`;
  }
}

// ─────────────────────────────────────────────────
// EXPORTS (Universal Module)
// ─────────────────────────────────────────────────

if (typeof module !== 'undefined' && module.exports) {
  // Node.js / CommonJS
  module.exports = {
    Torus, TorusNode, TorusEdge, ConsistencyEngine,
    ModeRegistry, ExpansionEngine, HookRegistry, TorusMemory,
    EXPANSION_STRATEGIES, NODE_STATES, DEFAULTS,
  };
} else if (typeof window !== 'undefined') {
  // Browser global
  window.TorusCore = {
    Torus, TorusNode, TorusEdge, ConsistencyEngine,
    ModeRegistry, ExpansionEngine, HookRegistry, TorusMemory,
    EXPANSION_STRATEGIES, NODE_STATES, DEFAULTS,
  };
}

// Also support ES module export
// export { Torus, TorusNode, TorusEdge, ... };
