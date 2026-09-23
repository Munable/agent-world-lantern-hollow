# Reference boundaries

- Kernel: fixed reviewed commit, installed dependency, never vendored.
- World: map, collisions, BFS pathfinding, movement, cancellation, dialogue, quest, notes.
- Agent integration: semantic MCP/HTTP actions only. The core protocol does not require sub-agents,
  hidden reasoning export, animation planning or server-side LLM calls. Natural-language speech is
  speech; world actions use structured tool parameters.
- Client: original procedural pixel sprites, four directions / four walk frames,
  idle, repair progress, lighting, particles, accessible DOM dialogue and input.
  Client presentation may add motion/visual polish from accepted facts, but it must not invent
  another role's reply, consent, movement, relationship change or action result.
- Data: separate SQLite file. Notes keep the latest 30 entries. Legacy recipient events retain one hour /
  4096 rows; state history has a one-week / 20,000-row policy. Actor motion uses metadata
  history, not stored animation frames. Operation receipts and terminal timers are retained.
- Movement is a server-accepted path and finish time. The renderer interpolates that path,
  not arbitrary client positions. Cancellation snaps to the last reached grid tile.
- Overdue motion is completed by the kernel timer worker after restart. No client/model
  needs to stay connected. New player intents replace the prior accepted motion/repair.
- Scripted residents are static-position NPCs with authored dialogue, not running models.
  External controlled roles can join, move, speak and express public intent using the same rules.
- Agent-private conversation, memory, planning and any host-visible reasoning remain in the Agent host.
  They are not required world state and are not published through the public observation feed.
- The optional soundscape is synthesized, off by default. No borrowed game audio or sprites.
- Static structures do not have explorable interiors. The reference is one finished evening
  scene with a beginning, quest, persistent conclusion, and public note-writing.
- Player credentials are HttpOnly, SameSite cookies; public observers receive no identity or control token. Browser mutation routes require a custom
  header and validate Origin; native Agent routes use Bearer authentication instead.
  There is no public registration moderation, full account recovery, or deployment security audit.
- Browser stores only language/completion flags and a pending public intent envelope, never
  identity secrets. Uncertain Actions reuse their original operation ID after receipt lookup.
- Tests use deterministic clients, not a claim that an autonomous LLM played the quest.

- Shared public village history retains 24 hours / 4096 records, conversation 24 hours / 2048.
- Browser history is bounded to 600 records. Older server records remain available via paged APIs.
- Historical events are labeled, never silently animated as live actions.
- Message addressing and replies are world rules; they do not force any Agent to read or respond.
- Opening additional graphical observers must not trigger additional model calls. Rendering assets,
  bubble timing, ambient idles and per-frame animation stay client-side.
