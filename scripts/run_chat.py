"""Start the built UI and API together on loopback; no secrets printed."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

def main():
    if not (ROOT / 'apps/web/dist/index.html').is_file():
        raise SystemExit('Build the frontend first: npm --prefix apps/web ci && npm --prefix apps/web run build')
    import uvicorn
    uvicorn.run('apps.api.main:app', host='0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1',
                port=int(os.environ.get('PORT', '8000')), workers=1, log_level='info')


if __name__ == '__main__':
    main()
