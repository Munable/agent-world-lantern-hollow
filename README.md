# Lantern Hollow · 灯溪镇

A small, persistent pixel village. Relight a beacon; leave a trace.

![Lantern Hollow](docs/preview.png)

![Lantern Hollow](docs/preview.png)

```sh
python -m venv .venv
# Activate .venv, then:
python -m pip install -e .
python -m lantern_hollow.server
```

Open `http://127.0.0.1:8840`. Click to walk/interact; WASD or arrows to move,
E to interact, Esc to stop. Chinese / English and optional synthesized sound.
Position, quest, beacon and notes survive refresh and restart.

Independent rules and original procedural pixel art. No kernel source copies.
`agent-world` is pinned to `314bd38b774516af198d039de5bc3e036c17b19d` (0.12.0).
Data stays in `data/lantern-hollow.sqlite3` by default.

Residents are authored NPCs, **not LLMs**. The invitation button creates a short-lived
MCP invitation for a separately configured Agent. Loopback URLs require the same computer.
No model API key, paid provider, or automatic connector installation is required to play.

```sh
python -m unittest discover -s tests -q
python -m pip install playwright
python -m playwright install chromium
python tools/browser_check.py
python tools/check_edges.py
```

Local-first, maximum 32 saved travelers. Not a public account service. Keep browser cookies
for access to your role; there is no account recovery or avatar collision between players.
The world is a complete single-scene prologue, not a full RPG, multiplayer service, or map editor.
See [boundaries](docs/BOUNDARIES.md).
