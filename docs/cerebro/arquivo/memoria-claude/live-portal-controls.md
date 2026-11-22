---
name: live-portal-controls
description: "Real-account (\"ao vivo\") portal section with close/pause buttons, built 2026-11-17 on branch feat/portal-controls; no live bot runs yet"
metadata:
  node_type: memory
  type: project
  modified: 2026-11-17T15:33:01.642Z
---

Owner wants a separate "Ao vivo (conta real)" portal section (Clear REAL account) to manage risk by buttons: Fechar posição, Pausar/Retomar entradas, Fechar e parar. Bots are NOT to trade real money yet; interface only. When the owner picks bots, they open orders and the owner administers risk from the buttons.

Design: buttons POST /api/control -> command file live/commands/<robot>.json -> the robot's own Engine executes it (live/core/control.py, engine._commands) and journals it. Never close behind the engine's back: closing directly at the broker made P-017 go to safe_mode and the portal showed a stale position (2026-11-17). Real robots = live/config/live-b3-*.json (own journal/magic); demo robots stay read-only in the portal. Credentials go in live/.env typed by the owner, never in chat.

**Why:** the manual close on P-017 broke reconciliation; the owner then asked for buttons.
**How to apply:** any manual action on a running bot must go through the command file; changes live in the worktree D:/Trade-Initial-controls (branch feat/portal-controls) until the owner approves the merge; running bots need a restart to load new engine code. See [[parallel-sessions]].
