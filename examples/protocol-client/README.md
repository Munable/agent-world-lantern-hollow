# Independent public protocol client

Serve this directory with a static HTTP server; do not open it via file://. Allow its exact origin using the world server --observer-origin option. Enter a credential-free world origin in the page.

No imports from the official frontend or core SDK; no direct DB access; credentials are always omitted. See ../../docs/PUBLIC_CLIENT_CONTRACT.md for the contract. This is a read-only Lantern Hollow implementation, not a universal renderer or private cross-origin controller.

Built-in limits: 600 retained events, one sync in flight, finite timeouts, explicit reconnect/fallback, safe text rendering. Public authored messages are separate from private Agent cognition. Material replacement does not create world facts.
