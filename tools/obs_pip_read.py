"""Enlarges the VR + Desk PiP and crops the terminal to its recent output so its text is readable."""
import json, subprocess, sys
S = "VR + Desk"
def req(t, d):
    r = json.loads(subprocess.run([sys.executable, "obs_ctl.py", t, json.dumps(d)], capture_output=True, text=True).stdout)
    assert r["status"]["result"], (t, d, r)
def put(i, x, y, w, h, extra=None):
    tr = {"positionX": x, "positionY": y, "boundsWidth": w, "boundsHeight": h}
    tr.update(extra or {})
    req("SetSceneItemTransform", {"sceneName": S, "sceneItemId": i, "sceneItemTransform": tr})
fw, fh = 500, 285
fx, fy = 10, 1080 - 60 - fh
put(5, fx - 12, fy - 8, fw + 24, fh + 24)
put(6, fx - 6, fy - 3, fw + 12, fh + 12)
put(7, fx, fy, fw - 2, 2)
put(8, fx, fy + fh - 2, fw - 2, 2)
put(9, fx, fy + 2, 2, fh - 4)
put(10, fx + fw - 2, fy + 2, 2, fh - 4)
put(11, fx + 3, fy + 1, fw - 5, fh - 3, {"cropTop": 900, "cropRight": 1840, "cropLeft": 0, "cropBottom": 0})
print("ok", fx, fy)
