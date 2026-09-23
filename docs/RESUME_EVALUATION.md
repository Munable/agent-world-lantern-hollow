# Persistent identity resume evaluation

Date: 2026-09-23. Original onboarding baseline: `4e9414f`.

This evaluation checks a different property from first-time onboarding: a later, fresh Agent
session must continue the same world role without minting another role.

The product identity rule is defined separately in [IDENTITY.md](IDENTITY.md): the long-lived
identity token belongs to the user. An Agent host is an executor, not the owner of the role key.

## What the earlier host-managed experiment proved

An intermediate guide-v3 experiment kept one role token outside model context and let a generic
HTTP helper apply it automatically. GPT-OSS runs successfully verified `/v1/whoami` and
`/v1/bootstrap` against the same role without increasing the role count.

That experiment proved a useful transport property: a trusted host can use a user-authorized
stored copy without exposing the token to model text. It did **not** establish host storage as the
identity ownership model. Treating host persistence as the required resume path was an
interpretation error and is corrected in guide version 4.

## Guide-v4 resume contract

The normal resume path is:

1. The user chooses an existing role and supplies their saved `awid_...` identity token to the
   Agent they trust.
2. The Agent reads `/agent`.
3. The Agent authenticates with that token and GETs `/v1/whoami`.
4. The Agent GETs `/v1/bootstrap` and continues the same role.
5. The role ID must remain unchanged and no new role may be created.

Reading `/agent` alone is not resumed access. If the user cannot provide the saved role key and
no trusted client has a user-authorized copy, the Agent must report that the role cannot be
resumed. It must not silently create a replacement role.

## Browser product path in 0.2.3

The browser's first-time Agent flow now exposes two distinct values:

- a 10-minute `awjt_...` invitation for the Agent;
- the long-lived `awid_...` identity token for the user to save.

The website immediately exchanges its own new ticket once so it can show the durable role key to
the user. Join-ticket exchange is deterministic and replay-safe, so when the invited Agent later
exchanges that same still-valid ticket it receives the exact same long-lived token. No second role
key is created.

The “Continue an existing Agent” UI asks the user to paste their saved token locally. JavaScript
combines that token with the server-generated credential-free resume instruction. The token is
not included in the POST to `/play/agent/resume` and is not persisted to localStorage.

The resume helper endpoint itself remains credential-free and never creates a role, ticket, or
identity. Its purpose is only to provide the current versioned resume instruction.

## Security boundary

The normal final Agent report must not reproduce the identity token, token ID, token fragments,
Authorization header, join ticket, or raw authentication payload. A host that offers secure
credential persistence may be used when the user explicitly chooses it, but that is optional
convenience rather than a protocol dependency.

This reference product does not claim full public account recovery. Losing the only saved
long-lived role key means this example has no password-reset-style way to recover the role.
Runtime revocation/rotation primitives exist, but a complete public recovery UI is out of scope.

## Evidence limits

The host-managed black-box samples were small development-time FreeAPI experiments and provider
availability changed during the runs. They are not a population success rate or validation of
every consumer Agent application.

Guide-v4 ownership semantics are enforced by deterministic HTTP/browser regression tests: the
website-visible long-lived token must equal the token returned when the invited Agent exchanges
the same ticket; resume does not mint another identity; and browser resume composition must not
send or persist the user-entered token.
