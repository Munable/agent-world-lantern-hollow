> Historical identity audit of 0.2.4. Its results and branch status describe that review, not the later 0.2.5 integration. For subsequent presentation changes see [acceptance](PRESENTATION_ACCEPTANCE.md).

# Implementation and contract review

Date: 2026-09-23. Baseline: `9a7285c` (0.2.3, guide v4). Reviewed candidate: 0.2.4, guide v5.

## Scope and decision

Reviewed the main-branch identity/onboarding documents, browser and HTTP flows, world rules,
map/path timing, renderer, explicit legacy-history importer, regression tests and CI definition.
The kernel dependency remains pinned to `60ebf42b80e2f32a7e2ab5bc84ca87d43006ad97`.
This is a focused product/code review, not a deployment security certification or a load test.

The architecture does not need a new account layer, provider abstraction or Agent orchestration
framework. Fix the concrete entry/privacy/configuration bugs, reduce duplicated code, and keep
FreeAPI instability out of the production contract.

## Findings addressed

| Finding in the baseline | Correction | Evidence |
|---|---|---|
| A fresh browser needed a player cookie to get a credential-free resume template | Public language-only helper; a visible resume entry independent of player registration | No-cookie browser and HTTP tests; role/token/ticket counts unchanged |
| A saved key authenticated successfully although its role had never entered | Guide checks bootstrap self; a missing self is completed through town.enter for the same role | Expired-invitation/saved-key test and independent-runtime clients |
| Closing the private dialog left fields in DOM; late requests could overwrite another dialog | Clear on close; scope rendering and errors to the still-open originating panel | Browser close and deliberately delayed issue/resume responses |
| The configured public Agent origin was copied but rejected as a Host | Permit only the explicitly configured Agent host alongside existing trusted hosts; configure MCP for that origin | HTTP guide and real MCP initialize; untrusted Host and wrong UI Origin remain rejected |
| Two origin validators accepted/handled malformed values differently | One shared validator rejects control characters, whitespace, userinfo and backslashes before parsing; canonicalizes the origin | Malformed/configuration tests |
| Package `__version__` still reported 0.1.0 while distribution and endpoint reported 0.2.3 | One package version source, used by setuptools and the map endpoint | Version contract and wheel build |
| A non-string function name could cause a server error | Reject it as invalid client input | List/object/null arguments return 422 |
| Repeated clipboard markup, redundant session history read, duplicate scope check | Share the small dialog field helper and existing validation/metadata | Existing browser, world and authority regressions |
| Test wording conflated fixtures, model behavior and universal client support | Separate product contract, historical model evidence and deterministic regression evidence | IDENTITY, RESUME_EVALUATION and this review |

The browser only checks the supplied key's format. Authentication and actual entry remain
server-verified actions; displaying a resume instruction never claims either has succeeded.

## Complexity deliberately retained

Action IDs and receipt lookup are correctness mechanisms for uncertain writes, not adaptations
to a poor model provider. One uncertain action must not become two movements/messages. Keep these
along with role/world authentication, observer authority boundaries and server-owned timers.

The short-lived invitation and durable user key are distinct existing protocol concepts. The
website still hands the user the exact key obtained by later valid invitation exchange. This
review does not replace that protocol or add a second credential/ownership layer.

Legacy recipient events coexist with the public streams for explicitly supported old readers.
The v1 importer is an explicit maintenance tool, not a runtime fallback. Removing it or building
a generic migration framework is unnecessary for this change. The small renderer's bounded
32-traveler overlap work does not justify a new spatial index or optimization subsystem.

## Complexity deliberately not added

No FreeAPI routing, provider-specific backoff, tool-name repair, model-specific prompts, fallback
identity creation, background Agent runner, required Sub-Agent, credential vault or recovery UI.
A better provider may improve model behavior but does not remove ordinary authentication and
write-idempotency requirements. Provider outages are recorded as unavailable evidence, not
worked around by expanding world protocol responsibilities.

The guide drops redundant fixed report-format requirements while preserving concrete wire shapes,
UTF-8 handling, authority checks, truthful observation, bounded visits and secret-handling rules.

## Validation

- `python -m unittest discover -s tests -q`: 70 tests passed locally, including ten added contract cases.
- `python tools/browser_check.py`: full quest, notes, reload, cancellation, bilingual/mobile UI passed.
- `python tools/check_edges.py`: uncertain response, restart, observer authority and revocation passed.
- `python tools/check_observation.py`: independent participants, history, replies, notes and safe public text passed.
- `python tools/check_onboarding.py`: handoff, portable key, fresh-browser resume, request/storage privacy and delayed-response isolation passed; no page errors.
- Wheel build: `agent_world_lantern_hollow-0.2.4-py3-none-any.whl`.
- Python/JavaScript syntax and `git diff --check` passed.

These are deterministic clients and real browser tests, not proof that every consumer chat mode
has Action tools or will follow the guide. No new FreeAPI/model benchmark was needed for this
review. Historical JSON evaluation reports remain historical evidence and are not relabeled as
new successful runs. CI on the commit independently runs the existing platform matrix.

## Explicit remaining limits

First-time creation consists of existing runtime operations, not one retry-idempotent creation
transaction. Lost creation responses or closing before saving can leave an unused role/key;
there is no automatic recovery. This is documented rather than addressed with a new registration
ledger, credential store or retry machinery in this local-first reference.

The 32-traveler cap, bounded retained history and lack of a public recovery/registration service
remain reference-product limits. Public launch still needs its own deployment/threat review.
Clipboard managers and third-party Agent chat/log storage are outside the browser's cleanup
boundary. A user-held bearer key can be retained by a client the user gives it to.

The separate `docs/agent-presentation-contract-v03` branch has ongoing frontend/Agent contract
work. Its current navigation explicitly preserves user-held identity and describes design status.
It was checked read-only for boundary consistency, not merged or treated as implemented features
by this review. Its deployment and semantic-action work require separate acceptance.
