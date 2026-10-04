"""obs_switch.py <vr|game|pilot>: picks Broadcast's full-frame main view; the PiP shows XR Pilot, or VR View when Pilot is main."""
import json, os, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
MAINS = {'vr': 'Main · VR', 'game': 'Main · Game', 'pilot': 'Main · Pilot'}
SOURCE = {'vr': 'VR View', 'game': 'Game Window', 'pilot': 'XR Pilot'}


def obs(r, d=None):
    a = [sys.executable, os.path.join(here, 'obs_ctl.py'), r]
    if d is not None:
        a.append(json.dumps(d))
    rep = json.loads(subprocess.run(a, capture_output=True, text=True, encoding='utf-8').stdout)
    if not rep['status']['result']:
        raise SystemExit(f'{r} {d}: {rep["status"]}')
    return rep.get('data') or {}


if len(sys.argv) != 2 or sys.argv[1] not in MAINS:
    raise SystemExit('usage: obs_switch.py <vr|game|pilot>')
choice = sys.argv[1]
pip_source = 'VR View' if choice == 'pilot' else 'XR Pilot'

items = obs('GetSceneItemList', {'sceneName': 'Broadcast'})['sceneItems']
mains = {i['sourceName']: i['sceneItemId'] for i in items if i['sourceName'] in MAINS.values()}
pips = {i['sourceName']: i['sceneItemId'] for i in items if i['sourceName'] in ('XR Pilot', 'VR View')}
missing = [n for n in MAINS.values() if n not in mains] + [n for n in ('XR Pilot', 'VR View') if n not in pips]
if missing:
    raise SystemExit(f'Broadcast is missing {missing}')

# Show the new layers before hiding the old ones, so no frame is empty.
obs('SetSceneItemEnabled', {'sceneName': 'Broadcast', 'sceneItemId': mains[MAINS[choice]], 'sceneItemEnabled': True})
obs('SetSceneItemEnabled', {'sceneName': 'Broadcast', 'sceneItemId': pips[pip_source], 'sceneItemEnabled': True})
for name, item_id in mains.items():
    if name != MAINS[choice]:
        obs('SetSceneItemEnabled', {'sceneName': 'Broadcast', 'sceneItemId': item_id, 'sceneItemEnabled': False})
for name, item_id in pips.items():
    if name != pip_source:
        obs('SetSceneItemEnabled', {'sceneName': 'Broadcast', 'sceneItemId': item_id, 'sceneItemEnabled': False})

time.sleep(1.0)
main_items = obs('GetSceneItemList', {'sceneName': MAINS[choice]})['sceneItems']
t = next(i for i in main_items if i['sourceName'] == SOURCE[choice])['sceneItemTransform']
size = f"{t['sourceWidth']:.0f}x{t['sourceHeight']:.0f}"
status = 'capturing' if t['sourceWidth'] > 0 else 'NOT CAPTURING (source is 0x0)'
print(json.dumps({'main': MAINS[choice], 'source': SOURCE[choice], 'size': size, 'status': status, 'pip': pip_source}))
sys.exit(0 if t['sourceWidth'] > 0 else 1)
