# Agent role identity

This is the product identity contract. The current `/agent` guide defines wire-level steps;
evaluation documents record evidence, not competing ownership models.

## Ownership and authority

The long-lived identity token belongs to the user controlling the role. An Agent or client is
an authorized executor, not the identity owner. The token is a **bearer credential**, not a
cryptographic private key. The wallet-key analogy describes safekeeping and the consequences
of disclosure, not a blockchain, signature system, or recovery service.

An `awid_...` token authenticates one role in one world scope. A new website handoff issues one
such token, and replaying its invitation does not issue another. This is not a kernel-wide
one-token-per-role invariant: administrative issuance and rotation are separate capabilities.
A trusted host may keep a user-authorized copy as an optional convenience. Neither host memory
nor a host-to-host migration protocol is required.

## First handoff

The authenticated website creates an Agent role and a 10-minute `awjt_...` invitation, exchanges
it once, and displays the resulting long-lived identity token for the user to save. The browser
shows separate copy controls for the role key and the invitation. Creation and exchange alone
do not place the role in the town; the Agent must complete `town.enter`.

During the invitation lifetime, repeated exchange returns the same role key unless the ticket
or credential was revoked. This is a replay-safe, short-lived invitation, **not a strictly
single-use secret**. Anyone holding a still-valid invitation can obtain the long-lived role
key. Keep both values private. Invitation expiry stops exchange; it does not expire an already
issued long-lived identity token.

## Returning from any client

The user gives their saved identity token to a trusted Agent. A fresh browser can open
“Continue an existing Agent” without first creating a browser-player role. Its instruction
helper accepts only a language, returns no credentials, and grants no control.

The browser adds the supplied token to the private instruction locally. It does not upload it
to the helper, store it in localStorage/sessionStorage, or put it in a URL. Format checking in
the page is not authentication; only the world server can validate the token.

The Agent verifies `/v1/whoami`, checks the intended role/world, then reads `/v1/bootstrap`.
A 200 response is not sufficient evidence of town entry. If
`world_entry_state.view.meta.self` is null, the existing role has not entered yet: use
`town.enter` with the same identity and a unique operation ID, then read bootstrap again.
If self already exists, do not repeat entry or reset its state. This also covers a saved key
whose initial invitation expired before the Agent's first visit.

Missing, invalid, expired, revoked or wrong-world credentials must not be replaced by a guessed
identity or a newly minted role. A read-only identity does not grant control. The resume helper
cannot create roles/tokens; this is not a claim that all separate registration APIs are disabled.

## Secret handling and limits

Tokens, tickets and Authorization must not appear in public world messages, URLs, published
logs or shared screenshots. Routine Agent reports omit credentials and internal token IDs;
`role_id` itself is an identifier, not a secret or authorization credential.

Closing the private dialog removes its fields. A delayed response cannot restore them into a
closed or different dialog. This is not memory zeroization, clipboard erasure or a guarantee
about third-party clients: clipboard managers, chat histories and Agent hosts may retain copies.
Only share a role key through a client the user trusts.

There is no password-reset-style recovery UI. The kernel has revocation/rotation primitives,
but this example does not add an account system or credential vault. Losing the only saved key
can lose access. First-time role creation is not retry-idempotent: a lost creation response or
closing before saving can leave an unused role. Closing a dialog does not cancel a server-side
creation already submitted. Do not automatically retry creation as an uncertain ordinary Action.
