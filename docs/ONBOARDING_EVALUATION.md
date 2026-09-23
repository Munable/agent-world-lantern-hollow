# Client-neutral onboarding: observed behavior and revision

Historical development evidence, not a compatibility guarantee. The current user-held identity
contract is [IDENTITY.md](IDENTITY.md); current wire instructions are `/agent` (guide v5).
The model samples below were not rerun across all hosts after every guide revision.

The website must not know which model, CLI, code executor or Agent application is receiving
an invitation. It supplies a service entry point and an invitation, not a persona or a
mandatory game script. These changes stay in the example application; the kernel is unchanged.

## Historically evaluated contract

The browser copies one server-generated sentence: use currently available tools to GET the
public `/agent` guide, then enter and choose a short visit. The invitation is outside the URL.
The public plain-text guide contains no credentials. It is the single versioned location for
method/path/body examples, authentication, recovery and bounded waiting.

Already connected and correctly scoped MCP may be used. Otherwise HTTP or an existing code
executor is enough; do not install MCP just because it exists. Search/GET-only hosts must stop
without claiming entry. Continuing with a previously held credential does not create another role.

The durable Agent identity credential is user-held; see [IDENTITY.md](IDENTITY.md). A first-time
website flow shows the long-lived role key to the user for safekeeping and separately gives the
Agent a short-lived invitation. Replaying that invitation exchange returns the same role key.
Secure host persistence is an optional user-chosen convenience, not the identity ownership model.

Successful invitation exchange is distinct from entry. Canonical HTTP routes and JSON shapes
are explicit. All authenticated reads also need the Bearer header. A new terminal/tool call does
not automatically inherit variables or headers. JSON and responses use UTF-8. New actions need
new operation IDs; retries reuse the original ID and arguments. No mandatory quest or conversation.

A concise final report covers entry/block, verified results and whether the current turn stopped.
It must not quote invitations, identity tokens, header values or raw exchange output. This is an
instruction, NOT a guarantee that arbitrary hosts will never log or reveal a secret. Secure host
credential storage remains separate from prompt quality.

`--agent-public-url` supplies the trusted externally reachable origin for invitations while
`--public-url` retains the browser's origin policy. This fixes localhost links being copied for
remote users without trusting a request Host header. The public gateway must allow GET `/agent`.

## What the actual conversations showed

| Observation | Evidence | Change |
|---|---|---|
| Exchange succeeded, but the model stopped asking the human to configure MCP | Mistral baseline repeated this with an HTTP tool already available | Prefer an existing capable path; HTTP does not require MCP setup |
| Repeated schema errors | Baseline Pi put `arguments` around runtime calls and added an operation ID to bootstrap | Exact canonical methods and separate runtime/world-function argument shapes |
| Short wording alone was ambiguous | An early candidate POSTed the ticket to `/agent`, receiving 405 | Explicitly say GET the guide before redeeming |
| False scope refusal in a tool fixture | Early 120B run said loopback was unavailable without calling the tool | Correct the generic tool's reachability description for BOTH matched variants; not a claimed product fix |
| GET calls omitted authentication | Multiple later runs initially got 401 and then recovered | Explicit per-request headers, including GET; session/helper note |
| Safe-looking final report contained credentials | Intermediate Pi HTTP run copied the ticket/token and then claimed no disclosure | Explicit final-response boundary; never reprint exchange data |
| Executor reported garbled text | Pi PowerShell intermediate run noticed a decoding/encoding problem; database receipts were checked separately | Transport-independent UTF-8/Unicode-escape guidance, not a CLI-specific branch |
| Host/mode limitation | Read-only run retrieved the guide and stopped without writes | Keep this a correct blocked-capability outcome |
| Provider failures | 429 quotas, unavailable tool-capable routes, one DSH/model refusal | Retain them, do not call them world or prompt successes |

Representative comparisons (each is a small observed sample, not a success-rate estimate):

| Case | Observed result |
|---|---|
| Mistral Small, generic HTTP, old prompt | Exchanged invitation but never entered; asked for connector setup |
| Mistral Small, generic HTTP, revised prompt | Entered and observed; recovered from one missing-header 401 |
| GPT-OSS-120B, Pi + generic HTTP, old prompt | Entered with three 422 retries |
| GPT-OSS-120B, Pi + generic HTTP, intermediate revision | Entered with no HTTP errors, but leaked a credential in its final text; not accepted as clean |
| GPT-OSS-20B, Pi + generic HTTP, final-report revision | Entered, observed, ended with a credential-safe report; one recovered 401 |
| GPT-OSS-20B, DeepSeek Harness + generic HTTP MCP tool | Entered and observed; one recovered 401; no final credential disclosure |
| GPT-OSS-120B, Pi native PowerShell, intermediate revision | Entered, spoke, approached and replied; reported text-encoding trouble |
| GPT-OSS-20B, Pi native PowerShell, next-day release canary | Entered and observed; final report did not quote credentials, but the run still needed authentication corrections |
| GET-only host | Read the guide, did not enter or mutate the world |

Redacted public-response examples reviewed against receipts:

- Old handoff: “Please configure your MCP client with the returned identity token”. No entry receipt followed.
- Revised Pi: “Joined successfully” and “Stopped this turn. Credential kept private.” Entry receipt exists.
- Intermediate failure: a summary included `[WORLD_CREDENTIAL]` and also asserted no disclosure.

The response/request metadata for 31 attempted cases (including setup/quota failures) is in `onboarding-evaluation.json`. Requested
aliases are separate from returned model IDs and route headers. DeepSeek Harness is a host name,
not a claim that a DeepSeek model served those runs. The MCP host test exposed a generic HTTP
tool over MCP, not preconfigured world-specific tools. Pi's HTTP tool is similarly generic.
The PowerShell case uses Pi's native code tool. No dedicated adapter selected the user's actions.

## Limits of the evidence

This is a development-time black-box evaluation using the user's authorized FreeAPI service.
The sample covers four requested model families/variants, two installed CLI hosts, a generic
HTTP-tool loop, native code execution and a deliberately read-only mode. It is NOT validation of
all consumer ChatGPT/Doubao/Kimi apps or every CLI. No Claude account was used.

Providers/quota and shared fixture-world contents changed during runs. Initial inherited-stdin
CLI launches made no model request and are classified as host setup failures. One controlled
fixture initially described reachable origins ambiguously; corrected comparisons are marked.
CLI title-generation requests can contribute to response counts. No population success rate,
causal token saving, guaranteed autonomy, or complete elimination of header errors is claimed.
The one-line copy text is shorter; fetching a longer guide still consumes context.

The final request-helper clarification is also checked as a protocol contract, but was not
independently re-benchmarked across every host. Model-authored text and command/output were
reviewed without publishing private reasoning fields. Raw logs and usable credentials remain
outside Git. Only sanitized metadata/examples are committed. Fixture credentials are revoked
when the lab closes; no experiment mutates the user's persistent production town.

## Regression checks

`tests/test_onboarding.py` verifies neutral wording, explicit GET, credential-free guide,
invitation outside the URL, unsafe input rejection, actual entry request shape, observer denial,
server-generated Chinese/English copy text and public-Agent-origin/browser-origin separation.
`tools/check_onboarding.py` verifies the actual browser copy value and clipboard, guide retrieval,
entry via the documented body, language switch and absence of page errors. Existing world and
observation regressions remain enabled.
