"""obs_shot.py <source> <out.png>: saves what an OBS source or scene shows to a PNG."""
import json
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.abspath(sys.argv[2])
request = {"sourceName": sys.argv[1], "imageFormat": "png", "imageWidth": 1280, "imageFilePath": out}
result = subprocess.run([sys.executable, os.path.join(here, 'obs_ctl.py'), 'SaveSourceScreenshot', json.dumps(request)],
                        capture_output=True, text=True)
print(result.stdout.strip()[-200:], result.stderr.strip()[-200:])
