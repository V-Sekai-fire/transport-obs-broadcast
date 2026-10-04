# transport-obs-broadcast

The desk's OBS broadcast: its scene collection and the obs-websocket scripts that lay out, switch and repair it.

## What is here

- `scenes/desk.json` is the scene collection as OBS saved it, so it can be restored into a fresh
  OBS: copy it to `basic/scenes/` in the OBS config directory under the collection's name.
- `tools/obs_ctl.py <RequestType> [json]` sends one obs-websocket v5 request and prints the
  reply. Everything else is built on it. It reads the server's port and password from OBS's own
  websocket config; set `OBS_CONFIG` when OBS is not a scoop install.
- `tools/polish.py` puts every scene on one grid with unified sources.
- `tools/broadcast.py` builds the Broadcast scene: three switchable full-frame views and a
  shared picture-in-picture.
- `tools/obs_switch.py <vr|game|pilot>` picks Broadcast's main view.
- `tools/obs_pip_read.py` sizes and crops the terminal picture-in-picture so its text reads.
- `tools/obs_rebind.py <input> <window>` re-targets a window capture after the window restarts.
- `tools/obs_shot.py <source> <out.png>` saves what a source or scene shows.

Every script is idempotent and leaves outputs (recording, streaming) alone.
