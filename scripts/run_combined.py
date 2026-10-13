"""Start the built chat UI with the verified combined knowledge route."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def main():
    if not (ROOT / 'apps/web/dist/index.html').is_file():
        raise SystemExit('Build the frontend first: npm --prefix apps/web run build')
    from scripts.combined_runtime import knowledge_server
    import uvicorn

    with knowledge_server() as (url, token):
        os.environ.update(FSIE_AGENT_ORCHESTRATION='hybrid', FSIE_AGENT_PROVIDER='combined',
                          FSIE_AGENT_C_URL=url, FSIE_AGENT_C_TOKEN=token)
        uvicorn.run('apps.api.main:app', host='127.0.0.1', port=8000, log_level='info')


if __name__ == '__main__':
    main()
