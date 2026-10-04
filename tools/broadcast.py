"""Build the Broadcast scene: three nested full-frame main views plus the shared PiP. Idempotent."""
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))


def obs(r, d=None):
    a = [sys.executable, os.path.join(here, 'obs_ctl.py'), r]
    if d is not None:
        a.append(json.dumps(d))
    rep = json.loads(subprocess.run(a, capture_output=True, text=True).stdout)
    if not rep['status']['result']:
        raise SystemExit(f'{r} {d}: {rep["status"]}')
    return rep.get('data') or {}


W, H, MARGIN, PIP_W, PIP_H, BORDER = 1920, 1080, 48, 560, 315, 2
FRAME_W, FRAME_H = PIP_W + 2 * BORDER, PIP_H + 2 * BORDER
FX, FY = W - MARGIN - FRAME_W, H - MARGIN - FRAME_H


def box(x, y, w, h, kind='OBS_BOUNDS_STRETCH', crop=False):
    return {'positionX': float(x), 'positionY': float(y), 'rotation': 0.0, 'scaleX': 1.0, 'scaleY': 1.0,
            'alignment': 5, 'boundsType': kind, 'boundsAlignment': 0,
            'boundsWidth': float(w), 'boundsHeight': float(h), 'cropToBounds': crop,
            'cropLeft': 0, 'cropRight': 0, 'cropTop': 0, 'cropBottom': 0}


FULL_FIT = box(0, 0, W, H, 'OBS_BOUNDS_SCALE_INNER')
VR_FULL = box(-96, -54, W * 1.1, H * 1.1, 'OBS_BOUNDS_SCALE_OUTER', True)
PIP_CONTENT = box(FX + BORDER, FY + BORDER, PIP_W, PIP_H, 'OBS_BOUNDS_SCALE_OUTER', True)
PIP = [('PiP Shadow', box(FX - 12, FY - 8, FRAME_W + 24, FRAME_H + 24), True),
       ('PiP Shadow', box(FX - 6, FY - 3, FRAME_W + 12, FRAME_H + 12), True),
       ('PiP Frame', box(FX, FY, FRAME_W, BORDER), True),
       ('PiP Frame', box(FX, FY + FRAME_H - BORDER, FRAME_W, BORDER), True),
       ('PiP Frame', box(FX, FY + BORDER, BORDER, PIP_H), True),
       ('PiP Frame', box(FX + FRAME_W - BORDER, FY + BORDER, BORDER, PIP_H), True),
       ('XR Pilot', PIP_CONTENT, True),
       ('VR View', PIP_CONTENT, False)]
NESTED = box(0, 0, W, H)

LAYOUT = {
    'Main · VR': [('Backdrop', box(0, 0, W, H), True), ('VR View', VR_FULL, True)],
    'Main · Game': [('Backdrop', box(0, 0, W, H), True), ('Game Window', FULL_FIT, True)],
    'Main · Pilot': [('Backdrop', box(0, 0, W, H), True), ('XR Pilot', FULL_FIT, True)],
    'Broadcast': [('Main · VR', NESTED, True), ('Main · Game', NESTED, False), ('Main · Pilot', NESTED, False)] + PIP,
}

existing = {s['sceneName'] for s in obs('GetSceneList')['scenes']}
for scene in LAYOUT:
    if scene not in existing:
        obs('CreateScene', {'sceneName': scene})

for scene, wanted in LAYOUT.items():
    items = obs('GetSceneItemList', {'sceneName': scene})['sceneItems']
    pool = {}
    for it in sorted(items, key=lambda i: i['sceneItemIndex']):
        pool.setdefault(it['sourceName'], []).append(it['sceneItemId'])
    order = []
    for name, t, enabled in wanted:
        ids = pool.get(name, [])
        item_id = ids.pop(0) if ids else obs('CreateSceneItem', {'sceneName': scene, 'sourceName': name})['sceneItemId']
        obs('SetSceneItemTransform', {'sceneName': scene, 'sceneItemId': item_id, 'sceneItemTransform': t})
        obs('SetSceneItemEnabled', {'sceneName': scene, 'sceneItemId': item_id, 'sceneItemEnabled': enabled})
        order.append(item_id)
    for name, ids in pool.items():
        for item_id in ids:
            obs('RemoveSceneItem', {'sceneName': scene, 'sceneItemId': item_id})
    for idx, item_id in enumerate(order):
        obs('SetSceneItemIndex', {'sceneName': scene, 'sceneItemId': item_id, 'sceneItemIndex': idx})
    print(scene, [n for n, _, _ in wanted])

obs('SetCurrentProgramScene', {'sceneName': 'Broadcast'})
print('program scene: Broadcast')
