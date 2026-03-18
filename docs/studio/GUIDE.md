# Torus Studio — User Guide

## What This Is

A 3D creative studio built on toroidal architecture. Everything you create becomes an input for the next creation. No linear timeline — enter anywhere, expand in any direction.

## Quick Start (30 seconds)

1. **Click the 3D viewport** to interact with the scene
2. **Left click** to select objects
3. **Right click + drag** to rotate the camera
4. **Scroll** to zoom in/out
5. **Click a primitive** (Cube, Sphere, Cylinder, Cone) on the left to add shapes
6. **Click the character model** to select bones and pose them

## The Interface

### Center: 3D Viewport
Your creative workspace. Contains objects, characters, and the toroidal flow field.

### Left Panel: Tools
- **Bone Controls** — Select any bone on the character to adjust Position (X/Y/Z) and Rotation
- **Lighting** — Ambient (overall brightness) and Directional (spotlight angle)
- **Add Primitive** — Drop basic shapes into the scene: Cube, Sphere, Cylinder, Cone

### Right Panel: Torus Operations
- **Expansion** — The core torus actions:
  - **Bifurcate** — Create branching variations from a single asset
  - **Broadcast** — Distribute across all modalities simultaneously
  - **Mutate** — Generate evolved variations with controlled randomness
- **Characters** — Manage posable figures in your scene
- **Recent Assets** — Your creation history

### Top Bar
- **Consistency** — View coherence metrics (how stable is your creative topology?)
- **Expansion** — View growth metrics (how much has your creation expanded?)
- **Back to Hub** — Return to the main torus navigation view
- **Save** — Preserve your current state

## The Hub View

The main screen shows the torus topology:
- **Center**: Torus core — "Enter Anywhere"
- **Orbiting nodes**: Illustration, Animation, 3D Stage — each a creative modality
- **Bottom actions**: Bifurcate, Broadcast, Mutate — the three expansion operations

Click any node to enter that modality's workspace.

## The Philosophy

Every creation in Torus Studio is a **seed**. Seeds don't get consumed — they **expand**:

- **Bifurcate** explores branches (what else could this be?)
- **Broadcast** reaches all modalities (how does this look as animation? as 3D? as illustration?)
- **Mutate** evolves (what does this become with controlled randomness?)

The output of each operation becomes the input for the next. The torus expands through its own creations.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Left Click | Select |
| Right Click + Drag | Rotate camera |
| Scroll | Zoom |
| Middle Click + Drag | Pan |

## Technical

- Built with React + Three.js
- Static deployment (runs entirely in browser)
- No account required, no data sent anywhere
- Source: [GitHub](https://github.com/ChaiLifeOTFT/PUSH-Protocol)
