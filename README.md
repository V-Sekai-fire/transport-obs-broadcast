# transport-obs-broadcast

The desk's broadcast: its saved scene collection and the scripts that lay it out, switch its views and repair it over a WebSocket.

## What it is for

The scene collection restores the broadcast into a fresh install. The scripts build a broadcast scene of switchable full-frame views with a shared picture-in-picture, re-target a window capture after its window restarts, and save a still of any source. The layout scripts, `broadcast.py` and `polish.py`, are idempotent and leave recording and streaming alone.

## Build and run

The scripts need only the Python standard library and reach the running broadcast software through its own WebSocket settings. They read the WebSocket password from the broadcast software's plugin config, by default under the home directory's scoop-persisted config; set `OBS_CONFIG` to that config directory on any other install. Lay out the broadcast with:

    python tools/broadcast.py

## Licence

Apache-2.0 OR MIT; see `LICENSE-APACHE` and `LICENSE-MIT`.
