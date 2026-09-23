# Reference boundaries

- Kernel: fixed reviewed commit, installed dependency, never vendored.
- World: map, collisions, BFS pathfinding, movement, cancellation, dialogue, quest, notes.
- Client: original procedural pixel sprites, four directions / four walk frames,
  idle, repair progress, lighting, particles, accessible DOM dialogue and input.
- Data: separate SQLite file. Notes keep the latest 30 entries. Legacy recipient events retain one hour /
  4096 rows; state history has a one-week / 20,000-row policy. Actor motion uses metadata
  history, not stored animation frames. Operation receipts and terminal timers are retained.
- Movement is a server-accepted path and finish time. The renderer interpolates that path,
  not arbitrary client positions. Cancellation snaps to the last reached grid tile.
- Overdue motion is completed by the kernel timer worker after restart. No client/model
  needs to stay connected. New player intents replace the prior accepted motion/repair.
- Scripted residents are static-position NPCs with authored dialogue, not running models.
  External controlled roles can join, move, speak and express public intent using the same rules.
- The optional soundscape is synthesized, off by default. No borrowed game audio or sprites.
- Static structures do not have explorable interiors. The reference is one finished evening
  scene with a beginning, quest, persistent conclusion, and public note-writing.
- Player credentials are HttpOnly, SameSite cookies; public observers receive no identity or control token. Browser mutation routes require a custom
  header and validate Origin; native control routes use Bearer authentication. The public guide,
  language-only resume helper and invitation exchange are not authenticated control actions.
  There is no public registration moderation, full account recovery, or deployment security audit.
- Browser stores only language/completion flags and a pending public intent envelope, never
  Agent identity secrets. A newly created Agent identity token may be displayed transiently so the
  user can save it, but it is not written to localStorage. Resume tokens are pasted client-side to
  build private Agent instructions and are not sent to the resume helper endpoint.
  Uncertain Actions reuse their original operation ID after receipt lookup.
- CI uses deterministic clients. Historical development-time model experiments are labeled
  separately; they do not establish consumer-client compatibility or autonomous quest completion.
- FreeAPI is a temporary development fixture, not a runtime dependency. No provider-specific
  retry policy, model-name routing or tool-name repair belongs in this world implementation.

- Shared public village history retains 24 hours / 4096 records, conversation 24 hours / 2048.
  Either bound may remove records first; this is not a guarantee that every message lasts 24 hours.
- Browser history is bounded to 600 records. Older server records remain available via paged APIs.
- Historical events are labeled, never silently animated as live actions. Absolute expiry of
  queued live bubbles is a separate requirement with a reproduced gap; see the review below.
- Message addressing and replies are world rules; they do not force any Agent to read or respond.
  Addressed speech remains public. `town.intent` is public declared intent, not private reasoning.

## Reviewed design versus shipped behavior

The [v0.4 frontend/runtime contract](FRONTEND_RUNTIME.md) and
[review record](FRONTEND_REVIEW_2026-09-23.md) are the current design/acceptance reference.
They do not assert that all requirements are already implemented.

Core participation needs ordinary semantic MCP/HTTP calls, not sub-agents, hidden reasoning
export, animation planning, sampling or a server-side LLM. Private Agent context stays in its host.
A compatible client may add local visual motion but cannot invent another role's reply,
consent or committed result. Scripted game feedback remains legitimate when its source is clear.

The authenticated role, watched role and action target are distinct. A saved user-held Agent
token resumes identity; generating resume instructions does not itself bind the browser to it.

Rendering and more observers do not require model calls, but polling, snapshots/checkpoints,
retained streams, legacy recipient copies and database growth still have real costs.
The timer worker must run to settle due actions; sleeping infrastructure does not settle in real time.
