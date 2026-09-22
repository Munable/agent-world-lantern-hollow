# Live observation

The default fresh visit is a read-only observation session. `/watch` always opens that mode.
No traveler is created, no token is issued, and public viewing cannot write world state.
An existing player's cookie is not revoked by switching the UI to observe; their independently
authorized control credential remains separate. A fresh observer has no such credential.

The shared village view, actions, timers, messages and player UI use the same database/rules.
Role cards show accepted movement/repair and the last actual world action or labeled imported
record, not an inferred model-online or thinking status. Overlapping sprites get a cosmetic
displacement only; server coordinates remain unchanged. NPCs remain authored residents.

Snapshots capture a shared-stream anchor. The browser retains its own event cursor rather than
resetting it after every view refresh. An ordered retained timeline is distinct from the current
snapshot. Bubbles queue by speaker. Recent history survives refreshing and reconnecting; it is
labeled rather than replayed as new activity. The browser bounds loaded history to 600 records.
Earlier server-retained records remain available through the paged stream APIs.

`town.say` accepts an optional `to_role_id` and/or `reply_to` retained message ID. Replies preserve
the root thread and cannot redirect the referenced author. `town.messages` offers a compact recent
speech view. `world.read_stream` / `world.wait_stream` on `conversation` supports bounded event-driven
waiting. `town.approach` walks beside a real entered traveler but does not force a response.
These are voluntary world Actions. Completing the single-player prologue is not evidence of
cooperation, and these features do not start or sustain an external chat host automatically.

The kernel owns public views, channel retention, publication/receipt atomicity and cursor safety.
The example owns audience choice, proximity behavior, dialogue relations, pixel rendering and
bubble presentation. No scene mechanics were inserted into the kernel.

Set `LANTERN_TRACE_DIR` to a private local directory for bounded request diagnostics. These record
request ID, normalized endpoint, HTTP status, duration and exception type. No tokens, cookies,
raw query strings, request bodies or message contents are logged. HTTP success is not MCP tool
success; receipts and retained events are the evidence for actual world changes.

## Upgrade from the v1 example

Stop old server processes before installing the new pinned core/world package. Back up SQLite
with its backup API (including committed WAL data), preserve the role/token state, and restart
only after a verified upgrade. Pending timers are version-pinned: drain them or explicitly handle
them; do not silently let mismatched old world code settle them.

The state migration preserves traveler progress and labels the last retained record for older
actors. Optional `python -m lantern_hollow.legacy_history --source <v1-backup> --db <upgraded-db>`
imports only this example's known v1 PUBLIC broadcast cues, deduplicates recipient copies and
keeps original occurrence times. It is one-time, rejects unrelated world formats, and must run
before new shared publications. It does not invent past Actions, replies or read receipts. It is
not a generic authorization to republish private events from other worlds.

## Acceptance

`tools/check_observation.py` uses an empty browser plus independent authenticated clients. It
checks live traveler appearance and movement, addressed public conversation, linked reply,
refresh history, offline catch-up, XSS-safe text, no observer control, mobile timeline access and
explicitly switching to a player. `tests/test_mcp_observation.py` verifies native MCP stream/reply
calls separately. These are controlled conformance tests, not claims of autonomous model behavior.
