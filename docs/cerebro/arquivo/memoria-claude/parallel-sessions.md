---
name: parallel-sessions
description: Several Claude sessions work on D:\Trade-Initial at once and chain long lab.pipeline runs; check processes and coordinate before editing or restarting the loop
metadata:
  node_type: memory
  type: project
  modified: 2026-11-13T18:09:22.168Z
---

Several Claude Code sessions run on this PC against D:\Trade-Initial at the same time (seen 2026-11-13: one left a shell chain `recalibrate -> resume H-124..H-129 -> sh ops/linux/research-loop.sh` running; killing one link starts the next). Uncommitted portal/test files in the working copy belong to another session.

**Why:** the guard aborts a cycle if the repo changes during an agent step, and two concurrent `lab.pipeline resume`/loops would test the same hypothesis twice (a second draw in the registry).

**How to apply:** before editing the repo, list processes matching `lab.pipeline|research-loop|--agent` (filter by Name to avoid matching your own command); work in a git worktree while a run is active; ask the owner before stopping another session's run, message peers with SendMessage (ListAgents), kill the whole chain (shell parent included), and restart the same queue yourself. Never commit other sessions' files; lab/gitops.py commits only the given paths. Related: [[project-structural-decisions]].
