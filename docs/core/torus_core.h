/**
 * Torus Core — Universal Expanding Torus Framework (C99)
 * Drake Enterprise, LLC
 *
 * Single-header library. Zero dependencies beyond stdlib.
 * For embedded systems, microcontrollers, real-time hardware, WASM.
 *
 * #define TORUS_IMPLEMENTATION in ONE .c file before including:
 *
 *   #define TORUS_IMPLEMENTATION
 *   #include "torus_core.h"
 *
 * All other files just #include "torus_core.h" for declarations.
 *
 * Configuration (define before including):
 *   TORUS_MAX_NODES       - Max nodes (default 4096)
 *   TORUS_MAX_EDGES       - Max edges (default 8192)
 *   TORUS_MAX_MODES       - Max modes (default 32)
 *   TORUS_MAX_CHILDREN    - Max children per node (default 64)
 *   TORUS_MAX_LINEAGE     - Max lineage depth (default 256)
 *   TORUS_MAX_TAGS        - Max tags per node (default 16)
 *   TORUS_ID_LEN          - ID string length (default 13)
 *   TORUS_ESSENCE_LEN     - Essence hash length (default 17)
 *   TORUS_TAG_LEN         - Max tag string length (default 32)
 *   TORUS_MODE_NAME_LEN   - Max mode name length (default 32)
 *
 * The torus expands through its outputs.
 */

#ifndef TORUS_CORE_H
#define TORUS_CORE_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ─── Configuration Defaults ─────────────────── */

#ifndef TORUS_MAX_NODES
#define TORUS_MAX_NODES 4096
#endif

#ifndef TORUS_MAX_EDGES
#define TORUS_MAX_EDGES 8192
#endif

#ifndef TORUS_MAX_MODES
#define TORUS_MAX_MODES 32
#endif

#ifndef TORUS_MAX_CHILDREN
#define TORUS_MAX_CHILDREN 64
#endif

#ifndef TORUS_MAX_LINEAGE
#define TORUS_MAX_LINEAGE 256
#endif

#ifndef TORUS_MAX_TAGS
#define TORUS_MAX_TAGS 16
#endif

#ifndef TORUS_ID_LEN
#define TORUS_ID_LEN 13
#endif

#ifndef TORUS_ESSENCE_LEN
#define TORUS_ESSENCE_LEN 17
#endif

#ifndef TORUS_TAG_LEN
#define TORUS_TAG_LEN 32
#endif

#ifndef TORUS_MODE_NAME_LEN
#define TORUS_MODE_NAME_LEN 32
#endif

/* ─── Constants ──────────────────────────────── */

#define TORUS_COHERENCE_THRESHOLD 0.3f
#define TORUS_POTENTIAL_DECAY     0.7f
#define TORUS_RADIUS_GROWTH       0.5f
#define TORUS_ENTROPY_RATE        0.01f

/* ─── Enums ──────────────────────────────────── */

typedef enum {
    TORUS_EXPAND_BIFURCATE = 0,
    TORUS_EXPAND_BROADCAST,
    TORUS_EXPAND_RECOMBINE,
    TORUS_EXPAND_DEEPEN,
    TORUS_EXPAND_AMPLIFY,
    TORUS_EXPAND_BRIDGE,
    TORUS_EXPAND_MUTATE,
} torus_expansion_strategy_t;

typedef enum {
    TORUS_STATE_SEED = 0,
    TORUS_STATE_ACTIVE,
    TORUS_STATE_TRANSFORMING,
    TORUS_STATE_EXPANDED,
    TORUS_STATE_DORMANT,
    TORUS_STATE_ARCHIVED,
} torus_node_state_t;

typedef enum {
    TORUS_EDGE_TRANSFORM = 0,
    TORUS_EDGE_BIFURCATE,
    TORUS_EDGE_BROADCAST,
    TORUS_EDGE_RECOMBINE,
    TORUS_EDGE_DEEPEN,
    TORUS_EDGE_BRIDGE,
    TORUS_EDGE_MUTATE,
} torus_edge_type_t;

typedef enum {
    TORUS_OK = 0,
    TORUS_ERR_FULL,
    TORUS_ERR_NOT_FOUND,
    TORUS_ERR_INCOHERENT,
    TORUS_ERR_INVALID_MODE,
    TORUS_ERR_INVALID_PARAM,
} torus_result_t;

/* ─── Data Structures ────────────────────────── */

typedef struct {
    char    id[TORUS_ID_LEN];
    int     mode_index;
    torus_node_state_t state;
    char    essence[TORUS_ESSENCE_LEN];
    float   potential;
    float   coherence;
    int     generation;
    int     parent_index;                      /* -1 if root */
    int     children_indices[TORUS_MAX_CHILDREN];
    int     children_count;
    int     lineage_indices[TORUS_MAX_LINEAGE];
    int     lineage_count;
    double  created_at;
    double  updated_at;
    char    tags[TORUS_MAX_TAGS][TORUS_TAG_LEN];
    int     tag_count;
    uint64_t user_data;                        /* Opaque pointer/handle to app-specific data */
    uint8_t  active;                           /* 1 = alive, 0 = slot free */
} torus_node_t;

typedef struct {
    char    id[TORUS_ID_LEN];
    int     source_index;
    int     target_index;
    torus_edge_type_t edge_type;
    float   weight;
    double  created_at;
    uint8_t active;
} torus_edge_t;

typedef struct {
    char name[TORUS_MODE_NAME_LEN];
    uint8_t active;
} torus_mode_t;

typedef struct {
    int     total_nodes;
    int     total_edges;
    float   major_radius;
    float   minor_radius;
    float   surface_area;
    float   volume;
    float   mean_coherence;
    float   mean_potential;
    int     max_generation;
    int     expansion_count;
    int     transform_count;
} torus_metrics_t;

typedef struct {
    torus_node_t    nodes[TORUS_MAX_NODES];
    torus_edge_t    edges[TORUS_MAX_EDGES];
    torus_mode_t    modes[TORUS_MAX_MODES];
    int             node_count;
    int             edge_count;
    int             mode_count;
    torus_metrics_t metrics;
    float           coherence_threshold;
    float           potential_decay;
    float           radius_growth;
    uint32_t        rng_state;                 /* Simple PRNG for IDs */
} torus_t;

/* ─── API Declarations ───────────────────────── */

/* Lifecycle */
void            torus_init(torus_t *t);
void            torus_reset(torus_t *t);

/* Mode Management */
torus_result_t  torus_register_mode(torus_t *t, const char *name);
int             torus_find_mode(const torus_t *t, const char *name);

/* Core Operations */
torus_result_t  torus_seed(torus_t *t, const char *mode, uint64_t user_data, int *out_index);
torus_result_t  torus_transform(torus_t *t, int node_index, const char *target_mode, int *out_index);
torus_result_t  torus_expand(torus_t *t, int node_index, torus_expansion_strategy_t strategy,
                             int target_node_index, const char *target_mode,
                             int *out_indices, int *out_count, int max_out);

/* Query */
torus_node_t   *torus_get_node(torus_t *t, int index);
int             torus_lineage(const torus_t *t, int node_index, int *out_indices, int max_out);
int             torus_descendants(const torus_t *t, int node_index, int *out_indices, int max_out, int max_depth);
int             torus_find_by_mode(const torus_t *t, const char *mode, int *out_indices, int max_out);

/* Metrics */
torus_metrics_t torus_metrics(torus_t *t);

/* Utility */
void            torus_generate_id(torus_t *t, char *out);
void            torus_compute_essence(const char *input, size_t len, char *out);

#ifdef __cplusplus
}
#endif

/* ═══════════════════════════════════════════════ */
/*              IMPLEMENTATION                     */
/* ═══════════════════════════════════════════════ */

#ifdef TORUS_IMPLEMENTATION

#include <string.h>
#include <math.h>
#include <time.h>

/* ─── Internal Helpers ───────────────────────── */

static double _torus_now(void) {
    return (double)time(NULL);
}

static uint32_t _torus_xorshift(uint32_t *state) {
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

void torus_generate_id(torus_t *t, char *out) {
    static const char hex[] = "0123456789abcdef";
    for (int i = 0; i < TORUS_ID_LEN - 1; i++) {
        out[i] = hex[_torus_xorshift(&t->rng_state) % 16];
    }
    out[TORUS_ID_LEN - 1] = '\0';
}

void torus_compute_essence(const char *input, size_t len, char *out) {
    /* Simple FNV-1a hash → hex string (not crypto, but deterministic & fast) */
    uint64_t hash = 14695981039346656037ULL;
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint8_t)input[i];
        hash *= 1099511628211ULL;
    }
    static const char hex[] = "0123456789abcdef";
    for (int i = 0; i < TORUS_ESSENCE_LEN - 1; i++) {
        out[i] = hex[(hash >> (i * 4)) & 0xF];
    }
    out[TORUS_ESSENCE_LEN - 1] = '\0';
}

static int _torus_alloc_node(torus_t *t) {
    for (int i = 0; i < TORUS_MAX_NODES; i++) {
        if (!t->nodes[i].active) return i;
    }
    return -1;
}

static int _torus_alloc_edge(torus_t *t) {
    for (int i = 0; i < TORUS_MAX_EDGES; i++) {
        if (!t->edges[i].active) return i;
    }
    return -1;
}

static void _torus_update_metrics(torus_t *t) {
    int count = 0;
    float sum_c = 0, sum_p = 0;
    int max_gen = 0;
    for (int i = 0; i < TORUS_MAX_NODES; i++) {
        if (!t->nodes[i].active) continue;
        count++;
        sum_c += t->nodes[i].coherence;
        sum_p += t->nodes[i].potential;
        if (t->nodes[i].generation > max_gen) max_gen = t->nodes[i].generation;
    }
    int ecount = 0;
    for (int i = 0; i < TORUS_MAX_EDGES; i++) {
        if (t->edges[i].active) ecount++;
    }
    t->metrics.total_nodes = count;
    t->metrics.total_edges = ecount;
    t->metrics.mean_coherence = count > 0 ? sum_c / count : 1.0f;
    t->metrics.mean_potential = count > 0 ? sum_p / count : 1.0f;
    t->metrics.max_generation = max_gen;

    float R = t->metrics.major_radius;
    float r = t->metrics.minor_radius;
    float pi2 = (float)(2.0 * M_PI);
    t->metrics.surface_area = pi2 * pi2 * R * r;
    t->metrics.volume = 2.0f * (float)(M_PI * M_PI) * R * r * r;
}

static void _torus_init_node(torus_node_t *n) {
    memset(n, 0, sizeof(*n));
    n->parent_index = -1;
    n->potential = 1.0f;
    n->coherence = 1.0f;
    n->active = 1;
    n->created_at = 0;
    n->updated_at = 0;
}

/* ─── Lifecycle ──────────────────────────────── */

void torus_init(torus_t *t) {
    memset(t, 0, sizeof(*t));
    t->coherence_threshold = TORUS_COHERENCE_THRESHOLD;
    t->potential_decay = TORUS_POTENTIAL_DECAY;
    t->radius_growth = TORUS_RADIUS_GROWTH;
    t->metrics.major_radius = 1.0f;
    t->metrics.minor_radius = 0.5f;
    t->rng_state = (uint32_t)time(NULL) ^ 0xDEADBEEF;

    /* Mark all slots free */
    for (int i = 0; i < TORUS_MAX_NODES; i++) t->nodes[i].active = 0;
    for (int i = 0; i < TORUS_MAX_EDGES; i++) t->edges[i].active = 0;
    for (int i = 0; i < TORUS_MAX_MODES; i++) t->modes[i].active = 0;

    /* Register default mode */
    torus_register_mode(t, "default");
}

void torus_reset(torus_t *t) {
    torus_init(t);
}

/* ─── Mode Management ────────────────────────── */

torus_result_t torus_register_mode(torus_t *t, const char *name) {
    /* Check if already registered */
    if (torus_find_mode(t, name) >= 0) return TORUS_OK;

    for (int i = 0; i < TORUS_MAX_MODES; i++) {
        if (!t->modes[i].active) {
            strncpy(t->modes[i].name, name, TORUS_MODE_NAME_LEN - 1);
            t->modes[i].name[TORUS_MODE_NAME_LEN - 1] = '\0';
            t->modes[i].active = 1;
            t->mode_count++;
            return TORUS_OK;
        }
    }
    return TORUS_ERR_FULL;
}

int torus_find_mode(const torus_t *t, const char *name) {
    for (int i = 0; i < TORUS_MAX_MODES; i++) {
        if (t->modes[i].active && strncmp(t->modes[i].name, name, TORUS_MODE_NAME_LEN) == 0) {
            return i;
        }
    }
    return -1;
}

/* ─── Core: Seed ─────────────────────────────── */

torus_result_t torus_seed(torus_t *t, const char *mode, uint64_t user_data, int *out_index) {
    int mi = torus_find_mode(t, mode);
    if (mi < 0) {
        if (torus_register_mode(t, mode) != TORUS_OK) return TORUS_ERR_FULL;
        mi = torus_find_mode(t, mode);
    }

    int ni = _torus_alloc_node(t);
    if (ni < 0) return TORUS_ERR_FULL;

    torus_node_t *n = &t->nodes[ni];
    _torus_init_node(n);
    torus_generate_id(t, n->id);
    n->mode_index = mi;
    n->state = TORUS_STATE_ACTIVE;
    n->user_data = user_data;
    n->created_at = _torus_now();
    n->updated_at = n->created_at;

    /* Compute essence from mode name (minimal — app should enrich) */
    torus_compute_essence(mode, strlen(mode), n->essence);

    t->node_count++;
    _torus_update_metrics(t);

    if (out_index) *out_index = ni;
    return TORUS_OK;
}

/* ─── Core: Transform ────────────────────────── */

torus_result_t torus_transform(torus_t *t, int node_index, const char *target_mode, int *out_index) {
    if (node_index < 0 || node_index >= TORUS_MAX_NODES || !t->nodes[node_index].active)
        return TORUS_ERR_NOT_FOUND;

    int mi = torus_find_mode(t, target_mode);
    if (mi < 0) {
        if (torus_register_mode(t, target_mode) != TORUS_OK) return TORUS_ERR_FULL;
        mi = torus_find_mode(t, target_mode);
    }

    torus_node_t *src = &t->nodes[node_index];

    /* Allocate child node */
    int ci = _torus_alloc_node(t);
    if (ci < 0) return TORUS_ERR_FULL;

    torus_node_t *child = &t->nodes[ci];
    _torus_init_node(child);
    torus_generate_id(t, child->id);
    child->mode_index = mi;
    child->state = TORUS_STATE_ACTIVE;
    child->potential = src->potential * t->potential_decay;
    child->coherence = src->coherence;
    child->generation = src->generation + 1;
    child->parent_index = node_index;
    child->user_data = src->user_data;
    child->created_at = _torus_now();
    child->updated_at = child->created_at;

    /* Inherit lineage */
    child->lineage_count = src->lineage_count;
    if (child->lineage_count < TORUS_MAX_LINEAGE) {
        memcpy(child->lineage_indices, src->lineage_indices, sizeof(int) * src->lineage_count);
        child->lineage_indices[child->lineage_count++] = node_index;
    }

    /* Compute essence with parent chain */
    char buf[256];
    int blen = snprintf(buf, sizeof(buf), "%s:%s:%s", target_mode, src->essence, src->id);
    torus_compute_essence(buf, (size_t)blen, child->essence);

    /* Create edge */
    int ei = _torus_alloc_edge(t);
    if (ei >= 0) {
        torus_edge_t *e = &t->edges[ei];
        memset(e, 0, sizeof(*e));
        torus_generate_id(t, e->id);
        e->source_index = node_index;
        e->target_index = ci;
        e->edge_type = TORUS_EDGE_TRANSFORM;
        e->weight = child->coherence;
        e->created_at = _torus_now();
        e->active = 1;
        t->edge_count++;
    }

    /* Update parent */
    if (src->children_count < TORUS_MAX_CHILDREN) {
        src->children_indices[src->children_count++] = ci;
    }
    src->state = TORUS_STATE_EXPANDED;
    src->updated_at = _torus_now();

    t->node_count++;
    t->metrics.transform_count++;
    _torus_update_metrics(t);

    if (out_index) *out_index = ci;
    return TORUS_OK;
}

/* ─── Core: Expand ───────────────────────────── */

torus_result_t torus_expand(torus_t *t, int node_index, torus_expansion_strategy_t strategy,
                            int target_node_index, const char *target_mode,
                            int *out_indices, int *out_count, int max_out)
{
    if (node_index < 0 || node_index >= TORUS_MAX_NODES || !t->nodes[node_index].active)
        return TORUS_ERR_NOT_FOUND;

    torus_node_t *node = &t->nodes[node_index];
    if (node->coherence < t->coherence_threshold)
        return TORUS_ERR_INCOHERENT;

    int count = 0;

    switch (strategy) {
        case TORUS_EXPAND_BIFURCATE: {
            /* Create two children in same mode */
            for (int i = 0; i < 2 && count < max_out; i++) {
                int ci = _torus_alloc_node(t);
                if (ci < 0) break;

                torus_node_t *child = &t->nodes[ci];
                _torus_init_node(child);
                torus_generate_id(t, child->id);
                child->mode_index = node->mode_index;
                child->state = TORUS_STATE_ACTIVE;
                child->potential = node->potential * t->potential_decay;
                child->coherence = node->coherence - TORUS_ENTROPY_RATE;
                if (child->coherence < 0) child->coherence = 0;
                child->generation = node->generation + 1;
                child->parent_index = node_index;
                child->user_data = node->user_data;
                child->created_at = _torus_now();
                child->updated_at = child->created_at;

                /* Lineage */
                child->lineage_count = node->lineage_count;
                if (child->lineage_count < TORUS_MAX_LINEAGE) {
                    memcpy(child->lineage_indices, node->lineage_indices, sizeof(int) * node->lineage_count);
                    child->lineage_indices[child->lineage_count++] = node_index;
                }

                char buf[256];
                int blen = snprintf(buf, sizeof(buf), "bif:%d:%s:%s", i, node->essence, node->id);
                torus_compute_essence(buf, (size_t)blen, child->essence);

                /* Edge */
                int ei = _torus_alloc_edge(t);
                if (ei >= 0) {
                    torus_edge_t *e = &t->edges[ei];
                    memset(e, 0, sizeof(*e));
                    torus_generate_id(t, e->id);
                    e->source_index = node_index;
                    e->target_index = ci;
                    e->edge_type = TORUS_EDGE_BIFURCATE;
                    e->weight = child->coherence;
                    e->created_at = _torus_now();
                    e->active = 1;
                    t->edge_count++;
                }

                if (node->children_count < TORUS_MAX_CHILDREN) {
                    node->children_indices[node->children_count++] = ci;
                }
                t->node_count++;
                if (out_indices) out_indices[count] = ci;
                count++;
            }
            break;
        }

        case TORUS_EXPAND_BRIDGE: {
            if (!target_mode) return TORUS_ERR_INVALID_PARAM;
            int ci;
            torus_result_t r = torus_transform(t, node_index, target_mode, &ci);
            if (r != TORUS_OK) return r;
            /* Re-tag the edge type */
            for (int i = 0; i < TORUS_MAX_EDGES; i++) {
                if (t->edges[i].active && t->edges[i].target_index == ci) {
                    t->edges[i].edge_type = TORUS_EDGE_BRIDGE;
                    break;
                }
            }
            if (out_indices && count < max_out) out_indices[count] = ci;
            count++;
            break;
        }

        case TORUS_EXPAND_AMPLIFY: {
            node->potential *= 1.5f;
            if (node->potential > 10.0f) node->potential = 10.0f;
            node->coherence *= 1.1f;
            if (node->coherence > 1.0f) node->coherence = 1.0f;
            node->updated_at = _torus_now();
            if (out_indices && count < max_out) out_indices[count] = node_index;
            count++;
            break;
        }

        case TORUS_EXPAND_DEEPEN: {
            int ci = _torus_alloc_node(t);
            if (ci < 0) return TORUS_ERR_FULL;

            torus_node_t *child = &t->nodes[ci];
            _torus_init_node(child);
            torus_generate_id(t, child->id);
            child->mode_index = node->mode_index;
            child->state = TORUS_STATE_ACTIVE;
            child->potential = node->potential * 0.9f;
            child->coherence = node->coherence - TORUS_ENTROPY_RATE;
            if (child->coherence < 0) child->coherence = 0;
            child->generation = node->generation + 1;
            child->parent_index = node_index;
            child->user_data = node->user_data;
            child->created_at = _torus_now();
            child->updated_at = child->created_at;

            child->lineage_count = node->lineage_count;
            if (child->lineage_count < TORUS_MAX_LINEAGE) {
                memcpy(child->lineage_indices, node->lineage_indices, sizeof(int) * node->lineage_count);
                child->lineage_indices[child->lineage_count++] = node_index;
            }

            char buf[256];
            int blen = snprintf(buf, sizeof(buf), "deep:%s:%s", node->essence, node->id);
            torus_compute_essence(buf, (size_t)blen, child->essence);

            int ei = _torus_alloc_edge(t);
            if (ei >= 0) {
                torus_edge_t *e = &t->edges[ei];
                memset(e, 0, sizeof(*e));
                torus_generate_id(t, e->id);
                e->source_index = node_index;
                e->target_index = ci;
                e->edge_type = TORUS_EDGE_DEEPEN;
                e->weight = child->coherence;
                e->created_at = _torus_now();
                e->active = 1;
                t->edge_count++;
            }

            if (node->children_count < TORUS_MAX_CHILDREN) {
                node->children_indices[node->children_count++] = ci;
            }
            t->node_count++;
            if (out_indices && count < max_out) out_indices[count] = ci;
            count++;
            break;
        }

        case TORUS_EXPAND_BROADCAST: {
            /* Clone to all registered modes except current */
            for (int mi = 0; mi < TORUS_MAX_MODES && count < max_out; mi++) {
                if (!t->modes[mi].active) continue;
                if (mi == node->mode_index) continue;

                int ci;
                torus_result_t r = torus_transform(t, node_index, t->modes[mi].name, &ci);
                if (r != TORUS_OK) continue;

                for (int ei = 0; ei < TORUS_MAX_EDGES; ei++) {
                    if (t->edges[ei].active && t->edges[ei].target_index == ci) {
                        t->edges[ei].edge_type = TORUS_EDGE_BROADCAST;
                        break;
                    }
                }
                if (out_indices) out_indices[count] = ci;
                count++;
            }
            break;
        }

        case TORUS_EXPAND_MUTATE: {
            int ci = _torus_alloc_node(t);
            if (ci < 0) return TORUS_ERR_FULL;

            torus_node_t *child = &t->nodes[ci];
            _torus_init_node(child);
            torus_generate_id(t, child->id);
            child->mode_index = node->mode_index;
            child->state = TORUS_STATE_ACTIVE;
            child->potential = node->potential * t->potential_decay;
            child->coherence = node->coherence - TORUS_ENTROPY_RATE * 2;
            if (child->coherence < 0) child->coherence = 0;
            child->generation = node->generation + 1;
            child->parent_index = node_index;
            child->user_data = node->user_data;
            child->created_at = _torus_now();
            child->updated_at = child->created_at;

            child->lineage_count = node->lineage_count;
            if (child->lineage_count < TORUS_MAX_LINEAGE) {
                memcpy(child->lineage_indices, node->lineage_indices, sizeof(int) * node->lineage_count);
                child->lineage_indices[child->lineage_count++] = node_index;
            }

            char buf[256];
            int blen = snprintf(buf, sizeof(buf), "mut:%u:%s", _torus_xorshift(&t->rng_state), node->essence);
            torus_compute_essence(buf, (size_t)blen, child->essence);

            int ei = _torus_alloc_edge(t);
            if (ei >= 0) {
                torus_edge_t *e = &t->edges[ei];
                memset(e, 0, sizeof(*e));
                torus_generate_id(t, e->id);
                e->source_index = node_index;
                e->target_index = ci;
                e->edge_type = TORUS_EDGE_MUTATE;
                e->weight = child->coherence;
                e->created_at = _torus_now();
                e->active = 1;
                t->edge_count++;
            }

            if (node->children_count < TORUS_MAX_CHILDREN) {
                node->children_indices[node->children_count++] = ci;
            }
            t->node_count++;
            if (out_indices && count < max_out) out_indices[count] = ci;
            count++;
            break;
        }

        case TORUS_EXPAND_RECOMBINE: {
            if (target_node_index < 0 || target_node_index >= TORUS_MAX_NODES ||
                !t->nodes[target_node_index].active)
                return TORUS_ERR_NOT_FOUND;

            torus_node_t *other = &t->nodes[target_node_index];
            int ci = _torus_alloc_node(t);
            if (ci < 0) return TORUS_ERR_FULL;

            torus_node_t *child = &t->nodes[ci];
            _torus_init_node(child);
            torus_generate_id(t, child->id);
            child->mode_index = (node->coherence >= other->coherence) ? node->mode_index : other->mode_index;
            child->state = TORUS_STATE_ACTIVE;
            child->potential = (node->potential + other->potential) * t->potential_decay;
            child->coherence = (node->coherence + other->coherence) / 2.0f;
            child->generation = (node->generation > other->generation ? node->generation : other->generation) + 1;
            child->parent_index = node_index;
            child->user_data = node->user_data;
            child->created_at = _torus_now();
            child->updated_at = child->created_at;

            child->lineage_count = node->lineage_count;
            if (child->lineage_count < TORUS_MAX_LINEAGE) {
                memcpy(child->lineage_indices, node->lineage_indices, sizeof(int) * node->lineage_count);
                child->lineage_indices[child->lineage_count++] = node_index;
            }

            char buf[256];
            int blen = snprintf(buf, sizeof(buf), "recomb:%s:%s", node->essence, other->essence);
            torus_compute_essence(buf, (size_t)blen, child->essence);

            /* Two edges: from each parent */
            for (int p = 0; p < 2; p++) {
                int ei = _torus_alloc_edge(t);
                if (ei >= 0) {
                    torus_edge_t *e = &t->edges[ei];
                    memset(e, 0, sizeof(*e));
                    torus_generate_id(t, e->id);
                    e->source_index = (p == 0) ? node_index : target_node_index;
                    e->target_index = ci;
                    e->edge_type = TORUS_EDGE_RECOMBINE;
                    e->weight = child->coherence;
                    e->created_at = _torus_now();
                    e->active = 1;
                    t->edge_count++;
                }
            }

            if (node->children_count < TORUS_MAX_CHILDREN) {
                node->children_indices[node->children_count++] = ci;
            }
            if (other->children_count < TORUS_MAX_CHILDREN) {
                other->children_indices[other->children_count++] = ci;
            }
            t->node_count++;
            if (out_indices && count < max_out) out_indices[count] = ci;
            count++;
            break;
        }
    }

    /* Grow the torus */
    node->state = TORUS_STATE_EXPANDED;
    node->updated_at = _torus_now();
    t->metrics.major_radius += t->radius_growth * count;
    t->metrics.minor_radius += t->radius_growth * 0.3f * count;
    t->metrics.expansion_count++;
    _torus_update_metrics(t);

    if (out_count) *out_count = count;
    return TORUS_OK;
}

/* ─── Query ──────────────────────────────────── */

torus_node_t *torus_get_node(torus_t *t, int index) {
    if (index < 0 || index >= TORUS_MAX_NODES || !t->nodes[index].active)
        return NULL;
    return &t->nodes[index];
}

int torus_lineage(const torus_t *t, int node_index, int *out_indices, int max_out) {
    if (node_index < 0 || node_index >= TORUS_MAX_NODES || !t->nodes[node_index].active)
        return 0;
    const torus_node_t *n = &t->nodes[node_index];
    int count = 0;
    for (int i = 0; i < n->lineage_count && count < max_out; i++) {
        out_indices[count++] = n->lineage_indices[i];
    }
    if (count < max_out) {
        out_indices[count++] = node_index;
    }
    return count;
}

int torus_descendants(const torus_t *t, int node_index, int *out_indices, int max_out, int max_depth) {
    if (node_index < 0 || node_index >= TORUS_MAX_NODES || !t->nodes[node_index].active)
        return 0;

    /* Simple BFS with depth tracking */
    int queue[TORUS_MAX_NODES];
    int depths[TORUS_MAX_NODES];
    int qhead = 0, qtail = 0;
    int count = 0;
    uint8_t visited[TORUS_MAX_NODES];
    memset(visited, 0, sizeof(visited));

    queue[qtail] = node_index;
    depths[qtail] = 0;
    qtail++;
    visited[node_index] = 1;

    while (qhead < qtail && count < max_out) {
        int ci = queue[qhead];
        int d = depths[qhead];
        qhead++;
        if (d > max_depth) continue;

        const torus_node_t *n = &t->nodes[ci];
        for (int i = 0; i < n->children_count; i++) {
            int child_idx = n->children_indices[i];
            if (child_idx >= 0 && child_idx < TORUS_MAX_NODES &&
                t->nodes[child_idx].active && !visited[child_idx]) {
                visited[child_idx] = 1;
                if (count < max_out) out_indices[count++] = child_idx;
                if (qtail < TORUS_MAX_NODES) {
                    queue[qtail] = child_idx;
                    depths[qtail] = d + 1;
                    qtail++;
                }
            }
        }
    }
    return count;
}

int torus_find_by_mode(const torus_t *t, const char *mode, int *out_indices, int max_out) {
    int mi = torus_find_mode(t, mode);
    if (mi < 0) return 0;
    int count = 0;
    for (int i = 0; i < TORUS_MAX_NODES && count < max_out; i++) {
        if (t->nodes[i].active && t->nodes[i].mode_index == mi) {
            out_indices[count++] = i;
        }
    }
    return count;
}

/* ─── Metrics ────────────────────────────────── */

torus_metrics_t torus_metrics(torus_t *t) {
    _torus_update_metrics(t);
    return t->metrics;
}

#endif /* TORUS_IMPLEMENTATION */
#endif /* TORUS_CORE_H */
