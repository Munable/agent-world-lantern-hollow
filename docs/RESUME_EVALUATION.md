# Persistent identity resume evaluation

Reviewed: 2026-09-23. Audit baseline: `9a7285c` (0.2.3, guide v4).
Current product contract: [IDENTITY.md](IDENTITY.md). Current wire instructions: `/agent` (guide v5).

## Historical model experiments

The earlier host-managed fixture supplied a saved identity through an authenticated HTTP helper.
It demonstrated that a helper can authenticate without putting the token in model text. It did
not prove that arbitrary chat applications persist credentials, that two consumer Agent apps
were tested end-to-end, or that ownership belongs to a host. The user-held credential is the
product model; host storage is optional.

Provider timeouts/429/502 occurring before a tool call are **unverified model-behavior cases**,
not successful negative tests. In particular, a wrapper that disables creation cannot establish
that a model independently chose not to create a replacement. Historical samples must not be
used to claim universal client compatibility or a population success rate.

## Gaps found in 0.2.3

The credential-free browser helper required a player cookie, unnecessarily forcing a fresh
browser toward player registration. Also, whoami and bootstrap could return 200 while the role
had never entered the town. The guide did not explain how a saved key finishes that first entry.
Closing a private dialog left its fields in DOM; a delayed response could populate a different
dialog. These were product/implementation issues, not FreeAPI reliability problems.

## Current deterministic checks

`tests/test_onboarding.py` covers separate cookie-free HTTP clients using the same user-supplied
key; unchanged role/token/ticket counts; only one initial town.enter; expiry of an invitation
before entry; and missing/revoked/wrong-world credentials. It checks the public instruction
helper separately from actual authenticated control. A saved key may enter the same previously
created role; it never requires another role or another invitation.

`tools/check_onboarding.py` covers the real browser handoff and clipboard, a fresh browser
context without a player cookie, local token composition, absence of the key in captured
browser requests/storage, clearing private fields on close, and late-response isolation.
Delayed-response cases deliberately hold a request in Playwright, then release it after the
user closes that dialog and opens another. These are regression checks, not network benchmarks.

These tests establish server/browser behavior under their stated fixtures. Direct HTTP test
clients are not autonomous models and browser contexts are not ChatGPT/Claude/Kimi sessions.
No new FreeAPI benchmark or consumer-client compatibility claim is made for guide v5.

## Scope retained

Keep authenticated identity checks, same-role entry, action IDs and receipt lookup. Do not add
provider routing, model-specific tool-name repair, unlimited retries, a credential vault,
background Agent participation, or account recovery to make a development fixture pass.
