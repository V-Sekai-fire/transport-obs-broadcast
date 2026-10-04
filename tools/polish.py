"""Unify OBS sources and lay every scene out on one grid. Idempotent; never touches outputs."""
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))


def obs(r, d=None, ok_fail=False):
    a = [sys.executable, os.path.join(here, 'obs_ctl.py'), r]
    if d is not None:
        a.append(json.dumps(d))
    rep = json.loads(subprocess.run(a, capture_output=True, text=True).stdout)
    if not rep['status']['result'] and not ok_fail:
        raise SystemExit(f'{r} {d}: {rep["status"]}')
    return rep.get('data') or {}


W, H = 1920, 1080
MARGIN = 48
BAR = 138                      # 1920 / 2.39 = 803.3 -> 804 visible rows, 138 above and below
PIP_W, PIP_H = 560, 315        # 16:9 content
BORDER = 2
FRAME_W, FRAME_H = PIP_W + 2 * BORDER, PIP_H + 2 * BORDER
FX, FY = W - MARGIN - FRAME_W, H - MARGIN - FRAME_H

BLACK = 0xFF000000
BACKDROP = 0xFF141210          # rgb(16,18,20), dark neutral
FRAME = 0x4DFFFFFF             # 30% white hairline
SHADOW = 0x40000000            # 25% black, stacked twice for a soft falloff

# Inputs: rename, create, settings
names = {i['inputName'] for i in obs('GetInputList')['inputs']}
if 'OpenVR Capture' in names and 'VR View' not in names:
    obs('SetInputName', {'inputName': 'OpenVR Capture', 'newInputName': 'VR View'})
obs('SetInputSettings', {'inputName': 'Game Window', 'overlay': True,
                         'inputSettings': {'window': 'Half-Life#3A Alyx:SDL_app:hlvr.exe'}})
obs('SetInputSettings', {'inputName': 'Backdrop', 'overlay': True,
                         'inputSettings': {'color': BACKDROP, 'width': W, 'height': H}})
obs('SetInputSettings', {'inputName': 'PiP Frame', 'overlay': True,
                         'inputSettings': {'color': FRAME, 'width': 16, 'height': 16}})
names = {i['inputName'] for i in obs('GetInputList')['inputs']}
for name, color, w, h, scene in (('Letterbox Bar', BLACK, W, BAR, 'VR Cinematic'),
                                 ('PiP Shadow', SHADOW, 16, 16, 'VR + Desk')):
    if name not in names:
        obs('CreateInput', {'sceneName': scene, 'inputName': name, 'inputKind': 'color_source_v3',
                            'inputSettings': {'color': color, 'width': w, 'height': h},
                            'sceneItemEnabled': True})
    else:
        obs('SetInputSettings', {'inputName': name, 'overlay': True,
                                 'inputSettings': {'color': color, 'width': w, 'height': h}})


def box(x, y, w, h, kind='OBS_BOUNDS_STRETCH', crop=False):
    return {'positionX': float(x), 'positionY': float(y), 'rotation': 0.0, 'scaleX': 1.0, 'scaleY': 1.0,
            'alignment': 5, 'boundsType': kind, 'boundsAlignment': 0,
            'boundsWidth': float(w), 'boundsHeight': float(h), 'cropToBounds': crop,
            'cropLeft': 0, 'cropRight': 0, 'cropTop': 0, 'cropBottom': 0}


FULL_FIT = box(0, 0, W, H, 'OBS_BOUNDS_SCALE_INNER')
VR_FULL = box(-96, -54, W * 1.1, H * 1.1, 'OBS_BOUNDS_SCALE_OUTER', True)   # centred 110% fill
PIP = [('PiP Shadow', box(FX - 12, FY - 8, FRAME_W + 24, FRAME_H + 24)),
       ('PiP Shadow', box(FX - 6, FY - 3, FRAME_W + 12, FRAME_H + 12)),
       ('PiP Frame', box(FX, FY, FRAME_W, BORDER)),
       ('PiP Frame', box(FX, FY + FRAME_H - BORDER, FRAME_W, BORDER)),
       ('PiP Frame', box(FX, FY + BORDER, BORDER, PIP_H)),
       ('PiP Frame', box(FX + FRAME_W - BORDER, FY + BORDER, BORDER, PIP_H)),
       (None, box(FX + BORDER, FY + BORDER, PIP_W, PIP_H, 'OBS_BOUNDS_SCALE_OUTER', True))]
BARS = [('Letterbox Bar', box(0, 0, W, BAR)), ('Letterbox Bar', box(0, H - BAR, W, BAR))]


def pip(content):
    return [(n or content, t) for n, t in PIP]


LAYOUT = {
    'Desk + VR': [('Backdrop', box(0, 0, W, H)), ('Game Window', FULL_FIT)] + pip('VR View'),
    'VR + Desk': [('Backdrop', box(0, 0, W, H)), ('VR View', VR_FULL)] + BARS + pip('XR Pilot'),
    'VR Cinematic': [('Backdrop', box(0, 0, W, H)), ('VR View', VR_FULL)] + BARS,
}

for scene, wanted in LAYOUT.items():
    items = obs('GetSceneItemList', {'sceneName': scene})['sceneItems']
    pool = {}
    for it in sorted(items, key=lambda i: i['sceneItemIndex']):
        pool.setdefault(it['sourceName'], []).append(it['sceneItemId'])
    order = []
    for name, t in wanted:
        ids = pool.get(name, [])
        item_id = ids.pop(0) if ids else obs('CreateSceneItem', {'sceneName': scene, 'sourceName': name})['sceneItemId']
        obs('SetSceneItemTransform', {'sceneName': scene, 'sceneItemId': item_id, 'sceneItemTransform': t})
        obs('SetSceneItemEnabled', {'sceneName': scene, 'sceneItemId': item_id, 'sceneItemEnabled': True})
        order.append(item_id)
    for name, ids in pool.items():
        for item_id in ids:
            obs('RemoveSceneItem', {'sceneName': scene, 'sceneItemId': item_id})
            print(f'{scene}: removed extra {name} #{item_id}')
    for idx, item_id in enumerate(order):
        obs('SetSceneItemIndex', {'sceneName': scene, 'sceneItemId': item_id, 'sceneItemIndex': idx})
    print(scene, 'ok', [n for n, _ in wanted])
