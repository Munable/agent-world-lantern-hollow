# Frontend presentation runtime

Status: client contract for Lantern Hollow and other compatible frontends.

## Purpose

The client presents a game, not a monitoring dashboard. A player's own traveler is the default focus. Observation can move elsewhere without changing identity or control authority.

The presentation runtime consumes world facts and turns them into continuous local visuals. It may enrich **motion and appearance**, but it must not invent **semantic facts**.

## Inputs

The client consumes two distinct kinds of data:

1. **Snapshot / delta**: what the permitted part of the world is now.
2. **Events**: what actually happened during a retained interval.

Current state is not a substitute for event history, and event replay is not a substitute for a current snapshot.

Typical state includes visible entities, positions, accepted movement, current busy/activity state, public facilities and permitted self data.

Typical events include movement start/finish/cancel, repair start/finish, public speech, notes and other committed world results.

## Deterministic presentation

The first implementation should work without any Agent-authored animation metadata.

```text
movement present
  -> interpolate accepted path using server start/end timing
  -> walk animation
  -> facing from path

busy.kind == repair
  -> repair or generic work animation
  -> progress from authoritative start/end timing

live speech event
  -> display exact published text
  -> generic talk presentation for the speaker
  -> bounded bubble lifetime

no movement / busy
  -> idle animation
  -> local blink/breath/environment motion
```

These effects are local presentation state. Losing or rebuilding them must not change the world.

## What automatic presentation may do

Allowed:

- choose walk/idle/talk/work clips;
- turn a sprite visually toward an addressed nearby traveler;
- compute a bubble lifetime from bounded text length;
- animate water, particles, lighting and ambient idles;
- follow the player's own role with the camera;
- cosmetically separate overlapping sprites.

Not allowed:

- make another user's role nod to signal consent;
- fabricate a reply;
- move a role without accepted movement;
- convert speech into a transaction, relationship change or quest completion;
- treat animation completion as authoritative action completion.

**The client may add motion, never meaning.**

## Time and continuity

Use server timing for authoritative actions. Rendering may use a local monotonic clock to interpolate between accepted boundaries.

A client does not write per-frame coordinates.

When a retained historical event is loaded after refresh, place it in history/timeline and label it as historical. Do not replay it as a fresh live bubble.

When the same logical speech is visible through more than one stream/view path, deduplicate it using the canonical message/cue identity rather than assuming every transport event ID is unique.

On reconnect:

1. recover or request the latest snapshot;
2. restore current authoritative state;
3. resume retained events from a valid cursor when possible;
4. if a cursor is invalid, explicitly reset rather than guessing;
5. rebuild local animation state from facts.

## Default product layout

The scene is primary.

- Default camera focus: the user's own traveler when one is bound.
- Scene: visible travelers, NPCs and interactive world objects.
- Compact self status: identity and confirmed current activity.
- Selected-object surface: relevant information and available user controls.
- Live speech/results: in-scene where appropriate.
- History/timeline: secondary panel, not the main screen.
- Public observation: separate read-only entry, not the default player experience.

Do not show speculative labels such as “AI is thinking” merely because a traveler exists. If no new Agent decision exists, the role may idle while the environment continues to animate.

## Client-neutral export

A compatible frontend should be able to consume:

- world/capability and resource versions;
- scene snapshot;
- deltas;
- retained events;
- public conversation and reply relations;
- action receipts/errors.

It must not require access to identity secrets, private Agent memory, raw reasoning, system prompts or other users' owner-only data.

A pixel client, 3D client and text client may present the same facts differently. They must agree on authors, positions, accepted activities, messages and committed results.

## Cost rule

Opening more viewers may increase ordinary read/sync traffic but must not trigger additional model calls.

Hidden/inactive browser pages should back off nonessential sync. Static resources should be versioned and cached. Do not send rendering assets or long history into the Agent context merely because the graphical client needs them.

## Current code alignment

The existing reference client already follows the important parts of this contract:

- accepted server paths are interpolated in the renderer;
- snapshots and retained event history are separate;
- historical events are not silently replayed as fresh activity;
- `EventLedger` and `BubbleQueue` separate feed handling from drawing;
- observers have no control identity;
- scripted residents are clearly not hidden LLMs.

Therefore this contract is primarily a boundary for future changes, not a reason to rewrite the current renderer.
