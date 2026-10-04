"""obs_rebind.py <input> <window spec>: re-applies a window capture's target so OBS finds a restarted window."""
import json
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))


def obs(request, data):
    out = subprocess.run([sys.executable, os.path.join(here, 'obs_ctl.py'), request, json.dumps(data)],
                         capture_output=True, text=True).stdout
    return json.loads(out)


name, window = sys.argv[1], sys.argv[2]
print(obs('SetInputSettings', {'inputName': name, 'overlay': True, 'inputSettings': {'window': ''}})['status'])
print(obs('SetInputSettings', {'inputName': name, 'overlay': True, 'inputSettings': {'window': window}})['status'])
