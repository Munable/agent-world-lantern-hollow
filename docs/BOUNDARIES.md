# Reference boundaries

- Kernel: fixed reviewed commit, installed dependency, never vendored.
- World: map, collisions, BFS pathfinding, movement, cancellation, dialogue, quest, notes.
- Client: original procedural pixel sprites, four directions / four walk frames,
  idle, repair progress, lighting, particles, accessible DOM dialogue and input.
- Data: separate SQLite file. Notes keep the latest 30 entries. Events retain one hour /
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
- Guest credentials are HttpOnly, SameSite cookies. Browser mutation routes require a custom
  header and validate Origin; native Agent routes use Bearer authentication instead.
  There is no public registration moderation, full account recovery, or deployment security audit.
- Browser stores only language/completion flags and a pending public intent envelope, never
  identity secrets. Uncertain Actions reuse their original operation ID after receipt lookup.
- Tests use deterministic clients, not a claim that an autonomous LLM played the quest.
