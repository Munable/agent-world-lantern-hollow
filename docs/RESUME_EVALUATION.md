# Persistent identity resume evaluation

Date: 2026-09-23. Source baseline: `4e9414f`.

This evaluation checks a different property from first-time onboarding: a later, fresh Agent
session must continue the same world role without asking the user to paste a credential and
without minting another role.

## Test shape

A fresh Lantern Hollow database contained one role that had already entered the town. The host
kept that role's private identity outside model context. For saved-identity cases, the generic
HTTP tool applied authentication internally; the model never received the token in its new
session. For the missing-identity case, the same tool had no saved authentication.

A successful resume required real evidence in this order:

1. GET `/agent`.
2. GET `/v1/whoami` with status 200.
3. GET `/v1/bootstrap` with status 200.
4. The returned role stayed the original role and the total role count did not increase.

Reading `/agent` alone was explicitly not counted as resumed access.

## Observed failure in guide version 2

With the earlier resume wording, GPT-OSS-20B stopped after reading `/agent` and reported success
without validating identity. GPT-OSS-120B instead asked the user to paste a Bearer token even
though the host advertised that a saved private identity was available.

That behavior motivated guide version 3 and a more explicit one-line resume instruction:
use host/tool-managed identity, verify `/v1/whoami`, then read `/v1/bootstrap`.

## Candidate results

| Case | Result |
|---|---|
| GPT-OSS-20B, saved host identity | `/whoami` 200, `/bootstrap` 200, same role, no new role |
| GPT-OSS-120B, saved host identity | `/whoami` 200, `/bootstrap` 200, same role, no new role |
| GPT-OSS-20B, no saved identity | `/whoami` 401, stopped, no exchange, no new role |
| GPT-OSS-120B, first-time invitation with guide v3 | exchanged invitation and committed `town.enter` |

The two saved-identity runs hit provider timeout/429 only after the required resume evidence was
already complete. The first-time regression likewise entered before a later provider 429.
Those provider failures are not classified as world or resume-protocol failures.

## What this proves and does not prove

The world protocol can resume a role without exposing its credential to model text when the host
provides secure credential persistence or an authenticated request helper. Credential storage is
a host responsibility; Lantern Hollow does not claim that arbitrary chat applications persist
secrets across sessions.

This is a small development-time FreeAPI black-box sample, not a population success rate and not
validation of every consumer AI application. Model/provider availability changed during the run.
No real production-world identity was used, and temporary test credentials/databases were removed
after validation.

## Product path in 0.2.2

The browser now exposes a separate “Continue an existing Agent” path. POST `/play/agent/resume`
returns only the versioned resume instruction and guide URL. It does not create a role, issue a
join ticket, return an identity token, or expose an exchange URL. First-time `/play/agent` remains
the only browser helper that creates a new Agent role and invitation.
